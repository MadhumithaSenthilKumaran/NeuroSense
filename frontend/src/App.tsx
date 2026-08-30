import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import StartAssessment from './pages/StartAssessment'
import Lifestyle from './pages/Lifestyle'
import Cognitive from './pages/Cognitive'
import SpeechUpload from './pages/SpeechUpload'
import Finalize from './pages/Finalize'
import Reports from './pages/Reports'
import Knowledge from './pages/Knowledge'
import Health from './pages/Health'
import AdminDashboard from './pages/AdminDashboard'
import Profile from './pages/Profile'
import NavBar from './components/NavBar'
import { AuthProvider, useAuth } from './context/AuthContext'

function PrivateRoute({ children }: { children: JSX.Element }) {
  const { token } = useAuth()
  return token ? children : <Navigate to="/login" />
}

export default function App() {
  return (
    <AuthProvider>
      <NavBar />
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/health" element={<Health />} />
          <Route path="/knowledge" element={<Knowledge />} />

          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
          <Route path="/assessment/start" element={<PrivateRoute><StartAssessment /></PrivateRoute>} />
          <Route path="/assessment/lifestyle/:id" element={<PrivateRoute><Lifestyle /></PrivateRoute>} />
          <Route path="/assessment/cognitive/:id" element={<PrivateRoute><Cognitive /></PrivateRoute>} />
          <Route path="/assessment/speech/:id" element={<PrivateRoute><SpeechUpload /></PrivateRoute>} />
          <Route path="/assessment/finalize/:id" element={<PrivateRoute><Finalize /></PrivateRoute>} />

          <Route path="/reports" element={<PrivateRoute><Reports /></PrivateRoute>} />
          <Route path="/profile" element={<PrivateRoute><Profile /></PrivateRoute>} />
          <Route path="/admin/dashboard" element={<PrivateRoute><AdminDashboard /></PrivateRoute>} />
        </Routes>
      </main>
    </AuthProvider>
  )
}
