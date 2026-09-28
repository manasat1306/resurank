from django.contrib import admin

# Register your models here.
from .models import Resume, Job

admin.site.register(Resume)
admin.site.register(Job)