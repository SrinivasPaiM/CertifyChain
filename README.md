# CertifyChain (Refugee Certificate System) - v2.0

CertifyChain is a Django-based SSI framework for issuing refugee certificates and using them in a privacy-preserving identity flow with zero-knowledge proofs.

## Features
- Certificate issuance by authenticated staff (with blockchain transaction hash)
- DID creation tied to a verified certificate
- Explainable AI service matching
- ZK-style eligibility proof generation and verification
- API docs and JSON endpoints

## Quick Commands

```powershell
# Setup
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# Run app
python manage.py runserver

# Tests
python manage.py test
```

## Tech Stack
- Python 3.10+ / Django 5.2
- SQLite (default)
- Web3.py (for blockchain transaction hashes)
- ReportLab + qrcode (PDF and QR generation)
- Optional: Playwright (E2E tests), FAISS (semantic matching)

## Project Structure
```
manage.py                    # Django entry point
certificates/                # Core app (models, views, tests)
templates/                   # HTML templates
zk-circuits/                 # ZK circuit files
contracts/                   # Solidity smart contracts
```

## Setup

### Windows
```powershell
cd c:\Project\refugee\CertifyChain
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### macOS/Linux
```bash
cd /path/to/CertifyChain
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/

## Step-by-Step Guide

### Step 1: Login
1. Create superuser: `python manage.py createsuperuser`
2. Login at `/accounts/login/`

### Step 2: Issue Certificate
Go to `/certificates/generate/` (requires login)

**Required fields:**
- `recipient_address`: 0x + 40 hex chars (e.g., `0x1111111111111111111111111111111111111111`)
- `transaction_hash`: 0x + 64 hex chars (from blockchain deployment)

After submit, you'll receive a certificate ID (e.g., `REF-ABC-1712750000`).

### Step 3: Verify & Create DID
- Verify certificate: `/ssi/verify/`
- Create DID: `/ssi/create/`

### Step 4: AI Service Matching
Use `/services/match/` with your certificate ID to get eligible services with scores.

### Step 5: Generate ZK Proof
Use `/zk/proof/` to prove eligibility WITHOUT revealing identity.

**Important:** Copy the "SHAREABLE PROOF" to share with service providers - it contains NO personal data.

### Step 6: Verify / Apply
- Apply for service: `/services/request/`
- Verify eligibility: `/eligibility/verify/` or `/eligibility/verify/page/`

## Routes

| URL | Description |
|-----|-------------|
| `/` | Homepage |
| `/ssi/` | SSI Dashboard |
| `/ssi/verify/` | Verify Certificate |
| `/ssi/create/` | Create DID |
| `/services/match/` | AI Service Matching |
| `/zk/proof/` | Generate ZK Proof |
| `/services/request/` | Apply for Service |
| `/eligibility/verify/` | Verify (API) |
| `/eligibility/verify/page/` | Verify (Web Page) |
| `/certificates/generate/` | Issue Certificate (admin) |
| `/api/docs/` | API Documentation |
| `/admin/` | Django Admin |
| `/accounts/login/` | Login |

## Testing

```powershell
python manage.py test
```

## Troubleshooting

### Form error: invalid transaction_hash or recipient_address
- `recipient_address`: must be 0x + 40 hex characters
- `transaction_hash`: must be 0x + 64 hex characters

### Login fails
Run: `python manage.py createsuperuser`

### Port in use
Use: `python manage.py runserver 8001`

## Core Data Models

- **Certificate**: issued certificate + AI profile fields
- **RefugeeProfile**: DID linked to certificate
- **ServiceEligibility**: recommendation results
- **ZKProofRecord**: generated proof audit trail

## Security Note

Current setup is for local development (DEBUG=True, SQLite). Before production: set DEBUG=False, configure SECRET_KEY, ALLOWED_HOSTS, use production database, and add TLS.

---

For questions or contributions, open an issue on GitHub.
