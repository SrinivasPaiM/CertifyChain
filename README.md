# CertifyChain (Refugee Certificate System) - v2.0

CertifyChain is a blockchain-based SSI framework for **verifying refugees and issuing certificates** in a privacy-preserving manner. Refugees can prove eligibility for services WITHOUT revealing their identity using **zero-knowledge proofs**.

## Why CertifyChain?
- **Privacy-First**: Zero-knowledge proofs allow refugees to prove eligibility without revealing name, ID, address, or nationality
- **Self-Sovereign Identity**: Refugees own their identity - no central authority can revoke or track their credentials
- **AI-Powered Matching**: Smart matching recommends relevant services based on verified profile data
- **Blockchain-Verified**: Certificates are anchored with transaction hashes for auditability

## Tech Stack
- Python 3.10+ / Django 5.2
- SQLite (default database)
- Web3.py (blockchain integration)
- Remix + Ganache (local blockchain for development)
- ReportLab + qrcode (PDF and QR generation)
- Circom + Snarkjs (ZK proofs - optional for real proofs)

## Project Structure
```
manage.py                    # Django entry point
certificates/                # Core app (models, views, tests)
templates/                   # HTML templates
zk-circuits/                 # ZK circuit files
contracts/                   # Solidity smart contracts
```

## Quick Commands

```powershell
# Setup
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# Run tests
python manage.py test
```

## Local Blockchain Setup (Required for Transaction IDs)

Since this is a proof-of-concept without connecting to mainnet, use Ganache + Remix locally:

### 1. Start Ganache
```powershell
# Install Ganache or use CLI
ganache-cli --deterministic
# Or download Ganache desktop app and start it
```
Ganache runs at: http://127.0.0.1:7545

### 2. Deploy Smart Contract
1. Open **Remix IDE** (https://remix.ethereum.org)
2. Load the contract file: `contracts/Certificate.sol`
3. Compile the contract
4. Deploy to "Dev - Ganache" (or HTTP provider at http://127.0.0.1:7545)
5. Copy the **transaction hash** from the deployment (starts with 0x...)

### 3. Update Contract Address (if needed)
If the contract address in `certificates/views.py` differs from your deployment, update it:
```python
contract_address = "YOUR_DEPLOYED_CONTRACT_ADDRESS"
```

Open http://127.0.0.1:8000/

## Step-by-Step Guide

### Step 1: Login
1. Create superuser: `python manage.py createsuperuser`
2. Login at `/accounts/login/`

### Step 2: Issue Certificate (Requires Blockchain)
Go to `/certificates/generate/` (requires admin login)

**Important - Blockchain fields:**
- `recipient_address`: Ethereum address (0x + 40 hex chars)
- `transaction_hash`: From Remix/Ganache deployment (0x + 64 hex chars)

Example values for testing:
- `recipient_address`: 0x1111111111111111111111111111111111111111
- `transaction_hash`: 0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa

After submit, you'll receive a certificate ID (e.g., `REF-ABC-1712750000`).

**Why blockchain?** The transaction hash anchors the certificate to an immutable on-chain event, providing auditability.

### Step 3: Verify Certificate & Create DID
- Verify certificate: `/ssi/verify/`
- Create DID: `/ssi/create/`

The DID (`did:ethr:0x...`) is your self-sovereign identity for service interactions.

### Step 4: AI Service Matching
Use `/services/match/` with your certificate ID.

The AI analyzes your profile and recommends eligible services with scores and confidence levels.

### Step 5: Generate ZK Proof (Privacy Protection)
Use `/zk/proof/` to prove eligibility WITHOUT revealing identity.

**Key Feature:** You'll see two proofs:
- **Shareable Proof** - Safe to send to service providers (contains ONLY ZK proof data)
- **Full Proof** - Keep private (contains your commitment and DID)

The shareable proof proves "I am eligible for healthcare" WITHOUT revealing:
- Your name
- Your ID number
- Your address
- Your nationality

### Step 6: Verify / Apply for Service
- Apply: `/services/request/`
- Verify: `/eligibility/verify/` (API) or `/eligibility/verify/page/` (Web)

Service providers can verify the proof on-chain without knowing who you are.

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

## Security: How ZK Proofs Protect Privacy

Zero-knowledge proofs allow you to prove something is true WITHOUT revealing the underlying data:

```
Traditional: "Here is my ID card" → Shows EVERYTHING
ZK Proof:    "I am eligible"      → Shows ONLY "eligible"
```

**Example:**
- You need healthcare but don't want to reveal you're a refugee
- Generate ZK proof: "I have eligibility_score >= 50"
- Service provider sees: "✅ Eligible for healthcare"
- Service provider DOES NOT see: Your name, ID, address, or why you're eligible

## Testing

### Django Tests
```powershell
python manage.py test
```

### Browser E2E Tests (Playwright)
Install once:
```powershell
python -m pip install playwright
python -m playwright install chromium
```

Run:
```powershell
python e2e_playwright_test.py
```

This suite covers:
- Page availability
- API docs HTML/JSON behavior
- Login
- Certificate issuance
- End-to-end SSI workflow through verification

### Troubleshooting

### Form error: invalid transaction_hash
- Must be 0x + 64 hex characters
- Get this from Remix deployment or Ganache transaction

### Form error: invalid recipient_address
- Must be 0x + 40 hex characters
- Use an address from Ganache accounts

### Login fails
Run: `python manage.py createsuperuser`

### Port in use
Run: `python manage.py runserver 8001`

## Core Data Models

- **Certificate**: Issued certificate + profile fields for AI matching
- **RefugeeProfile**: DID linked to certificate
- **ServiceEligibility**: Recommendation results
- **ZKProofRecord**: Generated proof audit trail

## Security Note

Current setup is for local development (DEBUG=True, SQLite). Before production deployment:
- Set DEBUG=False
- Configure SECRET_KEY and ALLOWED_HOSTS
- Use production database (PostgreSQL recommended)
- Add TLS/HTTPS
- Review authentication/authorization

---

**Research Paper Context:** This system demonstrates privacy-preserving SSI for marginalized populations. The ZK proof architecture allows refugees to access public services while protecting their identity.
