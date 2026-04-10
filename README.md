# CertifyChain (Refugee Certificate System) - v2.0

CertifyChain is a Django web application for issuing refugee certificates and using those certificates in a privacy-preserving SSI flow.

It includes:
- Certificate issuance by authenticated staff
- DID creation tied to a verified certificate
- Explainable AI service matching
- ZK-style eligibility proof generation and verification
- API docs and JSON endpoints for integration

## 0) 5-Minute Quick Start (Recommended)

If you want the fastest successful run, use these exact commands.

```powershell
cd c:\Project\refugee\CertifyChain
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Then open:
- http://127.0.0.1:8000/
- http://127.0.0.1:8000/accounts/login/

If this works, continue with the full walkthrough below.

## 1) Project Goals

The system is designed to support a full service-access workflow:
1. Issue a verified certificate
2. Create a decentralized identity (DID)
3. Match services with explainable AI scoring
4. Generate a proof of eligibility without exposing full personal data
5. Verify eligibility for service providers

## 2) Tech Stack

- Python 3.x
- Django 5.2
- SQLite (default local database)
- Web3.py (optional blockchain integration)
- ReportLab + qrcode + Pillow (PDF and QR generation)

Optional tooling:
- Ganache + Remix (local smart contract testing)
- Playwright (browser end-to-end testing)

## 3) Project Structure

- manage.py: Django entry point
- refugee_certificate_system/: project settings and root URLs
- certificates/: core app (models, forms, views, routes, tests)
- templates/: HTML templates (legacy pages + enhanced SSI pages)
- contracts/: Solidity contracts
- zk-circuits/: ZK circuit and helper scripts
- ai-services/: additional AI helper module

## 4) Prerequisites

- Python 3.10+ recommended
- pip
- (Optional) Node.js if you plan to run blockchain/ZK CLI tools

## 5) Setup (Windows)

From project root:

```powershell
cd c:\Project\refugee\CertifyChain
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

If python is not in PATH, use py:

```powershell
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
py manage.py migrate
py manage.py createsuperuser
py manage.py runserver
```

Open:
- App: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
- Login: http://127.0.0.1:8000/accounts/login/

## 5.1) Setup (macOS/Linux)

