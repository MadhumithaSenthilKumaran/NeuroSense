import React, { useState } from 'react'
import api from '../api'
import { useNavigate, useParams } from 'react-router-dom'

export default function Finalize(){
  const { id } = useParams<{id:string}>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [nextLoading, setNextLoading] = useState(false)
  const [result, setResult] = useState<any | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notificationMessage, setNotificationMessage] = useState('')

  const run = async ()=>{
    setLoading(true); setError(null)
    try{
      const res = await api.post(`/assessment/${id}/finalize`)
      setResult(res.data.assessment)
      setNotificationMessage('Assessment completed successfully. Your report is ready. A notification has been sent to your selected communication channels.')
    }catch(err:any){
      setError(err?.response?.data?.error || err?.response?.data?.msg || 'Failed to finalize')
    }finally{setLoading(false)}
  }

  const startNextSession = async () => {
    setNextLoading(true)
    try {
      const res = await api.post(`/assessment/${id}/next`)
      navigate(`/assessment/lifestyle/${res.data.assessment._id}`)
    } catch (err: any) {
      setError(err?.response?.data?.error || 'The next session is not available yet')
    } finally { setNextLoading(false) }
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-medium">Finalize Assessment</h2>
      <p>When you finalize, the system will fuse available modalities and produce recommendations.</p>
      <div>
        <button className="form-submit" onClick={run} disabled={loading}>{loading? 'Processing...' : 'Finalize'}</button>
      </div>

      {error && <div className="text-red-600">{error}</div>}

      {result && (
        <div className="finalize-result">
          {notificationMessage && <div className="form-message">{notificationMessage}</div>}
          <div className="result-summary">
            <div><span>Overall risk</span><strong>{result.risk_class || 'Not available'}</strong><small>{formatProbability(result.risk_probability)}</small></div>
            <div><span>Modalities used</span><strong>{result.used_modalities?.length || 0}</strong><small>{result.used_modalities?.join(', ') || 'None recorded'}</small></div>
            <div><span>Next session date</span><strong>{result.next_session_date || 'Final session'}</strong><small>{result.next_session_date ? 'Available on this date' : 'Final session complete'}</small></div>
          </div>
          <div className="score-visuals">
            <ScoreBars result={result} />
            <ModalityChart scores={result.modality_scores} />
          </div>
          {result.cognitive_result?.breakdown && <CognitiveBreakdown breakdown={result.cognitive_result.breakdown} />}
          {result.next_session_date && (
            <button className="form-submit next-session" onClick={startNextSession} disabled={nextLoading}>
              {nextLoading ? 'Checking date...' : 'Start next session'}
            </button>
          )}
          {result.next_assessment_suggestion && (
            <div className="assessment-suggestion">
              <strong>Next assessment suggestion</strong><span>{result.next_assessment_suggestion}</span>
            </div>
          )}
          <div className="recommendation-panel">
            <h3>Recommended focus</h3>
            <p>{result.recommendations?.summary || 'Use these focus areas to guide your next steps.'}</p>
            <div className="recommendation-grid">
              <RecommendationList title="Personalized action plan" items={result.recommendations?.personalized_action_plan} />
              <RecommendationList title="Recommended exercises" items={result.recommendations?.exercise_recommendations} />
              <RecommendationList title="Sleep" items={result.recommendations?.sleep_recommendations} />
              <RecommendationList title="Diet" items={result.recommendations?.diet_suggestions} />
              <RecommendationList title="Memory strategies" items={result.recommendations?.memory_improvement_tips} />
              <RecommendationList title="Stress reduction" items={result.recommendations?.stress_reduction_recommendations} />
              <RecommendationList title="Clinical follow-up" items={result.recommendations?.medical_consultation_guidance} />
            </div>
            {result.recommendations?.disclaimer && <div className="recommendation-disclaimer">{result.recommendations.disclaimer}</div>}
          </div>
        </div>
      )}
    </div>
  )
}

function RecommendationList({ title, items }: { title: string; items?: string[] }) {
  if (!items?.length) return null
  return <div className="recommendation-item"><strong>{title}</strong><span>{items[0]}</span><small>{items.length} suggestion{items.length === 1 ? '' : 's'}</small></div>
}

function CognitiveBreakdown({ breakdown }: { breakdown: any }) {
  return <section className="recommendation-panel cognitive-breakdown"><h3>How the cognitive score was formed</h3><p>{breakdown.method}</p><div className="recommendation-grid">{breakdown.parts.map((part: any) => <div className="recommendation-item" key={part.key}><strong>{part.name} · {part.weight_percent}%</strong><span>{part.score == null ? 'Not recorded' : `${part.score}/100`}</span><small>{part.contribution_points == null ? 'No contribution' : `${part.contribution_points} points contributed`}</small><small>{part.explanation}</small>{part.key === 'visual_memory' && part.game_breakdown?.number_elapsed_ms != null && <small>Number-order time: {(Number(part.game_breakdown.number_elapsed_ms) / 1000).toFixed(2)}s · sequence completed: {part.game_breakdown.number_sequence_completed ? 'yes' : 'no'}.</small>}{part.key === 'praxis_camera' && <><small>Sequential camera cross-check: {part.game_breakdown?.camera_correct_trials ?? 0}/{part.game_breakdown?.camera_total_trials ?? 0} numbers correct ({part.game_breakdown?.camera_sequence_score ?? 0}/100).</small>{part.game_breakdown?.praxis_trials?.map((trial: any) => <small key={`${trial.prompted_number}-${trial.gestured_number_detected}`}>Number {trial.prompted_number}: detected {trial.gestured_number_detected}; latency {trial.metrics?.motor_latency_seconds ?? 'n/a'}s, frames with hand {trial.metrics?.frames_with_hand ?? 0}.</small>)}</>}</div>)}</div></section>
}

function formatProbability(value: number | null | undefined) {
  return value == null ? 'Not available' : `${Math.round(Number(value) * 100)}%`
}

function formatTimestamp(value: string, includeTime = false) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', ...(includeTime ? { timeStyle: 'short' } : {}) }).format(date)
}

function ScoreBars({ result }: { result: any }) {
  const scores = [
    ['Lifestyle', result.lifestyle_score],
    ['Clinical concern', result.clinical_concern_score],
    ['Cognitive', result.cognitive_result?.overall_cognitive_score],
    ['Speech risk', result.modality_scores?.speech == null ? null : Number(result.modality_scores.speech) * 100],
  ]
  return <section className="visual-card"><div className="visual-heading"><h3>Assessment profile</h3><span>0 to 100</span></div>{scores.map(([label, value]) => <div className="score-bar" key={label as string}><div><span>{label}</span><strong>{value == null ? 'N/A' : `${Math.round(Number(value))}%`}</strong></div><div className="bar-track"><i style={{ width: `${Math.min(100, Math.max(0, Number(value) || 0))}%` }} /></div></div>)}</section>
}

function ModalityChart({ scores }: { scores?: Record<string, number> }) {
  const entries = Object.entries(scores || {}).filter(([, value]) => value != null)
  if (!entries.length) return null
  return <section className="visual-card modality-card"><div className="visual-heading"><h3>Modality signals</h3><span>Risk probability</span></div><div className="modality-chart">{entries.map(([label, value]) => <div className="modality-column" key={label}><div className="column-value">{Math.round(Number(value) * 100)}%</div><div className="column-track"><i style={{ height: `${Math.min(100, Math.max(0, Number(value) * 100))}%` }} /></div><span>{label}</span></div>)}</div></section>
}
