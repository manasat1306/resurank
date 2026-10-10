from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase

from .models import Job, Application
from .scoring import (
    skill_in_text,
    find_evidence,
    similarity_percent,
    score_application,
)


class SkillInTextTests(SimpleTestCase):
    def test_finds_whole_word(self):
        self.assertTrue(skill_in_text('Python', 'i know python and sql'))

    def test_does_not_match_inside_another_word(self):
        # "java" must not match inside "javascript"
        self.assertFalse(skill_in_text('java', 'i know javascript only'))

    def test_handles_special_characters(self):
        self.assertTrue(skill_in_text('c++', 'worked with c++ and c#'))
        self.assertTrue(skill_in_text('node.js', 'built apis in node.js'))

    def test_handles_plurals(self):
        self.assertTrue(skill_in_text('api', 'designed rest apis'))

    def test_empty_skill_is_false(self):
        self.assertFalse(skill_in_text('', 'some text'))


class FindEvidenceTests(SimpleTestCase):
    def test_returns_sentence_with_skill(self):
        jd = 'We use Python daily. Docker is a plus.'
        self.assertEqual(find_evidence('docker', jd), 'Docker is a plus.')

    def test_returns_empty_when_not_mentioned(self):
        self.assertEqual(find_evidence('rust', 'We use Python daily.'), '')


class SimilarityTests(SimpleTestCase):
    def make_job(self, description, required=None):
        return SimpleNamespace(
            description_text=description,
            required_skills=required or [],
            preferred_skills=[],
        )

    def test_empty_resume_gives_zero(self):
        job = self.make_job('We need a python developer', ['python'])
        self.assertEqual(similarity_percent('', job), 0.0)

    def test_similar_text_scores_higher_than_different_text(self):
        job = self.make_job('python django developer', ['python', 'django'])
        close = similarity_percent('python django developer with apis', job)
        far = similarity_percent('chef cooking baking kitchen', job)
        self.assertGreater(close, far)

    def test_same_input_gives_same_score(self):
        job = self.make_job('python developer', ['python'])
        a = similarity_percent('python developer resume', job)
        b = similarity_percent('python developer resume', job)
        self.assertEqual(a, b)


class ScoreApplicationTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='rec', password='pass12345')
        self.job = Job.objects.create(
            recruiter=user,
            title='Backend',
            status='active',
            description_text='Python is required. Docker is a plus.',
            required_skills=['python', 'docker'],
            skill_weight=70,
            similarity_weight=30,
        )
        self.app = Application.objects.create(
            job=self.job,
            candidate_name='Test Person',
            candidate_email='t@example.com',
            resume_file='resumes/fake.pdf',
        )

    @patch('resume_analyzer.scoring.extract_resume_text')
    def test_matched_and_missing_skills(self, mock_text):
        mock_text.return_value = 'I am a python developer'
        result = score_application(self.app)
        self.assertEqual(result['matched'], ['python'])
        self.assertEqual(result['missing'], ['docker'])

    @patch('resume_analyzer.scoring.extract_resume_text')
    def test_score_is_saved_and_in_range(self, mock_text):
        mock_text.return_value = 'python docker developer'
        score_application(self.app)
        self.app.refresh_from_db()
        self.assertGreaterEqual(self.app.final_score, 0)
        self.assertLessEqual(self.app.final_score, 100)
        self.assertEqual(self.app.skill_score, 100.0)

    @patch('resume_analyzer.scoring.extract_resume_text')
    def test_every_missing_skill_has_a_reason(self, mock_text):
        mock_text.return_value = 'python developer'
        score_application(self.app)
        self.app.refresh_from_db()
        for item in self.app.severity_analysis:
            self.assertIn(item['severity'], ('critical', 'moderate'))
            self.assertTrue(item['note'])

    @patch('resume_analyzer.scoring.extract_resume_text')
    def test_unreadable_resume_reports_no_text(self, mock_text):
        mock_text.return_value = ''
        result = score_application(self.app)
        self.assertFalse(result['text_found'])
        self.assertEqual(result['final_score'], 0.0)

    @patch('resume_analyzer.scoring.extract_resume_text')
    def test_same_resume_gives_same_score(self, mock_text):
        mock_text.return_value = 'python developer with docker'
        first = score_application(self.app)['final_score']
        second = score_application(self.app)['final_score']
        self.assertEqual(first, second)

    @patch('resume_analyzer.scoring.extract_resume_text')
    def test_candidate_name_does_not_change_score(self, mock_text):
        # Fairness check: name is never used in scoring
        mock_text.return_value = 'python developer with docker'
        first = score_application(self.app)['final_score']
        self.app.candidate_name = 'Completely Different Name'
        self.app.save()
        second = score_application(self.app)['final_score']
        self.assertEqual(first, second)