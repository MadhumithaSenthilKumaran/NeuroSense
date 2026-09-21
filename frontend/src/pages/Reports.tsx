import React, { useEffect, useState } from 'react'
import api from '../api'
import { useNavigate } from 'react-router-dom'

export default function Reports(){
  const [history, setHistory] = useState<any[]>([])
  const [finalReports, setFinalReports] = useState<any[]>([])
  const [notifications, setNotifications] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(()=>{
    Promise.all([api.get('/reports/history'), api.get('/auth/notifications')]).then(([reports, messages])=>{
      setHistory(reports.data.history || [])
      setFinalReports(reports.data.final_reports || [])
      setNotifications(messages.data.notifications || [])
    }).catch(()=>{})
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
        {notifications.length > 0 && <div className="assessment-suggestion"><strong>Session messages</strong>{notifications.map((notification, index) => <span key={`${notification.scheduled_for}-${index}`}>{notification.message}{notification.emailed ? ' Email sent.' : ''}</span>)}</div>}
        {finalReports.map(report => (
          <div key={report.report_id} className="report-card final-report-card">
            <div>
              <div className="report-date">Final three-session report</div>
              <div className="report-risk">{report.session_count} sessions · generated {report.generated_at ? formatTimestamp(report.generated_at) : 'Unknown date'}</div>
            </div>
            <button className="form-submit small" onClick={() => downloadReport(report.report_id, `NeuroSense_Final_Report_${report.cycle_id || report.report_id}.pdf`)} disabled={loading}>Download PDF</button>
          </div>
        ))}
        {history.length===0 && finalReports.length===0 && <div className="empty-state">No completed assessments yet.</div>}
        {history.map((h,idx)=>(
          <div key={idx} className="report-card">
            <div>
              <div className="report-date">{h.session_label || `Session ${h.session_number || '?'}`} · {h.scheduled_for || 'Date unavailable'}</div>
              <div className="report-risk">Risk: <strong>{h.risk_class || 'Pending'}</strong> ({h.risk_probability != null ? `${Math.round(Number(h.risk_probability) * 100)}%` : 'n/a'})</div>
              <div className="report-risk">Completed {h.completed_at ? formatTimestamp(h.completed_at) : 'Unknown time'}</div>
            </div>
            <div className="report-actions">
              {h.next_session_date && <button className="form-submit small" onClick={async () => {
                try {
                  const next = await api.post(`/assessment/${h.assessment_id || h._id}/next`)
                  navigate(`/assessment/lifestyle/${next.data.assessment._id}`)
                } catch (err: any) { alert(err?.response?.data?.error || 'The next session is not available yet') }
              }}>Start next session</button>}
              <button className="form-submit small" onClick={() => generate(h.assessment_id || h._id)} disabled={loading}>Download PDF</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

async function downloadReport(reportId:string, filename:string) {
  const fileRes = await api.get(`/reports/download/${reportId}`, { responseType: 'blob' })
  const url = window.URL.createObjectURL(new Blob([fileRes.data], { type: 'application/pdf' }))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  window.URL.revokeObjectURL(url)
}

function formatTimestamp(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}
