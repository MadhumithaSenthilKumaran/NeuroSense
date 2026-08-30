import React, { useEffect, useState } from 'react'
import api from '../api'

export default function Knowledge(){
  const [articles,setArticles]=useState<any[]>([])
  useEffect(()=>{
    api.get('/knowledge/articles').then(r=>setArticles(r.data.articles)).catch(()=>{})
  },[])

  const grouped = articles.reduce((acc: Record<string, any[]>, article: any) => {
    const topic = article.tags?.[0] || 'general'
    const existing = acc[topic] || []
    acc[topic] = [...existing, article]
    return acc
  }, {}) as Record<string, any[]>

  return (
    <div className="knowledge-page">
      <div className="page-intro">
        <div className="eyebrow">Evidence-based guidance</div>
        <h1>Brain health knowledge base</h1>
        <p>Clear, practical information about habits that may support memory, resilience, and healthy aging.</p>
      </div>

      <div className="knowledge-grid">
        {Object.entries(grouped).map(([topic, items]) => (
          <section key={topic} className="knowledge-card">
            <div className="knowledge-header">
              <span className="knowledge-tag">{topic.replace(/_/g, ' ')}</span>
            </div>
            {items.map((a: any) => (
              <article key={a.id || a.title || a.source} className="knowledge-article">
                <h3>{a.title || 'Brain health update'}</h3>
                <p>{a.summary || a.text}</p>
                <div className="knowledge-meta">
                  <span>{a.source}</span>
                  {a.tags?.slice(0,3).map((tag: string) => (
                    <span key={tag} className="mini-pill">{tag.replace(/_/g, ' ')}</span>
                  ))}
                </div>
              </article>
            ))}
          </section>
        ))}
      </div>
    </div>
  )
}
