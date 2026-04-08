"""
Explainable AI decision engine for service eligibility.

This module intentionally uses a deterministic, transparent scoring pipeline
instead of a generative LLM. For regulated identity and benefits workflows,
predictability and auditability are more important than open-ended generation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from functools import lru_cache
import hashlib
import json
from typing import Any, Dict, Iterable, List, Optional


@dataclass(frozen=True)
class ServicePolicy:
    service_id: str
    name: str
    service_type: str
    min_age: int
    min_score: int
    documents_required: List[str]


class AIServiceDecisionEngine:
    """Explainable scoring engine for AI-assisted service matching."""

    # Tuned to keep scores interpretable and stable across deployments.
    BASE_SCORE = 40
    WEIGHTS = {
        "age_match": 10,
        "children_bonus": 15,
        "employment_priority": 12,
        "new_arrival_housing": 15,
        "new_arrival_food": 14,
        "special_needs_health": 18,
        "special_needs_mental_health": 18,
        "language_bonus": 8,
        "language_training_priority": 16,
        "skills_bonus": 10,
        "family_support_bonus": 10,
    }

    def __init__(self) -> None:
        self.model_version = "1.1.0"
        self.policies: List[ServicePolicy] = [
            ServicePolicy(
                service_id="health_001",
                name="Basic Healthcare Coverage",
                service_type="HEALTHCARE",
                min_age=0,
                min_score=50,
                documents_required=["refugee_id", "proof_of_residence"],
            ),
            ServicePolicy(
                service_id="edu_001",
                name="Primary Education Access",
                service_type="EDUCATION",
                min_age=5,
                min_score=50,
                documents_required=["child_birth_certificate"],
            ),
            ServicePolicy(
                service_id="edu_002",
                name="University Scholarship Program",
                service_type="EDUCATION",
                min_age=18,
                min_score=65,
                documents_required=["university_enrollment", "academic_records"],
            ),
            ServicePolicy(
                service_id="emp_001",
                name="Vocational Training Program",
                service_type="EMPLOYMENT",
                min_age=18,
                min_score=55,
                documents_required=["id_documents", "work_permit"],
            ),
            ServicePolicy(
                service_id="emp_002",
                name="Job Placement Services",
                service_type="EMPLOYMENT",
                min_age=18,
                min_score=60,
                documents_required=["resume", "certificates"],
            ),
            ServicePolicy(
                service_id="hous_001",
                name="Emergency Housing Assistance",
                service_type="HOUSING",
                min_age=0,
                min_score=50,
                documents_required=["refugee_id", "proof_of_need"],
            ),
            ServicePolicy(
                service_id="legal_001",
                name="Legal Aid Services",
                service_type="LEGAL_AID",
                min_age=16,
                min_score=50,
                documents_required=["case_documentation"],
            ),
            ServicePolicy(
                service_id="food_001",
                name="Food Assistance Program",
                service_type="FOOD_ASSISTANCE",
                min_age=0,
                min_score=50,
                documents_required=["proof_of_need"],
            ),
            ServicePolicy(
                service_id="mental_001",
                name="Mental Health Support",
                service_type="MENTAL_HEALTH",
                min_age=0,
                min_score=50,
                documents_required=["referral_letter"],
            ),
            ServicePolicy(
                service_id="lang_001",
                name="Language Training Program",
                service_type="LANGUAGE_TRAINING",
                min_age=10,
                min_score=50,
                documents_required=["id_document"],
            ),
        ]

    @staticmethod
    def _normalize_skills(skills_text: str) -> List[str]:
        if not skills_text:
            return []
        return [s.strip().lower() for s in skills_text.split(",") if s.strip()]

    @staticmethod
    def _calc_age(date_of_birth: date) -> int:
        today = date.today()
        return today.year - date_of_birth.year - (
            (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
        )

    @staticmethod
    def _clamp_int(value: Any, default: int, minimum: int, maximum: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return max(minimum, min(parsed, maximum))

    def _build_profile(self, certificate) -> Dict[str, Any]:
        age = self._calc_age(certificate.date_of_birth)
        skills = self._normalize_skills(getattr(certificate, "skills", ""))

        return {
            "age": self._clamp_int(age, default=18, minimum=0, maximum=120),
            "employment_status": getattr(certificate, "employment_status", "unemployed"),
            "family_size": self._clamp_int(getattr(certificate, "family_size", 1), default=1, minimum=1, maximum=20),
            "has_children": bool(getattr(certificate, "has_children", False)),
            "language_proficiency": self._clamp_int(
                getattr(certificate, "language_proficiency", 1), default=1, minimum=1, maximum=5
            ),
            "time_since_arrival": self._clamp_int(
                getattr(certificate, "time_since_arrival", 1), default=1, minimum=0, maximum=1200
            ),
            "special_needs": bool(getattr(certificate, "special_needs", False)),
            "skills_count": len(skills),
            "skills": skills,
        }

    @staticmethod
    def _profile_cache_key(certificate, profile: Dict[str, Any]) -> str:
        cache_payload = {
            "certificate_id": getattr(certificate, "certificate_id", ""),
            "date_of_birth": str(getattr(certificate, "date_of_birth", "")),
            "employment_status": profile["employment_status"],
            "family_size": profile["family_size"],
            "has_children": profile["has_children"],
            "language_proficiency": profile["language_proficiency"],
            "time_since_arrival": profile["time_since_arrival"],
            "special_needs": profile["special_needs"],
            "skills": profile["skills"],
            "model_version": "1.1.0",
        }
        return json.dumps(cache_payload, sort_keys=True)

    @staticmethod
    @lru_cache(maxsize=1024)
    def _cached_hash(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _score_policy(self, policy: ServicePolicy, profile: Dict) -> Dict:
        age = profile["age"]
        if age < policy.min_age:
            return {
                "eligible": False,
                "score": 0,
                "confidence": 0.0,
                "reasons": ["Age requirement not met"],
            }

        score = self.BASE_SCORE
        reasons: List[str] = ["Age requirement satisfied"]

        score += self.WEIGHTS["age_match"]

        if profile["has_children"] and policy.service_type in {"EDUCATION", "HEALTHCARE"}:
            score += self.WEIGHTS["children_bonus"]
            reasons.append("Children in family increase education/health priority")

        if profile["employment_status"] == "unemployed" and policy.service_type == "EMPLOYMENT":
            score += self.WEIGHTS["employment_priority"]
            reasons.append("Unemployed status increases employment support priority")

        if profile["time_since_arrival"] <= 3 and policy.service_type == "HOUSING":
            score += self.WEIGHTS["new_arrival_housing"]
            reasons.append("New arrival receives emergency housing priority")

        if profile["time_since_arrival"] <= 2 and policy.service_type == "FOOD_ASSISTANCE":
            score += self.WEIGHTS["new_arrival_food"]
            reasons.append("Recent arrival receives immediate food assistance priority")

        if profile["special_needs"] and policy.service_type == "HEALTHCARE":
            score += self.WEIGHTS["special_needs_health"]
            reasons.append("Special needs increase healthcare urgency")

        if profile["special_needs"] and policy.service_type == "MENTAL_HEALTH":
            score += self.WEIGHTS["special_needs_mental_health"]
            reasons.append("Special needs increase mental health support priority")

        if profile["language_proficiency"] <= 2 and policy.service_type in {"EDUCATION", "EMPLOYMENT"}:
            score += self.WEIGHTS["language_bonus"]
            reasons.append("Lower language proficiency adds integration support priority")

        if profile["language_proficiency"] <= 2 and policy.service_type == "LANGUAGE_TRAINING":
            score += self.WEIGHTS["language_training_priority"]
            reasons.append("Language training is prioritized for low proficiency")

        if profile["skills_count"] >= 2 and policy.service_type == "EMPLOYMENT":
            score += self.WEIGHTS["skills_bonus"]
            reasons.append("Existing skills improve employability pathways")

        if profile["family_size"] >= 4 and policy.service_type in {"HOUSING", "HEALTHCARE"}:
            score += self.WEIGHTS["family_support_bonus"]
            reasons.append("Larger family size increases support urgency")

        score = max(0, min(score, 100))
        eligible = score >= policy.min_score
        confidence = round(min(0.99, 0.55 + (score / 200)), 2)

        return {
            "eligible": eligible,
            "score": score,
            "confidence": confidence,
            "reasons": reasons,
        }

    def recommend(self, certificate, top_k: int = 5) -> Dict:
        """
        Generate ranked recommendations and audit-friendly metadata.
        """
        profile = self._build_profile(certificate)
        top_k = self._clamp_int(top_k, default=5, minimum=1, maximum=10)

        recs: List[Dict] = []
        for policy in self.policies:
            scored = self._score_policy(policy, profile)
            if not scored["eligible"]:
                continue
            recs.append(
                {
                    "service_id": policy.service_id,
                    "service_name": policy.name,
                    "service_type": policy.service_type,
                    "eligibility_score": scored["score"],
                    "confidence": scored["confidence"],
                    "min_score": policy.min_score,
                    "documents_required": policy.documents_required,
                    "action_required": "Apply" if scored["score"] >= 70 else "Contact for info",
                    "reasons": scored["reasons"],
                    "score_breakdown": {
                        "base_score": self.BASE_SCORE,
                        "min_required": policy.min_score,
                    },
                }
            )

        recs.sort(key=lambda r: (r["eligibility_score"], r["confidence"]), reverse=True)

        payload = {
            "certificate_id": certificate.certificate_id,
            "model_version": self.model_version,
            "recommended_services": [
                {
                    "service_id": item["service_id"],
                    "service_type": item["service_type"],
                    "eligibility_score": item["eligibility_score"],
                    "min_score": item["min_score"],
                }
                for item in recs
            ],
        }
        payload_str = json.dumps(payload, sort_keys=True)
        decision_hash = self._cached_hash(payload_str)
        profile_hash = self._cached_hash(self._profile_cache_key(certificate, profile))

        return {
            "refugee_name": certificate.refugee_name,
            "certificate_id": certificate.certificate_id,
            "total_eligible": len(recs),
            "recommendations": recs[:top_k],
            "ai_model": {
                "name": "ExplainablePolicyScoring-v1",
                "type": "deterministic",
                "auditability": "high",
                "version": self.model_version,
            },
            "decision_hash": decision_hash,
            "profile_hash": profile_hash,
            "contract_payload": payload,
            "ai_insights": self._insights(profile),
            "next_steps": self._next_steps(recs),
            "risk_flags": self._risk_flags(profile),
            "feature_vector": {
                "age": profile["age"],
                "skills_count": profile["skills_count"],
                "language_proficiency": profile["language_proficiency"],
                "time_since_arrival": profile["time_since_arrival"],
            },
        }

    def batch_recommend(self, certificates: Iterable[Any], top_k: int = 5) -> List[Dict[str, Any]]:
        return [self.recommend(cert, top_k=top_k) for cert in certificates]

    @staticmethod
    def _risk_flags(profile: Dict[str, Any]) -> List[str]:
        flags: List[str] = []
        if profile["time_since_arrival"] <= 1:
            flags.append("urgent_new_arrival")
        if profile["special_needs"]:
            flags.append("medical_priority")
        if profile["family_size"] >= 6:
            flags.append("large_family_support")
        if profile["language_proficiency"] <= 1:
            flags.append("language_access_priority")
        return flags

    @staticmethod
    def find_service_recommendation(ai_result: Dict[str, Any], service_type: str) -> Optional[Dict[str, Any]]:
        stype = (service_type or "").upper()
        for item in ai_result.get("recommendations", []):
            if item.get("service_type") == stype:
                return item
        return None

    @staticmethod
    def _insights(profile: Dict) -> List[str]:
        insights: List[str] = ["Eligibility is computed from verified certificate attributes."]
        if profile["time_since_arrival"] <= 6:
            insights.append("Recent arrival detected: prioritize immediate stabilization services.")
        if profile["employment_status"] == "unemployed":
            insights.append("Employment support has elevated priority for this profile.")
        if profile["has_children"]:
            insights.append("Family composition increases education and healthcare weighting.")
        return insights

    @staticmethod
    def _next_steps(recommendations: List[Dict]) -> List[Dict]:
        steps: List[Dict] = []
        for rec in recommendations[:3]:
            steps.append(
                {
                    "priority": "HIGH" if rec["eligibility_score"] >= 75 else "MEDIUM",
                    "action": f"Proceed with {rec['service_name']}",
                    "timeline": "Within 7 days" if rec["eligibility_score"] >= 75 else "Within 30 days",
                }
            )
        return steps

    @staticmethod
    def min_score_for_service(service_type: str) -> int:
        baseline = {
            "healthcare": 50,
            "education": 50,
            "employment": 55,
            "housing": 50,
            "legal_aid": 50,
            "food_assistance": 50,
            "mental_health": 50,
            "language_training": 50,
        }
        return baseline.get(service_type.lower(), 50)
