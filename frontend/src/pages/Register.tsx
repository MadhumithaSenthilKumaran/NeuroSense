import React, { useState } from 'react'
import api from '../api'
import { useNavigate } from 'react-router-dom'

export default function Register(){
  const [form,setForm]=useState({name:'',email:'',password:''})
  const [error,setError]=useState('')
  const navigate = useNavigate()

  const submit = async (e:React.FormEvent)=>{
    e.preventDefault(); setError('')
    try{
      await api.post('/auth/register', form)
      navigate('/login')
    }catch(err:any){
      setError(err?.response?.data?.error || 'Registration failed')
    }
  }

  return (
    <div style={{maxWidth:480}}>
      <h2>Register</h2>
      <form onSubmit={submit}>
        <div><label>Name</label><input value={form.name} onChange={e=>setForm({...form,name:e.target.value})} /></div>
        <div><label>Email</label><input value={form.email} onChange={e=>setForm({...form,email:e.target.value})} /></div>
        <div><label>Password</label><input type="password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})} /></div>
        {error && <div style={{color:'red'}}>{error}</div>}
        <button type="submit">Register</button>
      </form>
    </div>
  )
}
