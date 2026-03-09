"""
llm_analyzer.py
---------------
Uses Groq API (FREE) with proper headers to avoid Cloudflare blocks.
Free tier: 14,400 requests/day, no credit card needed.
Get your free key at: https://console.groq.com
"""

import json
import os
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def build_prompt(resume_text: str, job_text: str, scores: dict) -> str:
    matched = ', '.join(scores.get('matched_skills', [])) or 'None'
    missing = ', '.join(scores.get('missing_skills', [])) or 'None'
    return f"""You are an expert career coach and resume analyst.
You have already computed the following match scores:
- Overall Match Score: {scores.get('overall_score', 'N/A')}%
- Semantic Fit: {scores.get('semantic_score', 'N/A')}%
- Skill Overlap: {scores.get('skill_score', 'N/A')}%
- Experience Match: {scores.get('experience_score', 'N/A')}%
- Matched Skills: {matched}
- Missing Skills: {missing}

RESUME:
{resume_text[:3000]}

JOB DESCRIPTION:
{job_text[:2000]}

Return ONLY a valid JSON object, no markdown, no backticks, no explanation outside JSON:
{{
    "summary": "<2-3 sentence assessment>",
    "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
    "weaknesses": ["<weakness 1>", "<weakness 2>", "<weakness 3>"],
    "suggestions": ["<suggestion 1>", "<suggestion 2>", "<suggestion 3>", "<suggestion 4>"],
    "rewrite_tip": "<one sentence rewrite tip>"
}}"""


def analyze_with_llm(
    resume_text: str,
    job_text: str,
    scores: dict,
    model: str = "llama-3.3-70b-versatile",
) -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {"error": "GROQ_API_KEY not found. Get your free key at https://console.groq.com"}

    prompt = build_prompt(resume_text, job_text, scores)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "Mozilla/5.0",
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_tokens": 1024,
    }

    raw_text = ""
    try:
        response = requests.post(
            GROQ_API_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        raw_text = data["choices"][0]["message"]["content"].strip()
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()
        return json.loads(raw_text)

    except requests.exceptions.HTTPError as e:
        return {"error": f"Groq API HTTP error {e.response.status_code}: {e.response.text}"}
    except requests.exceptions.ConnectionError as e:
        return {"error": f"Connection error: {e}"}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out. Please try again."}
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse response as JSON: {e}", "raw_response": raw_text}
    except Exception as e:
        return {"error": f"Unexpected error: {e}"}


def format_insights_for_display(insights: dict) -> str:
    if "error" in insights:
        return f"Error: {insights['error']}"
    lines = ["=" * 60, "AI ANALYSIS (Groq LLaMA — Free)", "=" * 60]
    lines.append(f"\nSUMMARY:\n{insights.get('summary', 'N/A')}")
    lines.append("\nSTRENGTHS:")
    for s in insights.get("strengths", []):
        lines.append(f"  v {s}")
    lines.append("\nWEAKNESSES:")
    for w in insights.get("weaknesses", []):
        lines.append(f"  x {w}")
    lines.append("\nSUGGESTIONS:")
    for i, s in enumerate(insights.get("suggestions", []), 1):
        lines.append(f"  {i}. {s}")
    if insights.get("rewrite_tip"):
        lines.append(f"\nREWRITE TIP:\n  -> {insights['rewrite_tip']}")
    lines.append("=" * 60)
    return "\n".join(lines)
