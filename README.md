# 🔐 Celo-TimeVault - Celo Network

Lock CELO with a time-lock smart contract and get a proof-of-lock NFT. The NFT is automatically burned when you withdraw your funds.

## ✨ Features

- 🔐 **Time-locked CELO vaults** - Lock your CELO for up to 10 years
- 🖼️ **NFT proof-of-lock** - Get a unique NFT with image + metadata stored on IPFS
- 🔥 **Auto-burn on withdrawal** - NFT is automatically burned when you withdraw
- 💻 **Easy-to-use interface** - Simple Streamlit web interface
- 🌍 **Celo Network** - Fast, low-cost, carbon-negative blockchain

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/ProDiCeT/Celo-TimeVault.git
cd Celo-TimeVault
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the project root:

```env
# Celo Mainnet Configuration
RPC_URL=https://forno.celo.org
CHAIN_ID=42220
CONTRACT_ADDRESS=0xYourContractAddressAfterRemixDeploying
PRIVATE_KEY=0xYourPrivateKey
EXPLORER=https://celoscan.io
PINATA_API_KEY=your_pinata_api_key
PINATA_SECRET_KEY=your_pinata_secret_key
```

**Get Pinata API keys:**
1. Go to [pinata.cloud](https://pinata.cloud)
2. Sign up for a free account
3. Generate API keys from the dashboard

### 3. Deploy Smart Contract

1. Open [Remix IDE](https://remix.ethereum.org/)
2. Create a new file `Celo_Vault.sol` and paste the smart contract code
3. Compile the contract (Solidity 0.8.x)
4. In MetaMask, connect to **Celo Mainnet** (or Alfajores testnet)
5. Deploy using "Injected Provider - MetaMask"
6. Copy the deployed contract address to your `.env` file

### 4. Run the Application

```bash
streamlit run Celo_vault.py
```

The app will open in your browser at `http://localhost:8501`

## 📖 How to Use

### Lock CELO & Mint NFT

1. **Connect Wallet** - Use `.env` file or enter credentials manually in the app
2. **Upload Image** - Choose an image for your NFT
3. **Upload to IPFS** - Click the button to upload and get the IPFS URI
4. **Set Parameters**:
   - Amount of CELO to lock
   - Unlock date (when you can withdraw)
5. **Lock & Mint** - Execute the transaction to lock CELO and receive your NFT

### Withdraw CELO

1. Wait until the unlock date has passed
2. Click **Withdraw** on your vault
3. Your CELO is returned and the NFT is automatically burned

## 🏗️ Architecture

### Tech Stack

- **Smart Contract**: Solidity + OpenZeppelin
- **Blockchain**: Celo Network
- **Frontend**: Streamlit + Web3.py
- **Storage**: IPFS via Pinata
- **Token Standard**: ERC-721 (NFT)

### Main Smart Contract Functions

```solidity
deposit(unlockTime, tokenURI) 
// Lock CELO and mint an NFT

withdraw(vaultId) 
// Withdraw CELO after unlock time (auto-burns NFT)

burn(tokenId) 
// Burn NFT (called automatically on withdrawal)
```

## 🌐 Network Details

### Celo Mainnet
- **Network Name**: Celo Mainnet
- **RPC URL**: `https://forno.celo.org`
- **Chain ID**: 42220
- **Currency Symbol**: CELO
- **Block Explorer**: https://celoscan.io

### Alfajores Testnet (for testing)
- **Network Name**: Alfajores Testnet
- **RPC URL**: `https://alfajores-forno.celo-testnet.org`
- **Chain ID**: 44787
- **Currency Symbol**: CELO
- **Block Explorer**: https://alfajores.celoscan.io
- **Faucet**: https://faucet.celo.org

## 🧪 Testing

⚠️ **Always test on Alfajores Testnet first!**

1. Get free testnet CELO from the [faucet](https://faucet.celo.org)
2. Update your `.env` with Alfajores testnet settings:
   ```env
   RPC_URL=https://alfajores-forno.celo-testnet.org
   CHAIN_ID=44787
   EXPLORER=https://alfajores.celoscan.io
   ```
3. Deploy contract to testnet
4. Test all functions before deploying to mainnet

## 📁 Project Structure

```
timevault-nft/
├── Celo_vault.py              # Streamlit application
├── Celo_Vault.sol             # Smart contract (Solidity)
├── Celo_TimeVaultNFT.json     # Contract ABI
├── requirements.txt      # Python dependencies
├── .env                  # Configuration (create this)
├── Celo_vault.jpg             # Default NFT image
└── README.md             # This file
```

## 🔒 Security Features

- ✅ **ReentrancyGuard** on all critical functions
- ✅ **OpenZeppelin** audited contracts
- ✅ **Owner-only withdrawals** - Only vault creator can withdraw
- ✅ **Time-lock enforcement** - Withdrawals blocked until unlock time
- ✅ **Automatic NFT burning** - NFT destroyed on withdrawal to prevent reuse

## 🛠️ Development

### Requirements

```txt
streamlit>=1.28.0
web3>=6.0.0
python-dotenv>=1.0.0
requests>=2.31.0
Pillow>=10.0.0
```

### Adding Custom Features

Transform to miniapp

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📄 License

MIT License - see [LICENSE](LICENSE)

## 🙏 Acknowledgments

- Built on [Celo](https://celo.org) - Mobile-first blockchain
- [OpenZeppelin](https://openzeppelin.com) - Secure smart contract libraries
- [Pinata](https://pinata.cloud) - IPFS storage
- [Streamlit](https://streamlit.io) - Web app framework

**Made with love by dnapog.base.eth for Celo Network**

---

**Made with ❤️ by dnapog.base.eth**

*Adapted for Celo Network - Fast, Secure, Carbon-Negative*
