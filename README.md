# ResuRank – Final Project Plan

## 1. The idea

ResuRank is a hiring platform. A recruiter posts a job with required skills and scoring weights. Candidates apply with a PDF resume. ResuRank scores every applicant, ranks them, and shows exactly why each score was given. The recruiter makes the final decision. Scores never auto-reject anyone, and names, gender and photos are never used.

**Main selling point:** every score is explainable (skill match + text similarity + evidence from the resume).

**Who uses it:** Recruiters (main users) and Candidates (simple: browse jobs, apply, track).

**Who has the problem:** small companies and startups with no HR team. One person gets hundreds of resumes and has no time to read them. Big tools are expensive and hide how they score. ResuRank is simple and explains every score.

---

## 2. Tech stack (final)

| Area            | Choice                                                        |
| --------------- | ------------------------------------------------------------- |
| Backend         | Python, Django                                                |
| Database        | SQLite for dev, MySQL for production                          |
| Frontend        | Django templates + HTML + Tailwind CSS + JavaScript           |
| Charts          | Chart.js                                                      |
| Resume parsing  | pdfplumber                                                    |
| Matching        | Rule-based skills + TF-IDF / cosine similarity (scikit-learn) |
| Background jobs | Celery + Redis                                                |
| Tools           | Docker Compose, GitHub Actions, Render                        |

---

## 3. Scoring rules (final)

Final score = (Skill score × skill weight) + (Similarity × similarity weight)
Default weights = 70 / 30 (each job can change it, always adds up to 100)

* **Green:** 80 and above
* **Amber:** 60 to 79
* **Red:** below 60
* **Skill score:** how many required skills were found in the resume.
* **Skill matching now:** synonym list (JS = JavaScript) + text cleaning + whole-word matching.
* **Similarity now:** TF-IDF + cosine similarity.
* **Later (after deploy):** sentence embeddings (`all-MiniLM-L6-v2`). Keep TF-IDF as fallback.
* **Skill gap severity:** each missing skill is Critical, Moderate or Unclear, based on the job description wording.

---

## 4. Pages

### Candidate side (no login)

1. Landing page (choose Candidate or Recruiter)
2. Jobs list (search, filters, only active jobs)
3. Job details
4. Apply (name, email, phone, PDF resume up to 5 MB, consent box, duplicate-email check)
5. Success page
6. Track page (private link, score is never shown)

### Recruiter side (login needed)

1. Login / Signup
2. Dashboard (4 KPI cards, usage bar, recent jobs, recent applications)
3. Jobs (list, create, edit, publish, close)
4. Job details
5. Applicants (ranked table with filters)
6. Candidate analysis (score ring, "Why this score?", missing skills, resume quality, status history)
7. Analyze Resume (upload an outside PDF and score it against a job)
8. Compare (2 to 3 candidates side by side)
9. Analytics (KPIs, trends, status chart, score chart, most-missing skills)
10. Settings (profile, password, default weights)
11. Plans & Upgrade page

### Statuses

* Recruiter: New → Under Review → Shortlisted → Interview → Selected / Rejected
* Candidate: Applied → Under Review → Shortlisted → Interview → Decision

---

## 5. Data models

| Model                        | Main fields                                                                                                                                                                                            |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Job** (was JobDescription) | recruiter, title, department, location, experience, job_type, description, required_skills, preferred_skills, education, skill_weight, similarity_weight, status (draft / active / closed), created_at |
| **Candidate**                | name, email, phone                                                                                                                                                                                     |
| **Resume** (keep)            | file, raw_text, skills, final_score, score_breakdown, uploaded_by_recruiter (nullable)                                                                                                                 |
| **Application**              | candidate, job, resume, skill_score, similarity_score, final_score, matched_skills, missing_skills (with severity), status, source (Applied / Recruiter upload), track_token, score_locked, created_at |
| **StatusHistory**            | application, status, changed_by, changed_at                                                                                                                                                            |
| **Plan**                     | name (Free / Pro), max_active_jobs, max_resumes_per_month, price                                                                                                                                       |
| **Subscription**             | recruiter, plan, started_at, resets_on                                                                                                                                                                 |
| **Usage**                    | recruiter, month, resumes_scored                                                                                                                                                                       |

All changes are additive migrations. Do not delete your existing data.

---

## 6. Rules to avoid the mistakes in the UI mockups

1. **One source of data.** Dashboard, Jobs, Analytics and Compare must all read the same database numbers.
2. **Skill gaps come only from real missing skills.** If 5/5 matched, show "No missing skills".
3. **One recruiter name** everywhere (from the logged-in user).
4. **One base template** for all pages (same sidebar, logo, fonts, spacing).
5. **Empty form fields.** Use placeholder text, not fake filled skill chips.
6. **Draft jobs** must not show "Ready to review candidates?".
7. **Compare page** must show real data for every selected candidate, and the count must match the selection.
8. Add `@login_required` to every recruiter view (the ranking view is missing it now).
9. Do not create a new job row on every match (this is an old bug).

---

## 7. Build phases (do in this order)

