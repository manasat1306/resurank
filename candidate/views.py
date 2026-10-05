from django.shortcuts import render, get_object_or_404
from resume_analyzer.models import Job


def job_list(request):
    jobs = Job.objects.filter(status='active').order_by('-created_at')
    return render(request, 'candidate/job_list.html', {
        'jobs': jobs,
    })


def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id, status='active')
    return render(request, 'candidate/job_detail.html', {'job': job})

def apply(request, job_id):
    job = get_object_or_404(Job, id=job_id, status='active')
    return render(request, 'candidate/apply.html', {'job': job})