from django.contrib import admin

# Register your models here.
from .models import Resume, JobDescription

admin.site.register(Resume)
admin.site.register(JobDescription)