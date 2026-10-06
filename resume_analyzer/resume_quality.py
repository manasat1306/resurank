import re


SECTION_HEADERS = [
    'technical skills', 'core skills', 'key skills', 'work experience',
    'professional summary', 'education', 'experience', 'skills',
    'projects', 'certifications', 'achievements', 'summary',
    'objective', 'contact', 'soft skills'
]

SKILL_KEYS = ['skills', 'technical skills', 'core skills', 'key skills']
EXPERIENCE_KEYS = ['experience', 'work experience']

ACTION_VERBS = [
    'built', 'developed', 'implemented', 'designed', 'created',
    'improved', 'increased', 'decreased', 'reduced', 'optimized',
    'led', 'managed', 'launched', 'automated', 'achieved'
]


def detect_sections(text):
    sections = {'header': []}
    current = 'header'

    for line in text.split('\n'):
        clean = line.strip().lower()
        matched = None
        if clean and len(clean) <= 40:
            for header in SECTION_HEADERS:
                if clean == header or clean.startswith(header):
                    matched = header
                    break
        if matched:
            current = matched
            sections[current] = []
        elif line.strip():
            sections[current].append(line.strip())

    return sections


def check_ats(text, sections):
    issues = []
    score = 100

    if not re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text):
        issues.append("No email address found")
        score -= 20

    if not re.search(r'(\+?\d{1,3}[-.\s]?)?\d{10}', text):
        issues.append("No phone number found")
        score -= 20

    if not sections.get('education'):
        issues.append("Missing 'Education' section")
        score -= 15

    if not any(sections.get(k) for k in SKILL_KEYS):
        issues.append("Missing 'Skills' section")
        score -= 15

    word_count = len(text.split())
    if word_count < 100:
        issues.append("Resume seems too short")
        score -= 10
    elif word_count > 1000:
        issues.append("Resume seems too long")
        score -= 5

    return {'score': max(score, 0), 'issues': issues}


def check_action_and_metrics(sections):
    lines = []
    for key in ['projects'] + EXPERIENCE_KEYS:
        lines.extend(sections.get(key, []))

    total = 0
    verbs = 0
    metrics = 0

    for line in lines:
        clean = line.strip()
        if clean.startswith('•') or clean.startswith('-'):
            total += 1
            if any(v in clean.lower()[:30] for v in ACTION_VERBS):
                verbs += 1
            if re.search(r'\d+', clean):
                metrics += 1

    return {'total_bullets': total, 'action_verbs': verbs, 'metrics': metrics}


def analyze_resume_quality(text):
    sections = detect_sections(text)
    ats = check_ats(text, sections)
    action = check_action_and_metrics(sections)

    if action['total_bullets'] > 0:
        verb_ratio = action['action_verbs'] / action['total_bullets']
        metric_ratio = action['metrics'] / action['total_bullets']
        action_score = ((verb_ratio + metric_ratio) / 2) * 100
    else:
        action_score = 0

    quality_score = round((ats['score'] * 0.6) + (action_score * 0.4))

    if quality_score >= 80:
        label = 'Good'
    elif quality_score >= 60:
        label = 'Needs attention'
    else:
        label = 'Weak'

    sections_found = {
        'Education': bool(sections.get('education')),
        'Skills': any(sections.get(k) for k in SKILL_KEYS),
        'Experience': any(sections.get(k) for k in EXPERIENCE_KEYS),
        'Projects': bool(sections.get('projects')),
    }

    return {
        'quality_score': quality_score,
        'label': label,
        'ats_issues': ats['issues'],
        'sections_found': sections_found,
        'action_verbs': action['action_verbs'],
        'metrics': action['metrics'],
        'total_bullets': action['total_bullets'],
    }