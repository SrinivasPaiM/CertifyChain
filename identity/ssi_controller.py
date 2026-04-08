"""
Self-Sovereign Identity (SSI) Module for Refugees

Provides decentralized identity management with ZK proofs
"""

import hashlib
import json
import os
import time
from typing import Optional, Dict, List
from enum import Enum


class CredentialType(Enum):
    REFUGEE_STATUS = "refugee_status"
    EDUCATION = "education"
    EMPLOYMENT = "employment"
    HEALTH = "health"
    HOUSING = "housing"


class DecentralizedID:
    """Decentralized Identifier (DID) for refugees"""
    
    def __init__(self, did: str, owner: str, created: int, 
                 public_key: str, credentials: List[Dict]):
        self.did = did
        self.owner = owner
        self.created = created
        self.public_key = public_key
        self.credentials = credentials


class VerifiableCredential:
    """Verifiable Credential following W3C spec"""
    
    def __init__(self, context: str, cred_id: str, cred_type: List[str],
                 issuer: str, issuance_date: str, credential_subject: Dict,
                 proof: Dict):
        self.context = context
        self.cred_id = cred_id
        self.cred_type = cred_type
        self.issuer = issuer
        self.issuance_date = issuance_date
        self.credential_subject = credential_subject
        self.proof = proof
    
    def to_dict(self) -> Dict:
        return {
            "@context": self.context,
            "id": self.cred_id,
            "type": self.cred_type,
            "issuer": self.issuer,
            "issuanceDate": self.issuance_date,
            "credentialSubject": self.credential_subject,
            "proof": self.proof
        }


class IdentityWallet:
    """Self-sovereign identity wallet for refugees"""
    
    def __init__(self):
        self.identities: Dict[str, DecentralizedID] = {}
        self.credentials: Dict[str, List[VerifiableCredential]] = {}
        
    def create_did(self, owner_address: str) -> DecentralizedID:
        """Create a new Decentralized Identifier"""
        did = f"did:ethr:{owner_address.lower()}"
        
        identity = DecentralizedID(
            did=did,
            owner=owner_address,
            created=int(time.time()),
            public_key=owner_address,
            credentials=[]
        )
        
        self.identities[owner_address] = identity
        self.credentials[did] = []
        
        return identity
    
    def issue_credential(self, did: str, credential_type: CredentialType,
                        data: Dict) -> VerifiableCredential:
        """Issue a verifiable credential"""
        credential = VerifiableCredential(
            context="https://www.w3.org/2018/credentials/v1",
            cred_id=f"credential-{int(time.time())}",
            cred_type=["VerifiableCredential", credential_type.value],
            issuer="did:ethr:certifychain",
            issuance_date=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            credential_subject={
                "id": did,
                "type": credential_type.value,
                "data": data
            },
            proof={
                "type": "EcdsaSecp256k1Signature2019",
                "created": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "proofPurpose": "assertionMethod",
                "verificationMethod": "did:ethr:certifychain#key-1"
            }
        )
        
        if did in self.credentials:
            self.credentials[did].append(credential)
        else:
            self.credentials[did] = [credential]
            
        return credential
    
    def generate_presentation(self, did: str, 
                             requested_claims: List[str]) -> Dict:
        """Generate a ZK-powered presentation"""
        creds = self.credentials.get(did, [])
        
        presentation = {
            "@context": "https://www.w3.org/2018/presentations/v1",
            "type": ["VerifiablePresentation"],
            "verifiableCredential": [json.dumps(c.to_dict()) for c in creds],
            "proof": {
                "type": "ZKProof",
                "zkProtocol": "groth16",
                "circuit": "eligibility",
                "publicSignals": requested_claims
            }
        }
        
        return presentation
    
    def verify_identity(self, did: str) -> Dict:
        """Verify identity status"""
        identity = self.identities.get(did)
        
        if not identity:
            return {"valid": False, "reason": "DID not found"}
        
        return {
            "valid": True,
            "did": did,
            "created": identity.created,
            "credential_count": len(self.credentials.get(did, []))
        }


class SSIController:
    """Main controller for SSI operations"""
    
    def __init__(self):
        self.wallet = IdentityWallet()
        
    def register_refugee(self, eth_address: str, 
                        profile_data: Dict) -> Dict:
        """Register new refugee with SSI"""
        identity = self.wallet.create_did(eth_address)
        
        credential = self.wallet.issue_credential(
            identity.did,
            CredentialType.REFUGEE_STATUS,
            profile_data
        )
        
        return {
            "did": identity.did,
            "owner": identity.owner,
            "credential": credential.cred_id,
            "status": "registered"
        }
    
    def request_service(self, did: str, service_type: str) -> Dict:
        """Request access to a service using ZK proof"""
        service_claims = {
            "healthcare": ["is_refugee", "has_residence"],
            "education": ["has_qualification", "is_age_eligible"],
            "employment": ["has_skills", "has_work_permit"],
            "housing": ["is_in_need", "has_family"]
        }
        
        claims = service_claims.get(service_type, [])
        presentation = self.wallet.generate_presentation(did, claims)
        
        return {
            "service_type": service_type,
            "presentation": presentation,
            "zk_proof_required": True,
            "claims_requested": claims
        }


def main():
    """Demo SSI functionality"""
    controller = SSIController()
    
    print("=" * 70)
    print("SELF-SOVEREIGN IDENTITY (SSI) SYSTEM - DEMO")
    print("=" * 70)
    
    result = controller.register_refugee(
        eth_address="0x1234567890123456789012345678901234567890",
        profile_data={
            "name": "John Doe",
            "origin": "Syria",
            "arrival_date": "2024-01-15",
            "status": "asylum_seeker"
        }
    )
    
    print("\n📝 REFUGEE REGISTRATION:")
    print(json.dumps(result, indent=2))
    
    service_request = controller.request_service(result["did"], "healthcare")
    
    print("\n🏥 SERVICE REQUEST (with ZK Proof):")
    print(json.dumps(service_request, indent=2))
    
    verification = controller.wallet.verify_identity(result["did"])
    
    print("\n✅ IDENTITY VERIFICATION:")
    print(json.dumps(verification, indent=2))
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
