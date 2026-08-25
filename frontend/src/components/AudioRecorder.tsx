import React, { useState, useRef } from 'react'

type Props = {
  onRecorded: (blob: Blob, sampleRate: number) => void
}

export default function AudioRecorder({ onRecorded }: Props) {
  const [recording, setRecording] = useState(false)
  const mediaRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)

  async function start() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      const mr = new MediaRecorder(stream)
      mediaRef.current = mr
      chunksRef.current = []
      mr.ondataavailable = (e) => { if (e.data && e.data.size) chunksRef.current.push(e.data) }
      mr.start()
      setRecording(true)
    } catch (e) {
      console.error('Microphone access denied', e)
      alert('Microphone access is required for recording')
    }
  }

  async function stop() {
    const mr = mediaRef.current
    if (!mr) return
    return new Promise<void>((resolve) => {
      mr.onstop = async () => {
        try {
          const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
          // sampleRate via AudioContext
          let sampleRate = 48000
          try {
            const ac = new (window.AudioContext || (window as any).webkitAudioContext)()
            sampleRate = ac.sampleRate
            ac.close()
          } catch (e) {
            // keep default
          }
          onRecorded(blob, sampleRate)
        } catch (err) {
          console.error(err)
        } finally {
          // cleanup
          if (streamRef.current) {
            streamRef.current.getTracks().forEach(t => t.stop())
            streamRef.current = null
          }
          mediaRef.current = null
          chunksRef.current = []
          setRecording(false)
          resolve()
        }
      }
      mr.stop()
    })
  }

  return (
    <div className="flex items-center gap-3">
      {!recording ? (
        <button className="px-4 py-2 bg-indigo-600 text-white rounded" onClick={start}>Start Recording</button>
      ) : (
        <button className="px-4 py-2 bg-red-600 text-white rounded" onClick={stop}>Stop</button>
      )}
      <span className="text-sm text-gray-600">{recording ? 'Recording…' : 'Idle'}</span>
    </div>
  )
}
