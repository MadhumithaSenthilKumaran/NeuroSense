import React, { useState } from 'react'
import api from '../api'
import { useParams, useNavigate } from 'react-router-dom'
import { MEMORY_WORDS, ATTENTION_SEQUENCE } from '../utils/constants'

export default function Cognitive(){
  const { id } = useParams<{id:string}>()
  const [recalled, setRecalled] = useState<string>('')
  const [reaction, setReaction] = useState<string>('')
  const navigate = useNavigate()

  const submit = async ()=>{
    const payload = {
      recalled_words: recalled.split(',').map(s=>s.trim()),
      reaction_times_ms: reaction.split(',').map(s=>parseFloat(s.trim())).filter(Boolean),
      attention_answer: '',
      visual_memory: {},
      pattern_recognition: [],
      orientation: {},
    }
    try{
      await api.post(`/cognitive/submit/${id}`, payload)
      navigate(`/assessment/speech/${id}`)
    }catch(err:any){
      alert(err?.response?.data?.error || 'Failed')
    }
  }

  return (
    <div>
      <h2>Cognitive Tests</h2>
      <div>
        <h4>Memory words (read, then enter recalled words comma-separated)</h4>
        <div>{MEMORY_WORDS.join(', ')}</div>
        <input value={recalled} onChange={e=>setRecalled(e.target.value)} />
      </div>
      <div>
        <h4>Reaction times (ms) - comma separated</h4>
        <input value={reaction} onChange={e=>setReaction(e.target.value)} />
      </div>
      <button onClick={submit}>Submit cognitive</button>
    </div>
  )
}
