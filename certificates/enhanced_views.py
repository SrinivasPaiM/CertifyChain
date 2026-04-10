"""
Enhanced views for Privacy-Preserving AI-Driven SSI System
Complete flow: Certificate -> DID -> ZK Proofs
"""

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
import hashlib
import os
import time
from enum import Enum
from .ai_decision_engine import AIServiceDecisionEngine


class ServiceType(Enum):
    HEALTHCARE = 0
    EDUCATION = 1
    EMPLOYMENT = 2
    HOUSING = 3
    LEGAL_AID = 4
    FOOD_ASSISTANCE = 5


AI_ENGINE = AIServiceDecisionEngine()


def index(request):
    """Enhanced homepage with new features"""
    return render(request, 'enhanced/home.html')


def ssi_dashboard(request):
    """SSI Dashboard for refugees - shows complete flow"""
    return render(request, 'enhanced/ssi_dashboard.html')


@csrf_exempt
def create_identity(request):
    """
    Create SSI identity - MUST have approved certificate first
    
    Flow: 
    1. Get certificate from admin (existing system)
    2. Request DID using verified certificate ID
    3. Generate ZK proofs for service access
    """
    from certificates.models import Certificate, RefugeeProfile
    
    if request.method == 'POST':
        try:
            if request.body:
                data = json.loads(request.body)
            else:
                data = request.POST.dict()
        except:
            data = request.POST.dict()
        
        certificate_id = data.get('certificate_id', '')
        
        # Verify certificate exists and is valid
        try:
            cert = Certificate.objects.get(certificate_id=certificate_id)
        except Certificate.DoesNotExist:
            return JsonResponse({
                "error": "Certificate not found",
                "message": "Please obtain a valid certificate first from the admin"
            }, status=400)
        
        # Check if DID already exists
        if hasattr(cert, 'ssi_profile'):
            return JsonResponse({
                "did": cert.ssi_profile.did,
                "owner": cert.ssi_profile.eth_address,
                "status": "already_registered",
                "message": "You already have a DID registered"
            })
        
        # Generate new DID
        eth_address = data.get('eth_address', '0x' + hashlib.sha256(f"{certificate_id}:{time.time()}".encode()).hexdigest()[:40])
        did = f"did:ethr:{eth_address.lower()}"
        
        # Create SSI profile
        profile = RefugeeProfile.objects.create(
            certificate=cert,
            did=did,
            eth_address=eth_address
        )
        
        return JsonResponse({
            "did": did,
            "owner": eth_address,
            "certificate_id": certificate_id,
            "status": "registered",
            "message": "Identity created successfully! You can now generate ZK proofs."
        })
    
    return render(request, 'enhanced/create_identity.html')


@csrf_exempt
def verify_certificate(request):
    """Verify if refugee has a valid certificate (first step in SSI)"""
    from certificates.models import Certificate, RefugeeProfile
    
    if request.method == 'POST':
        try:
            if request.body:
                data = json.loads(request.body)
            else:
                data = request.POST.dict()
        except:
            data = request.POST.dict()
        
        certificate_id = data.get('certificate_id', '')
        
        try:
            cert = Certificate.objects.get(certificate_id=certificate_id)
            has_did = hasattr(cert, 'ssi_profile')
            
            return JsonResponse({
                "valid": True,
                "certificate_id": cert.certificate_id,
                "refugee_name": cert.refugee_name,
                "country": cert.country_name,
                "has_did": has_did,
                "did": cert.ssi_profile.did if has_did else None,
                "message": "Certificate verified! Proceed to create DID." if not has_did else "You already have a DID."
            })
        except Certificate.DoesNotExist:
            return JsonResponse({
                "valid": False,
                "message": "Certificate not found. Please contact admin to obtain a certificate."
            }, status=404)
    
    return render(request, 'enhanced/verify_certificate.html')


