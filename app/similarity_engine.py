"""
similarity_engine.py
--------------------
Computes semantic similarity between resume text and job description
using sentence-transformers embeddings + cosine similarity.
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer


# ---------------------------------------------------------------
# Embedding-based similarity (uses sentence-transformers)
# Best accuracy — requires model download on first run (~90MB)
# ---------------------------------------------------------------

_embedding_model = None  # lazy-loaded


def _get_embedding_model():
    """Lazy-load the sentence transformer model."""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        except ImportError:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Run: pip install sentence-transformers"
            )
    return _embedding_model


def semantic_similarity(text1: str, text2: str) -> float:
    """
    Compute semantic similarity using sentence embeddings.
    Returns a score between 0.0 and 1.0.
    """
    model = _get_embedding_model()
    embeddings = model.encode([text1, text2])
    score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return float(np.clip(score, 0.0, 1.0))


# ---------------------------------------------------------------
# TF-IDF fallback (no model download needed)
# Fast but less accurate than embeddings
# ---------------------------------------------------------------

def tfidf_similarity(text1: str, text2: str) -> float:
    """
    Compute similarity using TF-IDF vectors + cosine similarity.
    Returns a score between 0.0 and 1.0.
    Useful as a fast fallback or for ensemble scoring.
    """
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    try:
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        score = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
        return float(np.clip(score, 0.0, 1.0))
    except ValueError:
        return 0.0


# ---------------------------------------------------------------
# Combined scorer — weighted ensemble of both methods
# ---------------------------------------------------------------

def compute_similarity_scores(
    resume_text: str,
    job_text: str,
    skill_match_pct: float = 0.0,
    use_embeddings: bool = True,
) -> dict:
    """
    Compute all similarity scores and return a combined match score.

    Parameters:
    -----------
    resume_text     : cleaned resume text
    job_text        : cleaned job description text
    skill_match_pct : 0–100 score from skill_extractor.compare_skills()
    use_embeddings  : if False, falls back to TF-IDF only (faster)

    Returns dict:
    {
        "semantic_score":   int (0-100),  # embedding or TF-IDF similarity
        "skill_score":      int (0-100),  # from skill comparison
        "experience_score": int (0-100),  # heuristic from text cues
        "overall_score":    int (0-100),  # weighted combination
    }
    """
    # 1. Semantic similarity
    if use_embeddings:
        try:
            raw_semantic = semantic_similarity(resume_text, job_text)
        except Exception:
            raw_semantic = tfidf_similarity(resume_text, job_text)
    else:
        raw_semantic = tfidf_similarity(resume_text, job_text)

    # Scale to 0–100 and boost slightly (raw cosine is conservative)
    semantic_score = int(min(raw_semantic * 130, 100))

    # 2. Skill score (already 0–100)
    skill_score = int(min(skill_match_pct, 100))

    # 3. Experience score — heuristic based on year mentions
    experience_score = _estimate_experience_score(resume_text, job_text)

    # 4. Weighted overall score
    # Semantic 40% | Skills 40% | Experience 20%
    overall = (
        semantic_score * 0.40
        + skill_score * 0.40
        + experience_score * 0.20
    )

    return {
        "semantic_score": semantic_score,
        "skill_score": skill_score,
        "experience_score": experience_score,
        "overall_score": int(round(overall)),
    }


def _estimate_experience_score(resume_text: str, job_text: str) -> int:
    """
    Rough heuristic: check if years of experience mentioned in the job
    description are consistent with what the resume shows.
    Returns 0–100.
    """
    import re

    def extract_years(text):
        matches = re.findall(r"(\d+)\+?\s*(?:years?|yrs?)", text.lower())
        return [int(m) for m in matches]

    job_years = extract_years(job_text)
    resume_years = extract_years(resume_text)

    if not job_years:
        return 70  # no requirement stated — neutral

    required = max(job_years)
    candidate = max(resume_years) if resume_years else 0

    if candidate >= required:
        return 90
    elif candidate >= required - 1:
        return 70
    elif candidate >= required - 2:
        return 50
    else:
        return 30


if __name__ == "__main__":
    resume = """
    Data Engineer with 5 years of experience in Python, SQL, Apache Spark,
    and building ETL pipelines on AWS. Proficient in Docker and Airflow.
    """
    job = """
    Seeking a Data Engineer with 4+ years of experience in Python, SQL, Spark,
    and AWS. Knowledge of Kafka and Airflow preferred.
    """
    scores = compute_similarity_scores(resume, job, skill_match_pct=75.0, use_embeddings=False)
    print("Scores:", scores)