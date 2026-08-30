import React from 'react'
import { Link } from 'react-router-dom'

export default function Dashboard(){
  return (
    <div>
      <header className="page-intro">
        <div className="eyebrow">Your wellbeing workspace</div>
        <h1>Good to see you.</h1>
        <p>Choose a next step to understand your cognitive health with more clarity and confidence.</p>
      </header>
      <div className="dashboard-grid">
        <Link to="/assessment/start" className="dashboard-card"><span className="card-icon">+</span><h3>New assessment</h3><p>Explore lifestyle, cognitive, and speech signals in one guided session.</p><span className="card-arrow">&#8594;</span></Link>
        <Link to="/reports" className="dashboard-card"><span className="card-icon">&#9678;</span><h3>Reports</h3><p>Review your previous assessment results and generated summaries.</p><span className="card-arrow">&#8594;</span></Link>
        <Link to="/knowledge" className="dashboard-card"><span className="card-icon">?</span><h3>Knowledge base</h3><p>Find accessible, evidence-informed information about brain health.</p><span className="card-arrow">&#8594;</span></Link>
      </div>
    </div>
  )
}
