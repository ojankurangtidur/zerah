
# Online IDE - Code Editor, Compiler, Interpreter

print('Welcome to Online IDE!! Happy Coding :)')
from web3 import Web3
from eth_account import Account
import json
import random
import time
import datetime
import requests
from colorama import Fore, Back, Style, init
import threading
from threading import Semaphore

# Inisialisasi colorama
init(autoreset=True)

# Konfigurasi User Agent dan Headers
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
]

def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Connection": "keep-alive"
    }

# Fungsi untuk membuat teks pelangi
def rainbow_text(text):
    colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]
    rainbow = ""
    for i, char in enumerate(text):
        rainbow += colors[i % len(colors)] + Style.BRIGHT + char
    return rainbow + Style.RESET_ALL

# Header yang lebih sederhana dengan warna kuning
def print_sky_header():
    width = 50
    print(f"{Fore.CYAN}{'='*width}{Style.RESET_ALL}")
    
    # Teks di tengah dengan warna kuning
    title = "0G HUB Swapper"
    padding = (width - len(title)) // 2
    print(" " * padding + f"{Fore.YELLOW}{Style.BRIGHT}{title}{Style.RESET_ALL}")
    
    author = "By : SKY"
    padding = (width - len(author)) // 2
    print(" " * padding + f"{Fore.YELLOW}{Style.BRIGHT}{author}{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}{'='*width}{Style.RESET_ALL}")

# Daftar RPC yang tersedia
RPC_ENDPOINTS = [
    "https://evmrpc-testnet.0g.ai",  
    "https://og-testnet-evm.itrocket.net"  # RPC alternatif
]

# Baca ABI dari file abi.js
def load_abi_from_js():
    try:
        import json
        import re
        
        with open('abi.js', 'r') as file:
            js_content = file.read()
            
        # Ekstrak ROUTER_ABI menggunakan regex
        router_match = re.search(r'const ROUTER_ABI = (\[[\s\S]*?\]);', js_content)
        if router_match:
            router_abi_str = router_match.group(1)
            # Bersihkan string dari komentar JavaScript
            router_abi_str = re.sub(r'//.*?\n', '\n', router_abi_str)
            router_abi = json.loads(router_abi_str)
        else:
            raise Exception("ROUTER_ABI tidak ditemukan di abi.js")
            
        # Ekstrak USDT_ABI menggunakan regex
        usdt_match = re.search(r'const USDT_ABI = (\[[\s\S]*?\]);', js_content)
        if usdt_match:
            usdt_abi_str = usdt_match.group(1)
            # Bersihkan string dari komentar JavaScript
            usdt_abi_str = re.sub(r'//.*?\n', '\n', usdt_abi_str)
            usdt_abi = json.loads(usdt_abi_str)
        else:
            raise Exception("USDT_ABI tidak ditemukan di abi.js")
            
        # Ekstrak ETH_ABI menggunakan regex
        eth_match = re.search(r'const ETH_ABI = (\[[\s\S]*?\]);', js_content)
        if eth_match:
            eth_abi_str = eth_match.group(1)
            # Bersihkan string dari komentar JavaScript
            eth_abi_str = re.sub(r'//.*?\n', '\n', eth_abi_str)
            eth_abi = json.loads(eth_abi_str)
        else:
            raise Exception("ETH_ABI tidak ditemukan di abi.js")
            
        return {
            'router_abi': router_abi,
            'usdt_abi': usdt_abi,
            'eth_abi': eth_abi
        }
    except Exception as e:
        print(f"{Fore.RED}Error saat memuat ABI dari abi.js: {str(e)}{Style.RESET_ALL}")
        raise Exception(f"Gagal memuat ABI dari file abi.js: {str(e)}")

