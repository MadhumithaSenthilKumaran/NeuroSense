import React, { useState } from 'react'
import api from '../api'
import { useNavigate } from 'react-router-dom'

export default function StartAssessment(){
  const navigate = useNavigate()
  const [schedule, setSchedule] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const start = async ()=>{
    setLoading(true)
    try{
      const res = await api.post('/assessment/start')
      const id = res.data.assessment._id
      setSchedule(res.data.assessment.cycle_schedule || [])
      navigate(`/assessment/lifestyle/${id}`)
    }catch(err:any){
      alert(err?.response?.data?.error || 'Failed to start')
    } finally { setLoading(false) }
  }
  return (
    <div>
      <h2>Start Assessment</h2>
      <p>This will create the first session. The follow-up sessions are available only on their scheduled dates.</p>
      <button onClick={start} disabled={loading}>{loading ? 'Starting...' : 'Start Session 1'}</button>
      {schedule.length > 0 && <ul>{schedule.map(item => <li key={item.session_number}>Session {item.session_number}: {item.scheduled_for}</li>)}</ul>}
    </div>
  )
}
