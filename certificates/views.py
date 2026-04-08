from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.safestring import mark_safe
from django.conf import settings
from .forms import IssueCertificateForm
from .models import Certificate
import time
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import qrcode
from qrcode.image.styledpil import StyledPilImage
from PIL import Image
import datetime

try:
    from web3 import Web3
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False

GANACHE_URL = "http://127.0.0.1:7545"

contract_address = "0x6c78d2a5f4ba9fd7a2c3b542ffb1b4746baae37e"

contract_abi = [
    {
        "inputs": [
            {"internalType": "address", "name": "recipient", "type": "address"},
            {"internalType": "string", "name": "refugeeName", "type": "string"},
            {"internalType": "string", "name": "countryName", "type": "string"},
            {"internalType": "string", "name": "dateOfBirth", "type": "string"},
            {"internalType": "string", "name": "addres", "type": "string"},
            {"internalType": "string", "name": "gender", "type": "string"},
            {"internalType": "string", "name": "certificateId", "type": "string"},
            {"internalType": "string", "name": "issueDate", "type": "string"},
            {"internalType": "string", "name": "validUntil", "type": "string"},
            {"internalType": "address", "name": "generatedBy", "type": "address"}
        ],
        "name": "issueCertificate",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "string", "name": "certificateId", "type": "string"}],
        "name": "verifyCertificateById",
        "outputs": [
            {"internalType": "string", "name": "refugeeName", "type": "string"},
            {"internalType": "string", "name": "countryName", "type": "string"},
            {"internalType": "string", "name": "dateOfBirth", "type": "string"},
            {"internalType": "string", "name": "addres", "type": "string"},
            {"internalType": "string", "name": "gender", "type": "string"},
            {"internalType": "string", "name": "certificateId_", "type": "string"},
            {"internalType": "string", "name": "issueDate", "type": "string"},
            {"internalType": "string", "name": "validUntil", "type": "string"},
            {"internalType": "address", "name": "generatedBy", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "recipient", "type": "address"}],
        "name": "verifyCertificateByAddress",
        "outputs": [
            {"internalType": "string", "name": "refugeeName", "type": "string"},
            {"internalType": "string", "name": "countryName", "type": "string"},
            {"internalType": "string", "name": "dateOfBirth", "type": "string"},
            {"internalType": "string", "name": "addres", "type": "string"},
            {"internalType": "string", "name": "gender", "type": "string"},
            {"internalType": "string", "name": "certificateId_", "type": "string"},
            {"internalType": "string", "name": "issueDate", "type": "string"},
            {"internalType": "string", "name": "validUntil", "type": "string"},
            {"internalType": "address", "name": "generatedBy", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

web3 = None
contract = None

def init_web3():
    global web3, contract
    if WEB3_AVAILABLE:
        try:
            web3 = Web3(Web3.HTTPProvider(GANACHE_URL))
            if web3.is_connected():
                contract = web3.eth.contract(address=contract_address, abi=contract_abi)
        except Exception as e:
            print(f"Web3 connection failed: {e}")
            web3 = None
            contract = None

init_web3()

def home(request):
    verified = None
    certificate = None
    if request.method == 'POST':
        cert_id = request.POST.get('certificate_id')
        if cert_id:
            try:
                certificate = Certificate.objects.get(certificate_id=cert_id)
                verified = True
                if contract:
                    try:
                        bc_cert = contract.functions.verifyCertificateById(cert_id).call()
                        if bc_cert[0]:
                            verified = True
                    except:
                        verified = True
            except Certificate.DoesNotExist:
                verified = False
                
    return render(request, 'verifier/home.html', {'verified': verified, 'certificate': certificate})

def about(request):
    return render(request, 'verifier/faq.html')

def community(request):
    return render(request, 'verifier/community.html')

def getapp(request):
    return render(request, 'verifier/getapp.html')

@login_required
def issue_certificate(request):
    if request.method == 'POST':
        form = IssueCertificateForm(request.POST)
        if form.is_valid():
            recipient = form.cleaned_data['recipient_address']
            refname = form.cleaned_data['refugee_name']
            cerdata = form.cleaned_data['certificate_data']
            add = form.cleaned_data['address']
            valuntil = form.cleaned_data['valid_until']
            dob = form.cleaned_data['date_of_birth']
            refcount = form.cleaned_data['country']
            issdate = form.cleaned_data['issuing_date']
            gend = form.cleaned_data['gender']

            certificate_id = f"REF-{form.cleaned_data['refugee_name'][:3].upper()}-{int(time.time())}"
            transaction_hash = form.cleaned_data.get('transaction_hash', '')

            refugee = Certificate.objects.create(
                refugee_name=refname,
                country_name=refcount,
                date_of_birth=dob,
                address=add,
                gender=gend,
                certificate_id=certificate_id,
                valid_until=valuntil,
                generated_by=request.user,
                transaction_hash=transaction_hash if transaction_hash else None,
                skills=form.cleaned_data.get('skills', ''),
                employment_status=form.cleaned_data.get('employment_status', 'unemployed'),
                family_size=form.cleaned_data.get('family_size', 1),
                has_children=form.cleaned_data.get('has_children', False),
                language_proficiency=form.cleaned_data.get('language_proficiency', 1),
                time_since_arrival=form.cleaned_data.get('time_since_arrival', 1),
                special_needs=form.cleaned_data.get('special_needs', False)
            )

            if contract and web3:
                try:
                    issuer_address = web3.eth.accounts[0]
                    tx_hash = contract.functions.issueCertificate(
                        recipient,
                        form.cleaned_data['refugee_name'],
                        form.cleaned_data['country'],
                        str(form.cleaned_data['date_of_birth']),
                        form.cleaned_data['address'],
                        form.cleaned_data['gender'],
                        str(certificate_id),
                        str(form.cleaned_data['issuing_date']),
                        str(form.cleaned_data['valid_until']),
                        issuer_address
                    ).transact({'from': issuer_address})
                    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
                except Exception as e:
                    print(f"Blockchain transaction failed: {e}")

            return render(request, 'certificates/certificate_confirmation.html', {
                'certificate_id': certificate_id,
                'refugee_name': form.cleaned_data['refugee_name'],
                'valid_until': form.cleaned_data['valid_until']
            })
    else:
        form = IssueCertificateForm()
    return render(request, 'certificates/generate_certificate.html', {'form': form})

@login_required
def generate_certificate_pdf(request, certificate_id):
    try:
        cert = Certificate.objects.get(certificate_id=certificate_id)
    except Certificate.DoesNotExist:
        return HttpResponse("Certificate not found", status=404)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setStrokeColor(colors.darkblue)
    c.setLineWidth(3)
    c.rect(20, 20, width - 40, height - 40)

    c.setStrokeColor(colors.darkblue)
    c.setLineWidth(1)
    c.rect(30, 30, width - 60, height - 60)

    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(colors.darkblue)
    c.drawCentredString(width / 2, height - 80, "REFUGEE CERTIFICATE")
    
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 120, "CertifyChain - Blockchain Verification System")

    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    y = height - 180
    
    c.drawString(80, y, f"Certificate ID: {cert.certificate_id}")
    y -= 30
    c.drawString(80, y, f"Refugee Name: {cert.refugee_name}")
    y -= 30
    c.drawString(80, y, f"Country of Origin: {cert.country_name}")
    y -= 30
    c.drawString(80, y, f"Date of Birth: {cert.date_of_birth}")
    y -= 30
    c.drawString(80, y, f"Address: {cert.address}")
    y -= 30
    c.drawString(80, y, f"Gender: {cert.gender}")
    y -= 30
    c.drawString(80, y, f"Issue Date: {cert.issue_date}")
    y -= 30
    c.drawString(80, y, f"Valid Until: {cert.valid_until}")
    y -= 30
    c.drawString(80, y, f"Generated By: {cert.generated_by.username}")

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr_data = f"Certificate ID: {cert.certificate_id}\nRefugee: {cert.refugee_name}\nCountry: {cert.country_name}\nDOB: {cert.date_of_birth}\nValid Until: {cert.valid_until}"
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    
    c.drawImage(ImageReader(qr_buffer), width - 200, 100, width=120, height=120)

    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(colors.gray)
    c.drawCentredString(width / 2, 50, "This certificate is verified on the Ethereum blockchain. Scan QR code to verify.")

    c.showPage()
    c.save()

    buffer.seek(0)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificate_{certificate_id}.pdf"'
    response.write(buffer.getvalue())
    return response
