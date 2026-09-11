import React, { useState } from 'react'
import api from '../api'
import { useNavigate } from 'react-router-dom'

const emptyForm = {
  name: '',
  email: '',
  password: '',
  age: '',
  gender: '',
  phone: '',
  education: '',
  occupation: '',
  guardian_email: '',
  guardian_phone: '',
  consent_share: false,
}

export default function Register(){
  const [form,setForm]=useState(emptyForm)
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
    <div className="auth-layout">
      <div className="auth-copy"><div className="eyebrow">Begin your journey</div><h1>Small steps, <span className="auth-accent">better insight.</span></h1><p>Create a private NeuroSense account and build a personal picture of the signals that shape your wellbeing.</p></div>
      <div className="auth-card auth-card-wide"><h2>Create account</h2><form onSubmit={submit} className="auth-form-grid">
        <div className="form-field"><label>Name</label><input value={form.name} onChange={e=>setForm({...form,name:e.target.value})} /></div>
        <div className="form-field"><label>Email</label><input type="email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})} /></div>
        <div className="form-field"><label>Password</label><input type="password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})} /></div>
        <div className="form-field"><label>Age</label><input type="number" value={form.age} onChange={e=>setForm({...form,age:e.target.value})} /></div>
        <div className="form-field"><label htmlFor="register-gender">Gender</label><select id="register-gender" value={form.gender} onChange={e=>setForm({...form,gender:e.target.value})}><option value="">Select gender</option><option value="Female">Female</option><option value="Male">Male</option><option value="Non-binary">Non-binary</option><option value="Prefer not to say">Prefer not to say</option></select></div>
        <div className="form-field"><label>Phone number</label><input value={form.phone} onChange={e=>setForm({...form,phone:e.target.value})} /></div>
        <div className="form-field"><label>Education</label><input value={form.education} onChange={e=>setForm({...form,education:e.target.value})} /></div>
        <div className="form-field"><label>Occupation</label><input value={form.occupation} onChange={e=>setForm({...form,occupation:e.target.value})} /></div>
        <div className="form-field"><label>Guardian email</label><input type="email" value={form.guardian_email} onChange={e=>setForm({...form,guardian_email:e.target.value})} /></div>
        <div className="form-field"><label>Guardian phone</label><input value={form.guardian_phone} onChange={e=>setForm({...form,guardian_phone:e.target.value})} /></div>
        <label className="consent-box consent-box-inline">
          <input type="checkbox" checked={form.consent_share} onChange={e=>setForm({...form,consent_share:e.target.checked})} />
          I consent to share assessment updates with my guardian.
        </label>
        {error && <div className="form-error">{error}</div>}
        <button className="form-submit" type="submit">Register</button>
      </form></div>
    </div>
  )
}
