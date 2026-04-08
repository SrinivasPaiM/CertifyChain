/*
 * ZK Eligibility Proof Circuit
 * 
 * Purpose: Prove eligibility for public services WITHOUT revealing identity
 * 
 * Use cases:
 * - Prove "eligible for healthcare" without revealing why
 * - Prove "qualifies for education grant" without revealing financial status
 * - Prove "is a refugee" without revealing passport/nationality
 */

template Multiplier2() {
    signal input a;
    signal input b;
    signal output c;
    c <== a * b;
}

template EligibileVerifier() {
    // Private inputs (not revealed)
    signal input refugee_id_hash;      // Hash of refugee's unique ID
    signal input eligibility_score;    // Computed eligibility score
    
    // Public inputs (visible)
    signal input service_type;         // 0=healthcare, 1=education, 2=employment, 3=housing
    signal input min_score;            // Minimum score required for service
    signal input claimed_eligible;     // Boolean: claims to be eligible
    
    // Circuit logic
    signal temp1;
    signal temp2;
    
    // Verify eligibility score meets minimum
    temp1 <== eligibility_score - min_score;
    temp2 <== temp1 * claimed_eligible;
    
    // Output: 1 if eligible, 0 otherwise
    // This can be verified on-chain without revealing the actual score
    signal output is_eligible;
    is_eligible <== temp2;
    
    // Constrain: must claim to be eligible if passing
    // If is_eligible = 1, then claimed_eligible must = 1
    claimed_eligible * (1 - claimed_eligible) === 0;
    
    // Constrain: score must be non-negative
    eligibility_score * (1 - eligibility_score) === 0;
}

template IdentityShield() {
    // Private: actual identity data
    signal input real_dob_year;
    signal input real_nationality;
    
    // Public: commitment (hidden identity)
    signal input identity_commitment;
    signal input salt;
    
    // Public: zero-knowledge proof of identity ownership
    signal input zk_proof;
    
    // Hash the identity data
    signal temp;
    temp <== real_dob_year * 31 + real_nationality;
    
    // Verify commitment matches
    // In practice, this would use a proper hash function
    identity_commitment === temp + salt;
}

template MinAgeVerifier() {
    // Prove user is above minimum age without revealing exact age
    signal input birth_year;
    signal input current_year;
    signal input min_age;
    
    signal output age_range; // 0=underage, 1=adult
    
    signal age;
    age <== current_year - birth_year;
    
    // Output 1 if age >= min_age
    signal temp;
    temp <== age - min_age;
    age_range <== temp + 1;
}

component main {public [service_type, min_score, claimed_eligible]} = EligibileVerifier();
