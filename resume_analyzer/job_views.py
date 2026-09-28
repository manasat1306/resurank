from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Job


@login_required
def job_list(request):
    jobs = Job.objects.filter(recruiter=request.user).order_by('-created_at')
    return render(request, 'resume_analyzer/job_list.html', {'jobs': jobs})