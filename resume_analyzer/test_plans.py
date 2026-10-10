from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Job, RecruiterProfile
from .plans import (
    get_plan, get_limits, active_jobs_used, can_activate_job,
)


def make_user(name):
    return User.objects.create_user(username=name, password='pass12345')


def make_job(user, title='Job', status='active'):
    return Job.objects.create(
        recruiter=user,
        title=title,
        status=status,
        required_skills=['python'],
        skill_weight=70,
        similarity_weight=30,
    )


class PlanLimitTests(TestCase):
    def setUp(self):
        self.user = make_user('rec1')

    def test_new_user_is_on_free_plan(self):
        self.assertEqual(get_plan(self.user), 'free')

    def test_free_limits_are_correct(self):
        limits = get_limits(self.user)
        self.assertEqual(limits['active_jobs'], 3)
        self.assertEqual(limits['apps_per_month'], 50)
        self.assertEqual(limits['compare'], 4)

    def test_free_user_can_publish_until_limit(self):
        make_job(self.user, 'A')
        make_job(self.user, 'B')
        self.assertTrue(can_activate_job(self.user))
        make_job(self.user, 'C')
        self.assertFalse(can_activate_job(self.user))

    def test_draft_jobs_do_not_count(self):
        for i in range(5):
            make_job(self.user, f'Draft {i}', status='draft')
        self.assertEqual(active_jobs_used(self.user), 0)
        self.assertTrue(can_activate_job(self.user))

    def test_pro_user_has_no_job_limit(self):
        profile, _ = RecruiterProfile.objects.get_or_create(user=self.user)
        profile.plan = 'pro'
        profile.save()
        for i in range(6):
            make_job(self.user, f'Job {i}')
        self.assertTrue(can_activate_job(self.user))


class DataIsolationTests(TestCase):
    def setUp(self):
        self.owner = make_user('owner')
        self.other = make_user('other')
        self.job = make_job(self.owner, 'Secret job')

    def test_other_recruiter_gets_404_on_job_detail(self):
        self.client.login(username='other', password='pass12345')
        response = self.client.get(reverse('job_detail', args=[self.job.pk]))
        self.assertEqual(response.status_code, 404)

    def test_other_recruiter_gets_404_on_applicants(self):
        self.client.login(username='other', password='pass12345')
        response = self.client.get(reverse('job_applicants', args=[self.job.pk]))
        self.assertEqual(response.status_code, 404)

    def test_owner_can_open_own_job(self):
        self.client.login(username='owner', password='pass12345')
        response = self.client.get(reverse('job_detail', args=[self.job.pk]))
        self.assertEqual(response.status_code, 200)

    def test_job_list_shows_only_own_jobs(self):
        make_job(self.other, 'Other job')
        self.client.login(username='owner', password='pass12345')
        response = self.client.get(reverse('job_list'))
        titles = [j.title for j in response.context['jobs']]
        self.assertIn('Secret job', titles)
        self.assertNotIn('Other job', titles)