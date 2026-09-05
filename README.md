# ResuRank – Explainable Resume Screening & Candidate Ranking System

ResuRank is a recruiter-focused resume screening and candidate ranking system built with Django. It analyzes resumes, compares candidates with job descriptions, identifies matched and missing skills, and ranks candidates based on their job match score.

## Features

### 1. Resume Analyzer
- Upload resumes in PDF format
- Extract resume text using pdfplumber
- Detect common resume sections
- Extract technical skills
- Check ATS compatibility
- Detect action verbs and measurable achievements
- Generate an overall resume score
- Provide an explainable score breakdown
- Bias-aware scoring that does not use name, gender, or photo for scoring

### 2. Resume vs Job Description Matcher
- Compare a resume with a job description
- Calculate match percentage
- Skill overlap scoring
- TF-IDF text similarity
- Cosine similarity
- Identify matched skills
- Identify missing technical skills
- Display match count and total resume skills
- Unit tests for matching functionality

### 3. Candidate Ranking
- Select a saved job description or enter a new one
- Compare the job description with all stored resumes
- Calculate match percentage for every candidate
- Display matched and missing skills
- Rank candidates from highest to lowest match score

## Tech Stack

- Python
- Django
- MySQL
- HTML
- CSS
- JavaScript
- Bootstrap
- pdfplumber
- scikit-learn
- TF-IDF
- Cosine Similarity

## How It Works

```text
Resume PDF
    ↓
Text Extraction
    ↓
Section Detection
    ↓
Skill Extraction
    ↓
ATS & Achievement Analysis
    ↓
Resume Score
    ↓
Job Description Matching
    ↓
Matched / Missing Skills
    ↓
Candidate Ranking