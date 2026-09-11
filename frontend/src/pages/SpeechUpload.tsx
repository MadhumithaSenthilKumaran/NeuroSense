import React, { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api from '../api'
import AudioRecorder from '../components/AudioRecorder'
import Waveform from '../components/Waveform'

type SpeechTask = { id: string; title: string; prompt: string; duration_hint_s?: number }
type SpeechFeature = { _id: string; transcript?: string | null; duration_s: number; pitch_hz?: number | null; pause_duration_s: number; speech_rate_wpm?: number | null; content_match?: { score?: number | null } }

export default function SpeechUpload() {
  const { id } = useParams<{ id: string }>()
  const [task, setTask] = useState('reading')
  const [tasks, setTasks] = useState<SpeechTask[]>([])
  const [file, setFile] = useState<File | null>(null)
  const [localPoints, setLocalPoints] = useState<number[] | null>(null)
  const [serverPoints, setServerPoints] = useState<number[] | null>(null)
  const [result, setResult] = useState<SpeechFeature | null>(null)
  const [status, setStatus] = useState('Ready for a recording')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api.get('/speech/tasks').then(({ data }) => setTasks(data.tasks)).catch(() => setTasks([
      { id: 'reading', title: 'Reading statement', prompt: 'Please read the paragraph aloud at a comfortable pace: Yesterday I went to the market with my family. We bought fruits, vegetables, and milk.' },
    ]))
    if (id) api.get(`/speech/session/${id}`).then(({ data }) => {
      if (!data.speech_set?.paragraph) return
      setTasks(current => current.map(item => item.id === 'reading' ? { ...item, prompt: data.speech_set.paragraph } : item))
    }).catch(() => {})
  }, [id])

  const selectedTask = tasks.find(item => item.id === task)

  const handleFileChange = (selected: File | null) => {
    setFile(selected)
    setServerPoints(null)
    if (!selected) { setLocalPoints(null); return }
    const reader = new FileReader()
    reader.onload = async () => {
      try {
        const context = new (window.AudioContext || (window as any).webkitAudioContext)()
        const buffer = await context.decodeAudioData(reader.result as ArrayBuffer)
        setLocalPoints(downsampleForPreview(buffer.getChannelData(0)))
        context.close()
      } catch { setLocalPoints(null) }
    }
    reader.readAsArrayBuffer(selected)
  }

  const upload = async (blob?: Blob) => {
    const toUpload = blob || file
    if (!toUpload) { setStatus('Choose an audio file or record your response first'); return }
    const form = new FormData()
    setBusy(true)
    setStatus('Processing audio and extracting speech features...')
    setResult(null)
    setServerPoints(null)
    try {
      const wav = await audioToWav(toUpload)
      form.append('audio', wav, 'recording.wav')
      const response = await api.post(`/speech/upload/${id}/${task}`, form, { headers: { 'Content-Type': 'multipart/form-data' } })
      const feature = response.data.speech_feature as SpeechFeature
      setResult(feature)
      setStatus('Analysis complete')
      const waveform = await api.get(`/speech/waveform/${feature._id}`)
      setServerPoints(waveform.data.points)
    } catch (error: any) {
      setStatus(error?.response?.data?.error || 'The audio could not be processed. Please try again.')
    } finally { setBusy(false) }
  }

  return <div className="speech-page">
    <header className="speech-header"><div><p className="eyebrow">VOICE ASSESSMENT / STEP 04</p><h1>Speech & language</h1><p className="lede">Complete one prompt in your own voice. NeuroSense will measure acoustic patterns and prepare them for your assessment.</p></div><div className="step-mark">04<span>/04</span></div></header>
    <div className="speech-grid">
      <section className="speech-panel prompt-panel"><div className="panel-kicker">01 / Choose a prompt</div><div className="task-list">{tasks.map(item => <button key={item.id} className={`task-option ${task === item.id ? 'selected' : ''}`} onClick={() => { setTask(item.id); setResult(null); setStatus('Ready for a recording') }}><span>{item.title}</span><b>{task === item.id ? 'Selected' : 'Select'}</b></button>)}</div><div className="prompt-copy"><span className="quote-mark">&quot;</span><p>{selectedTask?.prompt || 'Loading prompt...'}</p></div>{selectedTask?.duration_hint_s && <small>Recommended response: about {selectedTask.duration_hint_s} seconds</small>}</section>
      <section className="speech-panel capture-panel"><div className="panel-kicker">02 / Capture response</div><div className="capture-actions"><label className="dropzone"><input type="file" accept="audio/*" onChange={e => handleFileChange(e.target.files?.[0] || null)} /><strong>{file ? file.name : 'Choose an audio file'}</strong><span>WAV, MP3, M4A, WEBM or OGG - up to 25 MB</span></label><div className="or-divider">or record directly</div><AudioRecorder onRecorded={blob => { setFile(new File([blob], 'recording.webm', { type: 'audio/webm' })); upload(blob) }} /></div>{(localPoints || serverPoints) && <div className="waveform-wrap"><div className="waveform-label"><span>{serverPoints ? 'Processed waveform' : 'Local preview'}</span><span>{result ? `${result.duration_s}s` : 'Ready'}</span></div><Waveform points={serverPoints || localPoints || []} /></div>}<button className="primary-action" disabled={busy || !file} onClick={() => upload()}>{busy ? 'Processing...' : 'Upload and analyze'}<span>-&gt;</span></button><p className={`status-line ${status === 'Analysis complete' ? 'success' : ''}`}><i />{status}</p></section>
    </div>
    {result && <section className="results-panel"><div><div className="panel-kicker">03 / Results ready</div><h2>Speech signal captured</h2><p className="result-note">Your acoustic profile has been added to this assessment.</p></div><div className="metric-row"><Metric label="Duration" value={`${result.duration_s}s`} /><Metric label="Pitch" value={result.pitch_hz ? `${result.pitch_hz} Hz` : 'Not detected'} /><Metric label="Pause time" value={`${result.pause_duration_s}s`} /><Metric label="Speech rate" value={result.speech_rate_wpm ? `${result.speech_rate_wpm} WPM` : 'Transcript unavailable'} /><Metric label="Prompt match" value={result.content_match?.score != null ? `${result.content_match.score}%` : 'Unavailable'} /></div><div className="transcript"><span>Transcript</span><p>{result.transcript || 'Transcription is unavailable in lightweight mode. Acoustic features were extracted successfully.'}</p></div><Link className="continue-action" to={`/assessment/finalize/${id}`}>Continue to final review <span>-&gt;</span></Link></section>}
  </div>
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="metric"><span>{label}</span><strong>{value}</strong></div> }
function downsampleForPreview(data: Float32Array, target = 400) { const step = Math.max(1, Math.floor(data.length / target)); const points: number[] = []; for (let index = 0; index < data.length; index += step) points.push(data[index]); return points }

