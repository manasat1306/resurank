from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

def calculate_match_percentage(resume_skills, jd_text):
    jd_text_lower = jd_text.lower()

    matched_count = sum(1 for skill in resume_skills if skill.lower() in jd_text_lower)

    # Count how many of our known reference skills the JD actually mentions
    jd_required_skills_count = sum(1 for skill in COMMON_TECH_SKILLS if skill in jd_text_lower)

    if jd_required_skills_count > 0:
        skills_overlap_ratio = matched_count / jd_required_skills_count
    else:
        # Fallback: if we can't detect any reference skills in the JD, use the old method
        skills_overlap_ratio = matched_count / len(resume_skills) if resume_skills else 0

    skills_overlap_ratio = min(skills_overlap_ratio, 1.0)  # cap at 100%, in case of edge cases

    resume_text_for_comparison = " ".join(resume_skills) if resume_skills else ""
    documents = [resume_text_for_comparison, jd_text]

    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)
    text_similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

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

CRITICAL_PHRASES = ['must have', 'required', 'essential', 'mandatory', 'strong experience in']
MODERATE_PHRASES = ['nice to have', 'a plus', 'familiarity with', 'preferred', 'bonus']

def analyze_skill_gap_severity(missing_skills, jd_text):
    sentences = re.split(r'(?<=[.!?])\s+', jd_text.lower())
    negation_words = ['not', "n't", 'never', 'without']

    analysis = []

    for skill in missing_skills:
        skill_lower = skill.lower()
        severity = 'unclear'
        note = "Mentioned in the job description, but not with clear priority language."

        matching_sentence = None
        for sentence in sentences:
            if skill_lower in sentence:
                matching_sentence = sentence
                break

        if matching_sentence:
            # Check MODERATE phrases first - if explicitly "a plus"/"preferred", that wins
            # regardless of other words in the sentence
            found_moderate = any(phrase in matching_sentence for phrase in MODERATE_PHRASES)
            found_critical = False

            for phrase in CRITICAL_PHRASES:
                if phrase in matching_sentence:
                    # Check if this critical phrase is negated (e.g. "not mandatory")
                    phrase_index = matching_sentence.find(phrase)
                    text_before = matching_sentence[max(0, phrase_index - 15):phrase_index]
                    is_negated = any(neg in text_before for neg in negation_words)
                    if not is_negated:
                        found_critical = True
                    break

            if found_moderate:
                severity = 'moderate'
                note = "Job description language suggests this is preferred, not mandatory."
            elif found_critical:
                severity = 'critical'
                note = "Job description language suggests this is a strict requirement."

        analysis.append({
            'skill': skill,
            'severity': severity,
            'note': note
        })

    severity_order = {'critical': 0, 'unclear': 1, 'moderate': 2}
    analysis.sort(key=lambda x: severity_order[x['severity']])

    return analysis

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