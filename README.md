# Refugee Certificate System (CertifyChain)

## Overview

CertifyChain is a comprehensive blockchain-powered refugee certificate management system built with Django and Ethereum smart contracts. The system provides secure, tamper-proof digital certificates for refugees, ensuring authenticity and preventing fraud through decentralized verification.

## What the Project Proves

This project demonstrates the practical application of blockchain technology in humanitarian aid and refugee management by:

1. **Immutability**: Once issued, certificates cannot be altered or forged
2. **Decentralized Verification**: Anyone can verify certificate authenticity without relying on a central authority
3. **Transparency**: All certificate data is publicly verifiable on the blockchain
4. **Security**: Cryptographic guarantees prevent unauthorized modifications
5. **Accessibility**: Web-based interface makes certificate generation and validation user-friendly

## Architecture Overviewo

The system follows a layered architecture integrating traditional web development with blockchain technology:

### 1. Presentation Layer (Frontend)
- **Framework**: Django Templates with Bootstrap CSS
- **Components**:
  - Landing pages (Home, About Us, Features, etc.)
  - Certificate generation form
  - Certificate validation interface
  - PDF certificate viewer with QR codes

### 2. Application Layer (Backend)
- **Framework**: Django 5.0.6
- **Authentication**: Django's built-in user authentication
- **Business Logic**: Certificate issuance and validation workflows

### 3. Data Layer
- **Database**: SQLite (development) / PostgreSQL (production)
- **Models**: Certificate model with refugee details
- **Migrations**: Django migrations for schema management

### 4. Blockchain Integration Layer
- **Library**: Web3.py for Ethereum interaction
- **Network**: Local Ganache testnet (configurable for mainnet/testnet)
- **Smart Contract**: Solidity contract for certificate storage and verification

## Smart Contract Details

### Contract Address
```
0x9dd61d9c68823E5884E7909285620D3B0FB7561d
```
*(Note: This is a testnet address. Update for production deployment)*

### Contract ABI
The smart contract provides the following functions:

#### `issueCertificate(address recipient, string refugeeName, string countryName, string dateOfBirth, string address, string gender, string certificateId, string issueDate, string validUntil)`
- **Purpose**: Issues a new certificate and stores it on the blockchain
- **Parameters**:
  - `recipient`: Ethereum address of the certificate recipient
  - `refugeeName`: Full name of the refugee
  - `countryName`: Country of origin
  - `dateOfBirth`: Date of birth (YYYY-MM-DD format)
  - `address`: Residential address
  - `gender`: Gender specification
  - `certificateId`: Unique certificate identifier
  - `issueDate`: Certificate issuance date
  - `validUntil`: Certificate expiration date

#### `verifyCertificateByAddress(address recipient)`
- **Purpose**: Retrieves certificate details by recipient's Ethereum address
- **Returns**: All certificate fields for the given address

#### `verifyCertificateById(string certificateId)`
- **Purpose**: Retrieves certificate details by certificate ID
- **Returns**: All certificate fields for the given ID

### Contract Storage
- `certificates`: Mapping from address to certificate struct
- `certificateIds`: Mapping from certificate ID string to recipient address

## Prerequisites

Before running this project, ensure you have the following installed:

1. **Python 3.8+**
2. **Django 5.0.6**
3. **Ganache** (for local blockchain development)
4. **MetaMask** or similar Ethereum wallet (for testing)
5. **Node.js** and **npm** (for potential frontend enhancements)

## Installation and Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd refugee_certificate_system
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install django web3 qrcode reportlab pillow
```

### 4. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser
```bash
python manage.py createsuperuser
```

### 6. Blockchain Setup

#### Start Ganache
```bash
# Install Ganache globally via npm
npm install -g ganache-cli

# Start local blockchain
ganache-cli
```
Ganache will start on `http://127.0.0.1:7545` with test accounts pre-funded with ETH.

