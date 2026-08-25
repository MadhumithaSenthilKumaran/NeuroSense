import React from 'react'
import api from '../api'
import { useNavigate } from 'react-router-dom'

export default function StartAssessment(){
  const navigate = useNavigate()
  const start = async ()=>{
    try{
      const res = await api.post('/assessment/start')
      const id = res.data.assessment._id
      navigate(`/assessment/lifestyle/${id}`)
    }catch(err:any){
      alert(err?.response?.data?.error || 'Failed to start')
    }
  }
  return (
    <div>
      <h2>Start Assessment</h2>
      <p>This will create a new assessment and take you through the modules.</p>
      <button onClick={start}>Start</button>
    </div>
  )
}
