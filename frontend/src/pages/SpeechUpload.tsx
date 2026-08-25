import React, { useState } from 'react'
import api from '../api'
import { useParams } from 'react-router-dom'

import AudioRecorder from '../components/AudioRecorder'
import Waveform from '../components/Waveform'

export default function SpeechUpload(){
  const { id } = useParams<{id:string}>()
  const [task, setTask] = useState('reading')
  const [file, setFile] = useState<File | null>(null)
  const [localPoints, setLocalPoints] = useState<number[] | null>(null)

  const handleFileChange = (f: File | null) => {
    setFile(f)
    // generate local waveform preview using WebAudio
    if (!f) { setLocalPoints(null); return }
    const r = new FileReader()
    r.onload = async () => {
      try{
        const ab = r.result as ArrayBuffer
        const ac = new (window.AudioContext || (window as any).webkitAudioContext)()
        const buf = await ac.decodeAudioData(ab)
        const data = buf.getChannelData(0)
        const points = downsampleForPreview(data, 400)
        setLocalPoints(points)
        ac.close()
      }catch(e){ console.warn('waveform preview failed', e) }
    }
    r.readAsArrayBuffer(f)
  }

  function downsampleForPreview(data: Float32Array, target = 400){
    const step = Math.max(1, Math.floor(data.length / target))
    const out:number[] = []
    for(let i=0;i<data.length;i+=step) out.push(data[i])
    return out
  }

  const upload = async (blob?: Blob)=>{
    const toUpload = blob || file
    if(!toUpload) return alert('Select or record a file')
    const fd = new FormData()
    fd.append('audio', toUpload, 'upload.webm')
    try{
      const res = await api.post(`/speech/upload/${id}/${task}`, fd, { headers: {'Content-Type':'multipart/form-data'} })
      alert('Uploaded')
    }catch(err:any){
      alert(err?.response?.data?.error || 'Upload failed')
    }
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-medium">Speech Upload</h2>
      <div>
        <label className="block mb-1">Task</label>
        <select value={task} onChange={e=>setTask(e.target.value)} className="border rounded px-2 py-1">
          <option value="reading">Reading</option>
          <option value="picture">Picture description</option>
          <option value="routine">Daily routine</option>
        </select>
      </div>

      <div>
        <label className="block mb-1">Choose file</label>
        <input type="file" accept="audio/*" onChange={e=>handleFileChange(e.target.files?.[0]||null)} />
      </div>

      {localPoints && (
        <div>
          <label className="block mb-1">Waveform preview</label>
          <Waveform points={localPoints} />
        </div>
      )}

      <div className="flex items-center gap-3">
        <AudioRecorder onRecorded={(blob)=>{ upload(blob) }} />
        <button className="px-4 py-2 bg-indigo-600 text-white rounded" onClick={()=>upload()}>Upload Selected</button>
      </div>
    </div>
  )
}
