from django.test import TestCase

# Create your tests here.
from .views import (
    detect_sections,
    extract_skills,
    check_ats_compatibility,
    check_action_verbs_and_metrics,
    calculate_overall_score,
)
from .matcher import calculate_match_percentage, find_matched_and_missing_skills

class SectionDetectionTests(TestCase):
    def test_detects_basic_sections(self):
        text = "John Doe\nEDUCATION\nBCA College\nSKILLS\nPython, SQL"
        sections = detect_sections(text)
        self.assertIn('education', sections)
        self.assertIn('skills', sections)

    def test_handles_technical_skills_variation(self):
        text = "Name\nTECHNICAL SKILLS\nJava, Python"
        sections = detect_sections(text)
        self.assertIn('technical skills', sections)


class SkillExtractionTests(TestCase):
    def test_extracts_comma_separated_skills(self):
        sections = {'skills': ['Languages: Python, SQL', 'Tools: Git, GitHub']}
        skills = extract_skills(sections)
        self.assertIn('Python', skills)
        self.assertIn('Git', skills)
        self.assertEqual(len(skills), 4)

    def test_empty_skills_section_returns_empty_list(self):
        sections = {'skills': []}
        skills = extract_skills(sections)
        self.assertEqual(skills, [])

    def test_missing_skills_key_returns_empty_list(self):
        sections = {}
        skills = extract_skills(sections)
        self.assertEqual(skills, [])


class ATSCompatibilityTests(TestCase):
    def test_full_score_for_complete_resume(self):
        text = "Contact: test@email.com +919876543210 " + ("word " * 100)
        sections = {'education': ['BCA'], 'skills': ['Python']}
        result = check_ats_compatibility(text, sections)
        self.assertEqual(result['score'], 100)
        self.assertEqual(result['issues'], [])

    def test_flags_missing_email(self):
        text = "Contact: +919876543210 " + ("word " * 100)
        sections = {'education': ['BCA'], 'skills': ['Python']}
        result = check_ats_compatibility(text, sections)
        self.assertIn("No email address found", result['issues'])
        self.assertLess(result['score'], 100)

    def test_flags_missing_education_section(self):
        text = "test@email.com +919876543210 " + ("word " * 100)
        sections = {'skills': ['Python']}
        result = check_ats_compatibility(text, sections)
        self.assertIn("Missing 'Education' section", result['issues'])

    def test_flags_too_short_resume(self):
        text = "test@email.com +919876543210 short resume"
        sections = {'education': ['BCA'], 'skills': ['Python']}
        result = check_ats_compatibility(text, sections)
        self.assertIn("Resume seems too short", result['issues'])

    def test_score_never_goes_below_zero(self):
        text = "short"
        sections = {}
        result = check_ats_compatibility(text, sections)
        self.assertGreaterEqual(result['score'], 0)


class ActionVerbsAndMetricsTests(TestCase):
    def test_counts_bullets_correctly(self):
        sections = {
            'projects': [
                '• Built a chatbot using Python',
                '• Improved response time by 30%',
                'Not a bullet line',
            ]
        }
        result = check_action_verbs_and_metrics(sections)
        self.assertEqual(result['total_bullets'], 2)
        self.assertEqual(result['bullets_with_action_verbs'], 2)
        self.assertEqual(result['bullets_with_metrics'], 1)

    def test_no_bullets_returns_zeros(self):
        sections = {'projects': ['Just a plain sentence with no bullet']}
        result = check_action_verbs_and_metrics(sections)
        self.assertEqual(result['total_bullets'], 0)
        self.assertEqual(result['bullets_with_action_verbs'], 0)
        self.assertEqual(result['bullets_with_metrics'], 0)


