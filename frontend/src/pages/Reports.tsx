import React, { useEffect, useState } from 'react'
import api from '../api'

export default function Reports(){
  const [history, setHistory] = useState<any[]>([])

  useEffect(()=>{
    api.get('/reports/history').then(r=>setHistory(r.data.history)).catch(()=>{})
  },[])

  const generate = async (assessment_id:string)=>{
    try{
      const res = await api.post(`/reports/generate/${assessment_id}`)
      alert('Report generation started; use download link from response or history')
    }catch(err:any){
      alert(err?.response?.data?.error || 'Failed')
    }
  }

  return (
    <div>
      <h2>Reports / History</h2>
      <div>
        {history.length===0 && <div>No completed assessments yet.</div>}
        {history.map((h,idx)=>(
          <div key={idx} style={{border:'1px solid #eee', padding:10, marginBottom:8}}>
            <div>Date: {h.date}</div>
            <div>Risk: {h.risk_class} ({h.risk_probability})</div>
          </div>
        ))}
      </div>
    </div>
  )
}
