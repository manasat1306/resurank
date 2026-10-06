import re

import pdfplumber
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .matcher import analyze_skill_gap_severity


def extract_resume_text(file_path):
    """Read all text from a PDF. Returns '' if it can't be read."""
    text = ''
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or '') + '\n'
    except Exception:
        return ''
    return text.strip()


def skill_in_text(skill, text_lower):
    """True if the skill appears as a whole word or phrase (handles C++, Node.js, plurals)."""
    skill = str(skill).strip().lower()
    if not skill:
        return False
    variants = {skill}
    variants.add(skill[:-1] if skill.endswith('s') else skill + 's')
    for variant in variants:
        pattern = r'(?<![a-z0-9+#])' + re.escape(variant) + r'(?![a-z0-9+#])'
        if re.search(pattern, text_lower):
            return True
    return False


def find_evidence(skill, jd_text):
    """The job description sentence that mentions this skill ('' if none)."""
    sentences = re.split(r'(?<=[.!?])\s+|\n+', jd_text)
    for sentence in sentences:
        if skill.lower() in sentence.lower():
            return sentence.strip()
    return ''


def similarity_percent(resume_text, job):
    """How close the resume text is to the job text, 0-100."""
    job_text = ' '.join(
        [job.description_text]
        + [str(s) for s in job.required_skills]
        + [str(s) for s in job.preferred_skills]
    )
    if not resume_text.strip() or not job_text.strip():
        return 0.0
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        matrix = vectorizer.fit_transform([resume_text, job_text])
        score = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
        return round(float(score) * 100, 1)
    except ValueError:
        return 0.0


def score_application(application):
    """Score one Application against its job and save the results.
    Uses resume text only: no name, gender or photo is read."""
    job = application.job
    resume_text = extract_resume_text(application.resume_file.path)
    text_lower = resume_text.lower()

    required = [str(s) for s in job.required_skills]
    matched = [s for s in required if skill_in_text(s, text_lower)]
    missing = [s for s in required if s not in matched]

    skill_score = round(len(matched) / len(required) * 100, 1) if required else 0.0
    similarity = similarity_percent(resume_text, job)
    final = round(
        skill_score * job.skill_weight / 100
        + similarity * job.similarity_weight / 100,
        1,
    )

    severity = analyze_skill_gap_severity(missing, job.description_text)
    for item in severity:
        item['evidence'] = find_evidence(item['skill'], job.description_text)

    application.skill_score = skill_score
    application.similarity_score = similarity
    application.final_score = final
    application.matched_skills = matched
    application.missing_skills = [item['skill'] for item in severity]
    application.severity_analysis = severity
    application.save(update_fields=[
        'skill_score', 'similarity_score', 'final_score',
        'matched_skills', 'missing_skills', 'severity_analysis',
    ])

    return {
        'text_found': bool(resume_text),
        'skill_score': skill_score,
        'similarity': similarity,
        'final_score': final,
        'matched': matched,
        'missing': application.missing_skills,
    }