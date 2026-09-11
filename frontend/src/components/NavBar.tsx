import React from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function NavBar() {
  const { token, logout } = useAuth()
  return (
    <nav className="site-nav">
      <div className="nav-links">
        <Link to="/" className="brand-mark">NeuroSense</Link>
        <Link to="/knowledge" className="nav-link">About</Link>
      </div>
      <div className="nav-actions">
        {token ? (
          <>
            <Link to="/dashboard" className="nav-link nav-link-strong">Dashboard</Link>
            <Link to="/profile" className="nav-link">Profile</Link>
            <Link to="/reports" className="nav-link">Reports</Link>
            <button onClick={logout} className="nav-logout">Logout</button>
          </>
        ) : (
          <>
            <Link to="/login" className="nav-link">Login</Link>
            <Link to="/register" className="nav-link nav-link-strong">Register</Link>
          </>
        )}
      </div>
    </nav>
  )
}
