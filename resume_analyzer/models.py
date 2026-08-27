from django.db import models

class Resume(models.Model):
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    raw_text = models.TextField()
    skills = models.JSONField(default=list)  # stores list like ['Python', 'SQL']

    def __str__(self):
        return self.file_name