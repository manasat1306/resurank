from django.contrib.auth.decorators import login_required
from collections import Counter
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q, Avg, Max, Count
from django.shortcuts import render, redirect, get_object_or_404
from .models import Job, Application, StatusHistory, RecruiterProfile
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .settings_forms import ProfileForm
from django.views.decorators.http import require_POST
from .forms import JobForm
from django.core.paginator import Paginator
import pdfplumber
from .resume_quality import analyze_resume_quality
from .resume_parts import extract_resume_parts
from .analyze_forms import AnalyzeResumeForm
from .scoring import score_application
from .plans import (
    get_limits, can_activate_job, can_accept_application,
    get_plan, active_jobs_used, apps_used_this_month,
)


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
    limit_reached = False
    limit_number = None
    if request.method == 'POST':
        form = JobForm(request.POST)
        action = request.POST.get('action')  # 'draft' or 'publish'
        if form.is_valid():
            if action == 'publish' and not form.cleaned_data['required_skills']:
                form.add_error('required_skills', 'Add at least one required skill to publish.')
            elif action == 'publish' and not can_activate_job(request.user):
                limit_reached = True
                limit_number = get_limits(request.user)['active_jobs']
            else:
                job = form.save(commit=False)
                job.recruiter = request.user
                job.similarity_weight = 100 - job.skill_weight
                job.status = 'active' if action == 'publish' else 'draft'
                job.save()
                return redirect('job_list')
    else:
        form = JobForm(initial={'skill_weight': 70})

    return render(request, 'resume_analyzer/job_form.html', {
        'form': form,
        'limit_reached': limit_reached,
        'limit_number': limit_number,
    })

@login_required
def job_edit(request, pk):
    # recruiter=request.user means you can only edit your own jobs
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)
    was_active = job.status == 'active'

    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        action = request.POST.get('action')  # 'save' or 'publish'
        if form.is_valid():
            if action == 'publish' and not form.cleaned_data['required_skills']:
                form.add_error('required_skills', 'Add at least one required skill to publish.')
            elif action == 'publish' and not was_active and not can_activate_job(request.user):
                limit = get_limits(request.user)['active_jobs']
                form.add_error(
                    'required_skills',
                    f'Your Free plan allows {limit} active jobs. Save your changes, or upgrade to Pro to publish more.'
                )
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
        if job.status != 'active' and not can_activate_job(request.user):
            limit = get_limits(request.user)['active_jobs']
            messages.error(
                request,
                f'Your Free plan allows {limit} active jobs. Upgrade to Pro to publish more.'
            )
            return redirect('plans')
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
        'compare_max': get_limits(request.user)['compare'],
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
            if not can_accept_application(request.user):
                limit = get_limits(request.user)['apps_per_month']
                messages.error(
                    request,
                    f'Your Free plan allows {limit} resume uploads per month. Upgrade to Pro for unlimited uploads.'
                )
                return redirect('plans')
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
    ids = ids[:get_limits(request.user)['compare']]

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

@login_required
def analytics(request):
    apps = Application.objects.filter(job__recruiter=request.user)
    scored = apps.filter(final_score__gt=0)
    stats = scored.aggregate(avg=Avg('final_score'), top=Max('final_score'))

    # Status breakdown (all 6 statuses, even if 0)
    raw = {r['status']: r['n'] for r in apps.values('status').annotate(n=Count('id'))}
    status_rows = [
        {'key': key, 'label': label, 'count': raw.get(key, 0)}
        for key, label in Application.STATUS_CHOICES
    ]

    # Applications per week (last 6 weeks)
    now = timezone.now()
    weekly = []
    for i in range(5, -1, -1):
        end = now - timedelta(weeks=i)
        start = end - timedelta(weeks=1)
        weekly.append({
            'label': start.strftime('%b %d'),
            'count': apps.filter(applied_at__gt=start, applied_at__lte=end).count(),
        })

    # Score distribution (6 buckets)
    edges = [(0, 50, '<50'), (50, 60, '50+'), (60, 70, '60+'),
             (70, 80, '70+'), (80, 90, '80+'), (90, 101, '90+')]
    score_buckets = [
        {
            'label': label,
            'low': low,
            'count': scored.filter(final_score__gte=low, final_score__lt=high).count(),
        }
        for low, high, label in edges
    ]

    # Most missing skills, split by severity
    skill_data = {}
    for a in scored:
        sev_map = {}
        for item in (a.severity_analysis or []):
            if isinstance(item, dict):
                sev_map[item.get('skill')] = str(item.get('severity', '')).lower()
        for skill in (a.missing_skills or []):
            sev = sev_map.get(skill, 'unclear')
            if sev not in ('critical', 'moderate'):
                sev = 'unclear'
            row = skill_data.setdefault(
                skill, {'skill': skill, 'critical': 0, 'moderate': 0, 'unclear': 0}
            )
            row[sev] += 1
    top_missing = sorted(
        skill_data.values(),
        key=lambda r: r['critical'] + r['moderate'] + r['unclear'],
        reverse=True,
    )[:6]
    for r in top_missing:
        r['total'] = r['critical'] + r['moderate'] + r['unclear']

    # Jobs performance table
    jobs = (
        Job.objects.filter(recruiter=request.user)
        .annotate(
            app_count=Count('applications'),
            avg_score=Avg('applications__final_score',
                          filter=Q(applications__final_score__gt=0)),
            top_score=Max('applications__final_score'),
        )
        .order_by('-created_at')
    )

    return render(request, 'resume_analyzer/analytics.html', {
        'total_jobs': jobs.count(),
        'active_jobs': jobs.filter(status='active').count(),
        'total_apps': apps.count(),
        'processed_count': scored.count(),
        'shortlisted_count': raw.get('shortlisted', 0),
        'avg_score': stats['avg'] or 0,
        'jobs': jobs,
        'status_rows': status_rows,
        'top_missing': top_missing,
        'chart_data': {
            'weekly': weekly,
            'status': status_rows,
            'scores': score_buckets,
        },
    })

