import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import api from '../api';
import AudioRecorder from '../components/AudioRecorder';
import Waveform from '../components/Waveform';
export default function SpeechUpload() {
    const { id } = useParams();
    const [task, setTask] = useState('reading');
    const [tasks, setTasks] = useState([]);
    const [file, setFile] = useState(null);
    const [localPoints, setLocalPoints] = useState(null);
    const [serverPoints, setServerPoints] = useState(null);
    const [result, setResult] = useState(null);
    const [status, setStatus] = useState('Ready for a recording');
    const [busy, setBusy] = useState(false);
    useEffect(() => {
        api.get('/speech/tasks').then(({ data }) => setTasks(data.tasks)).catch(() => setTasks([
            { id: 'reading', title: 'Reading statement', prompt: 'Please read the paragraph aloud at a comfortable pace: Yesterday I went to the market with my family. We bought fruits, vegetables, and milk.' },
        ]));
        if (id)
            api.get(`/speech/session/${id}`).then(({ data }) => {
                if (!data.speech_set?.paragraph)
                    return;
                setTasks(current => current.map(item => item.id === 'reading' ? { ...item, prompt: data.speech_set.paragraph } : item));
            }).catch(() => { });
    }, [id]);
    const selectedTask = tasks.find(item => item.id === task);
    const handleFileChange = (selected) => {
        setFile(selected);
        setServerPoints(null);
        if (!selected) {
            setLocalPoints(null);
            return;
        }
        const reader = new FileReader();
        reader.onload = async () => {
            try {
                const context = new (window.AudioContext || window.webkitAudioContext)();
                const buffer = await context.decodeAudioData(reader.result);
                setLocalPoints(downsampleForPreview(buffer.getChannelData(0)));
                context.close();
            }
            catch {
                setLocalPoints(null);
            }
        };
        reader.readAsArrayBuffer(selected);
    };
    const upload = async (blob) => {
        const toUpload = blob || file;
        if (!toUpload) {
            setStatus('Choose an audio file or record your response first');
            return;
        }
        const form = new FormData();
        setBusy(true);
        setStatus('Processing audio and extracting speech features...');
        setResult(null);
        setServerPoints(null);
        try {
            const wav = await audioToWav(toUpload);
            form.append('audio', wav, 'recording.wav');
            const response = await api.post(`/speech/upload/${id}/${task}`, form, { headers: { 'Content-Type': 'multipart/form-data' } });
            const feature = response.data.speech_feature;
            setResult(feature);
            setStatus('Analysis complete');
            const waveform = await api.get(`/speech/waveform/${feature._id}`);
            setServerPoints(waveform.data.points);
        }
        catch (error) {
            setStatus(error?.response?.data?.error || 'The audio could not be processed. Please try again.');
        }
        finally {
            setBusy(false);
        }
    };
    return _jsxs("div", { className: "speech-page", children: [_jsxs("header", { className: "speech-header", children: [_jsxs("div", { children: [_jsx("p", { className: "eyebrow", children: "VOICE ASSESSMENT / STEP 04" }), _jsx("h1", { children: "Speech & language" }), _jsx("p", { className: "lede", children: "Complete one prompt in your own voice. NeuroSense will measure acoustic patterns and prepare them for your assessment." })] }), _jsxs("div", { className: "step-mark", children: ["04", _jsx("span", { children: "/04" })] })] }), _jsxs("div", { className: "speech-grid", children: [_jsxs("section", { className: "speech-panel prompt-panel", children: [_jsx("div", { className: "panel-kicker", children: "01 / Choose a prompt" }), _jsx("div", { className: "task-list", children: tasks.map(item => _jsxs("button", { className: `task-option ${task === item.id ? 'selected' : ''}`, onClick: () => { setTask(item.id); setResult(null); setStatus('Ready for a recording'); }, children: [_jsx("span", { children: item.title }), _jsx("b", { children: task === item.id ? 'Selected' : 'Select' })] }, item.id)) }), _jsxs("div", { className: "prompt-copy", children: [_jsx("span", { className: "quote-mark", children: "\"" }), _jsx("p", { children: selectedTask?.prompt || 'Loading prompt...' })] }), selectedTask?.duration_hint_s && _jsxs("small", { children: ["Recommended response: about ", selectedTask.duration_hint_s, " seconds"] })] }), _jsxs("section", { className: "speech-panel capture-panel", children: [_jsx("div", { className: "panel-kicker", children: "02 / Capture response" }), _jsxs("div", { className: "capture-actions", children: [_jsxs("label", { className: "dropzone", children: [_jsx("input", { type: "file", accept: "audio/*", onChange: e => handleFileChange(e.target.files?.[0] || null) }), _jsx("strong", { children: file ? file.name : 'Choose an audio file' }), _jsx("span", { children: "WAV, MP3, M4A, WEBM or OGG - up to 25 MB" })] }), _jsx("div", { className: "or-divider", children: "or record directly" }), _jsx(AudioRecorder, { onRecorded: blob => { setFile(new File([blob], 'recording.webm', { type: 'audio/webm' })); upload(blob); } })] }), (localPoints || serverPoints) && _jsxs("div", { className: "waveform-wrap", children: [_jsxs("div", { className: "waveform-label", children: [_jsx("span", { children: serverPoints ? 'Processed waveform' : 'Local preview' }), _jsx("span", { children: result ? `${result.duration_s}s` : 'Ready' })] }), _jsx(Waveform, { points: serverPoints || localPoints || [] })] }), _jsxs("button", { className: "primary-action", disabled: busy || !file, onClick: () => upload(), children: [busy ? 'Processing...' : 'Upload and analyze', _jsx("span", { children: "->" })] }), _jsxs("p", { className: `status-line ${status === 'Analysis complete' ? 'success' : ''}`, children: [_jsx("i", {}), status] })] })] }), result && _jsxs("section", { className: "results-panel", children: [_jsxs("div", { children: [_jsx("div", { className: "panel-kicker", children: "03 / Results ready" }), _jsx("h2", { children: "Speech signal captured" }), _jsx("p", { className: "result-note", children: "Your acoustic profile has been added to this assessment." })] }), _jsxs("div", { className: "metric-row", children: [_jsx(Metric, { label: "Duration", value: `${result.duration_s}s` }), _jsx(Metric, { label: "Pitch", value: result.pitch_hz ? `${result.pitch_hz} Hz` : 'Not detected' }), _jsx(Metric, { label: "Pause time", value: `${result.pause_duration_s}s` }), _jsx(Metric, { label: "Speech rate", value: result.speech_rate_wpm ? `${result.speech_rate_wpm} WPM` : 'Transcript unavailable' })] }), _jsxs("div", { className: "transcript", children: [_jsx("span", { children: "Transcript" }), _jsx("p", { children: result.transcript || 'Transcription is unavailable in lightweight mode. Acoustic features were extracted successfully.' })] }), _jsxs(Link, { className: "continue-action", to: `/assessment/finalize/${id}`, children: ["Continue to final review ", _jsx("span", { children: "->" })] })] })] });
}
function Metric({ label, value }) { return _jsxs("div", { className: "metric", children: [_jsx("span", { children: label }), _jsx("strong", { children: value })] }); }
function downsampleForPreview(data, target = 400) { const step = Math.max(1, Math.floor(data.length / target)); const points = []; for (let index = 0; index < data.length; index += step)
    points.push(data[index]); return points; }
