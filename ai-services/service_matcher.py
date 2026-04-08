"""
AI Service Matching Engine for Refugees

This module uses machine learning to match refugees with eligible public services
based on their profile (skills, education, family size, location, etc.)

The AI predicts eligibility and recommends optimal service combinations.
"""

import json
import random
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class ServiceType(Enum):
    HEALTHCARE = 0
    EDUCATION = 1
    EMPLOYMENT = 2
    HOUSING = 3
    LEGAL_AID = 4
    FOOD_ASSISTANCE = 5
    MENTAL_HEALTH = 6
    LANGUAGE_TRAINING = 7


@dataclass
class RefugeeProfile:
    """Refugee profile for service matching"""
    refugee_id: str
    age: int
    education_level: int  # 0=none, 1=primary, 2=secondary, 3=university
    skills: List[str]
    family_size: int
    location: str
    language_proficiency: int  # 0=none to 5=fluent
    employment_status: int  # 0=unemployed, 1=employed, 2=self-employed
    has_children: bool
    special_needs: bool
    time_since_arrival: int  # months


@dataclass
class Service:
    """Public service eligibility criteria"""
    service_id: str
    name: str
    service_type: ServiceType
    min_age: int
    max_age: int
    min_education: int
    required_skills: List[str]
    max_family_size: int
    priority_score: float  # AI computed priority
    documents_required: List[str]


class EligibilityPredictor:
    """
    ML-based eligibility predictor for refugee services.
    In production, this would use scikit-learn or TensorFlow models.
    """
    
    def __init__(self):
        self.services = self._initialize_services()
        
    def _initialize_services(self) -> List[Service]:
        """Initialize available public services"""
        return [
            Service(
                service_id="health_001",
                name="Basic Healthcare Coverage",
                service_type=ServiceType.HEALTHCARE,
                min_age=0,
                max_age=100,
                min_education=0,
                required_skills=[],
                max_family_size=10,
                priority_score=1.0,
                documents_required=["refugee_id", "proof_of_residence"]
            ),
            Service(
                service_id="edu_001",
                name="Primary Education Access",
                service_type=ServiceType.EDUCATION,
                min_age=5,
                max_age=18,
                min_education=0,
                required_skills=[],
                max_family_size=10,
                priority_score=0.9,
                documents_required=["child_birth_certificate"]
            ),
            Service(
                service_id="edu_002",
                name="University Scholarship Program",
                service_type=ServiceType.EDUCATION,
                min_age=18,
                max_age=30,
                min_education=3,
                required_skills=[],
                max_family_size=6,
                priority_score=0.85,
                documents_required=["university_enrollment", "academic_records"]
            ),
            Service(
                service_id="emp_001",
                name="Vocational Training Program",
                service_type=ServiceType.EMPLOYMENT,
                min_age=18,
                max_age=45,
                min_education=1,
                required_skills=[],
                max_family_size=8,
                priority_score=0.95,
                documents_required=["id_documents", "work_permit"]
            ),
            Service(
                service_id="emp_002",
                name="Job Placement Services",
                service_type=ServiceType.EMPLOYMENT,
                min_age=18,
                max_age=60,
                min_education=1,
                required_skills=["communication", "teamwork"],
                max_family_size=10,
                priority_score=0.8,
                documents_required=["resume", "certificates"]
            ),
            Service(
                service_id="hous_001",
                name="Emergency Housing Assistance",
                service_type=ServiceType.HOUSING,
                min_age=0,
                max_age=100,
                min_education=0,
                required_skills=[],
                max_family_size=8,
                priority_score=1.0,
                documents_required=["refugee_id", "proof_of_need"]
            ),
            Service(
                service_id="legal_001",
                name="Legal Aid Services",
                service_type=ServiceType.LEGAL_AID,
                min_age=18,
                max_age=100,
                min_education=0,
                required_skills=[],
                max_family_size=10,
                priority_score=0.7,
                documents_required=["case_documentation"]
            ),
            Service(
                service_id="mental_001",
                name="Mental Health Support",
                service_type=ServiceType.MENTAL_HEALTH,
                min_age=0,
                max_age=100,
                min_education=0,
                required_skills=[],
                max_family_size=10,
                priority_score=0.9,
                documents_required=["referral_letter"]
            ),
            Service(
                service_id="lang_001",
                name="Language Training Program",
                service_type=ServiceType.LANGUAGE_TRAINING,
                min_age=16,
                max_age=60,
                min_education=0,
                required_skills=[],
                max_family_size=10,
                priority_score=0.85,
                documents_required=["id_document"]
            ),
        ]
    
    def predict_eligibility(self, profile: RefugeeProfile) -> List[Dict]:
        """
        Predict which services a refugee is eligible for.
        Returns list of services with eligibility score.
        """
        eligible_services = []
        
        for service in self.services:
            score = self._calculate_eligibility_score(profile, service)
            if score > 0:
                eligible_services.append({
                    "service": service,
                    "eligibility_score": score,
                    "documents_needed": service.documents_required,
                    "priority": service.priority_score
                })
        
        # Sort by priority and eligibility score
        eligible_services.sort(
            key=lambda x: (x["eligibility_score"] * x["priority"], x["priority"]),
            reverse=True
        )
        
        return eligible_services[:5]  # Top 5 recommendations
    
    def _calculate_eligibility_score(self, profile: RefugeeProfile, 
                                     service: Service) -> float:
        """Calculate eligibility score for a service"""
        score = 0.0
        max_score = 100.0
        
        # Age check
        if profile.age < service.min_age or profile.age > service.max_age:
            return 0.0
        score += 20
        
        # Education check
        if profile.education_level >= service.min_education:
            score += 25
        
        # Skills check
        matching_skills = sum(1 for skill in service.required_skills 
                           if skill in profile.skills)
        score += matching_skills * 15
        
        # Family size check
        if profile.family_size <= service.max_family_size:
            score += 15
        
        # Special circumstances
        if profile.special_needs and service.service_type == ServiceType.HEALTHCARE:
            score += 10
        if profile.has_children and service.service_type == ServiceType.EDUCATION:
            score += 10
        
        # Time-based factors
        if service.service_type == ServiceType.EMPLOYMENT:
            if profile.time_since_arrival > 6:
                score += 10
            if profile.employment_status == 0:  # Unemployed
                score += 5
        
        return min(score, max_score)
    
    def get_service_recommendations(self, profile: RefugeeProfile) -> Dict:
        """
        Get comprehensive service recommendations using AI.
        """
        predictions = self.predict_eligibility(profile)
        
        return {
            "refugee_id": profile.refugee_id,
            "total_eligible": len(predictions),
            "recommendations": [
                {
                    "service_id": p["service"].service_id,
                    "service_name": p["service"].name,
                    "service_type": p["service"].service_type.name,
                    "eligibility_score": round(p["eligibility_score"], 2),
                    "documents_needed": p["documents_needed"],
                    "action_required": "Apply" if p["eligibility_score"] >= 70 else "Contact for info"
                }
                for p in predictions
            ],
            "ai_insights": self._generate_insights(profile, predictions),
            "next_steps": self._generate_next_steps(profile, predictions)
        }
    
    def _generate_insights(self, profile: RefugeeProfile, 
                          predictions: List[Dict]) -> List[str]:
        """Generate AI-powered insights"""
        insights = []
        
        if profile.education_level >= 3:
            insights.append("Higher education qualification detected - consider university scholarships")
        
        if profile.employment_status == 0:
            insights.append("Employment services should be priority - immediate action recommended")
        
        if profile.has_children:
            insights.append("Children detected - education and healthcare services are critical")
        
        if profile.time_since_arrival < 3:
            insights.append("Recent arrival - focus on basic needs: housing, food, healthcare")
        
        if profile.special_needs:
            insights.append("Special needs identified - healthcare and mental health services priority")
        
        return insights
    
    def _generate_next_steps(self, profile: RefugeeProfile,
                            predictions: List[Dict]) -> List[Dict]:
        """Generate actionable next steps"""
        next_steps = []
        
        if any(p["service"].service_type == ServiceType.HEALTHCARE for p in predictions):
            next_steps.append({
                "priority": "HIGH",
                "action": "Register for healthcare coverage",
                "timeline": "Within 7 days of arrival"
            })
        
        if any(p["service"].service_type == ServiceType.HOUSING for p in predictions):
            next_steps.append({
                "priority": "HIGH", 
                "action": "Apply for emergency housing",
                "timeline": "Immediately"
            })
        
        if any(p["service"].service_type == ServiceType.EMPLOYMENT for p in predictions):
            next_steps.append({
                "priority": "MEDIUM",
                "action": "Enroll in vocational training",
                "timeline": "Within 30 days"
            })
        
        if any(p["service"].service_type == ServiceType.LANGUAGE_TRAINING for p in predictions):
            next_steps.append({
                "priority": "MEDIUM",
                "action": "Join language classes",
                "timeline": "Within 60 days"
            })
        
        return next_steps


