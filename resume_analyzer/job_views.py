from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from .models import Job
from .forms import JobForm
from django.core.paginator import Paginator


@login_required
def job_list(request):
    # Only show jobs belonging to the logged-in recruiter
    all_jobs = Job.objects.filter(recruiter=request.user)

    tab = request.GET.get('status', 'all')
    q = request.GET.get('q', '').strip()

    jobs = all_jobs

    # Status filter
    if tab in ('active', 'draft', 'closed'):
        jobs = jobs.filter(status=tab)

    # Search
    if q:
        jobs = jobs.filter(
            Q(title__icontains=q) |
            Q(department__icontains=q) |
            Q(location__icontains=q)
        )

    # Counts
    counts = {
        'all': all_jobs.count(),
        'active': all_jobs.filter(status='active').count(),
        'draft': all_jobs.filter(status='draft').count(),
        'closed': all_jobs.filter(status='closed').count(),
    }

    # Newest first
    jobs = jobs.order_by('-created_at')

    # Pagination
    paginator = Paginator(jobs, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'resume_analyzer/job_list.html', {
        'jobs': page_obj,
        'page_obj': page_obj,
        'counts': counts,
        'tab': tab,
        'q': q,
        'tabs': [
            ('all', 'All Jobs'),
            ('active', 'Active'),
            ('draft', 'Draft'),
            ('closed', 'Closed'),
        ],
    })

@login_required
def job_create(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        action = request.POST.get('action')  # 'draft' or 'publish'
        if form.is_valid():
            if action == 'publish' and not form.cleaned_data['required_skills']:
                form.add_error('required_skills', 'Add at least one required skill to publish.')
            else:
                job = form.save(commit=False)
                job.recruiter = request.user
                job.similarity_weight = 100 - job.skill_weight
                job.status = 'active' if action == 'publish' else 'draft'
                job.save()
                return redirect('job_list')
    else:
        form = JobForm(initial={'skill_weight': 70})

    return render(request, 'resume_analyzer/job_form.html', {'form': form})

@login_required
def job_edit(request, pk):
    # recruiter=request.user means you can only edit your own jobs
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)

    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        action = request.POST.get('action')  # 'save' or 'publish'
        if form.is_valid():
            if action == 'publish' and not form.cleaned_data['required_skills']:
                form.add_error('required_skills', 'Add at least one required skill to publish.')
            else:
                job = form.save(commit=False)
                job.similarity_weight = 100 - job.skill_weight
                if action == 'publish':
                    job.status = 'active'
                job.save()
                return redirect('job_list')
    else:
        form = JobForm(instance=job)

    return render(request, 'resume_analyzer/job_form.html', {
        'form': form, 'job': job, 'is_edit': True,
    })

@login_required
def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)
    return render(request, 'resume_analyzer/job_detail.html', {
        'job': job,
        'applicant_count': job.applications.count(),
        'shortlisted_count': job.applications.filter(status='shortlisted').count(),
    })

@login_required
def job_publish(request, pk):
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)
    if request.method == 'POST':
        if not job.required_skills:
            return redirect('job_edit', pk=job.pk)
        job.status = 'active'
        job.save()
    return redirect('job_detail', pk=job.pk)


@login_required
def job_close(request, pk):
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)
    if request.method == 'POST':
        job.status = 'closed'
        job.save()
    return redirect('job_detail', pk=job.pk)    

@login_required
def job_applicants(request, pk):
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)
    applications = job.applications.order_by('-final_score', '-applied_at')
    return render(request, 'resume_analyzer/job_applicants.html', {
        'job': job,
        'applications': applications,
    })