#### Deploy Smart Contract
1. Open Remix IDE (https://remix.ethereum.org/)
2. Create a new Solidity file with the contract code
3. Compile and deploy to your local Ganache network
4. Update the `contract_address` in `certificates/views.py` with your deployed contract address
5. Copy the contract ABI and replace the `contract_abi` array in `certificates/views.py`

### 7. Configure Settings

Update `refugee_certificate_system/settings.py`:
- Set `DEBUG = False` for production
- Configure `ALLOWED_HOSTS`
- Set up proper database (PostgreSQL recommended for production)
- Configure static files serving

### 8. Run the Application
```bash
python manage.py runserver
```

Access the application at `http://127.0.0.1:8000`

## Usage Guide

### Certificate Issuance Process

1. **Login**: Access the admin panel or user authentication system
2. **Navigate to Certificate Generation**: Go to `/certificates/generate/`
3. **Fill Form**:
   - Recipient's Ethereum address
   - Refugee details (name, country, DOB, address, gender)
   - Certificate validity period
4. **Submit**: The system will:
   - Save certificate to Django database
   - Issue certificate on blockchain
   - Generate PDF with QR code
   - Display confirmation

### Certificate Validation

1. **Access Validation Page**: Go to `/certificates/validate/`
2. **Enter Certificate ID**: Input the certificate ID to verify
3. **View Results**: System checks both database and blockchain for authenticity

### PDF Generation

- Access PDF certificates at `/certificates/pdf/<certificate_id>/`
- PDFs include QR codes for easy verification
- Professional layout with border and styling

## Project Structure

```
refugee_certificate_system/
├── certificates/                    # Main Django app
│   ├── models.py                   # Certificate data model
│   ├── views.py                    # Business logic and blockchain integration
│   ├── forms.py                    # Django forms for certificate creation
│   ├── urls.py                     # URL routing
│   ├── templates/                  # HTML templates
│   │   ├── certificates/           # Certificate-specific templates
│   │   └── *.html                  # General pages
│   └── static/                     # CSS, images, videos
├── refugee_certificate_system/     # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── db.sqlite3                      # SQLite database
├── manage.py                       # Django management script
└── README.md
```

## Key Features

### Security Features
- User authentication required for certificate issuance
- Blockchain-backed immutability
- Cryptographic verification of certificates
- QR code integration for easy validation

### User Experience
- Responsive web interface
- PDF certificate generation
- Real-time validation
- Intuitive navigation

### Blockchain Integration
- Ethereum smart contract deployment
- Web3.py library for seamless interaction
- Gas-optimized transactions
- Event logging for audit trails

## API Endpoints

- `GET /` - Home page
- `GET /certificates/generate/` - Certificate generation form
- `POST /certificates/generate/` - Issue new certificate
- `GET /certificates/validate/` - Certificate validation form
- `POST /certificates/validate/` - Validate certificate
- `GET /certificates/pdf/<id>/` - Generate PDF certificate

## Testing

### Unit Tests
```bash
python manage.py test certificates
```

### Blockchain Testing
1. Use Ganache for local testing
2. Test contract functions via Remix IDE
3. Verify transactions on blockchain explorer

## Deployment

### Production Considerations
1. **Database**: Switch to PostgreSQL
2. **Static Files**: Configure CDN or cloud storage
3. **Security**: 
   - Set `DEBUG = False`
   - Use HTTPS
   - Secure secret keys
   - Configure CORS properly
4. **Blockchain**: Deploy to Ethereum testnet/mainnet

### Docker Deployment
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with proper tests
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Future Enhancements

- Multi-blockchain support (Polygon, Binance Smart Chain)
- Mobile app development
- Integration with UNHCR databases
- Advanced analytics dashboard
- Multi-language support
- Certificate renewal automation

## Support

For questions or issues, please open an issue on the GitHub repository or contact the development team.

---

**CertifyChain** - Empowering refugees through secure, blockchain-verified certificates.</content>
