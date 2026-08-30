import React, { useState } from 'react'
import api from '../api'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login(){
  const [email,setEmail]=useState('')
  const [password,setPassword]=useState('')
  const [error,setError]=useState('')
  const navigate = useNavigate()
  const { login } = useAuth()

  const submit = async (e:React.FormEvent)=>{
    e.preventDefault()
    setError('')
    try{
      const res = await api.post('/auth/login', { email, password })
      const token = res.data.access_token
      login(token, res.data.user)
      navigate('/dashboard')
    }catch(err:any){
      setError(err?.response?.data?.error || 'Login failed')
    }
  }

  return (
    <div className="auth-layout">
      <div className="auth-copy"><div className="eyebrow">A clearer picture of you</div><h1>Understand your mind, <span className="auth-accent">gently.</span></h1><p>NeuroSense brings together meaningful signals to help you notice patterns and make informed next steps.</p></div>
      <div className="auth-card"><h2>Welcome back</h2><form onSubmit={submit}>
        <div className="form-field"><label>Email</label><input type="email" value={email} onChange={e=>setEmail(e.target.value)} /></div>
        <div className="form-field"><label>Password</label><input type="password" value={password} onChange={e=>setPassword(e.target.value)} /></div>
        {error && <div className="form-error">{error}</div>}
        <button className="form-submit" type="submit">Login</button>
      </form></div>
    </div>
  )
}
