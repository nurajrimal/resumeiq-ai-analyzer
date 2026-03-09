import { useState, useRef, useEffect } from 'react'
import { analyzeResume, checkHealth } from './api'

/* ─────────────────────────────────────────────
   Tiny reusable components
───────────────────────────────────────────── */

function ScoreRing({ value, label, color }) {
  const r = 36, circ = 2 * Math.PI * r
  const dash = circ * (value / 100)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
      <svg width={90} height={90} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={45} cy={45} r={r} fill="none" stroke="var(--border)" strokeWidth={7} />
        <circle
          cx={45} cy={45} r={r} fill="none"
          stroke={color} strokeWidth={7}
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 1s ease' }}
        />
        <text
          x={45} y={45}
          textAnchor="middle" dominantBaseline="central"
          fill={color}
          fontSize={16} fontWeight={800}
          style={{ transform: 'rotate(90deg)', transformOrigin: '45px 45px', fontFamily: 'var(--font)' }}
        >
          {value}%
        </text>
      </svg>
      <span style={{ fontSize: 11, color: 'var(--muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.07em' }}>
        {label}
      </span>
    </div>
  )
}

function SkillChip({ label, matched }) {
  return (
    <span style={{
      display: 'inline-block', padding: '4px 11px', borderRadius: 20, margin: 3,
      fontSize: 12, fontWeight: 600,
      background: matched ? 'rgba(0,229,160,0.1)' : 'rgba(255,82,114,0.1)',
      color: matched ? 'var(--green)' : 'var(--red)',
      border: `1px solid ${matched ? 'rgba(0,229,160,0.25)' : 'rgba(255,82,114,0.25)'}`,
    }}>
      {matched ? '✓' : '✗'} {label}
    </span>
  )
}

function SuggestionCard({ index, text }) {
  return (
    <div style={{
      display: 'flex', gap: 12, alignItems: 'flex-start',
      padding: '12px 14px', borderRadius: 10,
      background: 'var(--surface)', border: '1px solid var(--border)',
      fontSize: 13, lineHeight: 1.65,
    }}>
      <span style={{
        minWidth: 24, height: 24, borderRadius: '50%',
        background: 'var(--accent)', color: '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 11, fontWeight: 800, flexShrink: 0,
      }}>
        {index}
      </span>
      {text}
    </div>
  )
}

function StatusDot({ online }) {
  return (
    <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: online ? 'var(--green)' : 'var(--red)' }}>
      <span style={{
        width: 7, height: 7, borderRadius: '50%',
        background: online ? 'var(--green)' : 'var(--red)',
        boxShadow: online ? '0 0 6px var(--green)' : 'none',
      }} />
      {online ? 'API connected' : 'API offline — start FastAPI server'}
    </span>
  )
}

