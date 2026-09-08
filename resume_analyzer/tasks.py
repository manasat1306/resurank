from celery import shared_task
from .models import Resume


@shared_task
def process_resume_task(resume_id, extracted_text, skills_list, final_score, score_breakdown):
    """
    Background task that saves resume analysis results.
    In a full async setup, parsing itself would also happen here —
    for now, this demonstrates moving the DB write to a background task.
    """
    resume = Resume.objects.get(id=resume_id)
    resume.raw_text = extracted_text
    resume.skills = skills_list
    resume.final_score = final_score
    resume.score_breakdown = score_breakdown
    resume.save()
    return f"Processed resume {resume_id}"