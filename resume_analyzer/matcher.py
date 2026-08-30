from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def calculate_match_percentage(resume_skills, jd_text):
    """
    Calculates match % using two signals:
    1. Skills overlap (how many resume skills appear in the JD) - weighted heavily (70%)
    2. General text similarity between resume skills and JD (TF-IDF + cosine) - supporting signal (30%)
    """
    jd_text_lower = jd_text.lower()

    # Signal 1: Skills overlap ratio
    matched_count = sum(1 for skill in resume_skills if skill.lower() in jd_text_lower)
    skills_overlap_ratio = matched_count / len(resume_skills) if resume_skills else 0

    # Signal 2: General text similarity (skills list vs JD text)
    resume_text_for_comparison = " ".join(resume_skills) if resume_skills else ""
    documents = [resume_text_for_comparison, jd_text]

    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)
    text_similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

    # Combine: skills overlap matters more (70%) than general text similarity (30%)
    combined_score = (skills_overlap_ratio * 0.7) + (text_similarity * 0.3)
    match_percentage = round(combined_score * 100, 1)

    return match_percentage

# A reference list of common tech skills to check for in job descriptions
COMMON_TECH_SKILLS = [
    'python', 'java', 'javascript', 'c++', 'c#', 'sql', 'html', 'css',
    'django', 'flask', 'react', 'angular', 'vue', 'node.js', 'express',
    'mysql', 'postgresql', 'mongodb', 'sqlite', 'redis',
    'git', 'github', 'docker', 'kubernetes', 'aws', 'azure', 'gcp',
    'rest api', 'graphql', 'celery', 'linux', 'agile', 'scrum',
    'machine learning', 'data analysis', 'pandas', 'numpy', 'tensorflow',
    'unit testing', 'ci/cd', 'jenkins', 'jira'
]


def find_matched_and_missing_skills(resume_skills, jd_text):
    """
    Compares resume's extracted skills against the job description text.
    Returns which skills matched, and which required skills are missing.
    """
    jd_text_lower = jd_text.lower()
    resume_skills_lower = [s.lower() for s in resume_skills]

    # Matched: resume skills that appear in the JD
    matched_skills = [skill for skill in resume_skills if skill.lower() in jd_text_lower]

    # Missing: common tech skills mentioned in the JD that the resume does NOT have
    missing_skills = []
    for skill in COMMON_TECH_SKILLS:
        if skill in jd_text_lower and skill not in resume_skills_lower:
            missing_skills.append(skill)

    return {
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'match_count': len(matched_skills),
        'total_resume_skills': len(resume_skills)
    }