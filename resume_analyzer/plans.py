from datetime import timedelta
from django.utils import timezone
from .models import Job, Application, RecruiterProfile

PLAN_LIMITS = {
    'free': {'label': 'Free', 'active_jobs': 3, 'apps_per_month': 50, 'compare': 4},
    'pro': {'label': 'Pro', 'active_jobs': None, 'apps_per_month': None, 'compare': 100},
}


def get_plan(user):
    profile, _ = RecruiterProfile.objects.get_or_create(user=user)
    return profile.plan if profile.plan in PLAN_LIMITS else 'free'


def get_limits(user):
    return PLAN_LIMITS[get_plan(user)]


def active_jobs_used(user):
    return Job.objects.filter(recruiter=user, status='active').count()


def apps_used_this_month(user):
    # Counts only resumes the recruiter uploads themselves (last 30 days)
    since = timezone.now() - timedelta(days=30)
    return Application.objects.filter(
        job__recruiter=user,
        source='recruiter_upload',
        applied_at__gte=since,
    ).count()


def can_activate_job(user):
    limit = get_limits(user)['active_jobs']
    return limit is None or active_jobs_used(user) < limit


def can_accept_application(user):
    limit = get_limits(user)['apps_per_month']
    return limit is None or apps_used_this_month(user) < limit