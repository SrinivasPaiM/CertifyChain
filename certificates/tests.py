from datetime import date, timedelta
import json
from pathlib import Path
from types import SimpleNamespace

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .ai_decision_engine import AIServiceDecisionEngine
from .models import Certificate, RefugeeProfile, ZKProofRecord
from .vector_matcher import ServiceVectorMatcher


class AIServiceDecisionEngineTests(SimpleTestCase):
	def setUp(self):
		self.engine = AIServiceDecisionEngine()

	def _certificate(self, **overrides):
		defaults = {
			"certificate_id": "REF-ABC-123",
			"refugee_name": "Test User",
			"date_of_birth": date(1997, 4, 12),
			"skills": "communication, teamwork, basic_computing",
			"employment_status": "unemployed",
			"family_size": 5,
			"has_children": True,
			"language_proficiency": 2,
			"time_since_arrival": 2,
			"special_needs": False,
		}
		defaults.update(overrides)
		return SimpleNamespace(**defaults)

	def test_recommend_returns_hash_and_model_metadata(self):
		cert = self._certificate()
		result = self.engine.recommend(cert)

		self.assertIn("decision_hash", result)
		self.assertIn("profile_hash", result)
		self.assertEqual(len(result["decision_hash"]), 64)
		self.assertEqual(len(result["profile_hash"]), 64)
		self.assertEqual(result["ai_model"]["name"], "ExplainablePolicyScoring-v1")
		self.assertEqual(result["ai_model"]["version"], "2.0.0")
		self.assertEqual(result["ai_model"]["matching"]["semantic"], "cosine_similarity")
		self.assertGreaterEqual(result["total_eligible"], 1)

	def test_new_arrival_boosts_housing_likelihood(self):
		recent_cert = self._certificate(time_since_arrival=1)
		settled_cert = self._certificate(time_since_arrival=18)

		recent = self.engine.recommend(recent_cert)
		settled = self.engine.recommend(settled_cert)

		def find_housing(payload):
			for rec in payload["recommendations"]:
				if rec["service_type"] == "HOUSING":
					return rec["eligibility_score"]
			return 0

		self.assertGreater(find_housing(recent), find_housing(settled))

	def test_unemployed_user_gets_employment_match(self):
		cert = self._certificate(employment_status="unemployed")
		result = self.engine.recommend(cert)

		employment_services = [
			rec for rec in result["recommendations"] if rec["service_type"] == "EMPLOYMENT"
		]
		self.assertTrue(employment_services)

	def test_decision_hash_is_deterministic_for_same_profile(self):
		cert = self._certificate()
		result_1 = self.engine.recommend(cert)
		result_2 = self.engine.recommend(cert)

		self.assertEqual(result_1["decision_hash"], result_2["decision_hash"])
		self.assertEqual(result_1["profile_hash"], result_2["profile_hash"])

	def test_top_k_is_bounded(self):
		cert = self._certificate()

		one = self.engine.recommend(cert, top_k=1)
		many = self.engine.recommend(cert, top_k=100)

		self.assertLessEqual(len(one["recommendations"]), 1)
		self.assertLessEqual(len(many["recommendations"]), 10)

	def test_risk_flags_emitted(self):
		cert = self._certificate(
			time_since_arrival=1,
			special_needs=True,
			family_size=7,
			language_proficiency=1,
		)
		result = self.engine.recommend(cert)

		self.assertIn("urgent_new_arrival", result["risk_flags"])
		self.assertIn("medical_priority", result["risk_flags"])
		self.assertIn("large_family_support", result["risk_flags"])
		self.assertIn("language_access_priority", result["risk_flags"])

	def test_find_service_recommendation(self):
		cert = self._certificate()
		result = self.engine.recommend(cert)

		health = self.engine.find_service_recommendation(result, "healthcare")
		missing = self.engine.find_service_recommendation(result, "cash_assistance")

		self.assertIsNotNone(health)
		self.assertEqual(health["service_type"], "HEALTHCARE")
		self.assertIsNone(missing)

	def test_batch_recommend_returns_all_results(self):
		certs = [
			self._certificate(certificate_id="REF-1", refugee_name="A"),
			self._certificate(certificate_id="REF-2", refugee_name="B", special_needs=True),
		]
		results = self.engine.batch_recommend(certs, top_k=3)

		self.assertEqual(len(results), 2)
		self.assertLessEqual(len(results[0]["recommendations"]), 3)


class AIWorkflowIntegrationTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="issuer", password="pass123")
		self.certificate = Certificate.objects.create(
			refugee_name="Integration User",
			country_name="CountryX",
			date_of_birth=date(1995, 1, 15),
			address="Sample Address",
			gender="other",
			certificate_id="REF-INT-001",
			valid_until=date(2030, 1, 1),
			generated_by=self.user,
			skills="communication,teamwork",
			employment_status="unemployed",
			family_size=4,
			has_children=True,
			language_proficiency=2,
			time_since_arrival=2,
			special_needs=False,
		)

	def test_service_matching_returns_audit_metadata(self):
		response = self.client.post(
			reverse("service_matching"),
			data=json.dumps({"certificate_id": self.certificate.certificate_id, "top_k": 3}),
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertIn("decision_hash", payload)
		self.assertIn("profile_hash", payload)
		self.assertIn("risk_flags", payload)
		self.assertIn("matching", payload["ai_model"])
		self.assertEqual(payload["ai_model"]["matching"]["semantic"], "cosine_similarity")
		self.assertLessEqual(len(payload["recommendations"]), 3)

		profile = RefugeeProfile.objects.get(certificate=self.certificate)
		self.assertTrue(profile.did.startswith("did:ethr:"))

	def test_generate_zk_proof_contains_ai_decision_hash(self):
		response = self.client.post(
			reverse("generate_zk_proof"),
			data=json.dumps({
				"certificate_id": self.certificate.certificate_id,
				"service_type": "healthcare",
			}),
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertTrue(payload["success"])
		self.assertIn("ai_decision_hash", payload["proof"])
		self.assertIn("risk_flags", payload)

		self.assertEqual(
			ZKProofRecord.objects.filter(refugee__certificate=self.certificate).count(),
			1,
		)

	def test_service_matching_rejects_unknown_certificate(self):
		response = self.client.post(
			reverse("service_matching"),
			data=json.dumps({"certificate_id": "REF-UNKNOWN"}),
			content_type="application/json",
		)
		self.assertEqual(response.status_code, 400)
		self.assertIn("error", response.json())


class ProjectRouteAndFlowTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="adminuser", password="pass123")
		self.certificate = Certificate.objects.create(
			refugee_name="Route User",
			country_name="CountryY",
			date_of_birth=date(1990, 6, 5),
			address="Route Address",
			gender="male",
			certificate_id="REF-ROUTE-001",
			valid_until=date.today() + timedelta(days=365),
			generated_by=self.user,
			transaction_hash="0x" + "a" * 64,
			skills="communication,analysis",
			employment_status="unemployed",
			family_size=3,
			has_children=False,
			language_proficiency=2,
			time_since_arrival=4,
			special_needs=False,
		)

	def test_public_routes_load(self):
		routes = [
			reverse("home"),
			reverse("ssi_dashboard"),
			reverse("verify_certificate"),
			reverse("create_identity"),
			reverse("service_matching"),
			reverse("generate_zk_proof"),
			reverse("request_service"),
			reverse("verify_eligibility"),
			reverse("api_documentation"),
			reverse("about"),
			reverse("community"),
			reverse("getapp"),
		]
		for route in routes:
			response = self.client.get(route)
			self.assertEqual(response.status_code, 200, msg=f"Route failed: {route}")

	def test_login_and_logout_pages_load(self):
		login_response = self.client.get(reverse("login"))
		self.assertEqual(login_response.status_code, 200)

		self.client.login(username="adminuser", password="pass123")
		logout_response = self.client.post(reverse("logout"))
		self.assertIn(logout_response.status_code, [200, 302])

	def test_issue_certificate_requires_login(self):
		response = self.client.get(reverse("issue_certificate"))
		self.assertEqual(response.status_code, 302)

	def test_issue_certificate_post_flow(self):
		self.client.login(username="adminuser", password="pass123")
		payload = {
			"transaction_hash": "0x" + "b" * 64,
			"recipient_address": "0x" + "1" * 40,
			"certificate_data": "Generated in integration test",
			"valid_until": (date.today() + timedelta(days=365)).isoformat(),
			"issuing_date": date.today().isoformat(),
			"address": "Integration Address",
			"refugee_name": "Issued User",
			"date_of_birth": date(1996, 1, 1).isoformat(),
			"country": "CountryZ",
			"gender": "female",
			"skills": "teaching,healthcare",
			"employment_status": "unemployed",
			"family_size": 2,
			"has_children": False,
			"language_proficiency": 3,
			"time_since_arrival": 6,
			"special_needs": False,
		}

		response = self.client.post(reverse("issue_certificate"), data=payload)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Certificate Generated Successfully")

	def test_service_request_and_verifier_flow(self):
		RefugeeProfile.objects.create(
			certificate=self.certificate,
			did="did:ethr:0x" + "2" * 40,
			eth_address="0x" + "2" * 40,
		)

		request_response = self.client.post(
			reverse("request_service"),
			data=json.dumps({
				"certificate_id": self.certificate.certificate_id,
				"service_type": "healthcare",
			}),
			content_type="application/json",
		)
		self.assertEqual(request_response.status_code, 200)
		self.assertIn("presentation", request_response.json())

		verify_response = self.client.post(
			reverse("verify_eligibility"),
			data=json.dumps({
				"proof": {
					"zk_proof": {
						"public_signals": ["healthcare", 50, 1],
					}
				}
			}),
			content_type="application/json",
		)
		self.assertEqual(verify_response.status_code, 200)
		self.assertTrue(verify_response.json()["valid"])

	def test_api_services_endpoint(self):
		response = self.client.get(reverse("api_service_eligibility", kwargs={"service_type": 0}))
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()["service_type"], "HEALTHCARE")

	def test_api_documentation_html_and_json_modes(self):
		html_response = self.client.get(reverse("api_documentation"))
		self.assertEqual(html_response.status_code, 200)
		self.assertContains(html_response, "CertifyChain SSI API v2.0")
		self.assertIn("text/html", html_response["Content-Type"])

		json_response = self.client.get(reverse("api_documentation") + "?format=json")
		self.assertEqual(json_response.status_code, 200)
		self.assertEqual(json_response.json()["title"], "CertifyChain SSI API v2.0")


