import React, { useEffect, useState } from 'react'
import api from '../api'
import { useParams, useNavigate } from 'react-router-dom'
import { MEMORY_WORDS, ATTENTION_SEQUENCE } from '../utils/constants'

export default function Cognitive(){
  const { id } = useParams<{id:string}>()
  const [stage, setStage] = useState<'memory-display' | 'memory-test' | 'reaction' | 'complete'>('memory-display')
  const [timeLeft, setTimeLeft] = useState(10)
  const [recalled, setRecalled] = useState<string[]>([])
  const [currentRecall, setCurrentRecall] = useState('')
  const [reaction, setReaction] = useState<string>('')
  const navigate = useNavigate()

  // Timer for memory display
  useEffect(() => {
    if (stage === 'memory-display' && timeLeft > 0) {
      const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000)
      return () => clearTimeout(timer)
    } else if (stage === 'memory-display' && timeLeft === 0) {
      setStage('memory-test')
    }
  }, [timeLeft, stage])

  const handleAddRecalledWord = () => {
    if (currentRecall.trim()) {
      setRecalled([...recalled, currentRecall.trim()])
      setCurrentRecall('')
    }
  }

  const handleRemoveWord = (index: number) => {
    setRecalled(recalled.filter((_, i) => i !== index))
  }

  const handleMemoryTestComplete = () => {
    setStage('reaction')
  }

  const submit = async ()=>{
    const payload = {
      recalled_words: recalled,
      reaction_times_ms: reaction.split(',').map(s=>parseFloat(s.trim())).filter(Boolean),
      attention_answer: '',
      visual_memory: {},
      pattern_recognition: [],
      orientation: {},
    }
    try{
      await api.post(`/cognitive/submit/${id}`, payload)
      navigate(`/assessment/speech/${id}`)
    }catch(err:any){
      alert(err?.response?.data?.error || 'Failed')
    }
  }

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h2>Cognitive Tests</h2>
      
      {stage === 'memory-display' && (
        <div style={{ 
          padding: '30px', 
          backgroundColor: '#f0f8ff', 
          borderRadius: '8px', 
          textAlign: 'center',
          marginBottom: '20px'
        }}>
          <h3>Memory Game - Read and Remember</h3>
          <p style={{ fontSize: '18px', color: '#666', marginBottom: '20px' }}>
            You have {timeLeft} seconds to memorize these words:
          </p>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '15px',
            marginBottom: '20px'
          }}>
            {MEMORY_WORDS.map((word, idx) => (
              <div 
                key={idx}
                style={{
                  padding: '20px',
                  backgroundColor: '#4CAF50',
                  color: 'white',
                  borderRadius: '8px',
                  fontSize: '20px',
                  fontWeight: 'bold',
                  textTransform: 'uppercase'
                }}
              >
                {word}
              </div>
            ))}
          </div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ff6b6b' }}>
            ⏱️ {timeLeft}s
          </div>
        </div>
      )}

      {stage === 'memory-test' && (
        <div style={{ 
          padding: '20px', 
          backgroundColor: '#fff3cd', 
          borderRadius: '8px',
          marginBottom: '20px'
        }}>
          <h3>Memory Test - Recall the Words</h3>
          <p>How many words do you remember? Type them one by one and click "Add Word".</p>
          
          <div style={{ marginBottom: '15px' }}>
            <input
              type="text"
              value={currentRecall}
              onChange={e => setCurrentRecall(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') handleAddRecalledWord()
              }}
              placeholder="Enter a word..."
              style={{
                width: '70%',
                padding: '10px',
                marginRight: '10px',
                borderRadius: '4px',
                border: '1px solid #ddd'
              }}
            />
            <button 
              onClick={handleAddRecalledWord}
              style={{
                padding: '10px 20px',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Add Word
            </button>
          </div>

          <div>
            <h4>Recalled Words ({recalled.length}/{MEMORY_WORDS.length}):</h4>
            <div style={{ 
              display: 'flex', 
              flexWrap: 'wrap', 
              gap: '8px',
              marginBottom: '15px'
            }}>
              {recalled.map((word, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '8px 12px',
                    backgroundColor: '#28a745',
                    color: 'white',
                    borderRadius: '20px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  {word}
                  <button
                    onClick={() => handleRemoveWord(idx)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'white',
                      cursor: 'pointer',
                      fontSize: '16px'
                    }}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>

          <button 
            onClick={handleMemoryTestComplete}
            style={{
              padding: '10px 20px',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
            Continue to Reaction Test
          </button>
        </div>
      )}

      {stage === 'reaction' && (
        <div style={{ marginBottom: '20px' }}>
          <h3>Reaction Time Test</h3>
          <p>Enter your reaction times (in milliseconds), comma-separated:</p>
          <input 
            value={reaction} 
            onChange={e=>setReaction(e.target.value)}
            placeholder="e.g., 250, 320, 280"
            style={{
              width: '100%',
              padding: '10px',
              marginBottom: '15px',
              borderRadius: '4px',
              border: '1px solid #ddd'
            }}
          />
          <button 
            onClick={submit}
            style={{
              padding: '10px 20px',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
            Submit Cognitive Tests
          </button>
        </div>
      )}
    </div>
  )
}
