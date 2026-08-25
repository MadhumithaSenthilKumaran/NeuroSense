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
    <div style={{maxWidth:480}}>
      <h2>Login</h2>
      <form onSubmit={submit}>
        <div><label>Email</label><input value={email} onChange={e=>setEmail(e.target.value)} /></div>
        <div><label>Password</label><input type="password" value={password} onChange={e=>setPassword(e.target.value)} /></div>
        {error && <div style={{color:'red'}}>{error}</div>}
        <button type="submit">Login</button>
      </form>
    </div>
  )
}
