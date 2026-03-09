"""
skill_extractor.py
------------------
Extracts technical and professional skills from resume or job description text.
Uses a curated skills dictionary + basic NLP matching.
"""

import re

# ---------------------------------------------------------------
# Master skills dictionary — grouped by category
# Add or remove skills here to customize detection
# ---------------------------------------------------------------
SKILLS_DICT = {
    "programming_languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "c",
        "r", "go", "rust", "swift", "kotlin", "scala", "ruby", "php",
        "matlab", "bash", "shell", "perl", "dart", "lua",
    ],
    "web_frontend": [
        "html", "css", "react", "vue", "angular", "next.js", "nuxt",
        "tailwind", "bootstrap", "sass", "webpack", "vite", "jquery",
        "svelte", "redux", "graphql",
    ],
    "web_backend": [
        "node.js", "express", "django", "flask", "fastapi", "spring boot",
        "rails", "asp.net", "laravel", "rest api", "restful", "microservices",
    ],
    "data_and_ml": [
        "machine learning", "deep learning", "nlp", "natural language processing",
        "computer vision", "tensorflow", "pytorch", "keras", "scikit-learn",
        "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
        "hugging face", "transformers", "llm", "rag", "fine-tuning",
        "feature engineering", "model deployment",
    ],
    "data_engineering": [
        "sql", "mysql", "postgresql", "sqlite", "mongodb", "redis",
        "elasticsearch", "kafka", "spark", "hadoop", "airflow", "dbt",
        "etl", "data pipeline", "data warehousing", "snowflake", "bigquery",
        "databricks", "tableau", "power bi", "looker",
    ],
    "cloud_and_devops": [
        "aws", "azure", "gcp", "google cloud", "docker", "kubernetes",
        "terraform", "ansible", "jenkins", "ci/cd", "github actions",
        "linux", "nginx", "cloudformation", "lambda", "s3", "ec2",
    ],
    "tools_and_practices": [
        "git", "github", "gitlab", "jira", "agile", "scrum", "kanban",
        "tdd", "unit testing", "pytest", "selenium", "postman", "swagger",
        "figma", "vs code", "jupyter", "excel", "word", "powerpoint",
    ],
    "soft_skills": [
        "communication", "leadership", "teamwork", "problem solving",
        "project management", "time management", "critical thinking",
        "collaboration", "mentoring", "presentation",
    ],
}

# Flatten to a single lookup list (preserve category info)
ALL_SKILLS = {}
for category, skills in SKILLS_DICT.items():
    for skill in skills:
        ALL_SKILLS[skill] = category


def normalize(text: str) -> str:
    """Lowercase and normalize text for matching."""
    text = text.lower()
    text = re.sub(r"[^\w\s\.\+#/]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def extract_skills(text: str) -> dict:
    """
    Scan text and return all detected skills.

    Returns:
    {
        "skills": ["python", "sql", ...],          # flat list
        "by_category": {"programming_languages": ["python"], ...},
        "total_count": int
    }
    """
    normalized = normalize(text)
    found = {}

    for skill, category in ALL_SKILLS.items():
        # Use word boundary matching to avoid partial matches
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, normalized):
            found[skill] = category

    # Group by category
    by_category = {}
    for skill, category in found.items():
        by_category.setdefault(category, []).append(skill)

    return {
        "skills": sorted(found.keys()),
        "by_category": by_category,
        "total_count": len(found),
    }


def compare_skills(resume_skills: list, job_skills: list) -> dict:
    """
    Compare resume skills vs job description skills.

    Returns:
    {
        "matched": [...],       # skills in both
        "missing": [...],       # in job but not resume
        "extra": [...],         # in resume but not in job
        "match_percentage": float
    }
    """
    resume_set = set(resume_skills)
    job_set = set(job_skills)

    matched = sorted(resume_set & job_set)
    missing = sorted(job_set - resume_set)
    extra = sorted(resume_set - job_set)

    match_pct = (len(matched) / len(job_set) * 100) if job_set else 0.0

    return {
        "matched": matched,
        "missing": missing,
        "extra": extra,
        "match_percentage": round(match_pct, 1),
    }


if __name__ == "__main__":
    # Quick smoke test
    sample_resume = """
    Software Engineer with 4 years experience in Python, Django, and PostgreSQL.
    Built REST APIs and deployed services to AWS using Docker and Kubernetes.
    Proficient in Git, Agile, and unit testing with Pytest.
    """
    sample_job = """
    We are looking for a Backend Engineer skilled in Python, FastAPI, PostgreSQL,
    AWS, Docker, and Kubernetes. Experience with CI/CD pipelines and GitHub Actions preferred.
    """
    r = extract_skills(sample_resume)
    j = extract_skills(sample_job)
    comparison = compare_skills(r["skills"], j["skills"])

    print("Resume skills:", r["skills"])
    print("Job skills:   ", j["skills"])
    print("Matched:      ", comparison["matched"])
    print("Missing:      ", comparison["missing"])
    print(f"Skill Match:   {comparison['match_percentage']}%")