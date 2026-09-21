import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function NavBar() {
  const { token, logout } = useAuth()
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem('ns_theme') === 'dark')

  useEffect(() => {
    document.documentElement.dataset.theme = darkMode ? 'dark' : 'light'
    localStorage.setItem('ns_theme', darkMode ? 'dark' : 'light')
  }, [darkMode])

  return (
    <nav className="site-nav">
      <div className="nav-links">
        <Link to="/" className="brand-mark">NeuroSense</Link>
        <Link to="/knowledge" className="nav-link">About</Link>
      </div>
      <div className="nav-actions">
        <button
          type="button"
          className="theme-toggle"
          onClick={() => setDarkMode(value => !value)}
          aria-label={darkMode ? 'Use light theme' : 'Use dark theme'}
          title={darkMode ? 'Use light theme' : 'Use dark theme'}
        >
          {darkMode ? 'Light' : 'Dark'}
        </button>
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
