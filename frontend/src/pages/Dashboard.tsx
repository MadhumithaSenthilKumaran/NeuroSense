import React from 'react'
import { Link } from 'react-router-dom'

export default function Dashboard(){
  return (
    <div>
      <h2>Dashboard</h2>
      <ul>
        <li><Link to="/assessment/start">Start new assessment</Link></li>
        <li><Link to="/reports">Reports</Link></li>
        <li><Link to="/knowledge">Knowledge base</Link></li>
      </ul>
    </div>
  )
}
