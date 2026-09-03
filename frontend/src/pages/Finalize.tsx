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

  const run = async ()=>{
    setLoading(true); setError(null)
    try{
      const res = await api.post(`/assessment/${id}/finalize`)
      setResult(res.data.assessment)
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
        <button className="px-4 py-2 bg-indigo-600 text-white rounded" onClick={run} disabled={loading}>{loading? 'Processing...' : 'Finalize'}</button>
      </div>

      {error && <div className="text-red-600">{error}</div>}

      {result && (
        <div className="p-4 border rounded">
          <div className="mb-2">Risk: <strong>{result.risk_class}</strong> ({result.risk_probability})</div>
          <div className="mb-2">Used modalities: {result.used_modalities?.join(', ')}</div>
           <div className="mb-2"><strong>Lifestyle score:</strong> {result.lifestyle_score ?? 'Not available'} / 100</div>
           <div className="mb-2"><strong>Lifestyle risk probability:</strong> {formatProbability(result.lifestyle_probability)}</div>
           <div className="mb-2"><strong>Clinical concern score:</strong> {result.clinical_concern_score ?? 'Not available'} / 100</div>
           <div className="mb-2"><strong>Cognitive score:</strong> {result.cognitive_result?.overall_cognitive_score ?? 'Not available'} / 100</div>
           <div className="mb-2"><strong>Speech risk probability:</strong> {formatProbability(result.modality_scores?.speech)}</div>
          <div className="mb-2"><strong>Next scheduled session:</strong> {result.next_session_date || 'This is the final session'}</div>
          {result.next_session_date && (
            <button className="px-4 py-2 bg-emerald-600 text-white rounded" onClick={startNextSession} disabled={nextLoading}>
              {nextLoading ? 'Checking date...' : 'Start next session'}
            </button>
          )}
           <div className="mb-2">Integrated modality scores:</div>
          <pre className="bg-gray-100 p-2 rounded">{JSON.stringify(result.modality_scores, null, 2)}</pre>
          {result.next_assessment_suggestion && (
            <div className="mt-3 p-3 rounded bg-amber-50 border border-amber-200 text-amber-900">
              <strong>Next assessment suggestion:</strong> {result.next_assessment_suggestion}
            </div>
          )}
          <div className="mt-2">
            <h4 className="font-medium">Recommendations</h4>
            <div className="mt-1">
              {result.recommendations?.summary ? (
                <div>{result.recommendations.summary}</div>
              ) : null}
              {result.recommendations?.explanation && <div className="mt-2 text-sm text-gray-700">{result.recommendations.explanation}</div>}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function formatProbability(value: number | null | undefined) {
  return value == null ? 'Not available' : `${Math.round(Number(value) * 100)}%`
}