class SmartContractSourceTests(SimpleTestCase):
	def _read_contract(self, name):
		root = Path(__file__).resolve().parents[1]
		return (root / "contracts" / name).read_text(encoding="utf-8")

	def test_certificate_contract_has_required_functions(self):
		source = self._read_contract("Certificate.sol")
		self.assertIn("function issueCertificate(", source)
		self.assertIn("function verifyCertificateById", source)
		self.assertIn("function verifyCertificateByAddress", source)

	def test_privacy_contract_has_required_functions(self):
		source = self._read_contract("PrivacyPreservingIdentity.sol")
		self.assertIn("function registerIdentity", source)
		self.assertIn("function submitEligibilityProof", source)
		self.assertIn("function verifyEligibility", source)


class VectorMatcherTests(SimpleTestCase):
	def setUp(self):
		self.engine = AIServiceDecisionEngine()
		self.matcher = ServiceVectorMatcher(self.engine.policies)

	def test_match_profile_returns_scores_for_all_services(self):
		profile = {
			"age": 28,
			"employment_status": "unemployed",
			"family_size": 5,
			"has_children": True,
			"language_proficiency": 2,
			"time_since_arrival": 1,
			"special_needs": False,
			"skills_count": 3,
		}
		results = self.matcher.match_profile(profile, top_k=len(self.engine.policies))

		self.assertEqual(len(results), len(self.engine.policies))
		self.assertTrue(all(0.0 <= score <= 1.0 for score in results.values()))

	def test_match_profile_is_deterministic(self):
		profile = {
			"age": 34,
			"employment_status": "unemployed",
			"family_size": 2,
			"has_children": False,
			"language_proficiency": 3,
			"time_since_arrival": 8,
			"special_needs": True,
			"skills_count": 4,
		}
		first = self.matcher.match_profile(profile, top_k=5)
		second = self.matcher.match_profile(profile, top_k=5)

		self.assertEqual(first, second)
