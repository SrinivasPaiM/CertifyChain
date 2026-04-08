# Refugee Certificate System (CertifyChain) - v2.0

## Overview

CertifyChain is a blockchain-powered refugee certificate management system built with Django. It provides secure, tamper-proof digital certificates with AI-powered service matching, zero-knowledge proofs, and self-sovereign identity features.

## What's New in v2.0

- **AI Service Matching**: ML-based system that matches refugees with eligible public services
- **Zero-Knowledge Proofs**: Privacy-preserving proof generation using Circom
- **Self-Sovereign Identity**: Identity management with privacy-preserving verification
- **Privacy-Preserving Smart Contract**: Enhanced Solidity contract

## Prerequisites

- Python 3.8+
- Django 5.0.6
- Ganache (local blockchain)
- Node.js and npm

## Installation

```bash
# Clone and enter directory
git clone https://github.com/SrinivasPaiM/CertifyChain.git
cd CertifyChain

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install django web3 qrcode reportlab pillow

# Setup database
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Run server
python manage.py runserver
```

## How It Works - Complete Workflow

### Step 1: Start Ganache
```bash
npm install -g ganache-cli
ganache-cli
```
Ganache provides a local blockchain at `http://127.0.0.1:7545` with test accounts.

### Step 2: Deploy Smart Contract

1. Open Remix IDE: https://remix.ethereum.org/
2. Create a new file `Certificate.sol` and paste your contract code
3. In Remix, go to "Deploy & Run Transactions"
4. Set environment to "Ganache HTTP Provider" 
5. Enter the URL: `http://127.0.0.1:7545`
6. Click "Deploy" to deploy the contract
7. **Copy the Contract Address** from Remix (e.g., `0x...`)
8. Update `contract_address` in `certificates/views.py` with your address

### Step 3: Issue a Certificate

1. Go to http://127.0.0.1:8000/admin and login
2. Go to the certificate generation page (or use the form)
3. Fill in all refugee details
4. **In the "Transaction Hash" field**: 
   - First, in Remix, call the `issueCertificate` function with the certificate data
   - After the transaction completes, copy the **Transaction Hash** from Remix (looks like `0xabc123...`)
   - Paste this into the Transaction Hash field in the form
5. Submit the form - the certificate is now stored in both the database and linked to the blockchain transaction

### Step 4: Verify Certificate

1. Go to the verification page
2. Enter the Certificate ID
3. The system checks both the database and the blockchain

## Important Files

- `certificates/views.py` - Contains `contract_address` and `contract_abi` (update these!)
- `certificates/models.py` - Database models including Certificate
- `certificates/forms.py` - Form fields including transaction_hash
- `contracts/` - Solidity smart contracts
- `ai-services/` - AI service matching engine
- `zk-circuits/` - Zero-knowledge proof circuits

## Access

- App: http://127.0.0.1:8000
- Admin: http://127.0.0.1:8000/admin