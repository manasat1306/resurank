import pdfplumber
from django.shortcuts import render
from .models import Resume

import re

def detect_sections(text):
    # Common section headers found in resumes
    section_headers = [
    'technical skills', 'core skills', 'key skills', 'work experience',
    'professional summary', 'education', 'experience', 'skills',
    'projects', 'certifications', 'achievements', 'summary',
    'objective', 'contact', 'soft skills'
    ]

    sections = {}
    current_section = 'header'  # text before any section header
    sections[current_section] = []

    lines = text.split('\n')

    for line in lines:
        clean_line = line.strip().lower()

        # Check if this line is a section header
        matched_header = None
        for header in section_headers:
            if clean_line == header or clean_line.startswith(header):
                matched_header = header
                break

        if matched_header:
            current_section = matched_header
            sections[current_section] = []
        else:
            if line.strip():  # skip empty lines
                sections[current_section].append(line.strip())

    return sections

def extract_skills(sections):
    possible_keys = ['skills', 'technical skills', 'core skills', 'key skills']
    skills_lines = []
    for key in possible_keys:
        skills_lines.extend(sections.get(key, []))

    all_skills = []

    for line in skills_lines:
        # Remove the category label (like "Languages:") if present
        if ':' in line:
            line = line.split(':', 1)[1]

        # Split by comma and clean each skill
        skill_items = line.split(',')
        for skill in skill_items:
            skill = skill.strip()
            if skill:
                all_skills.append(skill)

    return all_skills

def check_ats_compatibility(text, sections):
    issues = []
    score = 100

    # Check for email
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    if not re.search(email_pattern, text):
        issues.append("No email address found")
        score -= 20

    # Check for phone number
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\d{10}'
    if not re.search(phone_pattern, text):
        issues.append("No phone number found")
        score -= 20

    # Check for key sections
    has_education = 'education' in sections and sections['education']
    has_skills = any(
        key in sections and sections[key]
        for key in ['skills', 'technical skills', 'core skills', 'key skills']
    )

    if not has_education:
        issues.append("Missing 'Education' section")
        score -= 15
    if not has_skills:
        issues.append("Missing 'Skills' section")
        score -= 15

    # Check resume length (word count)
    word_count = len(text.split())
    if word_count < 100:
        issues.append("Resume seems too short")
        score -= 10
    elif word_count > 1000:
        issues.append("Resume seems too long")
        score -= 5

    score = max(score, 0)  # don't go below 0

    return {
        'score': score,
        'issues': issues
    }
def check_action_verbs_and_metrics(sections):
    action_verbs = [
        'built', 'developed', 'implemented', 'designed', 'created',
        'improved', 'increased', 'decreased', 'reduced', 'optimized',
        'led', 'managed', 'launched', 'automated', 'achieved'
    ]

    # Look at Projects and Experience sections (where bullet points usually are)
    bullet_lines = []
    for key in ['projects', 'experience', 'work experience']:
        bullet_lines.extend(sections.get(key, []))

    total_bullets = 0
    action_verb_count = 0
    metric_count = 0

    for line in bullet_lines:
        clean_line = line.strip()
        if clean_line.startswith('•') or clean_line.startswith('-'):
            total_bullets += 1
            lower_line = clean_line.lower()

            # Check if it starts with an action verb
            for verb in action_verbs:
                if verb in lower_line[:30]:  # check near the start
                    action_verb_count += 1
                    break

            # Check for numbers (quantifiable achievement)
            if re.search(r'\d+', clean_line):
                metric_count += 1

    return {
        'total_bullets': total_bullets,
        'bullets_with_action_verbs': action_verb_count,
        'bullets_with_metrics': metric_count
    }

def calculate_overall_score(ats_result, action_result, skills_list, weights=None):
    # Default weights (recruiter can change these later, not hardcoded permanently)
    if weights is None:
        weights = {
            'ats': 0.4, #40%
            'action_verbs': 0.3,
            'skills': 0.3
        }

    breakdown = []

    # ATS part (already out of 100)
    ats_score = ats_result['score']
    breakdown.append({
        'category': 'ATS Compatibility',
        'points': round(ats_score * weights['ats'], 1),
        'reason': f"Scored {ats_score}/100 on formatting and required info"
    })

    # Action verbs + metrics part
    total_bullets = action_result['total_bullets']
    if total_bullets > 0:
        verb_ratio = action_result['bullets_with_action_verbs'] / total_bullets
        metric_ratio = action_result['bullets_with_metrics'] / total_bullets
        action_score = ((verb_ratio + metric_ratio) / 2) * 100
    else:
        action_score = 0

    breakdown.append({
        'category': 'Action Verbs & Metrics',
        'points': round(action_score * weights['action_verbs'], 1),
        'reason': f"{action_result['bullets_with_action_verbs']}/{total_bullets} bullets have action verbs, "
                  f"{action_result['bullets_with_metrics']}/{total_bullets} have measurable numbers"
    })

    # Skills part (simple: more skills listed = higher, capped at 10 skills = 100)
    skills_score = min(len(skills_list) / 10 * 100, 100)
    breakdown.append({
        'category': 'Skills Listed',
        'points': round(skills_score * weights['skills'], 1),
        'reason': f"{len(skills_list)} skills found: {', '.join(skills_list)}"
    })

    final_score = round(sum(item['points'] for item in breakdown), 1)

    return {
        'final_score': final_score,
        'breakdown': breakdown
    }    

def upload_resume(request):
    if request.method == 'POST':
        resume_file = request.FILES.get('resume')

        # Read text from the PDF
        extracted_text = ""
        with pdfplumber.open(resume_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n"

        sections = detect_sections(extracted_text)
        skills_list = extract_skills(sections)

        ats_result = check_ats_compatibility(extracted_text, sections)
        print("----- ATS CHECK -----")
        print(ats_result)

        action_result = check_action_verbs_and_metrics(sections)
        print("----- ACTION VERBS & METRICS CHECK -----")
        print(action_result)

        final_result = calculate_overall_score(ats_result, action_result, skills_list)
        print("----- FINAL SCORE -----")
        print(final_result)
      
        # Save to database
        new_resume = Resume.objects.create(
            file_name=resume_file.name,
            raw_text=extracted_text,
            skills=skills_list,
            final_score=final_result['final_score'],
            score_breakdown=final_result['breakdown']
        )

        return render(request, 'resume_analyzer/upload.html', {
            'message': f'File "{resume_file.name}" uploaded successfully!'
        })
    return render(request, 'resume_analyzer/upload.html')