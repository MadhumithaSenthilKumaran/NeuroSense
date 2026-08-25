import React, { useEffect, useState } from 'react'
import api from '../api'

export default function AdminDashboard(){
  const [data, setData] = useState<any | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(()=>{
    api.get('/admin/dashboard').then(r=>setData(r.data)).catch((err:any)=>{
      if (err?.response?.status === 403) setError('Access denied (admin only)')
      else setError(err?.response?.data?.error || 'Failed to load')
    })
  },[])

  if (error) return <div className="text-red-600">{error}</div>
  if (!data) return <div>Loading...</div>

  return (
    <div>
      <h2 className="text-2xl font-medium">Admin Dashboard</h2>
      <div className="grid grid-cols-3 gap-4 mt-4">
        <div className="p-4 border rounded">Users<br/><strong className="text-xl">{data.total_users}</strong></div>
        <div className="p-4 border rounded">Assessments<br/><strong className="text-xl">{data.total_assessments}</strong></div>
        <div className="p-4 border rounded">Completed<br/><strong className="text-xl">{data.completed_assessments}</strong></div>
      </div>

      <div className="mt-6">
        <h3 className="font-medium">Risk breakdown</h3>
        <div className="mt-2">
          {data.risk_breakdown && Object.keys(data.risk_breakdown).length>0 ? (
            <table className="w-full text-left border-collapse">
              <thead><tr><th>Class</th><th>Count</th></tr></thead>
              <tbody>
                {Object.entries(data.risk_breakdown as Record<string, number>).map(([k,v]) => (
                  <tr key={k} className="border-t"><td className="py-2">{k}</td><td className="py-2">{v}</td></tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div>No completed assessments yet.</div>
          )}
        </div>
      </div>
    </div>
  )
}