| #   | Phase                                                                                      | Done when                                |
| --- | ------------------------------------------------------------------------------------------ | ---------------------------------------- |
| 1   | **Base layout + Tailwind.** One base template, sidebar, login/signup restyled              | All pages share one layout               |
| 2   | **Job model + recruiter CRUD.** Create, edit, publish, close, job details                  | You can create and publish a job         |
| 3   | **Recruiter dashboard** with real KPI numbers                                              | Numbers match the Jobs page              |
| 4   | **Candidate model + public pages.** Jobs list and job details                              | Public can see active jobs only          |
| 5   | **Apply flow.** Form, PDF checks, duplicate check, success page                            | An application is saved                  |
| 6   | **Connect scoring to Application.** Reuse `matcher.py`, add synonyms + whole-word matching | Score is saved on apply                  |
| 7   | **Applicants page.** Ranked table, filters, missing-skill chips                            | Ranking works per job                    |
| 8   | **Candidate analysis page.** "Why this score?", evidence, resume quality, status buttons   | Score explained on screen                |
| 9   | **Status history + Track page**                                                            | Candidate sees status, never the score   |
| 13B | **Plans & limits** (details below)                                                         | Free user blocked at limit, Pro is not   |
| 10  | **Analyze Resume** (recruiter uploads outside PDF)                                         | Shows as source "Recruiter upload"       |
| 11  | **Compare page**                                                                           | 2 to 3 candidates side by side           |
| 12  | **Analytics** with Chart.js                                                                | All charts use real data                 |
| 13  | **Settings** (profile, password, default weights)                                          | Weights save and apply to new jobs       |
| 14  | **Tests + CI.** Add tests for views, apply flow, limits and data isolation                 | All tests pass on GitHub Actions         |
| 15  | **Deploy.** MySQL, cloud storage or persistent disk for PDFs, real demo data               | Live site keeps data after redeploy      |
| 16  | **Upgrade (optional).** Embeddings for similarity, test with 20+ real resumes              | Result added to README                   |

**Demo-ready goal:** phases 1 to 9 + 13B done by (DATE BEFORE DEADLINE). Phases 10, 11, 12 only if time is left.

### Phase 13B – Plans & limits

* **Free plan:** 1 active job, 25 resumes scored per month
* **Pro plan:** 10 active jobs, 500 resumes per month, Compare + Analytics
* Show a usage bar on the dashboard ("18 / 25 resumes used")
* Limits apply to **recruiters only**. Candidates are never blocked.
* Over the limit: the application is still saved, but the score and ranking are locked until the recruiter upgrades
* Over the job limit: "Publish" shows the Upgrade page
* Upgrade button just switches the plan (no real payment for the hackathon)
* Usage resets every month

---

## 8. Decide before phase 2

1. **Do preferred skills affect the score?** Suggested: yes, a small bonus, or show them separately as "nice to have" only. Pick one.
2. **Candidate login?** Suggested: no login, use the private track link.
3. **Keep the "I'm a Candidate" card on the landing page?** Suggested: yes.

---

## 9. Daily routine

* 1 DSA problem every day (do not stop, this matters most for placements)
* 1 project phase step (small, finish it, then commit)
* Commit and push to GitHub after every working step

---

## 10. Interview talking points

* "Every score is explainable: skill match, similarity and evidence from the resume."
* "Skill matching is rule-based on purpose, so every match can be shown as evidence."
* "Similarity uses TF-IDF now and can be upgraded to embeddings."
* "Scores use resume content only, never auto-reject, and the recruiter decides."
* "29+ tests, CI on every push, Docker, Celery, and data isolation between recruiters."
* "Freemium plans with usage limits, so the product has a real business model."
* Know the limits: multi-column PDFs, PDF only, keyword matching can miss unusual wording.

---

## 11. Business model (hackathon)

**Problem:** small companies and startups have no HR team. One person gets hundreds of resumes and cannot read them all. Big tools are expensive and hide how they score.

**Solution:** ResuRank ranks resumes and explains every score.

**Plans:**
* Free: 1 active job, 25 resumes per month, basic ranking
* Pro: more jobs, more resumes, Compare, Analytics (price: decide after checking what similar tools charge)
* Later: agency plan for small hiring agencies

**Limit rules:**
* Limits apply to recruiters only, never to candidates
* Over the limit: applications are saved, scores are locked until upgrade
* Usage resets every month

**Costs:** hosting, database, file storage, later the embedding model.

**Scalability:** DB indexing (measured 1.8× speedup), Celery + Redis for background parsing, Docker, MySQL. Next: cloud file storage and caching.

**Honest notes:** no made-up market numbers. Real payment (Stripe) is the next step. Skill matching is rule-based on purpose.

---

## 12. Demo video script (5 minutes)

| Time      | What to show                                                              |
| --------- | ------------------------------------------------------------------------- |
| 0:00–0:45 | Problem: 200 resumes, one person, slow and unfair                         |
| 0:45–1:30 | Solution: explainable scores, recruiters + candidates                     |
| 1:30–3:15 | Demo: post job, candidate applies, ranked list, "Why this score?", limit hit + upgrade |
| 3:15–4:00 | How it is built: architecture diagram, Django, pdfplumber, TF-IDF, Celery, Docker, CI |
| 4:00–4:30 | Scalability: indexing, background jobs, Docker, MySQL                     |
| 4:30–5:00 | Business: free vs Pro limits, costs, next steps                           |

**Tip:** the free Render site sleeps and loses data. Record on your local machine with good sample data, or deploy properly first.

---

## 13. First step tomorrow

Start **Phase 1 and Phase 2**: one base template, then the Job model with create / edit / publish / close pages. Send your current `models.py`, `urls.py`, `views.py` and templates to start.