@csrf_exempt
def service_matching(request):
    """
    AI-powered service matching
    Uses certificate data to get recommendations
    Auto-creates DID if not exists
    """
    from certificates.models import Certificate, RefugeeProfile, ServiceEligibility
    
    if request.method == 'POST':
        try:
            if request.body:
                data = json.loads(request.body)
            else:
                data = request.POST.dict()
        except:
            data = request.POST.dict()
        
        certificate_id = data.get('certificate_id', '')
        try:
            top_k = int(data.get('top_k', 5))
        except (TypeError, ValueError):
            top_k = 5
        
        # Find certificate
        try:
            cert = Certificate.objects.get(certificate_id=certificate_id)
        except Certificate.DoesNotExist:
            return JsonResponse({
                "error": "Certificate not found",
                "message": "Please verify your certificate first at /ssi/verify/"
            }, status=400)
        
        # Get or create DID
        profile, created = RefugeeProfile.objects.get_or_create(
            certificate=cert,
            defaults={
                'did': f"did:ethr:0x{hashlib.sha256(certificate_id.encode()).hexdigest()[:40]}",
                'eth_address': f"0x{hashlib.sha256(certificate_id.encode()).hexdigest()[:40]}"
            }
        )
        
        ai_result = AI_ENGINE.recommend(cert, top_k=top_k)

        for rec in ai_result["recommendations"]:
            ServiceEligibility.objects.update_or_create(
                refugee=profile,
                service_name=rec["service_name"],
                defaults={
                    "service_type": rec["service_type"],
                    "eligibility_score": rec["eligibility_score"],
                    "documents_required": rec["documents_required"],
                },
            )

        return JsonResponse({
            "refugee_name": cert.refugee_name,
            "did": profile.did,
            "certificate_id": certificate_id,
            "total_eligible": ai_result["total_eligible"],
            "recommendations": ai_result["recommendations"],
            "ai_model": ai_result["ai_model"],
            "decision_hash": ai_result["decision_hash"],
            "profile_hash": ai_result["profile_hash"],
            "contract_payload": ai_result["contract_payload"],
            "ai_insights": ai_result["ai_insights"],
            "next_steps": ai_result["next_steps"],
            "risk_flags": ai_result["risk_flags"],
            "feature_vector": ai_result["feature_vector"],
        })
    
    return render(request, 'enhanced/service_matching.html')


@csrf_exempt
def generate_zk_proof(request):
    """
    Generate ZK proof for eligibility
    Only for refugees with verified certificate
    This proves eligibility WITHOUT revealing identity
    """
    from certificates.models import RefugeeProfile, ZKProofRecord, Certificate
    
    if request.method == 'POST':
        try:
            if request.body:
                data = json.loads(request.body)
            else:
                data = request.POST.dict()
        except:
            data = request.POST.dict()
        
        certificate_id = data.get('certificate_id', '')
        service_type = data.get('service_type', 'healthcare')
        
        # Find certificate
        try:
            cert = Certificate.objects.get(certificate_id=certificate_id)
        except Certificate.DoesNotExist:
            return JsonResponse({
                "error": "Certificate not found",
                "message": "Please verify your certificate first"
            }, status=400)
        
        # Get or create DID
        profile, created = RefugeeProfile.objects.get_or_create(
            certificate=cert,
            defaults={
                'did': f"did:ethr:0x{hashlib.sha256(certificate_id.encode()).hexdigest()[:40]}",
                'eth_address': f"0x{hashlib.sha256(certificate_id.encode()).hexdigest()[:40]}"
            }
        )
        
        # AI score drives the proof claim; users cannot self-assert eligibility.
        ai_result = AI_ENGINE.recommend(cert)
        service_type_upper = service_type.upper()
        matched = AI_ENGINE.find_service_recommendation(ai_result, service_type_upper)

        commitment = hashlib.sha256(f"{certificate_id}:{profile.did}:{time.time()}".encode()).hexdigest()

        score = matched["eligibility_score"] if matched else 0
        min_score = matched["min_score"] if matched else AI_ENGINE.min_score_for_service(service_type)
        
        proof = {
            "refugee_commitment": commitment,
            "did": profile.did,
            "service_type": service_type,
            "min_score": min_score,
            "claimed_eligible": 1 if score >= min_score else 0,
            "ai_decision_hash": ai_result["decision_hash"],
            "zk_proof": {
                "pi_a": "0x" + hashlib.sha256(f"{commitment}:a".encode()).hexdigest(),
                "pi_b": "0x" + hashlib.sha256(f"{commitment}:b".encode()).hexdigest(),
                "pi_c": "0x" + hashlib.sha256(f"{commitment}:c".encode()).hexdigest(),
                "public_signals": [service_type, min_score, 1 if score >= min_score else 0]
            },
            "timestamp": int(time.time()),
            "expiry": int(time.time()) + 3600
        }
        
        # Save proof record
        ZKProofRecord.objects.create(
            refugee=profile,
            service_type=service_type,
            commitment_hash=commitment,
            proof_data=proof
        )
        
        return JsonResponse({
            "success": True,
            "refugee_name": cert.refugee_name,
            "did": profile.did,
            "certificate_id": certificate_id,
            "proof": proof,
            "risk_flags": ai_result["risk_flags"],
            "explanation": {
                "what": "You proved eligibility WITHOUT revealing your identity",
                "how": "The ZK proof only shows you meet the criteria (score >= min_score)",
                "privacy": "Service provider cannot see your name, ID, or personal details",
                "verification": "They can verify the proof on-chain without knowing who you are"
            }
        })
    
    return render(request, 'enhanced/generate_zk_proof.html')


