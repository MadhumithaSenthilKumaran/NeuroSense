import React, { useEffect, useState } from 'react'
import api from '../api'
import { useParams, useNavigate } from 'react-router-dom'

export default function Lifestyle(){
  const { id } = useParams<{id:string}>()
  const [questions, setQuestions] = useState<any[]>([])
  const [answers, setAnswers] = useState<any>({})
  const [concernAnswers, setConcernAnswers] = useState<any>({})
  const [concernQuestions, setConcernQuestions] = useState<any[]>([])
  const [concernScale, setConcernScale] = useState<string[]>([])
  const [stage, setStage] = useState<'lifestyle' | 'concerns'>('lifestyle')
  const navigate = useNavigate()

  useEffect(()=>{
    api.get('/lifestyle/questions').then(r=>setQuestions(r.data.questions)).catch(()=>{})
    api.get('/lifestyle/concern-questions').then(r=>{
      setConcernQuestions(r.data.questions)
      setConcernScale(r.data.scale)
    }).catch(()=>{})
  },[])

  const handleLifestyleNext = () => {
    setStage('concerns')
  }

  const submit = async ()=>{
    try{
      await api.post(`/lifestyle/submit/${id}`, { answers, concern_answers: concernAnswers })
      navigate(`/assessment/cognitive/${id}`)
    }catch(err:any){
      alert(err?.response?.data?.error || 'Failed')
    }
  }

  const getSliderLabel = (question: any, value: any) => {
    if (!value && value !== 0) return ''
    if (question.id === 'exercise_days') return `${value} days/week`
    if (question.id === 'sleep_hours') return `${value} hours/night`
    if (question.id === 'stress_level') return `${value}/10`
    if (question.id === 'age') return `${value} years`
    if (question.id === 'education_years') return `${value} years`
    if (question.id === 'bmi') return `${value}`
    if (question.id === 'medication_count') return `${value} medications`
    return value
  }

  return (
    <div style={{ padding: '20px', maxWidth: '900px', margin: '0 auto' }}>
      <h2>Lifestyle Assessment</h2>
      
      {stage === 'lifestyle' && (
        <div>
          <h3>Lifestyle Questionnaire</h3>
          <p style={{ color: '#666', marginBottom: '20px' }}>Please answer the following questions about your lifestyle and health.</p>
          
          {questions.map((q, idx) => (
            <div key={q.id} style={{
              marginBottom: '25px',
              padding: '15px',
              backgroundColor: '#f9f9f9',
              borderRadius: '8px',
              borderLeft: '4px solid #007bff'
            }}>
              <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '10px' }}>
                {idx + 1}. {q.text}
              </label>
              
              {q.type === 'radio' ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '8px' }}>
                  {q.options.map((option: string) => (
                    <label key={option} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <input 
                        type="radio" 
                        name={q.id} 
                        value={option}
                        checked={answers[q.id] === option}
                        onChange={() => setAnswers({...answers, [q.id]: option})} 
                        style={{ cursor: 'pointer' }}
                      />
                      <span>{option}</span>
                    </label>
                  ))}
                </div>
              ) : q.type === 'slider' ? (
                <div>
                  <input 
                    type="range"
                    min={q.min}
                    max={q.max}
                    value={answers[q.id] || q.min}
                    onChange={(e) => setAnswers({...answers, [q.id]: parseFloat(e.target.value)})}
                    style={{
                      width: '100%',
                      height: '6px',
                      cursor: 'pointer',
                      accentColor: '#007bff'
                    }}
                  />
                  <div style={{ 
                    marginTop: '8px', 
                    display: 'flex', 
                    justifyContent: 'space-between',
                    fontSize: '12px',
                    color: '#666'
                  }}>
                    <span>{q.min}</span>
                    <span style={{ fontWeight: 'bold', color: '#007bff' }}>
                      {getSliderLabel(q, answers[q.id])}
                    </span>
                    <span>{q.max}</span>
                  </div>
                </div>
              ) : q.type === 'number' ? (
                <input 
                  type="number"
                  value={answers[q.id] || ''}
                  onChange={(e) => setAnswers({...answers, [q.id]: e.target.value})}
                  placeholder={`Enter ${q.text.toLowerCase()}`}
                  style={{
                    padding: '10px',
                    borderRadius: '4px',
                    border: '1px solid #ddd',
                    width: '200px',
                    fontSize: '14px'
                  }}
                />
              ) : (
                <input 
                  type="text"
                  value={answers[q.id] || ''}
                  onChange={(e) => setAnswers({...answers, [q.id]: e.target.value})}
                  placeholder={`Enter ${q.text.toLowerCase()}`}
                  style={{
                    padding: '10px',
                    borderRadius: '4px',
                    border: '1px solid #ddd',
                    width: '100%',
                    fontSize: '14px'
                  }}
                />
              )}
            </div>
          ))}
          
          <button 
            onClick={handleLifestyleNext}
            style={{
              padding: '12px 30px',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '16px',
              marginTop: '20px'
            }}
          >
            Continue to Concerns Assessment
          </button>
        </div>
      )}

      {stage === 'concerns' && (
        <div>
          <h3>Self-Reported Cognitive Concerns</h3>
          <p style={{ color: '#666', marginBottom: '20px' }}>Rate how often you experience each of the following:</p>
          
          <div style={{ overflowX: 'auto', marginBottom: '20px' }}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: `250px repeat(${concernScale.length}, 85px)`,
              gap: '0',
              minWidth: '100%'
            }}>
              {/* Header Row */}
              <div style={{
                padding: '12px',
                backgroundColor: '#007bff',
                color: 'white',
                fontWeight: 'bold',
                borderBottom: '2px solid #0d47a1',
                minHeight: '50px',
                display: 'flex',
                alignItems: 'center'
              }}>
                Concern
              </div>
              {concernScale.map((scale) => (
                <div key={`header-${scale}`} style={{
                  padding: '12px',
                  backgroundColor: '#007bff',
                  color: 'white',
                  fontWeight: 'bold',
                  textAlign: 'center',
                  fontSize: '12px',
                  borderBottom: '2px solid #0d47a1',
                  minHeight: '50px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  {scale}
                </div>
              ))}

              {/* Question Rows */}
              {concernQuestions.map((q, qIdx) => (
                <React.Fragment key={q.id}>
                  <div style={{
                    padding: '12px',
                    backgroundColor: qIdx % 2 === 0 ? '#f9f9f9' : '#fff',
                    borderBottom: '1px solid #eee',
                    fontWeight: '500',
                    fontSize: '13px',
                    display: 'flex',
                    alignItems: 'center'
                  }}>
                    {qIdx + 1}. {q.text}
                  </div>
                  {concernScale.map((scale) => (
                    <div key={`${q.id}-${scale}`} style={{
                      padding: '12px',
                      backgroundColor: qIdx % 2 === 0 ? '#f9f9f9' : '#fff',
                      borderBottom: '1px solid #eee',
                      display: 'flex',
                      justifyContent: 'center',
                      alignItems: 'center',
                      minHeight: '50px'
                    }}>
                      <label style={{
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        cursor: 'pointer',
                        width: '100%'
                      }}>
                        <input 
                          type="radio"
                          name={q.id}
                          value={scale}
                          checked={concernAnswers[q.id] === scale}
                          onChange={() => setConcernAnswers({...concernAnswers, [q.id]: scale})}
                          style={{ cursor: 'pointer', width: '18px', height: '18px' }}
                        />
                      </label>
                    </div>
                  ))}
                </React.Fragment>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
            <button 
              onClick={() => setStage('lifestyle')}
              style={{
                padding: '12px 30px',
                backgroundColor: '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '16px'
              }}
            >
              Back
            </button>
            <button 
              onClick={submit}
              style={{
                padding: '12px 30px',
                backgroundColor: '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '16px'
              }}
            >
              Submit Assessment
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
