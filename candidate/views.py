from django.shortcuts import render, get_object_or_404, redirect
from resume_analyzer.models import Job, Application
from .forms import ApplyForm
from django.db.models import Q
import re
import uuid

def job_list(request):
    q_raw = request.GET.get('q', '').strip()
    q = q_raw.lower()
    department = request.GET.get('department', '')
    job_type = request.GET.get('job_type', '')
    experience = request.GET.get('experience', '')
    location = request.GET.get('location', '')
    sort = request.GET.get('sort', 'newest')

    active = Job.objects.filter(status='active')
    jobs = active

    if department:
        jobs = jobs.filter(department=department)
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    if experience:
        jobs = jobs.filter(experience=experience)
    if location:
        jobs = jobs.filter(location=location)

    jobs = jobs.order_by('created_at' if sort == 'oldest' else '-created_at')

    if q:
        def matches(job):
            parts = [job.title, job.department, job.location]
            parts += [str(s) for s in job.required_skills]
            parts += [str(s) for s in job.preferred_skills]
            text = ' ' + ' '.join(parts).lower().replace('/', ' ').replace('-', ' ')
            return (' ' + q) in text

        jobs = [job for job in jobs if matches(job)]

    def options(field):
        values = active.exclude(**{field: ''}).values_list(field, flat=True)
        return sorted(set(values))

    return render(request, 'candidate/job_list.html', {
        'jobs': jobs,
        'q': q_raw,
        'department': department,
        'job_type': job_type,
        'experience': experience,
        'location': location,
        'sort': sort,
        'departments': options('department'),
        'experiences': options('experience'),
        'locations': options('location'),
        'job_types': Job.TYPE_CHOICES,
    })
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id, status='active')
    return render(request, 'candidate/job_detail.html', {'job': job})

def apply(request, job_id):
    job = get_object_or_404(Job, id=job_id, status='active')

    if request.method == 'POST':
        form = ApplyForm(request.POST, request.FILES, job=job)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.source = 'applied'
            application.save()
            return redirect('candidate:apply_success', token=application.tracking_token)
    else:
        form = ApplyForm(job=job)

    return render(request, 'candidate/apply.html', {'job': job, 'form': form})

   
def apply_success(request, token):
       application = get_object_or_404(Application, tracking_token=token)
       return render(request, 'candidate/apply_success.html', {'application': application})

TRACK_STEPS = ['Applied', 'Under Review', 'Shortlisted', 'Interview', 'Decision']
STATUS_TO_STEP = {
    'new': 0,
    'under_review': 1,
    'shortlisted': 2,
    'interview': 3,
    'selected': 4,
    'rejected': 4,
}


def track(request, token):
    application = get_object_or_404(Application, tracking_token=token)
    current = STATUS_TO_STEP.get(application.status, 0)

    steps = []
    for i, label in enumerate(TRACK_STEPS):
        if i < current:
            state = 'done'
        elif i == current:
            state = 'current'
        else:
            state = 'upcoming'

        if i == 4 and application.status == 'selected':
            label, state = 'Selected', 'done'
        elif i == 4 and application.status == 'rejected':
            label, state = 'Not selected', 'closed'

        steps.append({'label': label, 'state': state})

    return render(request, 'candidate/track.html', {
        'application': application,
        'steps': steps,
    })

def track_lookup(request):
    error = ''
    code = ''

    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        match = re.search(
            r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}',
            code,
        )
        if match:
            token = uuid.UUID(match.group(0))
            if Application.objects.filter(tracking_token=token).exists():
                return redirect('candidate:track', token=token)
        error = "We couldn't find an application with that link or code. Please check it and try again."

    return render(request, 'candidate/track_lookup.html', {'error': error, 'code': code})
