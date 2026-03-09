/**
 * api.js
 * ------
 * All HTTP calls to the FastAPI backend.
 * Vite proxies /api/* → http://localhost:8000/*
 */

const BASE = '/api'

/**
 * Check if the backend is reachable.
 * @returns {Promise<boolean>}
 */
export async function checkHealth() {
  try {
    const res = await fetch(`${BASE}/health`)
    return res.ok
  } catch {
    return false
  }
}

/**
 * Analyze a resume against a job description.
 *
 * @param {Object} params
 * @param {File|null}   params.file           - uploaded resume file (PDF/DOCX/TXT)
 * @param {string}      params.resumeText     - pasted resume text (used if no file)
 * @param {string}      params.jobDescription - job posting text
 * @param {boolean}     params.useEmbeddings  - use sentence-transformers (slower, accurate)
 *
 * @returns {Promise<Object>} analysis result matching AnalysisResult schema
 */
export async function analyzeResume({ file, resumeText, jobDescription, useEmbeddings = false }) {
  const form = new FormData()
  form.append('job_description', jobDescription)
  form.append('use_embeddings', useEmbeddings)

  if (file) {
    form.append('resume_file', file)
  } else {
    form.append('resume_text', resumeText)
  }

  const res = await fetch(`${BASE}/analyze`, {
    method: 'POST',
    body: form,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Server error ${res.status}`)
  }

  return res.json()
}