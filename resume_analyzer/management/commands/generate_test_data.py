import random
from django.core.management.base import BaseCommand
from resume_analyzer.models import Resume

SAMPLE_SKILLS_POOL = [
    'Python', 'Java', 'JavaScript', 'SQL', 'Django', 'Flask', 'React',
    'Node.js', 'MySQL', 'PostgreSQL', 'MongoDB', 'Git', 'GitHub',
    'Docker', 'Kubernetes', 'AWS', 'Azure', 'REST API', 'GraphQL',
    'HTML', 'CSS', 'C++', 'C#', 'Redis', 'Celery', 'Jenkins', 'Agile'
]

SAMPLE_FIRST_NAMES = ['Aarav', 'Priya', 'Rahul', 'Sneha', 'Vikram', 'Ananya', 'Karan', 'Divya']
SAMPLE_LAST_NAMES = ['Sharma', 'Patel', 'Reddy', 'Kumar', 'Singh', 'Iyer', 'Nair', 'Gupta']


class Command(BaseCommand):
    help = 'Generates fake resume data for benchmarking/testing at scale'

    def add_arguments(self, parser):
        parser.add_argument('count', type=int, default=500, nargs='?')

    def handle(self, *args, **options):
        count = options['count']
        self.stdout.write(f'Generating {count} test resumes...')

        resumes_to_create = []
        for i in range(count):
            name = f"{random.choice(SAMPLE_FIRST_NAMES)} {random.choice(SAMPLE_LAST_NAMES)}"
            num_skills = random.randint(4, 10)
            skills = random.sample(SAMPLE_SKILLS_POOL, num_skills)
            fake_score = round(random.uniform(20, 95), 1)

            resumes_to_create.append(Resume(
                file_name=f"{name.replace(' ', '_').lower()}_resume_{i}.pdf",
                raw_text=f"{name}\nSkills: {', '.join(skills)}\nExperience in software development.",
                skills=skills,
                final_score=fake_score,
                score_breakdown=[
                    {'category': 'ATS Compatibility', 'points': round(fake_score * 0.4, 1), 'reason': 'Generated test data'},
                    {'category': 'Action Verbs & Metrics', 'points': round(fake_score * 0.3, 1), 'reason': 'Generated test data'},
                    {'category': 'Skills Listed', 'points': round(fake_score * 0.3, 1), 'reason': 'Generated test data'},
                ]
            ))

        Resume.objects.bulk_create(resumes_to_create)
        self.stdout.write(self.style.SUCCESS(f'Successfully created {count} test resumes.'))