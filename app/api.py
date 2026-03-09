"""
api.py
------
FastAPI server — exposes the resume analyzer pipeline as a REST API.

Endpoints:
  POST /analyze        — full analysis (file upload + job description)
  GET  /health         — health check

Run with:
  uvicorn app.api:app --reload --port 8000
"""

import io
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from resume_parser import parse_resume
from skill_extractor import extract_skills, compare_skills
from similarity_engine import compute_similarity_scores
from llm_analyzer import analyze_with_llm

load_dotenv()

# ---------------------------------------------------------------
# App setup
# ---------------------------------------------------------------
app = FastAPI(
    title="ResumeIQ API",
    description="AI-powered resume analyzer — match score, skill gap, LLM insights.",
    version="1.0.0",
)

# Allow the React dev server (localhost:5173) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # CRA dev server
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------
# Response model
# ---------------------------------------------------------------
class AnalysisResult(BaseModel):
    overall_score: int
    semantic_score: int
    skill_score: int
    experience_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    extra_skills: list[str]
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]
    rewrite_tip: str
    word_count: int
    file_type: str


# ---------------------------------------------------------------
# Routes
# ---------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "message": "ResumeIQ API is running"}


@app.post("/analyze", response_model=AnalysisResult)
async def analyze(
    job_description: str = Form(...),
    resume_file: UploadFile = File(None),
    resume_text: str = Form(None),
    use_embeddings: bool = Form(False),
):
    """
    Analyze a resume against a job description.

    Accepts either:
    - resume_file: uploaded PDF / DOCX / TXT file
    - resume_text: plain text pasted directly

    Always requires:
    - job_description: the job posting text
    """

    # 1. Extract resume text
    if resume_file and resume_file.filename:
        raw_bytes = await resume_file.read()
        file_like = io.BytesIO(raw_bytes)
        parsed = parse_resume(file_like, filename=resume_file.filename)
        if "error" in parsed:
            raise HTTPException(status_code=422, detail=f"Resume parse error: {parsed['error']}")
        clean_resume = parsed["clean_text"]
        word_count = parsed["word_count"]
        file_type = parsed["file_type"]
    elif resume_text and resume_text.strip():
        clean_resume = resume_text.strip()
        word_count = len(clean_resume.split())
        file_type = "plain text"
    else:
        raise HTTPException(status_code=400, detail="Provide either resume_file or resume_text.")

    if not job_description.strip():
        raise HTTPException(status_code=400, detail="job_description is required.")

    # 2. Skill extraction
    resume_skills = extract_skills(clean_resume)
    job_skills = extract_skills(job_description)
    skill_comparison = compare_skills(resume_skills["skills"], job_skills["skills"])

    # 3. Similarity scores
    scores = compute_similarity_scores(
        clean_resume,
        job_description,
        skill_match_pct=skill_comparison["match_percentage"],
        use_embeddings=use_embeddings,
    )
    scores["matched_skills"] = skill_comparison["matched"]
    scores["missing_skills"] = skill_comparison["missing"]

    # 4. LLM insights
    insights = analyze_with_llm(clean_resume, job_description, scores)

    if "error" in insights:
        raise HTTPException(status_code=502, detail=f"LLM error: {insights['error']}")

    # 5. Build response
    return AnalysisResult(
        overall_score=scores["overall_score"],
        semantic_score=scores["semantic_score"],
        skill_score=scores["skill_score"],
        experience_score=scores["experience_score"],
        matched_skills=skill_comparison["matched"],
        missing_skills=skill_comparison["missing"],
        extra_skills=skill_comparison.get("extra", []),
        summary=insights.get("summary", ""),
        strengths=insights.get("strengths", []),
        weaknesses=insights.get("weaknesses", []),
        suggestions=insights.get("suggestions", []),
        rewrite_tip=insights.get("rewrite_tip", ""),
        word_count=word_count,
        file_type=file_type,
    )