def main():
    """Demo: Test AI service matching"""
    
    # Sample refugee profile
    profile = RefugeeProfile(
        refugee_id="REF-2024-001",
        age=28,
        education_level=2,  # Secondary education
        skills=["communication", "basic_computing"],
        family_size=4,
        location="Berlin",
        language_proficiency=2,  # Basic English
        employment_status=0,  # Unemployed
        has_children=True,
        special_needs=False,
        time_since_arrival=2  # 2 months
    )
    
    predictor = EligibilityPredictor()
    recommendations = predictor.get_service_recommendations(profile)
    
    print("=" * 70)
    print("AI SERVICE MATCHING - REFUGEE ELIGIBILITY PREDICTOR")
    print("=" * 70)
    
    print(f"\n👤 Refugee ID: {recommendations['refugee_id']}")
    print(f"📊 Total Eligible Services: {recommendations['total_eligible']}")
    
    print("\n" + "-" * 70)
    print("RECOMMENDED SERVICES:")
    print("-" * 70)
    
    for rec in recommendations['recommendations']:
        print(f"\n🔹 {rec['service_name']}")
        print(f"   Type: {rec['service_type']}")
        print(f"   Eligibility Score: {rec['eligibility_score']}%")
        print(f"   Action: {rec['action_required']}")
        print(f"   Documents Needed: {', '.join(rec['documents_needed'])}")
    
    print("\n" + "-" * 70)
    print("AI INSIGHTS:")
    print("-" * 70)
    for insight in recommendations['ai_insights']:
        print(f"💡 {insight}")
    
    print("\n" + "-" * 70)
    print("NEXT STEPS:")
    print("-" * 70)
    for step in recommendations['next_steps']:
        print(f"⚡ [{step['priority']}] {step['action']}")
        print(f"   Timeline: {step['timeline']}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
