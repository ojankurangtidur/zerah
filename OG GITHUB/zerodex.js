const Web3 = require('web3');
const fs = require('fs');
const chalk = require('chalk');
const { HttpsProxyAgent } = require('https-proxy-agent');

// Proxy variables
let proxies = [];
let currentProxyIndex = 0;
let web3;

// Token configuration
const TOKENS = [
    { 
        address: '0x9A87C2412d500343c073E5Ae5394E3bE3874F76b',
        symbol: 'USDT'
    },
    {
        address: '0xce830d0905e0f7a9b300401729761579c5fb6bd6',
        symbol: 'ETH'
    },
    {
        address: '0x1E0D871472973c562650E991ED8006549F8CBEfc',
        symbol: 'BTC'
    }
];

// Contract addresses
const ROUTER_ADDRESS = '0xe233d75ce6f04c04610947188dec7c55790bef3b';
const POOL_ADDRESS = '0x62DF0E43e599a279015fFCFf70c2cF82bD19D69A';
const POOL_FEE = 3000;
const MAX_ALLOWANCE = '0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff';

// ABI definitions
const erc20ABI = [
    {
        "constant": true,
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": false,
        "type": "function"
    },
    {
        "constant": false,
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": false,
        "stateMutability": "nonpayable",
        "type": "function"
    }
];

