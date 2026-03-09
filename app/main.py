"""
main.py
-------
Streamlit web interface for the AI Resume Analyzer.
Run with: streamlit run app/main.py
"""

import sys
import os
import io

import streamlit as st

# Make sure sibling modules are importable when running from project root
sys.path.insert(0, os.path.dirname(__file__))

from resume_parser import parse_resume
from skill_extractor import extract_skills, compare_skills
from similarity_engine import compute_similarity_scores
from llm_analyzer import analyze_with_llm, format_insights_for_display

# ---------------------------------------------------------------
# Page config
# ---------------------------------------------------------------
st.set_page_config(
    page_title="ResumeIQ – AI Resume Analyzer",
    page_icon="🎯",
    layout="wide",
)

# ---------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------
st.markdown(
    """
    <style>
    body { background-color: #0a0a0f; }
    .score-card {
        background: #1a1a26;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        border: 1px solid #2a2a3d;
    }
    .score-number {
        font-size: 3.5rem;
        font-weight: 800;
        line-height: 1;
    }
    .skill-match   { color: #00e5a0; background: rgba(0,229,160,0.1);
                     border-radius: 20px; padding: 4px 12px; margin: 2px;
                     display: inline-block; font-size: 0.8rem; }
    .skill-missing { color: #ff5f7e; background: rgba(255,95,126,0.1);
                     border-radius: 20px; padding: 4px 12px; margin: 2px;
                     display: inline-block; font-size: 0.8rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------
# Header
# ---------------------------------------------------------------
st.markdown("# 🎯 ResumeIQ")
st.markdown("**AI-Powered Resume Analyzer** — Upload your resume, paste a job description, and get an instant match score with actionable feedback.")
st.divider()

# ---------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 Your Resume")
    uploaded_file = st.file_uploader(
        "Upload PDF, DOCX, or TXT",
        type=["pdf", "docx", "txt"],
        help="Your resume file",
    )
    resume_text_input = st.text_area(
        "Or paste resume text here",
        height=220,
        placeholder="Paste your resume content...",
    )

with col2:
    st.subheader("💼 Job Description")
    job_text = st.text_area(
        "Paste the job description",
        height=320,
        placeholder="Paste the full job posting — include required skills, responsibilities, qualifications...",
    )

use_embeddings = st.checkbox(
    "Use semantic embeddings (more accurate, slower first run)",
    value=False,
    help="Downloads ~90MB model on first use. Uncheck for instant TF-IDF fallback.",
)

analyze_btn = st.button("⚡ Analyze Match", type="primary", use_container_width=True)

# ---------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------
if analyze_btn:
    # --- Resolve resume text ---
    resume_text = ""
    if uploaded_file is not None:
        file_bytes = io.BytesIO(uploaded_file.read())
        parsed = parse_resume(file_bytes, filename=uploaded_file.name)
        if "error" in parsed:
            st.error(f"Failed to parse resume: {parsed['error']}")
            st.stop()
        resume_text = parsed["clean_text"]
        st.success(f" Parsed {parsed['file_type']} — {parsed['word_count']} words extracted")
    elif resume_text_input.strip():
        resume_text = resume_text_input.strip()
    else:
        st.warning("Please upload a resume or paste resume text.")
        st.stop()

    if not job_text.strip():
        st.warning("Please paste a job description.")
        st.stop()

    # --- Run pipeline ---
    with st.spinner("Extracting skills..."):
        resume_skills = extract_skills(resume_text)
        job_skills = extract_skills(job_text)
        skill_comparison = compare_skills(resume_skills["skills"], job_skills["skills"])

    with st.spinner("Computing similarity scores..."):
        scores = compute_similarity_scores(
            resume_text,
            job_text,
            skill_match_pct=skill_comparison["match_percentage"],
            use_embeddings=use_embeddings,
        )
        scores["matched_skills"] = skill_comparison["matched"]
        scores["missing_skills"] = skill_comparison["missing"]

    with st.spinner("Running AI analysis (Claude)..."):
        insights = analyze_with_llm(resume_text, job_text, scores)

    st.divider()
    st.subheader("📊 Results")

    # ---------------------------------------------------------------
    # Score cards
    # ---------------------------------------------------------------
    s1, s2, s3, s4 = st.columns(4)
    overall = scores["overall_score"]
    color = "#00e5a0" if overall >= 75 else "#ffd166" if overall >= 50 else "#ff5f7e"

    with s1:
        st.markdown(
            f'<div class="score-card"><div style="font-size:0.75rem;color:#7b78a8;margin-bottom:6px;">OVERALL MATCH</div>'
            f'<div class="score-number" style="color:{color}">{overall}%</div></div>',
            unsafe_allow_html=True,
        )
    with s2:
        st.markdown(
            f'<div class="score-card"><div style="font-size:0.75rem;color:#7b78a8;margin-bottom:6px;">SEMANTIC FIT</div>'
            f'<div class="score-number" style="color:#a99cff">{scores["semantic_score"]}%</div></div>',
            unsafe_allow_html=True,
        )
    with s3:
        st.markdown(
            f'<div class="score-card"><div style="font-size:0.75rem;color:#7b78a8;margin-bottom:6px;">SKILL OVERLAP</div>'
            f'<div class="score-number" style="color:#00e5a0">{scores["skill_score"]}%</div></div>',
            unsafe_allow_html=True,
        )
    with s4:
        st.markdown(
            f'<div class="score-card"><div style="font-size:0.75rem;color:#7b78a8;margin-bottom:6px;">EXPERIENCE</div>'
            f'<div class="score-number" style="color:#ffd166">{scores["experience_score"]}%</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------------
    # Skills comparison
    # ---------------------------------------------------------------
    sk1, sk2 = st.columns(2)
    with sk1:
        st.markdown("###  Matched Skills")
        if skill_comparison["matched"]:
            chips = " ".join(
                f'<span class="skill-match">{s}</span>'
                for s in skill_comparison["matched"]
            )
            st.markdown(chips, unsafe_allow_html=True)
        else:
            st.info("No matching skills detected.")

    with sk2:
        st.markdown("###  Missing Skills")
        if skill_comparison["missing"]:
            chips = " ".join(
                f'<span class="skill-missing">{s}</span>'
                for s in skill_comparison["missing"]
            )
            st.markdown(chips, unsafe_allow_html=True)
        else:
            st.success("No critical skill gaps!")

    st.divider()

    # ---------------------------------------------------------------
    # AI insights
    # ---------------------------------------------------------------
    if "error" in insights:
        st.error(f"AI Analysis error: {insights['error']}")
    else:
        st.markdown("###  AI Insights")

        if insights.get("summary"):
            st.info(insights["summary"])

        ai1, ai2 = st.columns(2)
        with ai1:
            st.markdown("####  Strengths")
            for s in insights.get("strengths", []):
                st.markdown(f"✓ {s}")

            st.markdown("#### ⚠️ Weaknesses")
            for w in insights.get("weaknesses", []):
                st.markdown(f"✗ {w}")

        with ai2:
            st.markdown("#### How to Improve")
            for i, sug in enumerate(insights.get("suggestions", []), 1):
                st.markdown(f"**{i}.** {sug}")

            if insights.get("rewrite_tip"):
                st.markdown("#### ✏️ Rewrite Tip")
                st.success(insights["rewrite_tip"])

    # ---------------------------------------------------------------
    # Raw text expanders (for debugging / portfolio demo)
    # ---------------------------------------------------------------
    with st.expander("🔍 View extracted resume text"):
        st.text(resume_text[:2000] + ("..." if len(resume_text) > 2000 else ""))

    with st.expander("📋 View all detected skills"):
        st.json({"resume_skills": resume_skills, "job_skills": job_skills})