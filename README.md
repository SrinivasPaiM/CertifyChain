# Refugee Certificate System (CertifyChain) - v2.0

## Overview

CertifyChain is a comprehensive blockchain-powered refugee certificate management system built with Django and Ethereum smart contracts. The system provides secure, tamper-proof digital certificates for refugees with AI-powered service matching, zero-knowledge proofs, and self-sovereign identity features.

## What's New in v2.0

- **AI Service Matching**: ML-based system that matches refugees with eligible public services based on their profile
- **Zero-Knowledge Proofs**: Privacy-preserving proof generation using Circom for eligibility verification
- **Self-Sovereign Identity**: Identity management that lets refugees control their own credentials
- **Privacy-Preserving Smart Contract**: Enhanced Solidity contract for privacy-focused verification

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
python manage.py makemigrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Run server
python manage.py runserver
```

## Blockchain Setup

```bash
# Install and start Ganache
npm install -g ganache-cli
ganache-cli
```

Then deploy the smart contract via Remix IDE and update `contract_address` in `certificates/views.py`.

## Access

- App: http://127.0.0.1:8000
- Admin: http://127.0.0.1:8000/admin
