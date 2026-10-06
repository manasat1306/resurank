from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg, Max
from django.shortcuts import render, redirect, get_object_or_404
from .models import Job, Application, StatusHistory
from django.views.decorators.http import require_POST
from .forms import JobForm
from django.core.paginator import Paginator
import pdfplumber
from .resume_quality import analyze_resume_quality
from .resume_parts import extract_resume_parts


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
    applications = list(job.applications.order_by('-final_score', '-applied_at'))
    for i, a in enumerate(applications, start=1):
        a.rank = i
        a.matched_count = len(a.matched_skills or [])
        a.total_skills = a.matched_count + len(a.missing_skills or [])
        a.skill_percent = round(a.matched_count * 100 / a.total_skills) if a.total_skills else 0
    scored = job.applications.filter(final_score__gt=0)
    stats = scored.aggregate(avg=Avg('final_score'), top=Max('final_score'))
    return render(request, 'resume_analyzer/job_applicants.html', {
        'job': job,
        'applications': applications,
        'total_count': len(applications),
        'shortlisted_count': job.applications.filter(status='shortlisted').count(),
        'avg_score': stats['avg'] or 0,
        'top_score': stats['top'] or 0,
    })

@login_required
def candidate_analysis(request, pk, app_id):
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)
    application = get_object_or_404(Application, pk=app_id, job=job)

    quality = None
    parts = None
    try:
        text = ""
        with application.resume_file.open('rb') as f:
            with pdfplumber.open(f) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text(x_tolerance=1.5)
                    if page_text:
                        text += page_text + "\n"
        if text.strip():
            quality = analyze_resume_quality(text)
            parts = extract_resume_parts(
                text,
                required=job.required_skills,
                preferred=job.preferred_skills,
            )
    except Exception:
        quality = None
        parts = None

    return render(request, 'resume_analyzer/candidate_analysis.html', {
        'job': job,
        'application': application,
        'quality': quality,
        'parts': parts,
    })



@login_required
@require_POST
def application_set_status(request, pk, app_id):
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)
    application = get_object_or_404(Application, pk=app_id, job=job)

    new_status = request.POST.get('status')
    if new_status in ('under_review', 'shortlisted', 'rejected') and new_status != application.status:
        application.status = new_status
        application.save()
        StatusHistory.objects.create(
            application=application,
            status=new_status,
            changed_by=request.user.username,
        )

    return redirect('candidate_analysis', pk=job.pk, app_id=application.pk)    