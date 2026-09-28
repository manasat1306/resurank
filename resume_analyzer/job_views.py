from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from .models import Job


@login_required
def job_list(request):
    # only this recruiter's jobs (data isolation)
    all_jobs = Job.objects.filter(recruiter=request.user)

    tab = request.GET.get('status', 'all')
    q = request.GET.get('q', '').strip()

    jobs = all_jobs
    if tab in ('active', 'draft', 'closed'):
        jobs = jobs.filter(status=tab)
    if q:
        jobs = jobs.filter(
            Q(title__icontains=q) |
            Q(department__icontains=q) |
            Q(location__icontains=q)
        )

    counts = {
        'all': all_jobs.count(),
        'active': all_jobs.filter(status='active').count(),
        'draft': all_jobs.filter(status='draft').count(),
        'closed': all_jobs.filter(status='closed').count(),
    }

    return render(request, 'resume_analyzer/job_list.html', {
        'jobs': jobs.order_by('-created_at'),
        'counts': counts,
        'tab': tab,
        'q': q,
        'tabs': [('all', 'All Jobs'), ('active', 'Active'), ('draft', 'Draft'), ('closed', 'Closed')],
    })