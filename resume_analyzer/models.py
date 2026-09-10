from django.db import models
from django.contrib.auth.models import User

class Resume(models.Model):
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    raw_text = models.TextField()
    skills = models.JSONField(default=list)
    final_score = models.FloatField(default=0, db_index=True)
    score_breakdown = models.JSONField(default=list)

    def __str__(self):
        return self.file_name


class JobDescription(models.Model):
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=255)
    description_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title