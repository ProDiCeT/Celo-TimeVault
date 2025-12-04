import streamlit as st
from web3 import Web3
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
import requests
from PIL import Image
import io
import base64

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Celo-TimeVault",
    page_icon="🔐",
    layout="wide"
)

# Celo Network Configuration
RPC_URL = os.getenv('RPC_URL', 'https://forno.celo.org')
CHAIN_ID = int(os.getenv('CHAIN_ID', '42220'))
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS', '')
PRIVATE_KEY = os.getenv('PRIVATE_KEY', '')
EXPLORER = os.getenv('EXPLORER', 'https://celoscan.io')
PINATA_API_KEY = os.getenv('PINATA_API_KEY', '')
PINATA_SECRET_KEY = os.getenv('PINATA_SECRET_KEY', '')

# Contract ABI (simplified - load from Celo_TimeVault.json in production)
CONTRACT_ABI = [
    {
        "inputs": [{"internalType": "uint256", "name": "unlockTime", "type": "uint256"},
                   {"internalType": "string", "name": "tokenURI", "type": "string"}],
        "name": "deposit",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "vaultId", "type": "uint256"}],
        "name": "withdraw",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
        "name": "getVaultsByOwner",
        "outputs": [{"internalType": "uint256[]", "name": "", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "vaults",
        "outputs": [
            {"internalType": "address", "name": "owner", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "uint256", "name": "unlockTime", "type": "uint256"},
            {"internalType": "bool", "name": "withdrawn", "type": "bool"},
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "tokenURI",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# Initialize Web3
@st.cache_resource
def init_web3():
    """Initialize Web3 connection to Celo network"""
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        st.error("❌ Failed to connect to Celo network")
        return None
    return w3

# Upload to IPFS via Pinata
def upload_to_ipfs(file_content, filename):
    """Upload file to IPFS using Pinata"""
    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    headers = {
        "pinata_api_key": PINATA_API_KEY,
        "pinata_secret_api_key": PINATA_SECRET_KEY
    }
    
    files = {
        'file': (filename, file_content)
    }
    
    try:
        response = requests.post(url, files=files, headers=headers)
        response.raise_for_status()
        ipfs_hash = response.json()['IpfsHash']
        return f"ipfs://{ipfs_hash}"
    except Exception as e:
        st.error(f"Failed to upload to IPFS: {str(e)}")
        return None

# Upload JSON metadata to IPFS
def upload_metadata_to_ipfs(metadata):
    """Upload NFT metadata JSON to IPFS"""
    url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
    headers = {
        "Content-Type": "application/json",
        "pinata_api_key": PINATA_API_KEY,
        "pinata_secret_api_key": PINATA_SECRET_KEY
    }
    
    try:
        response = requests.post(url, json=metadata, headers=headers)
        response.raise_for_status()
        ipfs_hash = response.json()['IpfsHash']
        return f"ipfs://{ipfs_hash}"
    except Exception as e:
        st.error(f"Failed to upload metadata to IPFS: {str(e)}")
        return None

# Create NFT metadata
def create_nft_metadata(image_uri, amount, unlock_time, owner):
    """Create NFT metadata following ERC-721 standard"""
    unlock_date = datetime.fromtimestamp(unlock_time).strftime('%Y-%m-%d %H:%M:%S')
    
    metadata = {
        "name": f"TimeVault Lock #{int(datetime.now().timestamp())}",
        "description": f"This NFT represents {amount} CELO locked until {unlock_date} on Celo Network",
        "image": image_uri,
        "attributes": [
            {"trait_type": "Amount", "value": f"{amount} CELO"},
            {"trait_type": "Unlock Date", "value": unlock_date},
            {"trait_type": "Owner", "value": owner},
            {"trait_type": "Network", "value": "Celo"},
            {"trait_type": "Status", "value": "Locked"}
        ]
    }
    return metadata

# Deposit CELO and mint NFT
def deposit_and_mint(w3, contract, account, private_key, amount, unlock_time, token_uri):
    """Lock CELO and mint NFT"""
    try:
        # Build transaction
        nonce = w3.eth.get_transaction_count(account)
        
        # Convert amount to Wei (1 CELO = 10^18 Wei)
        amount_wei = w3.to_wei(amount, 'ether')
        
        # Prepare transaction
        txn = contract.functions.deposit(unlock_time, token_uri).build_transaction({
            'from': account,
            'value': amount_wei,
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
            'chainId': CHAIN_ID
        })
        
        # Sign transaction
        signed_txn = w3.eth.account.sign_transaction(txn, private_key)
        
        # Send transaction
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        st.info(f"⏳ Transaction sent: {tx_hash.hex()}")
        
        # Wait for confirmation
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            return True, tx_hash.hex()
        else:
            return False, "Transaction failed"
            
    except Exception as e:
        return False, str(e)

# Withdraw from vault
def withdraw_from_vault(w3, contract, account, private_key, vault_id):
    """Withdraw CELO and burn NFT"""
    try:
        nonce = w3.eth.get_transaction_count(account)
        
        txn = contract.functions.withdraw(vault_id).build_transaction({
            'from': account,
            'gas': 200000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
            'chainId': CHAIN_ID
        })
        
        signed_txn = w3.eth.account.sign_transaction(txn, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        st.info(f"⏳ Withdrawal transaction sent: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            return True, tx_hash.hex()
        else:
            return False, "Transaction failed"
            
    except Exception as e:
        return False, str(e)

# Main UI
def main():
    st.title("🔐 Celo-TimeVault - Lock/Unlock your CELO")
    st.markdown("### Lock your CELO and get a proof-of-lock NFT on Celo Network")
    
    # Sidebar - Wallet Connection
    with st.sidebar:
        st.header("🔌 Wallet Configuration")
        
        use_env = st.checkbox("Use .env file", value=True)
        
        if use_env:
            wallet_address = os.getenv('WALLET_ADDRESS', '')
            if not wallet_address and PRIVATE_KEY:
                w3 = init_web3()
                if w3:
                    wallet_address = w3.eth.account.from_key(PRIVATE_KEY).address
            
            contract_addr = CONTRACT_ADDRESS
            priv_key = PRIVATE_KEY
        else:
            wallet_address = st.text_input("Wallet Address", "")
            contract_addr = st.text_input("Contract Address", "")
            priv_key = st.text_input("Private Key", "", type="password")
        
        st.divider()
        
        if wallet_address:
            st.success(f"✅ Connected: {wallet_address[:6]}...{wallet_address[-4:]}")
            
            # Show balance
            w3 = init_web3()
            if w3:
                balance = w3.eth.get_balance(wallet_address)
                balance_celo = w3.from_wei(balance, 'ether')
                st.metric("CELO Balance", f"{balance_celo:.4f} CELO")
        
        st.divider()
        st.markdown("### 🌐 Network Info")
        st.text(f"Chain ID: {CHAIN_ID}")
        st.text(f"RPC: {RPC_URL[:30]}...")
        st.link_button("View on Explorer", EXPLORER)
    
    # Check if configuration is valid
    if not CONTRACT_ADDRESS or not PRIVATE_KEY:
        st.warning("⚠️ Please configure your wallet in the .env file or sidebar")
        st.code("""
# Create a .env file with:
RPC_URL=https://forno.celo.org
CHAIN_ID=42220
CONTRACT_ADDRESS=0xYour...
PRIVATE_KEY=0xYour...
PINATA_API_KEY=your_key
PINATA_SECRET_KEY=your_secret
        """)
        return
    
    # Initialize Web3 and Contract
    w3 = init_web3()
    if not w3:
        return
    
    try:
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(contract_addr),
            abi=CONTRACT_ABI
        )
        account = w3.eth.account.from_key(priv_key)
    except Exception as e:
        st.error(f"❌ Error initializing contract: {str(e)}")
        return
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["🔒 Lock & Mint", "💰 My Vaults", "ℹ️ How It Works"])
    
    with tab1:
        st.header("Lock CELO & Mint NFT")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("1️⃣ Upload NFT Image")
            uploaded_file = st.file_uploader("Choose an image", type=['png', 'jpg', 'jpeg'])
            
            if uploaded_file:
                image = Image.open(uploaded_file)
                st.image(image, caption="Your NFT Image", use_container_width=True)
                
                if st.button("📤 Upload to IPFS", type="primary"):
                    with st.spinner("Uploading to IPFS..."):
                        img_byte_arr = io.BytesIO()
                        image.save(img_byte_arr, format='PNG')
                        img_byte_arr = img_byte_arr.getvalue()
                        
                        image_uri = upload_to_ipfs(img_byte_arr, uploaded_file.name)
                        
                        if image_uri:
                            st.session_state.image_uri = image_uri
                            st.success(f"✅ Uploaded! URI: {image_uri}")
        
        with col2:
            st.subheader("2️⃣ Lock Details")
            
            amount = st.number_input("Amount to lock (CELO)", min_value=0.01, value=1.0, step=0.1)
            
            unlock_date = st.date_input(
                "Unlock date",
                value=datetime.now() + timedelta(days=30),
                min_value=datetime.now() + timedelta(days=1)
            )
            
            unlock_time_input = st.time_input("Unlock time", value=datetime.now().time())
            
            # Combine date and time
            unlock_datetime = datetime.combine(unlock_date, unlock_time_input)
            unlock_timestamp = int(unlock_datetime.timestamp())
            
            st.info(f"🔓 Unlock on: {unlock_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if st.button("🔐 Lock & Mint NFT", type="primary", disabled='image_uri' not in st.session_state):
                if 'image_uri' not in st.session_state:
                    st.error("Please upload an image first!")
                else:
                    with st.spinner("Creating NFT metadata and locking CELO..."):
                        # Create and upload metadata
                        metadata = create_nft_metadata(
                            st.session_state.image_uri,
                            amount,
                            unlock_timestamp,
                            account.address
                        )
                        
                        token_uri = upload_metadata_to_ipfs(metadata)
                        
                        if token_uri:
                            st.info(f"📝 Metadata URI: {token_uri}")
                            
                            # Deposit and mint
                            success, result = deposit_and_mint(
                                w3, contract, account.address, priv_key,
                                amount, unlock_timestamp, token_uri
                            )
                            
                            if success:
                                st.success(f"✅ Successfully locked {amount} CELO and minted NFT!")
                                st.link_button(
                                    "View Transaction",
                                    f"{EXPLORER}/tx/{result}"
                                )
                                st.balloons()
                            else:
                                st.error(f"❌ Transaction failed: {result}")
    
    with tab2:
        st.header("💰 My Vaults")
        
        try:
            vault_ids = contract.functions.getVaultsByOwner(account.address).call()
            
            if not vault_ids:
                st.info("No vaults found. Create your first vault in the 'Lock & Mint' tab!")
            else:
                for vault_id in vault_ids:
                    vault = contract.functions.vaults(vault_id).call()
                    owner, amount, unlock_time, withdrawn, token_id = vault
                    
                    if not withdrawn:
                        with st.expander(f"🔒 Vault #{vault_id}", expanded=True):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                amount_celo = w3.from_wei(amount, 'ether')
                                st.metric("Amount", f"{amount_celo:.4f} CELO")
                            
                            with col2:
                                unlock_dt = datetime.fromtimestamp(unlock_time)
                                st.metric("Unlock Date", unlock_dt.strftime('%Y-%m-%d'))
                                st.caption(unlock_dt.strftime('%H:%M:%S'))
                            
                            with col3:
                                now = datetime.now()
                                if now < unlock_dt:
                                    time_left = unlock_dt - now
                                    st.metric("Status", "🔒 Locked")
                                    st.caption(f"{time_left.days} days left")
                                else:
                                    st.metric("Status", "🔓 Unlocked")
                            
                            # Withdraw button
                            if datetime.now() >= unlock_dt:
                                if st.button(f"💸 Withdraw", key=f"withdraw_{vault_id}"):
                                    with st.spinner("Processing withdrawal..."):
                                        success, result = withdraw_from_vault(
                                            w3, contract, account.address, priv_key, vault_id
                                        )
                                        
                                        if success:
                                            st.success("✅ Withdrawal successful! NFT burned.")
                                            st.link_button(
                                                "View Transaction",
                                                f"{EXPLORER}/tx/{result}"
                                            )
                                            st.rerun()
                                        else:
                                            st.error(f"❌ Withdrawal failed: {result}")
                            else:
                                st.warning("⏳ Vault is still locked")
                            
                            # Show NFT details
                            try:
                                token_uri = contract.functions.tokenURI(token_id).call()
                                st.caption(f"NFT Token ID: {token_id}")
                                st.caption(f"Metadata: {token_uri[:50]}...")
                            except:
                                pass
        
        except Exception as e:
            st.error(f"Error loading vaults: {str(e)}")
    
    with tab3:
        st.header("ℹ️ How It Works")
        
        st.markdown("""
        ### 🔐 Lock Your CELO
        
        **Celo-TimeVault** allows you to lock CELO tokens for a specific period and receive an NFT as proof of your lock.
        
        #### Step-by-Step Process:
        
        1. **Upload an Image** 📸
           - Choose an image that will be part of your NFT
           - The image is uploaded to IPFS (permanent storage)
        
        2. **Set Lock Parameters** ⚙️
           - Amount: How much CELO to lock
           - Unlock Date: When you want to withdraw
        
        3. **Lock & Mint** 🔒
           - Your CELO is locked in the smart contract
           - An NFT is minted as proof-of-lock
           - NFT metadata stored on IPFS
        
        4. **Wait for Unlock** ⏰
           - Your funds are safely locked
           - Check status in "My Vaults" tab
        
        5. **Withdraw** 💰
           - After unlock date, withdraw your CELO
           - NFT is automatically burned
        
        ### 🛡️ Security Features
        
        - ✅ **Non-custodial**: You control your funds via smart contract
        - ✅ **Time-locked**: Withdrawals only after unlock date
        - ✅ **Owner-only**: Only you can withdraw your CELO
        - ✅ **Auto-burn**: NFT destroyed upon withdrawal
        - ✅ **OpenZeppelin**: Industry-standard secure contracts
        
        ### 🌍 Why Celo?
        
        - ⚡ **Fast**: ~5 second block times
        - 💰 **Cheap**: Very low transaction fees
        - 🌱 **Carbon Negative**: Environmentally friendly
        - 📱 **Mobile-first**: Built for accessibility
        
        ### ⚠️ Important Notes
        
        - Always test on **Alfajores testnet** first
        - You **cannot** withdraw before unlock date
        - Keep your private key **safe**
        - NFT is **automatically burned** on withdrawal
        - Contract is **non-upgradeable** for security
        """)
        
        st.divider()
        
        st.info("💡 **Tip**: Start with small amounts on testnet to understand how it works!")

if __name__ == "__main__":
    main()