const routerABI = [
    {
        "inputs": [
            { 
                "name": "params", 
                "type": "tuple", 
                "components": [
                    {"name": "tokenIn", "type": "address"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "fee", "type": "uint24"},
                    {"name": "recipient", "type": "address"},
                    {"name": "deadline", "type": "uint256"},
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "amountOutMinimum", "type": "uint256"},
                    {"name": "sqrtPriceLimitX96", "type": "uint160"}
                ]
            }
        ],
        "name": "exactInputSingle",
        "outputs": [{"name": "amountOut", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
];

// Utility functions
function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
}

function getNextProxy() {
    if (proxies.length === 0) return null;
    const proxy = proxies[currentProxyIndex];
    currentProxyIndex = (currentProxyIndex + 1) % proxies.length;
    return proxy;
}

function initializeWeb3WithProxy(proxyUrl) {
    const providerOptions = proxyUrl ? { agent: new HttpsProxyAgent(proxyUrl) } : {};
    return new Web3(new Web3.providers.HttpProvider('https://evmrpc-testnet.0g.ai', providerOptions));
}

async function approveUnlimited(privateKey, tokenAddress) {
    const account = web3.eth.accounts.privateKeyToAccount(privateKey);
    const walletAddress = account.address;
    const tokenContract = new web3.eth.Contract(erc20ABI, tokenAddress);
    
    const token = TOKENS.find(t => t.address.toLowerCase() === tokenAddress.toLowerCase());
    const symbol = token ? token.symbol : tokenAddress;

    console.log(chalk.blue(`🚀 Approving unlimited ${symbol}...`));
    
    const txData = tokenContract.methods.approve(ROUTER_ADDRESS, MAX_ALLOWANCE).encodeABI();
    
    const gasEstimate = await tokenContract.methods.approve(
        ROUTER_ADDRESS, 
        MAX_ALLOWANCE
    ).estimateGas({ from: walletAddress });

    const tx = {
        to: tokenAddress,
        data: txData,
        gas: Math.floor(gasEstimate * 1.2),
        gasPrice: await web3.eth.getGasPrice(),
        nonce: await web3.eth.getTransactionCount(walletAddress, 'pending'),
        chainId: 16600
    };
    
    const signedTx = await web3.eth.accounts.signTransaction(tx, privateKey);
    const receipt = await web3.eth.sendSignedTransaction(signedTx.rawTransaction);
    console.log(chalk.green(`✅ Approval complete: ${receipt.transactionHash}`));
    return receipt;
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function checkBalance(walletAddress, tokenAddress) {
    const tokenContract = new web3.eth.Contract(erc20ABI, tokenAddress);
    const balance = await tokenContract.methods.balanceOf(walletAddress).call();
    return balance;
}

async function checkGasBalance(walletAddress) {
    const balance = await web3.eth.getBalance(walletAddress);
    return balance;
}

function logInfo(message) {
    console.log(chalk.blue(`[●] ${message}`));
}

function logSuccess(message) {
    console.log(chalk.greenBright(`[✓] ${message}`));
}

function logError(message) {
    console.log(chalk.red(`[✗] ${message}`));
}

function logWarning(message) {
    console.log(chalk.yellow(`[!] ${message}`));
}

async function executeTradeWithRetry(privateKey, retries = 3) {
    let attempt = 0;
    const account = web3.eth.accounts.privateKeyToAccount(privateKey);
    const walletAddress = account.address;
    
    while (attempt < retries) {
        try {
            logInfo(`Starting trade for wallet: ${walletAddress}`);
            
            const gasBalance = await checkGasBalance(walletAddress);
            if (web3.utils.toBN(gasBalance).lt(web3.utils.toBN(web3.utils.toWei('0.01', 'ether')))) {
                logWarning(`Insufficient gas (${web3.utils.fromWei(gasBalance, 'ether')} 0G)`);
                return;
            }

            await executeTrade(privateKey);
            logSuccess(`Trade successful for wallet: ${walletAddress}`);
            return;
        } catch (error) {
            attempt++;
            logError(`Attempt ${attempt} failed: ${error.message}`);
            if (attempt < retries) {
                await sleep(3000);
            }
        }
    }
    logError(`All attempts failed for wallet: ${walletAddress}`);
}

async function executeTrade(privateKey) {
    const account = web3.eth.accounts.privateKeyToAccount(privateKey);
    const walletAddress = account.address;
    const deadline = Math.floor(Date.now() / 1000) + 60 * 30;

    const [tokenInInfo, tokenOutInfo] = shuffleArray([...TOKENS]).slice(0, 2);
    logInfo(`Trading ${tokenInInfo.symbol} → ${tokenOutInfo.symbol}`);

    const tokenContract = new web3.eth.Contract(erc20ABI, tokenInInfo.address);
    const currentAllowance = await tokenContract.methods.allowance(walletAddress, ROUTER_ADDRESS).call();

    if (web3.utils.toBN(currentAllowance).lt(web3.utils.toBN(MAX_ALLOWANCE).div(web3.utils.toBN(2)))) {
        logInfo(`Approving ${tokenInInfo.symbol}...`);
        await approveUnlimited(privateKey, tokenInInfo.address);
        await sleep(2000);
    }

    const balance = await tokenContract.methods.balanceOf(walletAddress).call();
    const amountIn = web3.utils.toBN(balance).div(web3.utils.toBN(20));
    
    if (amountIn.isZero()) {
        throw new Error(`Insufficient ${tokenInInfo.symbol} balance`);
    }

    logInfo(`Swapping ${web3.utils.fromWei(amountIn, 'ether')} ${tokenInInfo.symbol}`);

    const router = new web3.eth.Contract(routerABI, ROUTER_ADDRESS);
    const params = [
        tokenInInfo.address,
        tokenOutInfo.address,
        POOL_FEE,
        walletAddress,
        deadline,
        amountIn.toString(),
        "0", // amountOutMinimum
        0    // sqrtPriceLimitX96
    ];

    const gasEstimate = await router.methods.exactInputSingle(params).estimateGas({ from: walletAddress });
    const txData = router.methods.exactInputSingle(params).encodeABI();

    const tx = {
        to: ROUTER_ADDRESS,
        data: txData,
        gas: Math.floor(gasEstimate * 1.3),
        gasPrice: await web3.eth.getGasPrice(),
        nonce: await web3.eth.getTransactionCount(walletAddress, 'pending'),
        chainId: 16600
    };

    const signedTx = await web3.eth.accounts.signTransaction(tx, privateKey);
    const receipt = await web3.eth.sendSignedTransaction(signedTx.rawTransaction);

    logSuccess(`Swap successful! TX: ${receipt.transactionHash}`);
}

async function processWallets() {
    const privateKeys = fs.readFileSync('privatekey.txt', 'utf-8')
        .split('\n')
        .map(line => line.trim())
        .filter(Boolean);

    logInfo(`Processing ${privateKeys.length} wallets`);

    for (let i = 0; i < privateKeys.length; i++) {
        const privateKey = privateKeys[i];
        const proxy = getNextProxy();
        web3 = initializeWeb3WithProxy(proxy);
        if (proxy) logInfo(`Using proxy: ${proxy}`);

        const account = web3.eth.accounts.privateKeyToAccount(privateKey);
        const walletAddress = account.address;
        
        // Enhanced wallet progress logging
        logInfo(`Processing wallet [${i+1}/${privateKeys.length}]: ${walletAddress.substring(0, 6)}...${walletAddress.substring(walletAddress.length - 4)}`);

        try {
            for (let j = 0; j < 5; j++) {
                logInfo(`[Wallet ${i+1}/${privateKeys.length}] Swap ${j + 1}/5`);
                await executeTradeWithRetry(privateKey);
                
                // Add delay between swaps
                const swapDelay = Math.floor(Math.random() * 10000) + 5000;
                await sleep(swapDelay);
            }
        } catch (error) {
            logError(`[Wallet ${i+1}/${privateKeys.length}] Processing failed: ${error.message}`);
        }

        const delay = Math.floor(Math.random() * 30000) + 30000;
        logInfo(`[Wallet ${i+1}/${privateKeys.length}] Waiting ${Math.floor(delay / 1000)} seconds before next wallet...`);
        await sleep(delay);
    }

    logInfo('Completed all wallets. Restarting in 1 hour...');
    setTimeout(processWallets, 3600000);
}

function printHeader() {
    console.log(chalk.green('=================================================='));
    console.log(chalk.green('           Auto Daily Swap 0G Labs v2.2           '));
    console.log(chalk.green('       Updated Proxy Support - Zer0dex Swap       '));
    console.log(chalk.green('=================================================='));
}

async function startScript() {
    printHeader();

    // Load proxies
    if (fs.existsSync('proxies.txt')) {
        proxies = fs.readFileSync('proxies.txt', 'utf-8')
            .split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0);
        logInfo(`Loaded ${proxies.length} proxies`);
    }

    // Verify private keys
    if (!fs.existsSync('privatekey.txt')) {
        logError('privatekey.txt not found!');
        return;
    }

    try {
        await processWallets();
    } catch (error) {
        logError(`Fatal error: ${error.message}`);
        logInfo('Restarting in 5 minutes...');
        setTimeout(startScript, 300000);
    }
}

// Verify dependencies
try {
    require('web3');
    require('chalk');
    require('https-proxy-agent');
    startScript();
} catch (e) {
    console.error('Missing dependencies. Please run:');
    console.error('npm install web3 chalk https-proxy-agent');
    process.exit(1);
}