```bash
cd /path/to/CertifyChain
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open:
- http://127.0.0.1:8000/

## 5.2) Setup Verification Checklist

After setup, verify each point in order:

1. Migration success:
	- Command: python manage.py migrate
	- Expected: no errors, migrations applied.

2. Server starts:
	- Command: python manage.py runserver
	- Expected: "Starting development server at http://127.0.0.1:8000/"

3. App opens:
	- Visit: http://127.0.0.1:8000/
	- Expected: CertifyChain home page loads.

4. Login page opens:
	- Visit: http://127.0.0.1:8000/accounts/login/
	- Expected: username/password form visible.

5. Auth works:
	- Login with your superuser.
	- Expected: redirect to /certificates/generate/.

If any step fails, go to section 11 (Troubleshooting).

## 6) First Run Walkthrough (Complete User Flow)

### Step A: Login
1. Create a superuser with createsuperuser.
2. Login at /accounts/login/.
3. After login, you are redirected to /certificates/generate/.

### Step B: Issue a certificate
Go to /certificates/generate/ and fill all required fields.

Important validation rules:
- recipient_address must be: 0x + 40 hex characters
- transaction_hash must be: 0x + 64 hex characters

Valid examples:
- recipient_address: 0x1111111111111111111111111111111111111111
- transaction_hash: 0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa

After submit, you will see a confirmation page with a generated certificate ID (example: REF-ABC-1712750000).

### Step C: Download PDF
Use the Download PDF button from confirmation page.

QR behavior:
- New PDFs include a verification URL in the QR code.
- Scanning opens /ssi/verify/?certificate_id=<ID> directly.

### Step D: Verify certificate
Open /ssi/verify/.
- Enter certificate ID manually, or
- Use QR link (auto-fills and verifies)

### Step E: Create DID
From verification flow, create DID if one does not already exist.

Direct page: /ssi/create/

### Step F: Run AI service matching
Use /services/match/ with certificate ID.

Output includes:
- total eligible services
- recommendation list
- confidence/score metadata
- decision_hash and profile_hash for auditability

### Step G: Generate proof
Use /zk/proof/.

Output includes a proof object with public_signals and metadata.

### Step H: Request service and verify eligibility
1. Create presentation request: /services/request/
2. Verify proof: /eligibility/verify/

For a quick verifier demo, paste:

```json
{"zk_proof":{"public_signals":["healthcare",50,1]}}
```

## 7) Routes and Endpoints

Main UI:
- / : Enhanced homepage
- /ssi/ : SSI dashboard
- /ssi/verify/ : Verify certificate
- /ssi/create/ : Create DID
- /services/match/ : AI service matching
- /zk/proof/ : Generate ZK proof
- /services/request/ : Service request with DID/proof context
- /eligibility/verify/ : Verifier page
- /certificates/generate/ : Certificate issuance form (login required)

API:
- /api/docs/ : Human-friendly API docs page
- /api/docs/?format=json : Raw JSON docs
- /api/services/<int:service_type>/ : Service eligibility API sample

Auth/Admin:
- /accounts/login/
- /accounts/logout/
- /admin/

## 8) Blockchain Integration (Optional Local Development)

The app can run without active chain calls for most UI workflows.

To test contract path locally:
1. Start Ganache at http://127.0.0.1:7545.
2. Deploy contracts in contracts/ using Remix.
3. Update contract_address in certificates/views.py if needed.
4. Use valid Ethereum addresses and tx hashes in the certificate form.

## 9) Testing

### Django tests

```powershell
python manage.py test
```

### Browser E2E tests (Playwright)

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
- page availability
- API docs HTML/JSON behavior
- login
- certificate issuance
- end-to-end SSI workflow through verification

### Optional: enable FAISS acceleration for semantic matching

The matcher now supports cosine similarity with optional FAISS indexing.

- Default behavior: deterministic Python cosine matcher (no extra dependency required)
- Accelerated behavior: FAISS inner-product index over normalized vectors

Install FAISS in environments that support it:

```powershell
python -m pip install faiss-cpu numpy
```

If FAISS is not available for your Python/OS build, the app automatically falls back to Python cosine.

## 10) Core Data Models

In certificates/models.py:
- Certificate: issued certificate + profile fields for AI matching
- RefugeeProfile: DID and identity linkage to certificate
- ServiceEligibility: persisted recommendation results
- ZKProofRecord: generated proof audit records

## 11) Common Troubleshooting

### Form error: invalid transaction_hash or recipient_address
Cause: wrong length or non-hex characters.

Fix:
- recipient_address: 0x + exactly 40 hex chars
- transaction_hash: 0x + exactly 64 hex chars

### QR scan opens Google search instead of app page
Cause: old PDF generated before QR URL update.

Fix:
- Generate a new certificate PDF and scan again.

### Login fails
Fix:
1. Create/reset superuser:

```powershell
python manage.py createsuperuser
```

2. Use /accounts/login/.

### Port already in use
Use a different port:

```powershell
python manage.py runserver 8001
```

## 12) Security and Production Notes

Current setup is for local/dev use:
- DEBUG=True
- SQLite default DB
- permissive hosts in settings

Before production:
- set DEBUG=False
- configure secure SECRET_KEY and ALLOWED_HOSTS
- move to production database
- deploy behind proper WSGI/ASGI stack and TLS
- add strict authentication/authorization review

## 13) Quick Commands Reference

```powershell
# activate venv
.venv\Scripts\activate

# install deps
pip install -r requirements.txt

# migrate
python manage.py migrate

# create admin
python manage.py createsuperuser

# run app
python manage.py runserver

# run tests
python manage.py test

# run browser e2e
python e2e_playwright_test.py
```

## 14) New Contributor Onboarding Path

If you are new to this project, follow this order exactly:

1. Run section 0 (5-Minute Quick Start).
2. Complete section 5.2 (Setup Verification Checklist).
3. Complete section 6 (First Run Walkthrough A-H).
4. Run tests from section 9.
5. Read section 7 (Routes and Endpoints) to understand what each page does.

This order avoids most setup mistakes and gives you a working understanding quickly.