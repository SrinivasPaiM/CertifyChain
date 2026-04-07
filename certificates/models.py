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

    def __str__(self):
        return self.certificate_id
