from django.db import models
from django.contrib.auth.models import User

class Certificate(models.Model):
    refugee_name = models.CharField(max_length=255)
    country_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    address = models.CharField(max_length=255)
    gender = models.CharField(max_length=10)
    certificate_id = models.CharField(max_length=50, unique=True)
    issue_date = models.DateField(auto_now_add=True)
    valid_until = models.DateField()
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Extended profile for AI matching
    skills = models.TextField(blank=True, help_text="Comma-separated skills")
    employment_status = models.CharField(max_length=20, default='unemployed', choices=[
        ('unemployed', 'Unemployed'),
        ('employed', 'Employed'),
        ('self_employed', 'Self-Employed'),
        ('student', 'Student'),
    ])
    family_size = models.IntegerField(default=1)
    has_children = models.BooleanField(default=False)
    language_proficiency = models.IntegerField(default=1, choices=[
        (1, 'None/Basic'),
        (2, 'Elementary'),
        (3, 'Intermediate'),
        (4, 'Advanced'),
        (5, 'Fluent'),
    ])
    time_since_arrival = models.IntegerField(default=1, help_text="Months since arrival")
    special_needs = models.BooleanField(default=False)
    
    def __str__(self):
        return self.certificate_id


class RefugeeProfile(models.Model):
    certificate = models.OneToOneField(Certificate, on_delete=models.CASCADE, related_name='ssi_profile')
    did = models.CharField(max_length=100, unique=True)
    eth_address = models.CharField(max_length=42)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    interested_healthcare = models.BooleanField(default=True)
    interested_education = models.BooleanField(default=False)
    interested_employment = models.BooleanField(default=False)
    interested_housing = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.certificate.refugee_name} - {self.did}"


class ZKProofRecord(models.Model):
    refugee = models.ForeignKey(RefugeeProfile, on_delete=models.CASCADE, related_name='zk_proofs')
    service_type = models.CharField(max_length=50)
    commitment_hash = models.CharField(max_length=100)
    proof_data = models.JSONField()
    generated_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=True)
    
    def __str__(self):
        return f"ZK Proof for {self.refugee.certificate.refugee_name} - {self.service_type}"


class ServiceEligibility(models.Model):
    refugee = models.ForeignKey(RefugeeProfile, on_delete=models.CASCADE, related_name='eligibilities')
    service_name = models.CharField(max_length=100)
    service_type = models.CharField(max_length=50)
    eligibility_score = models.IntegerField()
    documents_required = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.refugee.certificate.refugee_name} - {self.service_name} ({self.eligibility_score}%)"
