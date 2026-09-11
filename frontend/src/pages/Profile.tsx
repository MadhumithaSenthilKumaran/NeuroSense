import React, { useEffect, useState } from 'react'
import api from '../api'
import { useAuth } from '../context/AuthContext'

export default function Profile() {
  const { user, refreshUser } = useAuth()
  const [form, setForm] = useState<any>({
    name: '',
    age: '',
    gender: '',
    phone: '',
    education: '',
    occupation: '',
    guardian_email: '',
    guardian_phone: '',
    consent_share: false,
  })
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!user) return
    setForm({
      name: user.name || '',
      age: user.age ?? '',
      gender: user.gender || '',
      phone: user.phone || '',
      education: user.education || '',
      occupation: user.occupation || '',
      guardian_email: user.guardian_email || '',
      guardian_phone: user.guardian_phone || '',
      consent_share: !!user.consent_share,
    })
  }, [user])

  const save = async () => {
    setSaving(true)
    setMessage('')
    try {
      await api.put('/auth/me', form)
      await refreshUser()
      setMessage('Profile saved successfully.')
    } catch (err: any) {
      setMessage(err?.response?.data?.error || 'Unable to save profile.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="profile-page">
      <div className="page-intro">
        <div className="eyebrow">Your profile</div>
        <h1>Personal details</h1>
        <p>Keep your contact information current so your assessment updates and guardian alerts can reach the right people.</p>
      </div>

      <div className="profile-panel">
        <div className="profile-grid">
          <div className="form-field"><label>Name</label><input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></div>
          <div className="form-field"><label>Email</label><input value={user?.email || ''} readOnly /></div>
          <div className="form-field"><label>Age</label><input type="number" value={form.age} onChange={e => setForm({ ...form, age: e.target.value })} /></div>
          <div className="form-field"><label htmlFor="profile-gender">Gender</label><select id="profile-gender" value={form.gender} onChange={e => setForm({ ...form, gender: e.target.value })}><option value="">Select gender</option><option value="Female">Female</option><option value="Male">Male</option><option value="Non-binary">Non-binary</option><option value="Prefer not to say">Prefer not to say</option></select></div>
          <div className="form-field"><label>Phone number</label><input value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} /></div>
          <div className="form-field"><label>Education</label><input value={form.education} onChange={e => setForm({ ...form, education: e.target.value })} /></div>
          <div className="form-field"><label>Occupation</label><input value={form.occupation} onChange={e => setForm({ ...form, occupation: e.target.value })} /></div>
          <div className="form-field"><label>Guardian email</label><input type="email" value={form.guardian_email} onChange={e => setForm({ ...form, guardian_email: e.target.value })} /></div>
          <div className="form-field"><label>Guardian phone</label><input value={form.guardian_phone} onChange={e => setForm({ ...form, guardian_phone: e.target.value })} /></div>
        </div>

        <label className="consent-box">
          <input type="checkbox" checked={form.consent_share} onChange={e => setForm({ ...form, consent_share: e.target.checked })} />
          I consent to share my assessment reports with my guardian by email or SMS.
        </label>

        <button className="form-submit" onClick={save} disabled={saving}>{saving ? 'Saving...' : 'Save profile'}</button>
        {message && <div className="form-message">{message}</div>}
      </div>
    </div>
  )
}
