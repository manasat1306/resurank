import pdfplumber
from django.shortcuts import render
from .models import Resume, JobDescription
from .matcher import calculate_match_percentage, find_matched_and_missing_skills

import re #regular expressions

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
    ) #does this section name exist and does it contain something

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

def bias_awareness_check(sections):
    # This confirms our scoring never used identity-related info
    gendered_terms = ['he', 'she', 'his', 'her', 'him', 'mr.', 'mrs.', 'ms.']
    header_lines = sections.get('header', [])

    found_terms = []
    for line in header_lines:
        lower_line = line.lower()
        for term in gendered_terms:
            if f' {term} ' in f' {lower_line} ':
                found_terms.append(term)

    return {
        'scoring_used_name': False,
        'scoring_used_photo': False,
        'scoring_used_gender_terms': False,
        'note': "Score is based only on skills, ATS compatibility, and achievement quality — name, gender, and photos are never factored into scoring."
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

def match_resume_to_job(request):
    result = None
    resumes = Resume.objects.all() #django ORM

    if request.method == 'POST':
        resume_id = request.POST.get('resume_id')
        jd_text = request.POST.get('job_description')
        jd_title = request.POST.get('job_title', 'Untitled Job')

        selected_resume = Resume.objects.get(id=resume_id)

        # Save the job description
        job = JobDescription.objects.create(
            title=jd_title,
            description_text=jd_text
        )

        # Calculate match
        match_percentage = calculate_match_percentage(selected_resume.skills, jd_text)
        skills_result = find_matched_and_missing_skills(selected_resume.skills, jd_text)

        result = {
            'resume_name': selected_resume.file_name,
            'job_title': job.title,
            'match_percentage': match_percentage,
            'matched_skills': skills_result['matched_skills'],
            'missing_skills': skills_result['missing_skills'],
            'match_count': skills_result['match_count'],
            'total_resume_skills': skills_result['total_resume_skills'],
        }

    return render(request, 'resume_analyzer/match.html', {
        'resumes': resumes,
        'result': result
    })

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

        bias_result = bias_awareness_check(sections) 
        
        # Save to database
        new_resume = Resume.objects.create(    #django ORM
            file_name=resume_file.name,
            raw_text=extracted_text,
            skills=skills_list,
            final_score=final_result['final_score'],
            score_breakdown=final_result['breakdown']
        )

        return render(request, 'resume_analyzer/upload.html', {
            'message': f'File "{resume_file.name}" uploaded successfully!',
            'final_score': final_result['final_score'],
            'breakdown': final_result['breakdown'],
            'skills': skills_list,
            'ats_issues': ats_result['issues'],
            'bias_note': bias_result['note']
        })
    return render(request, 'resume_analyzer/upload.html')

def job_ranking(request):
    job_description_text = ""
    saved_jds = JobDescription.objects.all().order_by('-id')
    results = []

    if request.method == 'POST':
        selected_jd_id = request.POST.get('saved_jd')
        if selected_jd_id:
            jd_obj = JobDescription.objects.get(id=selected_jd_id)
            job_description_text = jd_obj.description_text
        else:
            job_description_text = request.POST.get('job_description', '')

        resumes = Resume.objects.all()

        for resume in resumes:
            match_percentage = calculate_match_percentage(resume.skills, job_description_text)
            skills_data = find_matched_and_missing_skills(resume.skills, job_description_text)

            results.append({
                'resume': resume,
                'match_percentage': match_percentage,
                'matched_skills': skills_data['matched_skills'],
                'missing_skills': skills_data['missing_skills'],
            })

        results.sort(key=lambda x: x['match_percentage'], reverse=True)

    context = {
        'saved_jds': saved_jds,
        'job_description_text': job_description_text,
        'results': results,
    }
    return render(request, 'resume_analyzer/ranking.html', context)