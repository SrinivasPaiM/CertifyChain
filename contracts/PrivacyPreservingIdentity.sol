// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract PrivacyPreservingIdentity is ReentrancyGuard {
    
    struct IdentityCommitment {
        bytes32 commitment;
        uint256 timestamp;
        bool exists;
    }
    
    struct ZKProof {
        uint256[2] pi_a;
        uint256[2][2] pi_b;
        uint256[2] pi_c;
        uint256[] publicSignals;
    }
    
    struct ServiceEligibility {
        uint8 serviceType;
        uint256 minimumScore;
        uint256 expirationTime;
    }
    
    struct ClaimRecord {
        address claimant;
        uint8 serviceType;
        uint256 timestamp;
        bool verified;
    }
    
    mapping(bytes32 => IdentityCommitment) public identityCommitments;
    mapping(address => bytes32) public userCommitments;
    mapping(bytes32 => bool) public validProofs;
    mapping(bytes32 => ClaimRecord[]) public claims;
    
    uint8 public constant SERVICE_HEALTHCARE = 0;
    uint8 public constant SERVICE_EDUCATION = 1;
    uint8 public constant SERVICE_EMPLOYMENT = 2;
    uint8 public constant SERVICE_HOUSING = 3;
    
    event IdentityRegistered(address indexed user, bytes32 commitment);
    event EligibilityClaimed(address indexed user, uint8 serviceType, bool verified);
    event ProofVerified(bytes32 indexed proofHash, bool valid);
    
    constructor() {
        // Initialize with default service types
    }
    
    function registerIdentity(bytes32 commitment) external nonReentrant {
        require(!userCommitments[msg.sender].exists, "Identity already registered");
        
        identityCommitments[commitment] = IdentityCommitment({
            commitment: commitment,
            timestamp: block.timestamp,
            exists: true
        });
        
        userCommitments[msg.sender] = commitment;
        
        emit IdentityRegistered(msg.sender, commitment);
    }
    
    function submitEligibilityProof(
        bytes32 identityCommitment,
        ZKProof calldata proof,
        uint8 serviceType,
        uint256 minimumScore
    ) external nonReentrant returns (bool) {
        require(identityCommitments[identityCommitment].exists, "Identity not registered");
        
        bytes32 proofHash = keccak256(abi.encodePacked(
            proof.pi_a[0], proof.pi_a[1],
            proof.pi_b[0][0], proof.pi_b[0][1],
            proof.pi_b[1][0], proof.pi_b[1][1],
            proof.pi_c[0], proof.pi_c[1],
            serviceType,
            minimumScore
        ));
        
        // In production, verify the ZK proof on-chain using a verifier contract
        // For now, we accept the proof and mark it as valid
        bool isValid = _verifyProof(proof, serviceType, minimumScore);
        
        validProofs[proofHash] = isValid;
        
        claims[identityCommitment].push(ClaimRecord({
            claimant: msg.sender,
            serviceType: serviceType,
            timestamp: block.timestamp,
            verified: isValid
        }));
        
        emit EligibilityClaimed(msg.sender, serviceType, isValid);
        emit ProofVerified(proofHash, isValid);
        
        return isValid;
    }
    
    function verifyEligibility(
        bytes32 identityCommitment,
        uint8 serviceType
    ) external view returns (bool) {
        ClaimRecord[] memory claimList = claims[identityCommitment];
        
        for (uint256 i = 0; i < claimList.length; i++) {
            if (claimList[i].serviceType == serviceType && claimList[i].verified) {
                return true;
            }
        }
        
        return false;
    }
    
    function getClaimHistory(bytes32 identityCommitment) 
        external view returns (ClaimRecord[] memory) {
        return claims[identityCommitment];
    }
    
    function _verifyProof(
        ZKProof calldata proof,
        uint8 serviceType,
        uint256 minimumScore
    ) internal pure returns (bool) {
        // Simplified verification for demonstration
        // In production, use a proper ZK verifier (Groth16, PLONK)
        
        require(proof.publicSignals.length >= 3, "Invalid proof format");
        
        // Check that the public signals match the claim
        // publicSignals[0] = serviceType
        // publicSignals[1] = minimumScore  
        // publicSignals[2] = claimed_eligible (1 or 0)
        
        if (proof.publicSignals[0] != serviceType) return false;
        if (proof.publicSignals[1] != minimumScore) return false;
        
        return proof.publicSignals[2] == 1;
    }
    
    function createService(uint8 serviceType, uint256 minimumScore) 
        external pure returns (ServiceEligibility memory) {
        return ServiceEligibility({
            serviceType: serviceType,
            minimumScore: minimumScore,
            expirationTime: block.timestamp + 365 days
        });
    }
}
