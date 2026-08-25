import React from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function NavBar() {
  const { token, logout } = useAuth()
  return (
    <nav className="flex items-center justify-between px-4 py-3 bg-white shadow-sm">
      <div className="space-x-4">
        <Link to="/" className="font-semibold">NeuroSense</Link>
        <Link to="/knowledge" className="text-sm text-gray-600">About</Link>
        <Link to="/health" className="text-sm text-gray-600">Health</Link>
      </div>
      <div>
        {token ? (
          <div className="space-x-3">
            <Link to="/dashboard" className="text-sm">Dashboard</Link>
            <Link to="/admin/dashboard" className="text-sm">Admin</Link>
            <a href="#" onClick={(e)=>{e.preventDefault(); logout();}} className="text-sm text-red-600">Logout</a>
          </div>
        ) : (
          <div className="space-x-3">
            <Link to="/login" className="text-sm">Login</Link>
            <Link to="/register" className="text-sm">Register</Link>
          </div>
        )}
      </div>
    </nav>
  )
}
