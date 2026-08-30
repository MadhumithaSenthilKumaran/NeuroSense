import React, { useEffect, useState } from 'react'
import api from '../api'

export default function Reports(){
  const [history, setHistory] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(()=>{
    api.get('/reports/history').then(r=>setHistory(r.data.history)).catch(()=>{})
  },[])

  const generate = async (assessment_id:string)=>{
    setLoading(true)
    try{
      console.log('Generating report for assessment:', assessment_id)
      const res = await api.post(`/reports/generate/${assessment_id}`)
      console.log('Generate response:', res.data)
      
      if (!res.data.download_url) {
        alert('Failed to generate report: No download URL returned')
        return
      }

      // Remove /api prefix if it exists in download_url since axios already has it as baseURL
      let downloadUrl = res.data.download_url
      if (downloadUrl.startsWith('/api/')) {
        downloadUrl = downloadUrl.substring(4) // Remove '/api' prefix
      }

      const fileRes = await api.get(downloadUrl, { 
        responseType: 'blob',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('ns_token')}` }
      })
      
      if (!fileRes.data || fileRes.data.size === 0) {
        alert('Failed to download report: Empty file received')
        return
      }

      const blob = new Blob([fileRes.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `NeuroSense_Report_${assessment_id}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      alert('Report downloaded successfully!')
    }catch(err:any){
      console.error('Report generation error:', err)
      const errorMsg = err?.response?.data?.error || err?.message || 'Failed to generate or download report'
      alert(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="report-page">
      <div className="page-intro">
        <div className="eyebrow">Assessment archive</div>
        <h1>Reports and summaries</h1>
        <p>Your screening reports, risk history, and recent insights are kept here for easy review.</p>
      </div>

      <div className="report-list">
        {history.length===0 && <div className="empty-state">No completed assessments yet.</div>}
        {history.map((h,idx)=>(
          <div key={idx} className="report-card">
            <div>
              <div className="report-date">{h.date ? new Date(h.date).toLocaleString() : 'Unknown date'}</div>
              <div className="report-risk">Risk: <strong>{h.risk_class || 'Pending'}</strong> ({h.risk_probability != null ? `${Math.round(Number(h.risk_probability) * 100)}%` : 'n/a'})</div>
            </div>
            <button className="form-submit small" onClick={() => generate(h.assessment_id || h._id)} disabled={loading}>Download PDF</button>
          </div>
        ))}
      </div>
    </div>
  )
}