async function audioToWav(source) {
    const context = new (window.AudioContext || window.webkitAudioContext)();
    try {
        const buffer = await context.decodeAudioData(await source.arrayBuffer());
        return new Blob([encodeWav(buffer)], { type: 'audio/wav' });
    }
    finally {
        await context.close();
    }
}
function encodeWav(buffer) {
    const channelCount = Math.min(buffer.numberOfChannels, 2);
    const frameCount = buffer.length;
    const bytesPerSample = 2;
    const dataSize = frameCount * channelCount * bytesPerSample;
    const output = new ArrayBuffer(44 + dataSize);
    const view = new DataView(output);
    const writeText = (offset, text) => [...text].forEach((character, index) => view.setUint8(offset + index, character.charCodeAt(0)));
    writeText(0, 'RIFF');
    view.setUint32(4, 36 + dataSize, true);
    writeText(8, 'WAVE');
    writeText(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, channelCount, true);
    view.setUint32(24, buffer.sampleRate, true);
    view.setUint32(28, buffer.sampleRate * channelCount * bytesPerSample, true);
    view.setUint16(32, channelCount * bytesPerSample, true);
    view.setUint16(34, 16, true);
    writeText(36, 'data');
    view.setUint32(40, dataSize, true);
    const channels = Array.from({ length: channelCount }, (_, index) => buffer.getChannelData(index));
    let offset = 44;
    for (let frame = 0; frame < frameCount; frame++) {
        for (let channel = 0; channel < channelCount; channel++) {
            const sample = Math.max(-1, Math.min(1, channels[channel][frame]));
            view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
            offset += 2;
        }
    }
    return output;
}