@login_required
def account_settings(request):
    user = request.user
    profile, _ = RecruiterProfile.objects.get_or_create(user=user)

    profile_form = ProfileForm(initial={
        'full_name': user.get_full_name(),
        'company_name': profile.company_name,
    })
    password_form = PasswordChangeForm(user)

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'profile':
            profile_form = ProfileForm(request.POST)
            if profile_form.is_valid():
                parts = profile_form.cleaned_data['full_name'].strip().split(None, 1)
                user.first_name = parts[0] if parts else ''
                user.last_name = parts[1] if len(parts) > 1 else ''
                user.save()
                profile.company_name = profile_form.cleaned_data['company_name'].strip()
                profile.save()
                messages.success(request, 'Your profile has been updated.')
                return redirect('account_settings')

        elif form_type == 'password':
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # keeps you logged in
                messages.success(request, 'Your password has been changed.')
                return redirect('account_settings')

    return render(request, 'resume_analyzer/settings.html', {
        'profile_form': profile_form,
        'password_form': password_form,
    })

@login_required
def help_page(request):
    return render(request, 'resume_analyzer/help.html') 

@login_required
def dashboard(request):
    jobs_qs = Job.objects.filter(recruiter=request.user)
    apps = Application.objects.filter(job__recruiter=request.user)
    scored = apps.filter(final_score__gt=0)
    stats = scored.aggregate(avg=Avg('final_score'))

    recent_jobs = (
        jobs_qs.annotate(
            app_count=Count('applications'),
            shortlisted_count=Count(
                'applications', filter=Q(applications__status='shortlisted')
            ),
        )
        .order_by('-created_at')[:5]
    )
    recent_apps = apps.select_related('job').order_by('-applied_at')[:6]

    return render(request, 'resume_analyzer/dashboard.html', {
        'first_name': request.user.first_name or request.user.username,
        'active_jobs': jobs_qs.filter(status='active').count(),
        'total_apps': apps.count(),
        'shortlisted_count': apps.filter(status='shortlisted').count(),
        'avg_score': stats['avg'] or 0,
        'recent_jobs': recent_jobs,
        'recent_apps': recent_apps,
    })   

@login_required
def plans_page(request):
    limits = get_limits(request.user)
    jobs_used = active_jobs_used(request.user)
    uploads_used = apps_used_this_month(request.user)

    jobs_limit = limits['active_jobs']
    uploads_limit = limits['apps_per_month']

    return render(request, 'resume_analyzer/plans.html', {
        'current_plan': get_plan(request.user),
        'jobs_used': jobs_used,
        'jobs_limit': jobs_limit,
        'jobs_percent': min(round(jobs_used * 100 / jobs_limit), 100) if jobs_limit else 0,
        'uploads_used': uploads_used,
        'uploads_limit': uploads_limit,
        'uploads_percent': min(round(uploads_used * 100 / uploads_limit), 100) if uploads_limit else 0,
    })


@login_required
@require_POST
def switch_plan(request):
    # Demo only: no real payment. Lets you show the full Free/Pro flow.
    new_plan = request.POST.get('plan')
    if new_plan in ('free', 'pro'):
        profile, _ = RecruiterProfile.objects.get_or_create(user=request.user)
        profile.plan = new_plan
        profile.save()
        if new_plan == 'pro':
            messages.success(request, 'You are now on the Pro plan. Enjoy unlimited jobs and uploads.')
        else:
            messages.success(request, 'You are now on the Free plan.')
    return redirect('plans')