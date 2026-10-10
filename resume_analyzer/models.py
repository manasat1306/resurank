from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
  
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



class Application(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('under_review', 'Under Review'),
        ('shortlisted', 'Shortlisted'),
        ('interview', 'Interview'),
        ('selected', 'Selected'),
        ('rejected', 'Rejected'),
    ]

    SOURCE_CHOICES = [
        ('applied', 'Applied'),
        ('recruiter_upload', 'Recruiter Upload'),
    ]

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications'
    )

    candidate_name = models.CharField(max_length=255)
    candidate_email = models.EmailField()
    candidate_phone = models.CharField(max_length=30, blank=True)

    resume_file = models.FileField(upload_to='applications/resumes/')
    consent_given = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        db_index=True
    )

    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='applied',
        db_index=True
    )

    # Used later for candidate ranking / analysis
    final_score = models.FloatField(default=0, db_index=True)
    skill_score = models.FloatField(default=0)
    similarity_score = models.FloatField(default=0)

    matched_skills = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    severity_analysis = models.JSONField(default=list, blank=True)

    # Token used by the candidate tracking page
    tracking_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True
    )

    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.candidate_name} - {self.job.title}"    

class StatusHistory(models.Model):
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='history'
    )
    status = models.CharField(max_length=20, choices=Application.STATUS_CHOICES)
    changed_by = models.CharField(max_length=100, default='System')
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.application} → {self.status}"

class RecruiterProfile(models.Model):
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company_name = models.CharField(max_length=150, blank=True)
    plan = models.CharField(max_length=10, choices=PLAN_CHOICES, default='free')

    def __str__(self):
        return f"{self.user.username} - {self.company_name}"