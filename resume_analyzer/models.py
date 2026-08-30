from django.db import models

class Resume(models.Model):
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    raw_text = models.TextField()
    skills = models.JSONField(default=list)  # stores list like ['Python', 'SQL']
    final_score = models.FloatField(default=0)
    score_breakdown = models.JSONField(default=list)

    def __str__(self):        
        return self.file_name
class JobDescription(models.Model):
    title = models.CharField(max_length=255)
    description_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title