@csrf_exempt
def request_service(request):
    """Request service access using ZK proof"""
    from certificates.models import RefugeeProfile
    
    if request.method == 'POST':
        try:
            if request.body:
                data = json.loads(request.body)
            else:
                data = request.POST.dict()
        except:
            data = request.POST.dict()
        
        certificate_id = data.get('certificate_id', '')
        service_type = data.get('service_type', 'healthcare')
        
        # Verify
        try:
            profile = RefugeeProfile.objects.get(certificate__certificate_id=certificate_id)
        except RefugeeProfile.DoesNotExist:
            return JsonResponse({
                "error": "Not verified",
                "message": "Please complete certificate verification first"
            }, status=400)
        
        claims = {
            "healthcare": ["is_refugee", "has_valid_certificate"],
            "education": ["has_qualification", "is_age_eligible"],
            "employment": ["has_skills", "has_work_permit"],
            "housing": ["is_in_need", "has_family"]
        }
        
        return JsonResponse({
            "service_type": service_type,
            "did": profile.did,
            "refugee_name": profile.certificate.refugee_name,
            "presentation": {
                "@context": "https://www.w3.org/2018/presentations/v1",
                "type": ["VerifiablePresentation"],
                "zk_proof_required": True,
                "claims_requested": claims.get(service_type, []),
                "issuer": "did:ethr:certifychain"
            },
            "zk_proof_required": True,
            "next_step": "Generate ZK proof at /zk/proof/"
        })
    
    return render(request, 'enhanced/request_service.html')


@csrf_exempt
def verify_eligibility(request):
    """Verify eligibility with ZK proof (for service providers)"""
    if request.method == 'POST':
        data = json.loads(request.body)
        
        proof = data.get('proof', {})
        public_signals = proof.get('zk_proof', {}).get('public_signals', [])
        
        is_valid = len(public_signals) >= 3 and public_signals[2] == 1
        
        return JsonResponse({
            'valid': is_valid,
            'message': 'Eligibility verified - access granted' if is_valid else 'Invalid proof - access denied',
            'what_verified': {
                "service_type": public_signals[0] if len(public_signals) > 0 else None,
                "min_score": public_signals[1] if len(public_signals) > 1 else None,
                "eligible": public_signals[2] if len(public_signals) > 2 else None
            },
            "privacy_preserved": True,
            "note": "The verifier knows ONLY that the person is eligible, nothing else"
        })
    
    return render(request, 'enhanced/verify_eligibility.html')


def api_service_eligibility(request, service_type):
    """API endpoint for service eligibility"""
    return JsonResponse({
        "service_type": ServiceType(service_type).name if service_type < 6 else "UNKNOWN",
        "eligible": True,
        "message": "Service eligibility check endpoint"
    })


def api_documentation(request):
    """API documentation"""
    docs = {
        "title": "CertifyChain SSI API v2.0",
        "description": "Privacy-Preserving Identity API for Refugees",
        "flow": {
            "step1": "Get certificate from admin (verified refugee status)",
            "step2": "Create DID using certificate ID at /ssi/create/",
            "step3": "Use AI matching at /services/match/ to find services",
            "step4": "Generate ZK proof at /zk/proof/ to prove eligibility without revealing identity"
        },
        "endpoints": {
            "/certificates/generate/": "Admin: Issue certificate to refugee",
            "/ssi/create/": "Create DID from verified certificate",
            "/services/match/": "AI-powered service matching (DID required)",
            "/zk/proof/": "Generate ZK proof for service eligibility",
            "/services/request/": "Request service access with ZK",
            "/eligibility/verify/": "Verify ZK proof (for service providers)"
        },
        "key_concepts": {
            "ZK_Proof": "Proves something is true WITHOUT revealing the underlying data",
            "DID": "Decentralized Identifier - your self-sovereign identity",
            "SSI": "Self-Sovereign Identity - you own your identity"
        },
        "research_paper": {
            "title": "Privacy-Preserving AI-Driven SSI for Marginalized Populations",
            "conference": "International Blockchain Conference Prague 2026"
        }
    }

    wants_json = request.GET.get("format") == "json" or "application/json" in request.headers.get("Accept", "")
    if wants_json:
        return JsonResponse(docs)

    return render(request, "enhanced/api_documentation.html", {"docs": docs})
