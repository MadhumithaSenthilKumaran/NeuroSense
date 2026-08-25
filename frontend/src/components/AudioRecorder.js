import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useRef } from 'react';
export default function AudioRecorder({ onRecorded }) {
    const [recording, setRecording] = useState(false);
    const mediaRef = useRef(null);
    const chunksRef = useRef([]);
    const streamRef = useRef(null);
    async function start() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            streamRef.current = stream;
            const mr = new MediaRecorder(stream);
            mediaRef.current = mr;
            chunksRef.current = [];
            mr.ondataavailable = (e) => { if (e.data && e.data.size)
                chunksRef.current.push(e.data); };
            mr.start();
            setRecording(true);
        }
        catch (e) {
            console.error('Microphone access denied', e);
            alert('Microphone access is required for recording');
        }
    }
    async function stop() {
        const mr = mediaRef.current;
        if (!mr)
            return;
        return new Promise((resolve) => {
            mr.onstop = async () => {
                try {
                    const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
                    // sampleRate via AudioContext
                    let sampleRate = 48000;
                    try {
                        const ac = new (window.AudioContext || window.webkitAudioContext)();
                        sampleRate = ac.sampleRate;
                        ac.close();
                    }
                    catch (e) {
                        // keep default
                    }
                    onRecorded(blob, sampleRate);
                }
                catch (err) {
                    console.error(err);
                }
                finally {
                    // cleanup
                    if (streamRef.current) {
                        streamRef.current.getTracks().forEach(t => t.stop());
                        streamRef.current = null;
                    }
                    mediaRef.current = null;
                    chunksRef.current = [];
                    setRecording(false);
                    resolve();
                }
            };
            mr.stop();
        });
    }
    return (_jsxs("div", { className: "flex items-center gap-3", children: [!recording ? (_jsx("button", { className: "px-4 py-2 bg-indigo-600 text-white rounded", onClick: start, children: "Start Recording" })) : (_jsx("button", { className: "px-4 py-2 bg-red-600 text-white rounded", onClick: stop, children: "Stop" })), _jsx("span", { className: "text-sm text-gray-600", children: recording ? 'Recording…' : 'Idle' })] }));
}