async function audioToWav(source: Blob) {
  const context = new (window.AudioContext || (window as any).webkitAudioContext)()
  try {
    const buffer = await context.decodeAudioData(await source.arrayBuffer())
    return new Blob([encodeWav(buffer)], { type: 'audio/wav' })
  } finally {
    await context.close()
  }
}

function encodeWav(buffer: AudioBuffer) {
  const channelCount = Math.min(buffer.numberOfChannels, 2)
  const frameCount = buffer.length
  const bytesPerSample = 2
  const dataSize = frameCount * channelCount * bytesPerSample
  const output = new ArrayBuffer(44 + dataSize)
  const view = new DataView(output)
  const writeText = (offset: number, text: string) => [...text].forEach((character, index) => view.setUint8(offset + index, character.charCodeAt(0)))
  writeText(0, 'RIFF'); view.setUint32(4, 36 + dataSize, true); writeText(8, 'WAVE')
  writeText(12, 'fmt '); view.setUint32(16, 16, true); view.setUint16(20, 1, true)
  view.setUint16(22, channelCount, true); view.setUint32(24, buffer.sampleRate, true)
  view.setUint32(28, buffer.sampleRate * channelCount * bytesPerSample, true)
  view.setUint16(32, channelCount * bytesPerSample, true); view.setUint16(34, 16, true)
  writeText(36, 'data'); view.setUint32(40, dataSize, true)
  const channels = Array.from({ length: channelCount }, (_, index) => buffer.getChannelData(index))
  let offset = 44
  for (let frame = 0; frame < frameCount; frame++) {
    for (let channel = 0; channel < channelCount; channel++) {
      const sample = Math.max(-1, Math.min(1, channels[channel][frame]))
      view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true)
      offset += 2
    }
  }
  return output
}
