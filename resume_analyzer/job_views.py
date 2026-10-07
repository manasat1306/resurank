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
from .analyze_forms import AnalyzeResumeForm
from .scoring import score_application


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



@login_required
def analyze_resume(request):
    if request.method == 'POST':
        form = AnalyzeResumeForm(request.POST, request.FILES, recruiter=request.user)
        if form.is_valid():
            job = form.cleaned_data['job']  # already limited to this recruiter's jobs
            application = Application.objects.create(
                job=job,
                candidate_name=form.cleaned_data['candidate_name'],
                candidate_email=form.cleaned_data['candidate_email'],
                resume_file=form.cleaned_data['resume_file'],
                source='recruiter_upload',
            )
            result = score_application(application)
            if not result['text_found']:
                # scanned / unreadable PDF: remove it and ask for another file
                application.resume_file.delete(save=False)
                application.delete()
                form.add_error('resume_file', 'No readable text found. This can happen with scanned or image-based PDFs. Please try a text-based PDF.')
            else:
                StatusHistory.objects.create(
                    application=application,
                    status='new',
                    changed_by=request.user.username,
                )
                return redirect('candidate_analysis', pk=job.pk, app_id=application.pk)
    else:
        form = AnalyzeResumeForm(recruiter=request.user)

    return render(request, 'resume_analyzer/analyze_resume.html', {'form': form})

@login_required
def compare_candidates(request, pk):
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)

    ids = []
    for part in request.GET.get('ids', '').split(','):
        part = part.strip()
        if part.isdigit() and int(part) not in ids:
            ids.append(int(part))
    ids = ids[:4]

    found = {a.pk: a for a in job.applications.filter(pk__in=ids)}
    candidates = [found[i] for i in ids if i in found]

    if len(candidates) < 2:
        return redirect('job_applicants', pk=job.pk)

    ranked_ids = list(
        job.applications.order_by('-final_score', '-applied_at').values_list('pk', flat=True)
    )
    for a in candidates:
        a.rank = ranked_ids.index(a.pk) + 1
        a.matched_count = len(a.matched_skills or [])
        a.total_skills = a.matched_count + len(a.missing_skills or [])
        a.skill_percent = round(a.matched_count * 100 / a.total_skills) if a.total_skills else 0

    skill_order = []
    for a in candidates:
        for s in list(a.matched_skills or []) + list(a.missing_skills or []):
            if s not in skill_order:
                skill_order.append(s)

    skill_rows = []
    for skill in skill_order:
        cells = []
        for a in candidates:
            if skill in (a.matched_skills or []):
                cells.append({'found': True, 'severity': '', 'note': ''})
            else:
                info = next(
                    (i for i in (a.severity_analysis or []) if i.get('skill') == skill),
                    None,
                )
                cells.append({
                    'found': False,
                    'severity': info.get('severity', 'unclear') if info else 'unclear',
                    'note': info.get('note', '') if info else '',
                })
        skill_rows.append({'skill': skill, 'cells': cells})

    return render(request, 'resume_analyzer/compare.html', {
        'job': job,
        'candidates': candidates,
        'total_count': len(ranked_ids),
        'best_score': max(a.final_score for a in candidates),
        'skill_rows': skill_rows,
    })

@login_required
def compare_picker(request):
    # Only this recruiter's own jobs
    jobs = list(Job.objects.filter(recruiter=request.user).order_by('-created_at'))
    for j in jobs:
        j.app_count = j.applications.count()

    selected_job = None
    applicants = []
    job_id = request.GET.get('job', '')
    if job_id.isdigit():
        selected_job = next((j for j in jobs if j.pk == int(job_id)), None)

    if selected_job:
        applicants = list(selected_job.applications.order_by('-final_score', '-applied_at'))
        for i, a in enumerate(applicants, start=1):
            a.rank = i

    return render(request, 'resume_analyzer/compare_picker.html', {
        'jobs': jobs,
        'selected_job': selected_job,
        'applicants': applicants,
    })    