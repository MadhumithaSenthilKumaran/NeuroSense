import React, { useEffect, useState } from 'react'
import api from '../api'

export default function Knowledge(){
  const [articles,setArticles]=useState<any[]>([])
  useEffect(()=>{
    api.get('/knowledge/articles').then(r=>setArticles(r.data.articles)).catch(()=>{})
  },[])
  return (
    <div>
      <h2>Knowledge base</h2>
      {articles.map(a=> (
        <div key={a.title} style={{border:'1px solid #eee', padding:10, marginBottom:8}}>
          <h3>{a.title}</h3>
          <div>{a.summary}</div>
          <div style={{fontSize:12, color:'#666'}}>Source: {a.source}</div>
        </div>
      ))}
    </div>
  )
}
