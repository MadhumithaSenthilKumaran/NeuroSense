import React, { useEffect, useState } from 'react'
import api from '../api'
import { useParams, useNavigate } from 'react-router-dom'

export default function Lifestyle(){
  const { id } = useParams<{id:string}>()
  const [questions, setQuestions] = useState<any[]>([])
  const [answers, setAnswers] = useState<any>({})
  const navigate = useNavigate()

  useEffect(()=>{
    api.get('/lifestyle/questions').then(r=>setQuestions(r.data.questions)).catch(()=>{})
  },[])

  const submit = async ()=>{
    try{
      await api.post(`/lifestyle/submit/${id}`, { answers })
      navigate(`/assessment/cognitive/${id}`)
    }catch(err:any){
      alert(err?.response?.data?.error || 'Failed')
    }
  }

  return (
    <div>
      <h2>Lifestyle Questionnaire</h2>
      {questions.map(q=> (
        <div key={q.id} style={{marginBottom:10}}>
          <label>{q.text}</label>
          {q.type==='radio' ? (
            q.options.map((o:any)=>(<div key={o}><label><input type="radio" name={q.id} onChange={()=>setAnswers({...answers,[q.id]:o})} /> {o}</label></div>))
          ) : (
            <input value={answers[q.id] || ''} onChange={e=>setAnswers({...answers,[q.id]:e.target.value})} />
          )}
        </div>
      ))}
      <button onClick={submit}>Submit</button>
    </div>
  )
}