/* ─────────────────────────────────────────────
   Main App
───────────────────────────────────────────── */
export default function App() {
  const [file, setFile] = useState(null)
  const [resumeText, setResumeText] = useState('')
  const [jobDesc, setJobDesc] = useState('')
  const [useEmbeddings, setUseEmbeddings] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const [apiOnline, setApiOnline] = useState(null)
  const fileRef = useRef()
  const resultsRef = useRef()

  // Check backend health on mount
  useEffect(() => {
    checkHealth().then(setApiOnline)
  }, [])

  const handleFile = (f) => {
    if (!f) return
    setFile(f)
    setResumeText('')
  }

  const handleAnalyze = async () => {
    setLoading(true)
    setError('')
    setResult(null)

    try {
      const data = await analyzeResume({
        file,
        resumeText,
        jobDescription: jobDesc,
        useEmbeddings,
      })
      setResult(data)
      // Scroll to results after render
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: 'smooth' }), 100)
    } catch (e) {
      setError(e.message || 'Analysis failed. Is the FastAPI server running?')
    } finally {
      setLoading(false)
    }
  }

  const canAnalyze = (file || resumeText.trim()) && jobDesc.trim() && !loading

  const scoreColor = (s) => s >= 75 ? 'var(--green)' : s >= 50 ? 'var(--yellow)' : 'var(--red)'
  const scoreLabel = (s) => s >= 75 ? '🟢 Strong Match' : s >= 50 ? '🟡 Moderate Match' : '🔴 Weak Match'

  return (
    <div style={{ minHeight: '100vh' }}>

      {/* ── Header ── */}
      <header style={{
        borderBottom: '1px solid var(--border)',
        background: 'var(--surface)',
        padding: '0 40px',
        height: 64,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        position: 'sticky', top: 0, zIndex: 100,
        backdropFilter: 'blur(12px)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: 'linear-gradient(135deg, var(--accent), var(--accent2))',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 17,
          }}>🎯</div>
          <div>
            <div style={{ fontWeight: 800, fontSize: 17, letterSpacing: '-0.3px' }}>ResumeIQ</div>
            <div style={{ fontSize: 11, color: 'var(--muted)' }}>AI Resume Analyzer</div>
          </div>
        </div>
        {apiOnline !== null && <StatusDot online={apiOnline} />}
      </header>

      {/* ── Hero ── */}
      <div style={{ textAlign: 'center', padding: '56px 24px 40px' }}>
        <h1 style={{
          fontSize: 'clamp(2rem, 5vw, 3.2rem)',
          fontWeight: 800, letterSpacing: '-1.5px',
          lineHeight: 1.15, marginBottom: 16,
          background: 'linear-gradient(135deg, var(--text) 40%, var(--accent2))',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        }}>
          Land the job.<br />Know your gaps.
        </h1>
        <p style={{ color: 'var(--muted)', fontSize: 16, maxWidth: 480, margin: '0 auto' }}>
          Upload your resume, paste a job description — get an instant AI-powered match score with actionable feedback.
        </p>
      </div>

      {/* ── Input Grid ── */}
      <div style={{
        maxWidth: 1080, margin: '0 auto', padding: '0 24px 32px',
        display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20,
      }}>

        {/* Resume card */}
        <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 16, padding: 24 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 14 }}>
            📄 Your Resume
          </div>

          {/* Drop zone */}
          <div
            style={{
              border: `2px dashed ${dragOver ? 'var(--accent)' : 'var(--border)'}`,
              borderRadius: 12, padding: '32px 16px', textAlign: 'center',
              cursor: 'pointer', transition: 'all 0.2s',
              background: dragOver ? 'rgba(124,109,255,0.06)' : 'transparent',
            }}
            onClick={() => fileRef.current.click()}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files[0]) }}
          >
            <input ref={fileRef} type="file" accept=".pdf,.docx,.txt" hidden
              onChange={(e) => handleFile(e.target.files[0])} />
            {file ? (
              <>
                <div style={{ fontSize: 28, marginBottom: 6 }}>✅</div>
                <div style={{ fontWeight: 700, color: 'var(--green)', fontSize: 14 }}>{file.name}</div>
                <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>
                  {(file.size / 1024).toFixed(1)} KB — click to replace
                </div>
              </>
            ) : (
              <>
                <div style={{ fontSize: 30, marginBottom: 8 }}>📂</div>
                <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>Drop your resume here</div>
                <div style={{ fontSize: 12, color: 'var(--muted)' }}>PDF, DOCX, or TXT</div>
              </>
            )}
          </div>

          <div style={{ margin: '14px 0 8px', fontSize: 11, color: 'var(--muted)', textAlign: 'center' }}>
            — or paste text below —
          </div>
          <textarea
            style={{
              width: '100%', background: 'var(--surface)', border: '1px solid var(--border)',
              borderRadius: 10, padding: '12px 14px', color: 'var(--text)', fontSize: 13,
              resize: 'vertical', outline: 'none', fontFamily: 'var(--font)',
              lineHeight: 1.6, minHeight: 120,
            }}
            placeholder="Paste resume text here..."
            value={resumeText}
            onChange={(e) => { setResumeText(e.target.value); setFile(null) }}
          />
        </div>

        {/* Job description card */}
        <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 16, padding: 24 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 14 }}>
            💼 Job Description
          </div>
          <textarea
            style={{
              width: '100%', background: 'var(--surface)', border: '1px solid var(--border)',
              borderRadius: 10, padding: '12px 14px', color: 'var(--text)', fontSize: 13,
              resize: 'vertical', outline: 'none', fontFamily: 'var(--font)',
              lineHeight: 1.6, minHeight: 300,
            }}
            placeholder="Paste the full job posting — include required skills, responsibilities, and qualifications..."
            value={jobDesc}
            onChange={(e) => setJobDesc(e.target.value)}
          />
          <div style={{ marginTop: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--muted)', cursor: 'pointer' }}>
              <input type="checkbox" checked={useEmbeddings} onChange={(e) => setUseEmbeddings(e.target.checked)} />
              Use semantic embeddings (more accurate)
            </label>
            <span style={{ fontSize: 11, color: 'var(--muted)' }}>{jobDesc.length} chars</span>
          </div>
        </div>
      </div>

      {/* ── Analyze Button ── */}
      <div style={{ maxWidth: 1080, margin: '0 auto', padding: '0 24px 40px' }}>
        <button
          disabled={!canAnalyze}
          onClick={handleAnalyze}
          style={{
            width: '100%', padding: '15px 0', borderRadius: 12, border: 'none',
            background: canAnalyze
              ? 'linear-gradient(135deg, var(--accent), #9e94ff)'
              : 'var(--border)',
            color: canAnalyze ? '#fff' : 'var(--muted)',
            fontSize: 15, fontWeight: 800, cursor: canAnalyze ? 'pointer' : 'not-allowed',
            letterSpacing: '0.03em', transition: 'opacity 0.2s',
          }}
        >
          {loading ? '⏳  Analyzing with AI...' : '⚡  Analyze Match'}
        </button>

        {error && (
          <div style={{
            marginTop: 16, padding: '14px 18px', borderRadius: 10,
            background: 'rgba(255,82,114,0.08)', border: '1px solid rgba(255,82,114,0.25)',
            color: 'var(--red)', fontSize: 13,
          }}>
            ⚠️ {error}
          </div>
        )}
      </div>

      {/* ── Results ── */}
      {result && (
        <div ref={resultsRef} style={{ maxWidth: 1080, margin: '0 auto', padding: '0 24px 80px' }}>

          <div style={{ borderTop: '1px solid var(--border)', paddingTop: 40, marginBottom: 32 }}>
            <h2 style={{ fontSize: 22, fontWeight: 800, marginBottom: 4 }}>📊 Analysis Results</h2>
            <p style={{ color: 'var(--muted)', fontSize: 13 }}>
              Parsed {result.word_count} words from your {result.file_type} resume
            </p>
          </div>

          {/* Score row */}
          <div style={{
            display: 'grid', gridTemplateColumns: '200px 1fr', gap: 20, marginBottom: 20,
          }}>
            {/* Big score */}
            <div style={{
              background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 16,
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              padding: '28px 16px', gap: 8,
            }}>
              <div style={{ fontSize: 11, color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                Overall Match
              </div>
              <div style={{ fontSize: 58, fontWeight: 900, lineHeight: 1, color: scoreColor(result.overall_score), letterSpacing: '-2px' }}>
                {result.overall_score}<span style={{ fontSize: 26, fontWeight: 500 }}>%</span>
              </div>
              <div style={{ fontSize: 13, color: 'var(--muted)' }}>{scoreLabel(result.overall_score)}</div>
            </div>

            {/* Ring scores + summary */}
            <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 16, padding: 24 }}>
              <div style={{ display: 'flex', gap: 32, justifyContent: 'center', marginBottom: 20 }}>
                <ScoreRing value={result.semantic_score} label="Semantic Fit" color="var(--accent2)" />
                <ScoreRing value={result.skill_score} label="Skill Overlap" color="var(--green)" />
                <ScoreRing value={result.experience_score} label="Experience" color="var(--yellow)" />
              </div>
              {result.summary && (
                <p style={{
                  fontSize: 13, color: 'var(--muted)', lineHeight: 1.75,
                  borderTop: '1px solid var(--border)', paddingTop: 16,
                }}>
                  {result.summary}
                </p>
              )}
            </div>
          </div>

          {/* Skills */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
            <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 16, padding: 24 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent2)', marginBottom: 14 }}>✅ Matched Skills</div>
              {result.matched_skills.length > 0
                ? result.matched_skills.map(s => <SkillChip key={s} label={s} matched />)
                : <span style={{ fontSize: 13, color: 'var(--muted)' }}>None detected</span>
              }
            </div>
            <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 16, padding: 24 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent2)', marginBottom: 14 }}>❌ Missing Skills</div>
              {result.missing_skills.length > 0
                ? result.missing_skills.map(s => <SkillChip key={s} label={s} matched={false} />)
                : <span style={{ fontSize: 13, color: 'var(--green)' }}>✨ No critical gaps!</span>
              }
            </div>
          </div>

          {/* AI Insights */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
            <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 16, padding: 24 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent2)', marginBottom: 14 }}>💪 Strengths</div>
              {result.strengths.map((s, i) => (
                <div key={i} style={{ fontSize: 13, lineHeight: 1.7, marginBottom: 8, paddingLeft: 14, borderLeft: '2px solid var(--green)', color: 'var(--text)' }}>
                  {s}
                </div>
              ))}
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent2)', margin: '20px 0 14px' }}>⚠️ Weaknesses</div>
              {result.weaknesses.map((w, i) => (
                <div key={i} style={{ fontSize: 13, lineHeight: 1.7, marginBottom: 8, paddingLeft: 14, borderLeft: '2px solid var(--red)', color: 'var(--text)' }}>
                  {w}
                </div>
              ))}
            </div>

            <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 16, padding: 24 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent2)', marginBottom: 14 }}>🚀 How to Improve</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {result.suggestions.map((s, i) => <SuggestionCard key={i} index={i + 1} text={s} />)}
              </div>

              {result.rewrite_tip && (
                <>
                  <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent2)', margin: '20px 0 10px' }}>✏️ Rewrite Tip</div>
                  <div style={{
                    padding: '12px 14px', borderRadius: 10, fontSize: 13, lineHeight: 1.65,
                    background: 'rgba(124,109,255,0.08)', border: '1px solid rgba(124,109,255,0.2)',
                    color: 'var(--accent2)',
                  }}>
                    {result.rewrite_tip}
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Reset */}
          <div style={{ textAlign: 'center', marginTop: 32 }}>
            <button
              onClick={() => { setResult(null); setFile(null); setResumeText(''); setJobDesc('') }}
              style={{
                padding: '10px 28px', borderRadius: 10, border: '1px solid var(--border)',
                background: 'transparent', color: 'var(--muted)', fontSize: 13,
                cursor: 'pointer', fontFamily: 'var(--font)',
              }}
            >
              ↩ Start Over
            </button>
          </div>
        </div>
      )}
    </div>
  )
}