import React, { useState } from 'react'
import api from '../api'
import { useParams } from 'react-router-dom'

export default function Finalize(){
  const { id } = useParams<{id:string}>()
  const [loading, setLoading] = useState(false)
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
          <div className="mb-2">Modality scores:</div>
          <pre className="bg-gray-100 p-2 rounded">{JSON.stringify(result.modality_scores, null, 2)}</pre>
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
