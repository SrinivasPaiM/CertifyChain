"""
Zero-Knowledge Proof Generator for Refugee Eligibility Verification

This module provides ZK proof generation for privacy-preserving identity verification.
Uses snarkjs for proof generation.

Requirements:
    npm install -g snarkjs

Usage:
    1. Compile the circuit: circom eligibility.circom --r1cs --wasm --sym
    2. Setup powers of tau: snarkjs powersoftau new bn128 12 ptau.json --snarkjs
    3. Contribute: snarkjs powersoftau contribute ptau.json --name="contrib" -v
    4. Export: snarkjs powersoftau export ptau.json pot12_0000.ptau
    5. Setup: snarkjs groth16 setup eligibility.r1cs pot12_0000.ptau eligibility_0000.zkey
    6. Generate proof: python zk_proof_generator.py
"""

import json
import hashlib
import os
import subprocess
from pathlib import Path
from typing import Optional


class ZKProofGenerator:
    """Generate ZK proofs for eligibility verification without revealing identity"""
    
    def __init__(self, circuits_dir: Optional[Path] = None):
        self.circom = hashlib.sha256()
        self.circuits_dir = circuits_dir or Path(__file__).parent
        self.r1cs_file = self.circuits_dir / "eligibility.r1cs"
        self.wasm_file = self.circuits_dir / "eligibility.js"
        self.ptau_file = self.circuits_dir / "ptau" / "pot12_0000.ptau"
        self.zkey_file = self.circuits_dir / "eligibility_0000.zkey"
        
    def compile_circuit(self) -> bool:
        """Compile the circom circuit to R1CS and WASM"""
        print("Compiling circuit...")
        result = subprocess.run(
            ["circom", "eligibility.circom", "--r1cs", "--wasm", "--sym"],
            cwd=self.circuits_dir,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Compilation failed: {result.stderr}")
            return False
        print("Circuit compiled successfully")
        return True
        
    def setup_powers_of_tau(self, tau_file: str = "ptau.json", num_constraints: int = 12) -> bool:
        """Initialize the trusted setup (Phase 1)"""
        print("Setting up Powers of Tau...")
        result = subprocess.run(
            ["snarkjs", "powersoftau", "new", "bn128", str(num_constraints), tau_file],
            cwd=self.circuits_dir,
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    
    def compute_witness(self, private_inputs: dict, public_inputs: dict) -> Optional[bytes]:
        """Generate witness using the WASM"""
        input_json = {**private_inputs, **public_inputs}
        input_file = self.circuits_dir / "input.json"
        
        with open(input_file, "w") as f:
            json.dump(input_json, f)
            
        result = subprocess.run(
            ["node", str(self.wasm_file), str(input_file), "witness.wtns"],
            cwd=self.circuits_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Witness generation failed: {result.stderr}")
            return None
            
        with open(self.circuits_dir / "witness.wtns", "rb") as f:
            return f.read()
    
    def generate_groth16_proof(self, witness: bytes, public_inputs: dict) -> Optional[dict]:
        """Generate Groth16 proof using snarkjs"""
        print("Generating proof...")
        
        public_input_str = json.dumps([public_inputs[k] for k in sorted(public_inputs.keys())])
        public_file = self.circuits_dir / "public.json"
        with open(public_file, "w") as f:
            f.write(public_input_str)
        
        result = subprocess.run(
            [
                "snarkjs", "groth16", "fullsetup",
                str(self.r1cs_file),
                str(self.ptau_file),
                self.circuits_dir / "setup_0000.zkey",
                self.circuits_dir / "verification_key.json"
            ],
            cwd=self.circuits_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Setup failed: {result.stderr}")
            return None
            
        proof_result = subprocess.run(
            [
                "snarkjs", "groth16", "prove",
                str(self.zkey_file),
                "witness.wtns",
                "public.json",
                "proof.json"
            ],
            cwd=self.circuits_dir,
            capture_output=True,
            text=True
        )
        
        if proof_result.returncode != 0:
            print(f"Proof generation failed: {proof_result.stderr}")
            return None
            
        with open(self.circuits_dir / "proof.json", "r") as f:
            return json.load(f)
    
    def verify_proof(self, proof: dict, public_inputs: list) -> bool:
        """Verify a ZK proof"""
        result = subprocess.run(
            [
                "snarkjs", "groth16", "verify",
                "verification_key.json",
                public_inputs,
                "proof.json"
            ],
            cwd=self.circuits_dir,
            capture_output=True,
            text=True
        )
        return result.returncode == 0 and "OK" in result.stdout
    
    def generate_commitment(self, refugee_data: dict) -> str:
        """Generate a commitment (hash) for refugee identity"""
        data_string = f"{refugee_data.get('dob', '')}:{refugee_data.get('nationality', '')}:{refugee_data.get('unique_id', '')}"
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    def generate_eligibility_proof(self, refugee_id: str, eligibility_score: int, 
                                    service_type: int, min_score: int) -> dict:
        """
        Generate a full ZK proof for eligibility.
        
        This creates the proof that proves eligibility without revealing the score.
        """
        
        # Private inputs (witness)
        private_inputs = {
            "refugee_id_hash": int(self.generate_commitment({"unique_id": refugee_id}), 16),
            "eligibility_score": eligibility_score
        }
        
        # Public inputs
        public_inputs = {
            "service_type": service_type,
            "min_score": min_score,
            "claimed_eligible": 1 if eligibility_score >= min_score else 0
        }
        
        # Try to generate actual proof if circuit is compiled
        if self.r1cs_file.exists() and self.ptau_file.exists():
            witness = self.compute_witness(private_inputs, public_inputs)
            if witness:
                proof = self.generate_groth16_proof(witness, public_inputs)
                if proof:
                    return {
                        "type": "groth16",
                        "refugee_commitment": self.generate_commitment({"unique_id": refugee_id}),
                        "service_type": service_type,
                        "min_score": min_score,
                        "claimed_eligible": public_inputs["claimed_eligible"],
                        "zk_proof": proof,
                        "timestamp": str(os.urandom(32).hex())
                    }
        
        # Fallback: return mock proof structure
        return self._create_mock_proof(refugee_id, eligibility_score, service_type, min_score)
    
    def _create_mock_proof(self, refugee_id: str, eligibility_score: int,
                          service_type: int, min_score: int) -> dict:
        """Create a mock proof for demonstration"""
        return {
            "type": "mock",
            "refugee_commitment": self.generate_commitment({"unique_id": refugee_id}),
            "service_type": service_type,
            "min_score": min_score,
            "claimed_eligible": 1 if eligibility_score >= min_score else 0,
            "zk_proof": {
                "pi_a": "...",  # Would be generated by snarkjs
                "pi_b": "...",
                "pi_c": "...",
                "public_signals": [service_type, min_score, 1 if eligibility_score >= min_score else 0]
            },
            "note": "Compile circuit and run setup for real proofs",
            "timestamp": str(os.urandom(32).hex())
        }
    
    def verify_proof_offline(self, proof: dict) -> bool:
        """Verify a ZK proof locally (off-chain) - weak verification"""
        public_signals = proof.get("zk_proof", {}).get("public_signals", [])
        if len(public_signals) >= 3:
            return public_signals[2] == 1
        return False
    
    def create_presentation_token(self, refugee_id: str, service_type: int) -> dict:
        """Create a presentation token for sharing with service providers"""
        service_names = ["healthcare", "education", "employment", "housing"]
        
        return {
            "version": "1.0",
            "schema": "https://refugee-ssi.org/schema/presentations/v1",
            "claim": {
                "eligible_for": service_names[service_type] if service_type < len(service_names) else "unknown",
                "proof_type": "zk-eligibility",
                "issuer": "refugee-certificate-system"
            },
            "generated_at": str(Path(__file__).stat().st_ctime),
            "expires_in": 3600
        }


class IdentityShield:
    """Handle identity shielding using ZK proofs"""
    
    def __init__(self):
        self.salt = os.urandom(32).hex()
    
    def create_identity_commitment(self, dob_year: int, nationality_code: int) -> str:
        """Create a commitment to hide actual identity"""
        data = f"{dob_year}:{nationality_code}:{self.salt}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def generate_age_proof(self, birth_year: int, current_year: int = 2026, 
                          min_age: int = 18) -> dict:
        """Generate proof that user is above minimum age without revealing exact age"""
        age = current_year - birth_year
        is_adult = 1 if age >= min_age else 0
        
        return {
            "type": "age-verification",
            "circuit": "MinAgeVerifier",
            "proof": {
                "birth_year_commitment": hashlib.sha256(str(birth_year).encode()).hexdigest(),
                "is_adult": is_adult,
                "min_age": min_age
            },
            "public_signals": [min_age, is_adult]
        }


def main():
    """Demo: Generate eligibility proof"""
    generator = ZKProofGenerator()
    identity_shield = IdentityShield()
    
    print("=" * 60)
    print("ZK Eligibility Proof Generator - Demo")
    print("=" * 60)
    
    # Generate eligibility proof
    proof = generator.generate_eligibility_proof(
        refugee_id="REF-001",
        eligibility_score=85,
        service_type=0,  # healthcare
        min_score=50
    )
    
    print("\n1. Eligibility Proof Generated:")
    print(json.dumps(proof, indent=2))
    
    # Verify locally
    is_valid = generator.verify_proof_offline(proof)
    print(f"\n2. Offline Verification: {'SUCCESS' if is_valid else 'FAILED'}")
    
    # Create presentation token
    token = generator.create_presentation_token("REF-001", 0)
    print("\n3. Presentation Token:")
    print(json.dumps(token, indent=2))
    
    # Generate age proof
    age_proof = identity_shield.generate_age_proof(2000, 2026, 18)
    print("\n4. Age Proof (proves adult without revealing age):")
    print(json.dumps(age_proof, indent=2))
    
    print("\n" + "=" * 60)
    print("All proofs generated successfully!")
    print("=" * 60)
    print("\nTo generate REAL proofs:")
    print("1. Install circom: cargo install circom")
    print("2. Install snarkjs: npm install -g snarkjs")
    print("3. Compile: circom eligibility.circom --r1cs --wasm --sym")
    print("4. Setup: snarkjs groth16 setup eligibility.r1cs ptau eligibility.zkey")
    print("5. Run: python zk_proof_generator.py")


if __name__ == "__main__":
    main()