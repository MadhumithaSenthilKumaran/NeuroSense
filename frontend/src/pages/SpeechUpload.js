import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import api from '../api';
import { useParams } from 'react-router-dom';
import AudioRecorder from '../components/AudioRecorder';
import Waveform from '../components/Waveform';
export default function SpeechUpload() {
    const { id } = useParams();
    const [task, setTask] = useState('reading');
    const [file, setFile] = useState(null);
    const [localPoints, setLocalPoints] = useState(null);
    const handleFileChange = (f) => {
        setFile(f);
        // generate local waveform preview using WebAudio
        if (!f) {
            setLocalPoints(null);
            return;
        }
        const r = new FileReader();
        r.onload = async () => {
            try {
                const ab = r.result;
                const ac = new (window.AudioContext || window.webkitAudioContext)();
                const buf = await ac.decodeAudioData(ab);
                const data = buf.getChannelData(0);
                const points = downsampleForPreview(data, 400);
                setLocalPoints(points);
                ac.close();
            }
            catch (e) {
                console.warn('waveform preview failed', e);
            }
        };
        r.readAsArrayBuffer(f);
    };
    function downsampleForPreview(data, target = 400) {
        const step = Math.max(1, Math.floor(data.length / target));
        const out = [];
        for (let i = 0; i < data.length; i += step)
            out.push(data[i]);
        return out;
    }
    const upload = async (blob) => {
        const toUpload = blob || file;
        if (!toUpload)
            return alert('Select or record a file');
        const fd = new FormData();
        fd.append('audio', toUpload, 'upload.webm');
        try {
            const res = await api.post(`/speech/upload/${id}/${task}`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
            alert('Uploaded');
        }
        catch (err) {
            alert(err?.response?.data?.error || 'Upload failed');
        }
    };
    return (_jsxs("div", { className: "space-y-4", children: [_jsx("h2", { className: "text-2xl font-medium", children: "Speech Upload" }), _jsxs("div", { children: [_jsx("label", { className: "block mb-1", children: "Task" }), _jsxs("select", { value: task, onChange: e => setTask(e.target.value), className: "border rounded px-2 py-1", children: [_jsx("option", { value: "reading", children: "Reading" }), _jsx("option", { value: "picture", children: "Picture description" }), _jsx("option", { value: "routine", children: "Daily routine" })] })] }), _jsxs("div", { children: [_jsx("label", { className: "block mb-1", children: "Choose file" }), _jsx("input", { type: "file", accept: "audio/*", onChange: e => handleFileChange(e.target.files?.[0] || null) })] }), localPoints && (_jsxs("div", { children: [_jsx("label", { className: "block mb-1", children: "Waveform preview" }), _jsx(Waveform, { points: localPoints })] })), _jsxs("div", { className: "flex items-center gap-3", children: [_jsx(AudioRecorder, { onRecorded: (blob) => { upload(blob); } }), _jsx("button", { className: "px-4 py-2 bg-indigo-600 text-white rounded", onClick: () => upload(), children: "Upload Selected" })] })] }));
}
