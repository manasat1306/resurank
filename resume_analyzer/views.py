import pdfplumber
from django.shortcuts import render
from .models import Resume

import re

def detect_sections(text):
    # Common section headers found in resumes
    section_headers = [
        'education', 'experience', 'work experience', 'skills',
        'projects', 'certifications', 'achievements', 'summary',
        'objective', 'contact'
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
    skills_lines = sections.get('skills', [])
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
      
        # Save to database
        new_resume = Resume.objects.create(
            file_name=resume_file.name,
            raw_text=extracted_text,
            skills=skills_list
        )

        return render(request, 'resume_analyzer/upload.html', {
            'message': f'File "{resume_file.name}" uploaded successfully!'
        })
    return render(request, 'resume_analyzer/upload.html')