"""
Vector similarity matcher for service recommendations.

This module builds a service vector index and scores a refugee profile using
cosine similarity. FAISS is used when available for fast nearest-neighbor
search; otherwise a deterministic pure-Python cosine fallback is used.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class PolicyVector:
    service_id: str
    values: Tuple[float, ...]


class ServiceVectorMatcher:
    """Cosine-similarity service matcher with optional FAISS acceleration."""

    DIMENSIONS = 11

    def __init__(self, policies: Iterable) -> None:
        self._policy_ids: List[str] = []
        self._policy_vectors: List[Tuple[float, ...]] = []
        self._faiss_index = None
        self._faiss_numpy = None

        for policy in policies:
            self._policy_ids.append(policy.service_id)
            self._policy_vectors.append(self._policy_to_vector(policy))

        self.backend = "python-cosine"
        self._init_faiss_index()

    def _init_faiss_index(self) -> None:
        try:
            import numpy as np  # type: ignore
            import faiss  # type: ignore
        except Exception:
            return

        if not self._policy_vectors:
            return

        matrix = np.asarray(self._policy_vectors, dtype="float32")
        matrix = self._normalize_matrix(matrix)
        index = faiss.IndexFlatIP(self.DIMENSIONS)
        index.add(matrix)

        self._faiss_index = index
        self._faiss_numpy = np
        self.backend = "faiss-cosine"

    @staticmethod
    def _policy_to_vector(policy) -> Tuple[float, ...]:
        stype = policy.service_type
        service_flags = {
            "HEALTHCARE": (1.0, 0.0, 0.0, 0.0, 0.0),
            "EDUCATION": (0.0, 1.0, 0.0, 0.0, 0.0),
            "EMPLOYMENT": (0.0, 0.0, 1.0, 0.0, 0.0),
            "HOUSING": (0.0, 0.0, 0.0, 1.0, 0.0),
            "FOOD_ASSISTANCE": (0.0, 0.0, 0.0, 0.0, 1.0),
            "LEGAL_AID": (0.3, 0.2, 0.2, 0.2, 0.1),
            "MENTAL_HEALTH": (0.7, 0.1, 0.0, 0.1, 0.1),
            "LANGUAGE_TRAINING": (0.0, 0.6, 0.4, 0.0, 0.0),
        }.get(stype, (0.2, 0.2, 0.2, 0.2, 0.2))

        age_floor = min(1.0, max(0.0, policy.min_age / 100.0))
        min_score = min(1.0, max(0.0, policy.min_score / 100.0))

        return (
            age_floor,
            min_score,
            *service_flags,
            1.0 if stype in {"EDUCATION", "HEALTHCARE"} else 0.0,  # children affinity
            1.0 if stype in {"EMPLOYMENT", "LANGUAGE_TRAINING"} else 0.0,  # language/skills affinity
            1.0 if stype in {"HOUSING", "FOOD_ASSISTANCE"} else 0.0,  # new arrival affinity
            1.0 if stype in {"HEALTHCARE", "MENTAL_HEALTH"} else 0.0,  # special needs affinity
        )

    @staticmethod
    def _profile_to_vector(profile: Dict[str, int]) -> Tuple[float, ...]:
        age = min(1.0, max(0.0, profile["age"] / 100.0))
        language_low = 1.0 - (min(5, max(1, profile["language_proficiency"])) - 1) / 4.0
        unemployed = 1.0 if profile["employment_status"] == "unemployed" else 0.0
        has_children = 1.0 if profile["has_children"] else 0.0
        family_large = 1.0 if profile["family_size"] >= 4 else 0.0
        new_arrival = 1.0 if profile["time_since_arrival"] <= 3 else 0.0
        special_needs = 1.0 if profile["special_needs"] else 0.0
        skills_strength = min(1.0, profile["skills_count"] / 6.0)

        service_interest = (
            special_needs * 0.4 + has_children * 0.3 + family_large * 0.3,  # healthcare
            has_children * 0.5 + language_low * 0.5,  # education
            unemployed * 0.6 + skills_strength * 0.4,  # employment
            new_arrival * 0.7 + family_large * 0.3,  # housing
            new_arrival * 0.8 + family_large * 0.2,  # food
        )

        min_score_proxy = min(1.0, 0.5 + 0.2 * (1.0 - language_low) + 0.3 * skills_strength)

        return (
            age,
            min_score_proxy,
            *service_interest,
            has_children,
            (language_low + skills_strength) / 2.0,
            new_arrival,
            special_needs,
        )

    @staticmethod
    def _normalize_vector(values: Tuple[float, ...]) -> Tuple[float, ...]:
        norm = math.sqrt(sum(v * v for v in values))
        if norm == 0:
            return values
        return tuple(v / norm for v in values)

    @staticmethod
    def _normalize_matrix(matrix):
        # `matrix` is a float32 numpy array.
        norms = (matrix ** 2).sum(axis=1) ** 0.5
        norms[norms == 0] = 1.0
        return matrix / norms[:, None]

    @staticmethod
    def _dot(a: Tuple[float, ...], b: Tuple[float, ...]) -> float:
        return sum(x * y for x, y in zip(a, b))

    def match_profile(self, profile: Dict[str, int], top_k: Optional[int] = None) -> Dict[str, float]:
        """
        Return mapping: service_id -> cosine similarity in [0, 1].
        """
        if not self._policy_ids:
            return {}

        limit = len(self._policy_ids) if top_k is None else max(1, min(top_k, len(self._policy_ids)))
        query = self._normalize_vector(self._profile_to_vector(profile))

        if self._faiss_index is not None and self._faiss_numpy is not None:
            np = self._faiss_numpy
            query_arr = np.asarray([query], dtype="float32")
            scores, indices = self._faiss_index.search(query_arr, limit)
            result: Dict[str, float] = {}
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0:
                    continue
                result[self._policy_ids[idx]] = max(0.0, min(1.0, float(score)))
            return result

        # Deterministic fallback without external dependencies.
        scored: List[Tuple[int, float]] = []
        for idx, vector in enumerate(self._policy_vectors):
            sim = self._dot(query, self._normalize_vector(vector))
            sim = max(0.0, min(1.0, sim))
            scored.append((idx, sim))

        scored.sort(key=lambda item: item[1], reverse=True)

        return {
            self._policy_ids[idx]: score
            for idx, score in scored[:limit]
        }