class OverallScoreTests(TestCase):
    def test_final_score_is_weighted_sum_of_parts(self):
        ats_result = {'score': 100, 'issues': []}
        action_result = {'total_bullets': 2, 'bullets_with_action_verbs': 2, 'bullets_with_metrics': 0}
        skills_list = ['Python', 'SQL']

        result = calculate_overall_score(ats_result, action_result, skills_list)

        self.assertIn('final_score', result)
        self.assertIn('breakdown', result)
        self.assertEqual(len(result['breakdown']), 3)

    def test_same_input_gives_same_score_every_time(self):
        # Determinism check - same input must always give same output
        ats_result = {'score': 85, 'issues': []}
        action_result = {'total_bullets': 5, 'bullets_with_action_verbs': 3, 'bullets_with_metrics': 1}
        skills_list = ['Python', 'Django', 'MySQL']

        result1 = calculate_overall_score(ats_result, action_result, skills_list)
        result2 = calculate_overall_score(ats_result, action_result, skills_list)

        self.assertEqual(result1['final_score'], result2['final_score'])

    def test_custom_weights_are_applied(self):
        ats_result = {'score': 100, 'issues': []}
        action_result = {'total_bullets': 0, 'bullets_with_action_verbs': 0, 'bullets_with_metrics': 0}
        skills_list = []

        custom_weights = {'ats': 1.0, 'action_verbs': 0, 'skills': 0}
        result = calculate_overall_score(ats_result, action_result, skills_list, weights=custom_weights)

        self.assertEqual(result['final_score'], 100.0)


#feature 2
class MatchPercentageTests(TestCase):
    def test_full_skills_overlap_gives_high_score(self):
        resume_skills = ['Python', 'Flask', 'MySQL']
        jd_text = "We need a developer with Python, Flask, and MySQL experience."
        score = calculate_match_percentage(resume_skills, jd_text)
        self.assertGreater(score, 60)

    def test_no_overlap_gives_low_score(self):
        resume_skills = ['Java', 'Spring']
        jd_text = "We are looking for a chef with cooking and baking experience."
        score = calculate_match_percentage(resume_skills, jd_text)
        self.assertLess(score, 20)

    def test_empty_skills_list_does_not_crash(self):
        resume_skills = []
        jd_text = "We need a Python developer."
        score = calculate_match_percentage(resume_skills, jd_text)
        self.assertGreaterEqual(score, 0)

    def test_same_input_gives_same_score_every_time(self):
        resume_skills = ['Python', 'SQL', 'Git']
        jd_text = "Looking for someone with Python and SQL skills."
        score1 = calculate_match_percentage(resume_skills, jd_text)
        score2 = calculate_match_percentage(resume_skills, jd_text)
        self.assertEqual(score1, score2)


class MatchedMissingSkillsTests(TestCase):
    def test_finds_matched_skills_correctly(self):
        resume_skills = ['Python', 'Flask', 'MySQL']
        jd_text = "We need Python and Flask experience."
        result = find_matched_and_missing_skills(resume_skills, jd_text)
        self.assertIn('Python', result['matched_skills'])
        self.assertIn('Flask', result['matched_skills'])
        self.assertNotIn('MySQL', result['matched_skills'])

    def test_finds_missing_skills_from_jd(self):
        resume_skills = ['Python']
        jd_text = "We need Python and Docker experience with AWS."
        result = find_matched_and_missing_skills(resume_skills, jd_text)
        self.assertIn('docker', result['missing_skills'])
        self.assertIn('aws', result['missing_skills'])

    def test_no_missing_skills_when_jd_has_none_from_reference_list(self):
        resume_skills = ['Python']
        jd_text = "We need someone who is friendly and hardworking."
        result = find_matched_and_missing_skills(resume_skills, jd_text)
        self.assertEqual(result['missing_skills'], [])

    def test_match_count_is_accurate(self):
        resume_skills = ['Python', 'SQL', 'Git', 'Docker']
        jd_text = "Need Python and SQL skills."
        result = find_matched_and_missing_skills(resume_skills, jd_text)
        self.assertEqual(result['match_count'], 2)
        self.assertEqual(result['total_resume_skills'], 4)        