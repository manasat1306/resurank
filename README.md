# ResuRank – Explainable Resume Screening & Candidate Ranking System

ResuRank is a recruiter-focused resume screening and candidate ranking system built with Django. It analyzes resumes, compares candidates with job descriptions, identifies matched and missing skills, and ranks candidates based on their job match score — with every score fully explainable, using rule-based logic instead of a black-box AI model.

**Live demo:** https://resurank.onrender.com/
*(Free-tier hosting — the app may take 30–60 seconds to wake up on first load.)*

## Why ResuRank

Most resume-screening tools either give an opaque match score with no reasoning, or rely on paid AI APIs with inconsistent results. ResuRank is fully rule-based and deterministic — the same resume and job description will always produce the same score, and every point is traceable to a specific, explainable reason.

It's built for recruiters, not candidates: the focus is on ranking and comparing candidates at scale, not on candidate self-improvement tools.

## Features

### 1. Resume Analyzer

* Upload resumes in PDF format
* Extract resume text using pdfplumber
* Detect common resume sections (handles variations like "Skills" vs "Technical Skills")
* Extract technical skills
* Check ATS compatibility
* Detect action verbs and measurable achievements
* Generate an overall resume score with configurable category weights
* Provide a full explainable score breakdown (audit-trail style — every point has a stated reason)
* Bias-aware scoring that does not use name, gender, or photo for scoring
* Graceful handling of corrupted, password-protected, or unreadable PDFs

### 2. Resume vs Job Description Matcher

* Compare a resume with a job description
* Calculate match percentage using a weighted combination of skills overlap (70%) and TF-IDF/cosine text similarity (30%)
* Identify matched skills
* Identify missing technical skills
* **Skill gap severity analysis** — classifies each missing skill as critical, moderate, or unclear, based on the actual language used in that specific job description (e.g. "required" vs "nice to have"), including negation handling (e.g. "not mandatory")
* Display match count and total resume skills

### 3. Candidate Ranking Dashboard

* Select a saved job description or enter a new one
* Compare the job description against all stored resumes for the logged-in recruiter
* Calculate match percentage for every candidate
* Display matched and missing skills per candidate
* Filter by minimum match percentage
* Rank candidates from highest to lowest match score

### 4. Recruiter Accounts

* Sign up / log in / log out
* Each recruiter's resumes and job descriptions are private to their own account
* Authentication and authorization are enforced across recruiter-specific data

## Tech Stack

* **Backend:** Python, Django
* **Database:** SQLite (development) / MySQL (planned production upgrade)
* **Frontend:** HTML, CSS, JavaScript, Bootstrap
* **Resume parsing:** pdfplumber
* **Matching engine:** scikit-learn (TF-IDF, cosine similarity)
* **Async processing:** Celery + Redis
* **Containerization:** Docker, Docker Compose
* **Deployment:** Render (gunicorn + whitenoise)
* **CI/CD:** GitHub Actions (runs the full test suite on every push)

## Engineering Highlights

* **29 automated tests** covering the scoring and matching engine, authentication, data isolation, and edge cases
* **Continuous integration** with GitHub Actions, automatically running the test suite on every push
* **Async task processing** with Celery and Redis, allowing resume processing to run outside the request cycle
* **Database indexing** benchmarked with repeated-run averages at 500-resume scale (~1.8× query speedup on the indexed field compared with an unindexed query)
* **Dockerized development environment** — Django, Redis, and the Celery worker can run together with a single `docker-compose up --build`
* **Authentication and data isolation** — each recruiter can access only their own resumes and job descriptions
* **Edge-case tested** — verified graceful handling of corrupted PDFs, password-protected PDFs, and non-resume documents
* **Deterministic scoring** — identical resume and job-description inputs produce reproducible results
* **Explainable ranking** — candidate scores can be traced back to skills overlap and text-similarity components rather than an opaque model

## How It Works

```text
Resume PDF
    ↓
Text Extraction (pdfplumber)
    ↓
Section Detection
    ↓
Skill Extraction
    ↓
ATS & Achievement Analysis
    ↓
Resume Score
    ↓
Explainable Score Breakdown
    ↓
Job Description Matching
    ↓
70% Skills Overlap + 30% TF-IDF Similarity
    ↓
Matched / Missing Skills
    ↓
Skill Gap Severity Analysis
    ↓
Candidate Ranking
```

## Running Locally

### With Docker Compose

**Recommended — runs Django, Redis, and Celery together:**

```bash
docker-compose up --build
```

Then visit:

```text
http://localhost:8000/
```

### Without Docker

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Celery and Redis need to be running separately if you want asynchronous processing locally without Docker.

### Running Tests

```bash
python manage.py test
```

The project includes automated tests covering core scoring and matching logic, authentication, recruiter data isolation, PDF edge cases, and related functionality.

## Known Limitations

* **Multi-column PDF layouts:** `pdfplumber` can jumble text order on resumes with side-by-side columns, which sometimes affects skill extraction. Single-column resumes are generally unaffected. A more robust fix using pdfplumber's word-position data is planned.
* **PDF only:** DOCX and other formats are not currently supported. Unsupported or invalid uploads fail gracefully with an error message rather than crashing.
* **Skill gap severity depends on JD wording:** if a job description does not use clear priority language such as "required" or "preferred," the skill is marked "unclear" rather than guessed.
* **SQLite deployment:** the current deployment uses SQLite; migrating the production environment to MySQL is planned for improved production scalability.

## What's Next

* **REST API layer** using Django REST Framework for programmatic access to resumes, job descriptions, matching, and candidate rankings
* **Full asynchronous UX** with live processing status via polling instead of keeping the UI flow synchronous
* **Production database migration** from SQLite to MySQL
* **Performance testing at larger scale** with thousands of resumes and benchmarked API/database response times
* **Expanded integration and API tests** covering asynchronous workflows and production-style request flows
* **Frontend visual design pass** for a more polished recruiter experience
* **Production monitoring and logging** for tracking application errors, task failures, and system performance

## Project Goals

ResuRank is designed as a production-oriented backend project rather than a basic CRUD application. The project focuses on demonstrating practical software engineering concepts including:

* Backend development with Django
* Explainable ranking algorithms
* Database design and optimization
* Authentication and authorization
* Asynchronous processing
* REST API architecture
* Automated testing
* Docker-based development
* CI/CD
* Performance benchmarking
* Production deployment
* Scalable system design

The long-term goal is to evolve ResuRank into a scalable recruiter platform capable of processing large numbers of resumes while maintaining explainable, reproducible, and auditable candidate-ranking results.