class TokenSwapper:
    def __init__(self, session=None):
        self.session = session or requests.Session()
        self.current_rpc_index = 0  # Indeks RPC yang sedang digunakan
        self.web3 = self.initialize_web3()
        # Inisialisasi koneksi ke RPC 0G-Newton-Testnet dengan headers
        self.headers = get_random_headers()
        
        # Buat provider dengan headers kustom
        provider = Web3.HTTPProvider('https://og-testnet-evm.itrocket.net', request_kwargs={'headers': self.headers})
        self.w3 = Web3(provider)
        
        # Verifikasi koneksi ke jaringan yang benar
        if self.w3.eth.chain_id != 16600:
            raise Exception("Koneksi tidak terhubung ke 0G-Newton-Testnet")
            
        # Muat ABI dari file abi.js
        abis = load_abi_from_js()
        
        # Detail kontrak DEX
        self.router_address = "0xD86b764618c6E3C078845BE3c3fCe50CE9535Da7" 
        self.router_abi = abis['router_abi']
        
        # Detail token dengan alamat yang benar
        self.usdt_address = Web3.to_checksum_address("0x9A87C2412d500343c073E5Ae5394E3bE3874F76b")
        self.eth_address = Web3.to_checksum_address("0xce830D0905e0f7A9b300401729761579c5FB6bd6")
        
        # Simpan ABI token
        self.usdt_abi = abis['usdt_abi']
        self.eth_abi = abis['eth_abi']
        
        # Tambahkan alamat token BTC
        self.btc_address = Web3.to_checksum_address("0x922D8563631B03C2c4cf817f4d18f6883AbA0109")
        
        # Simpan ABI token BTC (menggunakan ABI yang sama dengan ETH)
        self.btc_abi = abis['eth_abi']
        
    def initialize_web3(self):
        """Inisialisasi objek Web3 dengan RPC yang sedang aktif"""
        current_rpc = RPC_ENDPOINTS[self.current_rpc_index]
        print(f"{Fore.BLUE}Menggunakan RPC: {current_rpc}{Style.RESET_ALL}")
        return Web3(Web3.HTTPProvider(current_rpc))
    
    def switch_rpc(self):
        """Beralih ke RPC alternatif jika terjadi error"""
        self.current_rpc_index = (self.current_rpc_index + 1) % len(RPC_ENDPOINTS)
        print(f"{Fore.YELLOW}Beralih ke RPC alternatif: {RPC_ENDPOINTS[self.current_rpc_index]}{Style.RESET_ALL}")
        self.web3 = self.initialize_web3()
    
    def handle_transaction_error(self, error_message):
        """Menangani error transaksi dan mencoba beralih RPC jika diperlukan"""
        if isinstance(error_message, dict) and 'message' in error_message:
            error_text = error_message['message']
        else:
            error_text = str(error_message)
        
        # Cek apakah error adalah "mempool is full"
        if 'mempool is full' in error_text.lower():
            print(f"{Fore.YELLOW}Error: Mempool penuh. Mencoba beralih ke RPC alternatif...{Style.RESET_ALL}")
            self.switch_rpc()
            return True  
        
        return False 
    
    def swap_usdt_to_eth(self, private_key, amount_in):
        try:
            # Perbarui headers dengan membuat provider baru
            self.headers = get_random_headers()
            provider = Web3.HTTPProvider('https://og-testnet-evm.itrocket.net', request_kwargs={'headers': self.headers})
            self.w3 = Web3(provider)
            
            # Buat instance akun
            if private_key.startswith('0x'):
                private_key_bytes = bytes.fromhex(private_key[2:])
            else:
                private_key_bytes = bytes.fromhex(private_key)
                
            account = Account.from_key(private_key_bytes)
            
            time.sleep(2)
            current_nonce = self.w3.eth.get_transaction_count(account.address, 'pending')
            print(f"{Fore.YELLOW}Menggunakan nonce {current_nonce} untuk approval USDT{Style.RESET_ALL}")
            
            # Approve USDT
            usdt_contract = self.w3.eth.contract(address=self.usdt_address, abi=self.usdt_abi)
            
            approve_tx = usdt_contract.functions.approve(
                self.router_address,
                amount_in
            ).build_transaction({
                'from': account.address,
                'nonce': current_nonce,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id
            })
            
            # Sign dan kirim transaksi approval dengan cara yang benar
            signed_tx = self.w3.eth.account.sign_transaction(approve_tx, private_key_bytes)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            # Tunggu transaksi dengan timeout yang lebih lama (300 detik)
            try:
                print(f"{Fore.YELLOW}Menunggu konfirmasi approval USDT (timeout: 300 detik)...{Style.RESET_ALL}")
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
                print(f"{Fore.GREEN}Approval USDT berhasil dikonfirmasi!{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Timeout menunggu konfirmasi approval USDT: {str(e)}{Style.RESET_ALL}")
                # Coba beralih ke RPC alternatif
                self.switch_rpc()
                raise Exception(f"Timeout menunggu konfirmasi approval USDT: {str(e)}")
            
            # Tunggu sedikit untuk memastikan blockchain sudah diperbarui
            time.sleep(10)
            
            # Dapatkan nonce baru setelah transaksi approval
            current_nonce = self.w3.eth.get_transaction_count(account.address, 'pending')
            print(f"{Fore.YELLOW}Menggunakan nonce {current_nonce} untuk swap USDT ke ETH{Style.RESET_ALL}")
            
            # Swap tokens
            router_contract = self.w3.eth.contract(address=self.router_address, abi=self.router_abi)
            deadline = self.w3.eth.get_block('latest').timestamp + 300
            
            params = {
                'tokenIn': self.usdt_address,
                'tokenOut': self.eth_address,
                'fee': 3000,  # 0.3%
                'recipient': account.address,
                'deadline': deadline,
                'amountIn': amount_in,
                'amountOutMinimum': 0,  # Untuk testing
                'sqrtPriceLimitX96': 0
            }
            
            swap_tx = router_contract.functions.exactInputSingle(
                params
            ).build_transaction({
                'from': account.address,
                'nonce': current_nonce,
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id
            })
            
            # Sign dan kirim transaksi swap
            signed_swap = self.w3.eth.account.sign_transaction(swap_tx, private_key_bytes)
            swap_tx_hash = self.w3.eth.send_raw_transaction(signed_swap.raw_transaction)
            
            # Tunggu transaksi dengan timeout yang lebih lama (300 detik)
            try:
                print(f"{Fore.YELLOW}Menunggu konfirmasi swap USDT ke ETH (timeout: 300 detik)...{Style.RESET_ALL}")
                receipt = self.w3.eth.wait_for_transaction_receipt(swap_tx_hash, timeout=300)
                print(f"{Fore.GREEN}Swap USDT ke ETH berhasil dikonfirmasi!{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Timeout menunggu konfirmasi swap USDT ke ETH: {str(e)}{Style.RESET_ALL}")
                # Coba beralih ke RPC alternatif
                self.switch_rpc()
                raise Exception(f"Timeout menunggu konfirmasi swap USDT ke ETH: {str(e)}")
            
            return {
                'status': 'success',
                'transaction_hash': swap_tx_hash.hex(),
                'amount_in': amount_in
            }
            
        except Exception as e:
            error_message = str(e)
            
            # Coba ekstrak error JSON jika ada
            try:
                if 'message' in error_message and '{' in error_message:
                    error_json_str = error_message[error_message.find('{'):error_message.rfind('}')+1]
                    error_json = json.loads(error_json_str)
                    
                    # Cek apakah perlu beralih RPC
                    if self.handle_transaction_error(error_json):
                        return self.swap_usdt_to_eth(private_key, amount_in)
            except:
                pass
            
            # Jika error bukan "mempool is full" atau gagal parsing JSON
            return {
                'status': 'error',
                'message': str(e)
            }

    def swap_eth_to_usdt(self, private_key, amount_in):
        try:
            # Perbarui headers dengan membuat provider baru
            self.headers = get_random_headers()
            provider = Web3.HTTPProvider('https://og-testnet-evm.itrocket.net', request_kwargs={'headers': self.headers})
            self.w3 = Web3(provider)
            
            # Buat instance akun
            if private_key.startswith('0x'):
                private_key_bytes = bytes.fromhex(private_key[2:])
            else:
                private_key_bytes = bytes.fromhex(private_key)
                
            account = Account.from_key(private_key_bytes)
            
            # Tunggu sedikit untuk memastikan blockchain sudah diperbarui
            time.sleep(2)
            
            # Dapatkan nonce terbaru dengan memastikan transaksi sebelumnya sudah selesai
            current_nonce = self.w3.eth.get_transaction_count(account.address, 'pending')
            print(f"{Fore.YELLOW}Menggunakan nonce {current_nonce} untuk approval ETH{Style.RESET_ALL}")
            
            # Approve ETH
            eth_contract = self.w3.eth.contract(address=self.eth_address, abi=self.eth_abi)
            
            approve_tx = eth_contract.functions.approve(
                self.router_address,
                amount_in
            ).build_transaction({
                'from': account.address,
                'nonce': current_nonce,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id
            })
            
            # Sign dan kirim transaksi approval dengan cara yang benar
            signed_tx = self.w3.eth.account.sign_transaction(approve_tx, private_key_bytes)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            # Tunggu transaksi dengan timeout yang lebih lama (300 detik)
            try:
                print(f"{Fore.YELLOW}Menunggu konfirmasi approval ETH (timeout: 300 detik)...{Style.RESET_ALL}")
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
                print(f"{Fore.GREEN}Approval ETH berhasil dikonfirmasi!{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Timeout menunggu konfirmasi approval ETH: {str(e)}{Style.RESET_ALL}")
                # Coba beralih ke RPC alternatif
                self.switch_rpc()
                raise Exception(f"Timeout menunggu konfirmasi approval ETH: {str(e)}")
            
            # Tunggu sedikit untuk memastikan blockchain sudah diperbarui
            time.sleep(10)
            
            # Dapatkan nonce baru setelah transaksi approval
            current_nonce = self.w3.eth.get_transaction_count(account.address, 'pending')
            print(f"{Fore.YELLOW}Menggunakan nonce {current_nonce} untuk swap ETH ke USDT{Style.RESET_ALL}")
            
            # Swap tokens
            router_contract = self.w3.eth.contract(address=self.router_address, abi=self.router_abi)
            deadline = self.w3.eth.get_block('latest').timestamp + 300
            
            params = {
                'tokenIn': self.eth_address,
                'tokenOut': self.usdt_address,
                'fee': 3000,  # 0.3%
                'recipient': account.address,
                'deadline': deadline,
                'amountIn': amount_in,
                'amountOutMinimum': 0,  # Untuk testing
                'sqrtPriceLimitX96': 0
            }
            
            swap_tx = router_contract.functions.exactInputSingle(
                params
            ).build_transaction({
                'from': account.address,
                'nonce': current_nonce,
                'gas': 500000,  # Meningkatkan gas limit
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id
            })
            
            # Sign dan kirim transaksi swap
            signed_swap = self.w3.eth.account.sign_transaction(swap_tx, private_key_bytes)
            swap_tx_hash = self.w3.eth.send_raw_transaction(signed_swap.raw_transaction)
            
            # Tunggu transaksi dengan timeout yang lebih lama (300 detik)
            try:
                print(f"{Fore.YELLOW}Menunggu konfirmasi swap ETH ke USDT (timeout: 300 detik)...{Style.RESET_ALL}")
                receipt = self.w3.eth.wait_for_transaction_receipt(swap_tx_hash, timeout=300)
                print(f"{Fore.GREEN}Swap ETH ke USDT berhasil dikonfirmasi!{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Timeout menunggu konfirmasi swap ETH ke USDT: {str(e)}{Style.RESET_ALL}")
                # Coba beralih ke RPC alternatif
                self.switch_rpc()
                raise Exception(f"Timeout menunggu konfirmasi swap ETH ke USDT: {str(e)}")
            
            return {
                'status': 'success',
                'transaction_hash': swap_tx_hash.hex(),
                'amount_in': amount_in
            }
            
        except Exception as e:
            error_message = str(e)
            
            # Coba ekstrak error JSON jika ada
            try:
                if 'message' in error_message and '{' in error_message:
                    error_json_str = error_message[error_message.find('{'):error_message.rfind('}')+1]
                    error_json = json.loads(error_json_str)
                    
                    # Cek apakah perlu beralih RPC
                    if self.handle_transaction_error(error_json):
                        return self.swap_eth_to_usdt(private_key, amount_in)
            except:
                pass
            
            # Jika error bukan "mempool is full" atau gagal parsing JSON
            return {
                'status': 'error',
                'message': str(e)
            }

    def swap_usdt_to_btc(self, private_key, amount_in):
        try:
            # Perbarui headers dengan membuat provider baru
            self.headers = get_random_headers()
            provider = Web3.HTTPProvider('https://og-testnet-evm.itrocket.net', request_kwargs={'headers': self.headers})
            self.w3 = Web3(provider)
            
            # Buat instance akun
            if private_key.startswith('0x'):
                private_key_bytes = bytes.fromhex(private_key[2:])
            else:
                private_key_bytes = bytes.fromhex(private_key)
                
            account = Account.from_key(private_key_bytes)
            
            time.sleep(2)
            current_nonce = self.w3.eth.get_transaction_count(account.address, 'pending')
            print(f"{Fore.YELLOW}Menggunakan nonce {current_nonce} untuk approval USDT{Style.RESET_ALL}")
            
            # Approve USDT
            usdt_contract = self.w3.eth.contract(address=self.usdt_address, abi=self.usdt_abi)
            
            approve_tx = usdt_contract.functions.approve(
                self.router_address,
                amount_in
            ).build_transaction({
                'from': account.address,
                'nonce': current_nonce,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id
            })
            
            # Sign dan kirim transaksi approval
            signed_tx = self.w3.eth.account.sign_transaction(approve_tx, private_key_bytes)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            try:
                print(f"{Fore.YELLOW}Menunggu konfirmasi approval USDT (timeout: 300 detik)...{Style.RESET_ALL}")
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
                print(f"{Fore.GREEN}Approval USDT berhasil dikonfirmasi!{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Timeout menunggu konfirmasi approval USDT: {str(e)}{Style.RESET_ALL}")
                self.switch_rpc()
                raise Exception(f"Timeout menunggu konfirmasi approval USDT: {str(e)}")
            
            time.sleep(10)
            
            # Dapatkan nonce baru untuk swap
            current_nonce = self.w3.eth.get_transaction_count(account.address, 'pending')
            print(f"{Fore.YELLOW}Menggunakan nonce {current_nonce} untuk swap USDT ke BTC{Style.RESET_ALL}")
            
            # Swap USDT ke BTC
            router_contract = self.w3.eth.contract(address=self.router_address, abi=self.router_abi)
            deadline = self.w3.eth.get_block('latest').timestamp + 300
            
            params = {
                'tokenIn': self.usdt_address,
                'tokenOut': self.btc_address,
                'fee': 3000,
                'recipient': account.address,
                'deadline': deadline,
                'amountIn': amount_in,
                'amountOutMinimum': 0,
                'sqrtPriceLimitX96': 0
            }
            
            swap_tx = router_contract.functions.exactInputSingle(
                params
            ).build_transaction({
                'from': account.address,
                'nonce': current_nonce,
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id
            })
            
            signed_swap = self.w3.eth.account.sign_transaction(swap_tx, private_key_bytes)
            swap_tx_hash = self.w3.eth.send_raw_transaction(signed_swap.raw_transaction)
            
            try:
                print(f"{Fore.YELLOW}Menunggu konfirmasi swap USDT ke BTC (timeout: 300 detik)...{Style.RESET_ALL}")
                receipt = self.w3.eth.wait_for_transaction_receipt(swap_tx_hash, timeout=300)
                print(f"{Fore.GREEN}Swap USDT ke BTC berhasil dikonfirmasi!{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Timeout menunggu konfirmasi swap: {str(e)}{Style.RESET_ALL}")
                self.switch_rpc()
                raise Exception(f"Timeout menunggu konfirmasi swap: {str(e)}")
            
            return {
                'status': 'success',
                'transaction_hash': swap_tx_hash.hex(),
                'amount_in': amount_in
            }
            
        except Exception as e:
            error_message = str(e)
            try:
                if 'message' in error_message and '{' in error_message:
                    error_json_str = error_message[error_message.find('{'):error_message.rfind('}')+1]
                    error_json = json.loads(error_json_str)
                    if self.handle_transaction_error(error_json):
                        return self.swap_usdt_to_btc(private_key, amount_in)
            except:
                pass
            return {
                'status': 'error',
                'message': str(e)
            }

    def swap_btc_to_usdt(self, private_key, amount_in):
        try:
            # Implementasi yang sama dengan swap_usdt_to_btc tapi dengan token yang dibalik
            self.headers = get_random_headers()
            provider = Web3.HTTPProvider('https://og-testnet-evm.itrocket.net', request_kwargs={'headers': self.headers})
            self.w3 = Web3(provider)
            
            if private_key.startswith('0x'):
                private_key_bytes = bytes.fromhex(private_key[2:])
            else:
                private_key_bytes = bytes.fromhex(private_key)
                
            account = Account.from_key(private_key_bytes)
            
            time.sleep(2)
            current_nonce = self.w3.eth.get_transaction_count(account.address, 'pending')
            print(f"{Fore.YELLOW}Menggunakan nonce {current_nonce} untuk approval BTC{Style.RESET_ALL}")
            
            # Approve BTC
            btc_contract = self.w3.eth.contract(address=self.btc_address, abi=self.btc_abi)
            
            approve_tx = btc_contract.functions.approve(
                self.router_address,
                amount_in
            ).build_transaction({
                'from': account.address,
                'nonce': current_nonce,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(approve_tx, private_key_bytes)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            try:
                print(f"{Fore.YELLOW}Menunggu konfirmasi approval BTC (timeout: 300 detik)...{Style.RESET_ALL}")
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
                print(f"{Fore.GREEN}Approval BTC berhasil dikonfirmasi!{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Timeout menunggu konfirmasi approval BTC: {str(e)}{Style.RESET_ALL}")
                self.switch_rpc()
                raise Exception(f"Timeout menunggu konfirmasi approval BTC: {str(e)}")
            
            time.sleep(10)
            
            current_nonce = self.w3.eth.get_transaction_count(account.address, 'pending')
            print(f"{Fore.YELLOW}Menggunakan nonce {current_nonce} untuk swap BTC ke USDT{Style.RESET_ALL}")
            
            router_contract = self.w3.eth.contract(address=self.router_address, abi=self.router_abi)
            deadline = self.w3.eth.get_block('latest').timestamp + 300
            
            params = {
                'tokenIn': self.btc_address,
                'tokenOut': self.usdt_address,
                'fee': 3000,
                'recipient': account.address,
                'deadline': deadline,
                'amountIn': amount_in,
                'amountOutMinimum': 0,
                'sqrtPriceLimitX96': 0
            }
            
            swap_tx = router_contract.functions.exactInputSingle(
                params
            ).build_transaction({
                'from': account.address,
                'nonce': current_nonce,
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id
            })
            
            signed_swap = self.w3.eth.account.sign_transaction(swap_tx, private_key_bytes)
            swap_tx_hash = self.w3.eth.send_raw_transaction(signed_swap.raw_transaction)
            
            try:
                print(f"{Fore.YELLOW}Menunggu konfirmasi swap BTC ke USDT (timeout: 300 detik)...{Style.RESET_ALL}")
                receipt = self.w3.eth.wait_for_transaction_receipt(swap_tx_hash, timeout=300)
                print(f"{Fore.GREEN}Swap BTC ke USDT berhasil dikonfirmasi!{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Timeout menunggu konfirmasi swap: {str(e)}{Style.RESET_ALL}")
                self.switch_rpc()
                raise Exception(f"Timeout menunggu konfirmasi swap: {str(e)}")
            
            return {
                'status': 'success',
                'transaction_hash': swap_tx_hash.hex(),
                'amount_in': amount_in
            }
            
        except Exception as e:
            error_message = str(e)
            try:
                if 'message' in error_message and '{' in error_message:
                    error_json_str = error_message[error_message.find('{'):error_message.rfind('}')+1]
                    error_json = json.loads(error_json_str)
                    if self.handle_transaction_error(error_json):
                        return self.swap_btc_to_usdt(private_key, amount_in)
            except:
                pass
            return {
                'status': 'error',
                'message': str(e)
            }

def retry_on_mempool_full(func, *args, **kwargs):
    """
    Fungsi untuk melakukan retry saat terjadi error mempool full dengan delay 10 detik
    """
    while True:
        try:
            result = func(*args, **kwargs)
            
            # Cek jika hasil adalah dictionary dan mengandung error mempool full
            if isinstance(result, dict):
                if 'Error' in result and isinstance(result['Error'], dict):
                    error_msg = result['Error'].get('message', '')
                    if 'mempool is full' in str(error_msg).lower():
                        print(f"{Fore.YELLOW}Mempool penuh, menunggu 10 detik sebelum mencoba lagi...{Style.RESET_ALL}")
                        time.sleep(10)
                        continue
                elif result.get('status') == 'error' and 'mempool is full' in str(result).lower():
                    print(f"{Fore.YELLOW}Mempool penuh, menunggu 10 detik sebelum mencoba lagi...{Style.RESET_ALL}")
                    time.sleep(10)
                    continue
            
            return result
            
        except Exception as e:
            if 'mempool is full' in str(e).lower():
                print(f"{Fore.YELLOW}Mempool penuh, menunggu 10 detik sebelum mencoba lagi...{Style.RESET_ALL}")
                time.sleep(10)
                continue
            raise e

def process_transaction(func, *args, **kwargs):
    """
    Wrapper untuk memproses transaksi dengan retry
    """
    max_attempts = 50  # Maksimum percobaan
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        try:
            result = retry_on_mempool_full(func, *args, **kwargs)
            if isinstance(result, dict):
                if result.get('status') == 'success':
                    return result
                elif 'mempool is full' in str(result).lower():
                    print(f"{Fore.YELLOW}Percobaan ke-{attempt}: Mempool masih penuh, mencoba lagi...{Style.RESET_ALL}")
                    time.sleep(10)
                    continue
                else:
                    return result
            return result
        except Exception as e:
            if 'mempool is full' in str(e).lower():
                print(f"{Fore.YELLOW}Percobaan ke-{attempt}: Error - {str(e)}{Style.RESET_ALL}")
                time.sleep(10)
                continue
            raise e
    
    return {'status': 'error', 'message': 'Maksimum percobaan tercapai'}

def process_account(private_key, idx, semaphore, sleep_hours, proxy=None, total_transactions=15):
    try:
        with semaphore:
            account = Account.from_key(private_key)
            address = account.address
            
            print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*50}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Menggunakan Akun #{idx+1}: {address[:6]}...{address[-4:]}{Style.RESET_ALL}")
            
            if proxy:
                print(f"{Fore.BLUE}Menggunakan Proxy: {proxy.split('@')[1]}{Style.RESET_ALL}")
            else:
                print(f"{Fore.BLUE}Menggunakan koneksi langsung (tanpa proxy){Style.RESET_ALL}")
            
            # Buat instance TokenSwapper dengan session yang menggunakan proxy
            session = setup_proxy_session(proxy) if proxy else None
            swapper = TokenSwapper(session=session)
            
            # Lakukan transaksi sebanyak total_transactions kali
            tx_count = 0
            while tx_count < total_transactions:
                # USDT -> ETH
                random_amount = round(random.uniform(100, 300), 2)
                amount_to_swap = int(random_amount * (10 ** 18))
                print(f"\n{Fore.MAGENTA}Menukar {random_amount} USDT ke ETH...{Style.RESET_ALL}")
                result = process_transaction(swapper.swap_usdt_to_eth, private_key, amount_to_swap)
                
                if result['status'] == 'success':
                    tx_hash = result['transaction_hash']
                    if not tx_hash.startswith('0x'):
                        tx_hash = '0x' + tx_hash
                        
                    print(f"{Fore.GREEN}Status: {result['status']}")
                    print(f"Hash Transaksi: {tx_hash}")
                    print(f"Jumlah USDT: {random_amount}")
                    print(f"{Fore.BLUE}Block Explorer URL: https://chainscan-newton.0g.ai/tx/{tx_hash}{Style.RESET_ALL}")
                    
                    # Tunggu sebentar sebelum swap ETH ke USDT
                    time.sleep(60)
                    
                    # ETH -> USDT
                    random_eth_amount = round(random.uniform(0.02, 0.05), 6)
                    eth_amount_to_swap = int(random_eth_amount * (10 ** 18))
                    print(f"\n{Fore.MAGENTA}Menukar {random_eth_amount} ETH ke USDT...{Style.RESET_ALL}")
                    result_back = process_transaction(swapper.swap_eth_to_usdt, private_key, eth_amount_to_swap)
                    
                    if result_back['status'] == 'success':
                        back_tx_hash = result_back['transaction_hash']
                        if not back_tx_hash.startswith('0x'):
                            back_tx_hash = '0x' + back_tx_hash
                            
                        print(f"{Fore.GREEN}Status: {result_back['status']}")
                        print(f"Hash Transaksi: {back_tx_hash}")
                        print(f"Jumlah ETH: {random_eth_amount}")
                        print(f"{Fore.BLUE}Block Explorer URL: https://chainscan-newton.0g.ai/tx/{back_tx_hash}{Style.RESET_ALL}")
                        tx_count += 1
                    else:
                        print(f"{Fore.RED}Status: {result_back['status']}")
                        print(f"{Fore.RED}Error: {result_back['message']}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}Status: {result['status']}")
                    print(f"{Fore.RED}Error: {result['message']}{Style.RESET_ALL}")
                
                # Tunggu sebentar sebelum swap USDT ke BTC
                time.sleep(60)
                
                # USDT -> BTC
                random_amount = round(random.uniform(100, 300), 2)
                amount_to_swap = int(random_amount * (10 ** 18))
                print(f"\n{Fore.MAGENTA}Menukar {random_amount} USDT ke BTC...{Style.RESET_ALL}")
                result_btc = process_transaction(swapper.swap_usdt_to_btc, private_key, amount_to_swap)
                
                if result_btc['status'] == 'success':
                    btc_tx_hash = result_btc['transaction_hash']
                    if not btc_tx_hash.startswith('0x'):
                        btc_tx_hash = '0x' + btc_tx_hash
                        
                    print(f"{Fore.GREEN}Status: {result_btc['status']}")
                    print(f"Hash Transaksi: {btc_tx_hash}")
                    print(f"Jumlah USDT: {random_amount}")
                    print(f"{Fore.BLUE}Block Explorer URL: https://chainscan-newton.0g.ai/tx/{btc_tx_hash}{Style.RESET_ALL}")
                    
                    # Tunggu sebentar sebelum swap BTC ke USDT
                    time.sleep(60)
                    
                    # BTC -> USDT
                    random_btc_amount = round(random.uniform(0.002, 0.003), 8)
                    btc_amount_to_swap = int(random_btc_amount * (10 ** 18))
                    print(f"\n{Fore.MAGENTA}Menukar {random_btc_amount} BTC ke USDT...{Style.RESET_ALL}")
                    result_back_usdt = process_transaction(swapper.swap_btc_to_usdt, private_key, btc_amount_to_swap)
                    
                    if result_back_usdt['status'] == 'success':
                        back_usdt_tx_hash = result_back_usdt['transaction_hash']
                        if not back_usdt_tx_hash.startswith('0x'):
                            back_usdt_tx_hash = '0x' + back_usdt_tx_hash
                            
                        print(f"{Fore.GREEN}Status: {result_back_usdt['status']}")
                        print(f"Hash Transaksi: {back_usdt_tx_hash}")
                        print(f"Jumlah BTC: {random_btc_amount}")
                        print(f"{Fore.BLUE}Block Explorer URL: https://chainscan-newton.0g.ai/tx/{back_usdt_tx_hash}{Style.RESET_ALL}")
                        tx_count += 1
                    else:
                        print(f"{Fore.RED}Status: {result_back_usdt['status']}")
                        print(f"{Fore.RED}Error: {result_back_usdt['message']}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}Status: {result_btc['status']}")
                    print(f"{Fore.RED}Error: {result_btc['message']}{Style.RESET_ALL}")
                
                # Jeda antara siklus transaksi
                if tx_count < total_transactions - 1:
                    sleep_time = random.randint(60, 120)
                    print(f"\n{Fore.YELLOW}Menunggu {sleep_time} detik sebelum siklus transaksi berikutnya...{Style.RESET_ALL}")
                    time.sleep(sleep_time)
            
            print(f"\n{Fore.GREEN}{Style.BRIGHT}Akun #{idx+1} telah menyelesaikan {total_transactions} transaksi!{Style.RESET_ALL}")
            
    except Exception as e:
        print(f"{Fore.RED}{Style.BRIGHT}Error pada Akun #{idx+1}: {str(e)}{Style.RESET_ALL}")

def run_multi_account():
    try:
        print_sky_header()
        print(f"{Fore.CYAN}Memulai program swap otomatis multi-account...{Style.RESET_ALL}\n")
        
        # Baca semua private key dari file
        private_keys = read_private_keys()
        print(f"{Fore.GREEN}Berhasil memuat {len(private_keys)} akun dari priv.txt{Style.RESET_ALL}")
        
        # Tampilkan informasi user agent yang digunakan
        headers = get_random_headers()
        print(f"{Fore.BLUE}Menggunakan User-Agent: {headers['User-Agent']}{Style.RESET_ALL}")
        
        # Jumlah transaksi dan waktu jeda
        total_transactions = 15
        sleep_hours = 12
        
        # Loop untuk setiap putaran (setelah istirahat)
        while True:
            # Loop untuk setiap akun
            for idx, private_key in enumerate(private_keys):
                account = Account.from_key(private_key)
                address = account.address
                
                print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*50}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Menggunakan Akun #{idx+1}: {address[:6]}...{address[-4:]}{Style.RESET_ALL}")
                
                swapper = TokenSwapper()
                
                # Lakukan transaksi sebanyak total_transactions kali untuk akun ini
                for tx_count in range(total_transactions):
                    # Generate nominal random antara 0,5-2 USDT
                    usdt_decimals = 18
                    random_amount = round(random.uniform(100, 300), 2)  # Random antara 0,5-2 USDT dengan 2 desimal
                    amount_to_swap = int(random_amount * (10 ** usdt_decimals))
                    
                    # Timestamp untuk log
                    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"\n{Fore.CYAN}{Style.BRIGHT}[{current_time}] Akun #{idx+1} - Transaksi #{tx_count+1}/{total_transactions}{Style.RESET_ALL}")
                    
                    # Swap USDT ke ETH
                    result = process_transaction(swapper.swap_usdt_to_eth, private_key, amount_to_swap)
                    print(f"{Fore.MAGENTA}Menukar {random_amount} USDT ke ETH...{Style.RESET_ALL}")
                    
                    if result['status'] == 'success':
                        tx_hash = result['transaction_hash']
                        if not tx_hash.startswith('0x'):
                            tx_hash = '0x' + tx_hash
                            
                        print(f"{Fore.GREEN}Status: {result['status']}")
                        print(f"Hash Transaksi: {tx_hash}")
                        print(f"Jumlah USDT: {random_amount}")
                        print(f"{Fore.BLUE}Block Explorer URL: https://chainscan-newton.0g.ai/tx/{tx_hash}{Style.RESET_ALL}")
                        
                        # Tunggu beberapa detik sebelum melakukan swap balik
                        time.sleep(60)
                        
                        # Swap balik dari ETH ke USDT dengan nominal random
                        eth_decimals = 18
                        random_eth_amount = round(random.uniform(0.02, 0.05), 6)  # Random antara 0.0002-0.0005 ETH
                        eth_amount_to_swap = int(random_eth_amount * (10 ** eth_decimals))
                        
                        print(f"\n{Fore.MAGENTA}Menukar {random_eth_amount} ETH ke USDT...{Style.RESET_ALL}")
                        result_back = process_transaction(swapper.swap_eth_to_usdt, private_key, eth_amount_to_swap)
                        
                        if result_back['status'] == 'success':
                            back_tx_hash = result_back['transaction_hash']
                            if not back_tx_hash.startswith('0x'):
                                back_tx_hash = '0x' + back_tx_hash
                                
                            print(f"{Fore.GREEN}Status: {result_back['status']}")
                            print(f"Hash Transaksi: {back_tx_hash}")
                            print(f"Jumlah ETH: {random_eth_amount}")
                            print(f"{Fore.BLUE}Block Explorer URL: https://chainscan-newton.0g.ai/tx/{back_tx_hash}{Style.RESET_ALL}")
                        else:
                            print(f"{Fore.RED}Status: {result_back['status']}")
                            print(f"{Fore.RED}Error: {result_back['message']}{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}Status: {result['status']}")
                        print(f"{Fore.RED}Error: {result['message']}{Style.RESET_ALL}")
                    
                    # Jika bukan transaksi terakhir, tunggu sebentar sebelum transaksi berikutnya
                    if tx_count < total_transactions - 1:
                        sleep_time = random.randint(30, 60)
                        print(f"\n{Fore.YELLOW}Akun #{idx+1} - Transaksi #{tx_count+1} selesai. Menunggu {sleep_time} detik sebelum transaksi berikutnya...{Style.RESET_ALL}")
                        time.sleep(sleep_time)
                
                print(f"\n{Fore.GREEN}{Style.BRIGHT}Akun #{idx+1} telah menyelesaikan {total_transactions} transaksi!{Style.RESET_ALL}")
                
                # Jika bukan akun terakhir, tunggu sebentar sebelum beralih ke akun berikutnya
                if idx < len(private_keys) - 1:
                    sleep_time = random.randint(60, 120)
                    print(f"\n{Fore.YELLOW}Menunggu {sleep_time} detik sebelum beralih ke akun berikutnya...{Style.RESET_ALL}")
                    time.sleep(sleep_time)
            
            # Setelah semua akun selesai, tunggu beberapa jam sebelum putaran berikutnya
            next_run_time = datetime.datetime.now() + datetime.timedelta(hours=sleep_hours)
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}Semua akun telah selesai bertransaksi. Istirahat selama {sleep_hours} jam.")
            print(f"{Fore.YELLOW}Akan melanjutkan pada: {next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep(sleep_hours * 3600)  # Konversi jam ke detik
            print(f"\n{Fore.GREEN}{Style.BRIGHT}Melanjutkan transaksi untuk semua akun kalem joy...{Style.RESET_ALL}")
            
    except Exception as e:
        print(f"{Fore.RED}{Style.BRIGHT}Error: {str(e)}{Style.RESET_ALL}")

def run_multi_account_threaded():
    try:
        print_sky_header()
        print(f"{Fore.CYAN}Memulai program swap otomatis multi-account dengan threading kalem joy...{Style.RESET_ALL}\n")
        
        # Baca semua private key dari file
        private_keys = read_private_keys()
        print(f"{Fore.GREEN}Berhasil memuat {len(private_keys)} akun dari priv.txt{Style.RESET_ALL}")
        
        # Baca semua proxy dari file
        proxies = read_proxies()
        if proxies:
            print(f"{Fore.GREEN}Berhasil memuat {len(proxies)} proxy dari proxy.txt{Style.RESET_ALL}")
        
        # Tampilkan informasi user agent yang digunakan
        headers = get_random_headers()
        print(f"{Fore.BLUE}Menggunakan User-Agent: {headers['User-Agent']}{Style.RESET_ALL}")
        
        # Jumlah transaksi dan waktu jeda
        total_transactions = 15
        sleep_hours = 12
        
        # Tanyakan jumlah thread yang akan berjalan bersamaan
        max_concurrent = input(f"{Fore.GREEN}Masukkan jumlah akun yang akan berjalan bersamaan (default: 3): {Style.RESET_ALL}")
        if not max_concurrent or not max_concurrent.isdigit():
            max_concurrent = 3
        else:
            max_concurrent = int(max_concurrent)
            if max_concurrent > len(private_keys):
                max_concurrent = len(private_keys)
                print(f"{Fore.YELLOW}Jumlah akun bersamaan disesuaikan menjadi {max_concurrent} (jumlah total akun){Style.RESET_ALL}")
            elif max_concurrent < 1:
                max_concurrent = 1
                print(f"{Fore.YELLOW}Jumlah akun bersamaan disesuaikan menjadi 1{Style.RESET_ALL}")
        
        print(f"{Fore.GREEN}Akan menjalankan {max_concurrent} akun secara bersamaan{Style.RESET_ALL}")
        
        # Buat semaphore untuk membatasi jumlah thread yang berjalan bersamaan
        semaphore = Semaphore(max_concurrent)
        
        # Loop untuk menjalankan transaksi berulang kali
        while True:
            threads = []
            
            # Buat thread untuk setiap akun
            for idx, private_key in enumerate(private_keys):
                # Pilih proxy untuk akun ini (jika tersedia)
                proxy = None
                if proxies:
                    # Gunakan proxy berdasarkan indeks akun (dengan rotasi jika jumlah proxy < jumlah akun)
                    proxy_idx = idx % len(proxies)
                    proxy = proxies[proxy_idx]
                
                thread = threading.Thread(
                    target=process_account,
                    args=(private_key, idx, semaphore, sleep_hours, proxy, total_transactions)
                )
                threads.append(thread)
                thread.start()
                
                # Jeda kecil antara memulai thread untuk menghindari konflik
                time.sleep(1)
            
            # Tunggu semua thread selesai
            for thread in threads:
                thread.join()
            
            # Setelah semua akun selesai, tunggu beberapa jam sebelum putaran berikutnya
            next_run_time = datetime.datetime.now() + datetime.timedelta(hours=sleep_hours)
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}Semua akun telah selesai bertransaksi. Istirahat selama {sleep_hours} jam.")
            print(f"{Fore.YELLOW}Akan melanjutkan pada: {next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep(sleep_hours * 3600)  # Konversi jam ke detik
            print(f"\n{Fore.GREEN}{Style.BRIGHT}Melanjutkan transaksi untuk semua akun...{Style.RESET_ALL}")
            
    except Exception as e:
        print(f"{Fore.RED}{Style.BRIGHT}Error: {str(e)}{Style.RESET_ALL}")

# Fungsi helper untuk mendeteksi dan menangani error mempool penuh
def is_mempool_full_error(error):
    """Memeriksa apakah error adalah 'mempool is full'"""
    if isinstance(error, dict):
        if 'message' in error and 'mempool is full' in error['message'].lower():
            return True
    elif isinstance(error, str):
        if 'mempool is full' in error.lower():
            return True
    return False

def read_private_keys():
    """
    Membaca private key dari file priv.txt
    """
    try:
        with open('priv.txt', 'r') as file:
            # Baca setiap baris dan hilangkan whitespace
            private_keys = [line.strip() for line in file.readlines()]
            # Hilangkan baris kosong
            private_keys = [key for key in private_keys if key]
            
            if not private_keys:
                raise Exception("File priv.txt kosong")
                
            return private_keys
    except FileNotFoundError:
        print(f"{Fore.RED}Error: File priv.txt tidak ditemukan{Style.RESET_ALL}")
        raise Exception("File priv.txt tidak ditemukan")
    except Exception as e:
        print(f"{Fore.RED}Error saat membaca private keys: {str(e)}{Style.RESET_ALL}")
        raise

def read_private_key():
    """
    Membaca single private key dari input user atau file
    """
    try:
        # Coba baca dari file dulu
        private_keys = read_private_keys()
        if private_keys:
            return private_keys[0]  # Ambil private key pertama
    except:
        pass
    
    # Jika gagal baca dari file, minta input dari user
    private_key = input(f"{Fore.GREEN}Masukkan private key: {Style.RESET_ALL}")
    if not private_key:
        raise Exception("Private key tidak boleh kosong")
    return private_key.strip()

def read_proxies():
    """
    Membaca daftar proxy dari file proxy.txt
    Format: protocol://username:password@host:port
    atau: protocol://host:port
    """
    try:
        with open('proxy.txt', 'r') as file:
            # Baca setiap baris dan hilangkan whitespace
            proxies = [line.strip() for line in file.readlines()]
            # Hilangkan baris kosong
            proxies = [proxy for proxy in proxies if proxy]
            
            return proxies
    except FileNotFoundError:
        print(f"{Fore.YELLOW}Warning: File proxy.txt tidak ditemukan, melanjutkan tanpa proxy{Style.RESET_ALL}")
        return []
    except Exception as e:
        print(f"{Fore.YELLOW}Warning: Error saat membaca proxy: {str(e)}, melanjutkan tanpa proxy{Style.RESET_ALL}")
        return []

def setup_proxy_session(proxy_url):
    """
    Membuat session requests dengan proxy
    """
    if not proxy_url:
        return None
        
    try:
        session = requests.Session()
        session.proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        return session
    except Exception as e:
        print(f"{Fore.YELLOW}Warning: Gagal setup proxy {proxy_url}: {str(e)}{Style.RESET_ALL}")
        return None

# Contoh penggunaan
if __name__ == "__main__":
    # Tambahkan opsi untuk memilih mode
    print_sky_header()
    print(f"{Fore.CYAN}Pilih mode operasi:{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}1. Mode Single Account (1 private key)")
    print(f"{Fore.YELLOW}2. Mode Multi Account (baca semua private key dari priv.txt)")
    print(f"{Fore.YELLOW}3. Mode Multi Account dengan Threading dan Proxy (berjalan bersamaan)")
    
    choice = input(f"{Fore.GREEN}Masukkan pilihan (1/2/3): {Style.RESET_ALL}")
    
    if choice == "1":
        try:
            # Mode single account
            print_sky_header()
            print(f"{Fore.CYAN}Memulai program swap otomatis (Single Account)...{Style.RESET_ALL}\n")
            
            # Tampilkan informasi user agent yang digunakan
            headers = get_random_headers()
            print(f"{Fore.BLUE}Menggunakan User-Agent: {headers['User-Agent']}{Style.RESET_ALL}")
            
            swapper = TokenSwapper()
            private_key = read_private_key()
            print(f"{Fore.GREEN}Private key loaded successfully: {private_key[:6]}...{private_key[-4:]}{Style.RESET_ALL}")
            
            # Jumlah transaksi dan waktu jeda
            total_transactions = 15
            sleep_hours = 12
            
            # Loop untuk putaran (setelah istirahat)
            while True:
                # Loop untuk melakukan transaksi sebanyak total_transactions kali
                for transaction_count in range(total_transactions):
                    # Generate nominal random antara 0,5-2 USDT
                    usdt_decimals = 18
                    random_amount = round(random.uniform(100, 300), 2)  # Random antara 0,5-2 USDT dengan 2 desimal
                    amount_to_swap = int(random_amount * (10 ** usdt_decimals))
                    
                    # Timestamp untuk log
                    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"\n{Fore.CYAN}{Style.BRIGHT}[{current_time}] Transaksi #{transaction_count + 1}/{total_transactions}{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
                    
                    # Swap USDT ke ETH
                    result = process_transaction(swapper.swap_usdt_to_eth, private_key, amount_to_swap)
                    print(f"{Fore.MAGENTA}Menukar {random_amount} USDT ke ETH...{Style.RESET_ALL}")
                    
                    if result['status'] == 'success':
                        tx_hash = result['transaction_hash']
                        if not tx_hash.startswith('0x'):
                            tx_hash = '0x' + tx_hash
                            
                        print(f"{Fore.GREEN}Status: {result['status']}")
                        print(f"Hash Transaksi: {tx_hash}")
                        print(f"Jumlah USDT: {random_amount}")
                        print(f"{Fore.BLUE}Block Explorer URL: https://chainscan-newton.0g.ai/tx/{tx_hash}{Style.RESET_ALL}")
                        
                        # Tunggu beberapa detik sebelum melakukan swap balik
                        time.sleep(60)
                        
                        # Swap balik dari ETH ke USDT dengan nominal random
                        eth_decimals = 18
                        random_eth_amount = round(random.uniform(0.02, 0.05), 6)  # Random antara 0.0002-0.0005 ETH
                        eth_amount_to_swap = int(random_eth_amount * (10 ** eth_decimals))
                        
                        print(f"\n{Fore.MAGENTA}Menukar {random_eth_amount} ETH ke USDT...{Style.RESET_ALL}")
                        result_back = process_transaction(swapper.swap_eth_to_usdt, private_key, eth_amount_to_swap)
                        
                        if result_back['status'] == 'success':
                            back_tx_hash = result_back['transaction_hash']
                            if not back_tx_hash.startswith('0x'):
                                back_tx_hash = '0x' + back_tx_hash
                                
                            print(f"{Fore.GREEN}Status: {result_back['status']}")
                            print(f"Hash Transaksi: {back_tx_hash}")
                            print(f"Jumlah ETH: {random_eth_amount}")
                            print(f"{Fore.BLUE}Block Explorer URL: https://chainscan-newton.0g.ai/tx/{back_tx_hash}{Style.RESET_ALL}")
                        else:
                            print(f"{Fore.RED}Status: {result_back['status']}")
                            print(f"{Fore.RED}Error: {result_back['message']}{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}Status: {result['status']}")
                        print(f"{Fore.RED}Error: {result['message']}{Style.RESET_ALL}")
                    
                    # Jika bukan transaksi terakhir, tunggu sebentar sebelum transaksi berikutnya
                    if transaction_count < total_transactions - 1:
                        sleep_time = random.randint(60, 120)
                        print(f"\n{Fore.YELLOW}Menunggu {sleep_time} detik sebelum transaksi berikutnya...{Style.RESET_ALL}")
                        time.sleep(sleep_time)
                
                # Setelah semua transaksi selesai, tunggu beberapa jam sebelum putaran berikutnya
                next_run_time = datetime.datetime.now() + datetime.timedelta(hours=sleep_hours)
                print(f"\n{Fore.YELLOW}{Style.BRIGHT}{total_transactions} transaksi telah selesai. Istirahat selama {sleep_hours} jam.")
                print(f"{Fore.YELLOW}Akan melanjutkan pada: {next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
                time.sleep(sleep_hours * 3600)  # Konversi jam ke detik
                print(f"\n{Fore.GREEN}{Style.BRIGHT}Melanjutkan transaksi...{Style.RESET_ALL}")
                
        except Exception as e:
            print(f"{Fore.RED}{Style.BRIGHT}Error: {str(e)}{Style.RESET_ALL}")
    
    elif choice == "2":
        # Mode multi account
        run_multi_account()
    
    elif choice == "3":
        # Mode multi account dengan threading dan proxy
        run_multi_account_threaded()
    
    else:
        print(f"{Fore.RED}Pilihan tidak valid. Program berhenti.{Style.RESET_ALL}")
