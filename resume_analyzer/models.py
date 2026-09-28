from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

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


class Job(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]
    TYPE_CHOICES = [
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('internship', 'Internship'),
        ('contract', 'Contract'),
    ]

    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=255)
    department = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    experience = models.CharField(max_length=100, blank=True)
    job_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='full_time')
    description_text = models.TextField()
    required_skills = models.JSONField(default=list, blank=True)
    preferred_skills = models.JSONField(default=list, blank=True)
    education = models.CharField(max_length=255, blank=True)
    skill_weight = models.PositiveSmallIntegerField(
        default=70, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    similarity_weight = models.PositiveSmallIntegerField(default=30)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title