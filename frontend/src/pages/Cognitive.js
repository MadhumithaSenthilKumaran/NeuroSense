import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useRef, useState } from 'react';
import api from '../api';
import { useParams, useNavigate } from 'react-router-dom';
import { MEMORY_WORDS } from '../utils/constants';
const COLORS = ['#e16f4d', '#147d7e', '#f1bd48', '#6d5aa8', '#2c8c5a', '#d94f70', '#4776b5', '#9c6b30'];
const shuffle = (items) => [...items].sort(() => Math.random() - 0.5);
export default function Cognitive() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [words, setWords] = useState(MEMORY_WORDS);
    const [stage, setStage] = useState('memory-display');
    const [time, setTime] = useState(15);
    const [recalled, setRecalled] = useState([]);
    const [entry, setEntry] = useState('');
    const [cards, setCards] = useState(() => shuffle(COLORS.flatMap((color, pair) => [{ id: pair * 2, color, open: false, matched: false }, { id: pair * 2 + 1, color, open: false, matched: false }])));
    const [first, setFirst] = useState(null);
    const [moves, setMoves] = useState(0);
    const [grid] = useState(() => shuffle(Array.from({ length: 25 }, (_, n) => n + 1)));
    const [next, setNext] = useState(1);
    const [started, setStarted] = useState(null);
    const [stopped, setStopped] = useState(null);
    const [cameraPhase, setCameraPhase] = useState('memory');
    const [cameraTime, setCameraTime] = useState(10);
    const [cameraWords] = useState(() => shuffle(['lantern', 'garden', 'silver']));
    const [cameraNumber] = useState(() => Math.floor(Math.random() * 5) + 3);
    const [actionStarted, setActionStarted] = useState(null);
    const [actionEnded, setActionEnded] = useState(null);
    const [capturedWords, setCapturedWords] = useState([]);
    const [cameraError, setCameraError] = useState('');
    const video = useRef(null);
    const stream = useRef(null);
    const recorder = useRef(null);
    const speechRecognition = useRef(null);
    const chunks = useRef([]);
    useEffect(() => { if (id)
        api.get(`/cognitive/session/${id}`).then(({ data }) => { if (data.memory?.words?.length)
            setWords(data.memory.words); }).catch(() => { }); }, [id]);
    useEffect(() => { if (stage !== 'memory-display' || time <= 0)
        return; const timer = window.setTimeout(() => setTime(value => value - 1), 1000); return () => window.clearTimeout(timer); }, [stage, time]);
    useEffect(() => { if (stage === 'memory-display' && time === 0)
        setStage('memory-test'); }, [stage, time]);
    useEffect(() => { if (stage === 'pairs' && cards.every(card => card.matched))
        setStage('numbers'); }, [cards, stage]);
    useEffect(() => { if (stage === 'camera' && video.current && stream.current)
        video.current.srcObject = stream.current; }, [stage]);
    useEffect(() => { if (stage !== 'camera')
        return; if (cameraTime === 0) {
        if (cameraPhase === 'memory') {
            setCameraPhase('colors');
            setCameraTime(5);
        }
        else if (cameraPhase === 'colors') {
            startRecording();
            setActionStarted(Date.now());
            setCameraPhase('record');
            setCameraTime(8);
        }
        else if (cameraPhase === 'record') {
            setActionEnded(Date.now());
            stopRecording();
            setCameraPhase('done');
        }
        ;
        return;
    } ; const timer = window.setTimeout(() => setCameraTime(value => value - 1), 1000); return () => window.clearTimeout(timer); }, [stage, cameraPhase, cameraTime]);
    useEffect(() => () => stream.current?.getTracks().forEach(track => track.stop()), []);
    const addWord = () => { if (entry.trim()) {
        setRecalled(current => [...current, entry.trim()]);
        setEntry('');
    } };
    const flip = (index) => { if (cards[index].open || cards[index].matched)
        return; setCards(current => current.map((card, i) => i === index ? { ...card, open: true } : card)); if (first === null) {
        setFirst(index);
        return;
    } ; setMoves(value => value + 1); const match = cards[first].color === cards[index].color; if (match)
        setCards(current => current.map((card, i) => i === first || i === index ? { ...card, matched: true } : card));
    else
        window.setTimeout(() => setCards(current => current.map((card, i) => i === first || i === index ? { ...card, open: false } : card)), 600); setFirst(null); };
    const clickNumber = (value) => { if (started === null || stopped !== null || value !== next)
        return; if (value === 25)
        setStopped(Date.now()); setNext(number => number + 1); };
    const startNumbers = () => { setStarted(Date.now()); setStopped(null); setNext(1); };
    const startCamera = async () => { try {
        const current = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        stream.current = current;
        if (video.current)
            video.current.srcObject = current;
        setCameraError('');
        setCameraTime(10);
        setCameraPhase('memory');
        setStage('camera');
    }
    catch {
        setCameraError('Camera and microphone access is required for this session.');
    } };
    const startRecording = () => { if (!stream.current || typeof MediaRecorder === 'undefined')
        return; chunks.current = []; const current = new MediaRecorder(stream.current); current.ondataavailable = event => { if (event.data.size)
        chunks.current.push(event.data); }; current.start(); recorder.current = current; const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition; if (Recognition) {
        const recognition = new Recognition();
        recognition.continuous = true;
        recognition.interimResults = false;
        recognition.onresult = (event) => { const transcript = Array.from({ length: event.results.length }, (_, index) => event.results[index][0].transcript).join(' '); setCapturedWords(transcript.toLowerCase().split(/[,\s]+/).filter(Boolean)); };
        recognition.start();
        speechRecognition.current = recognition;
    } };
    const stopRecording = () => { if (recorder.current?.state === 'recording')
        recorder.current.stop(); speechRecognition.current?.stop(); speechRecognition.current = null; };
    const submit = async () => { const payload = { recalled_words: recalled, attention_answer: '', visual_memory: {}, pattern_recognition: [], orientation: {}, story_answers: [], game_results: { pair_game: { matched_pairs: 8, moves }, number_game: { completed: next > 25, elapsed_ms: started && stopped ? stopped - started : null }, camera_session: { expected_words: cameraWords, recalled_words: capturedWords, expected_number: cameraNumber, action_duration_ms: actionStarted && actionEnded ? actionEnded - actionStarted : null, recording_captured: chunks.current.length > 0, capture_verified: chunks.current.length > 0 && !!actionStarted && !!actionEnded } } }; try {
        await api.post(`/cognitive/submit/${id}`, payload);
        navigate(`/assessment/speech/${id}`);
    }
    catch (error) {
        alert(error?.response?.data?.error || 'Failed to submit cognitive tests');
    } };
    return _jsxs("div", { className: "cognitive-page", children: [_jsxs("header", { className: "page-intro", children: [_jsx("div", { className: "eyebrow", children: "COGNITIVE ASSESSMENT / STEP 03" }), _jsx("h1", { children: "Memory in motion" }), _jsx("p", { children: "Complete each short challenge. Your responses are recorded as one assessment session." })] }), stage === 'memory-display' && _jsxs("section", { className: "game-panel memory-panel", children: [_jsx("h2", { children: "Remember these words" }), _jsxs("p", { children: ["You have ", time, " seconds."] }), _jsx("div", { className: "memory-word-grid", children: words.map(word => _jsx("strong", { children: word }, word)) }), _jsxs("div", { className: "game-countdown", children: [time, "s"] })] }), stage === 'memory-test' && _jsxs("section", { className: "game-panel", children: [_jsx("h2", { children: "Recall the words" }), _jsx("p", { children: "Add each word you remember." }), _jsxs("div", { className: "recall-entry", children: [_jsx("input", { value: entry, onChange: event => setEntry(event.target.value), onKeyDown: event => event.key === 'Enter' && addWord(), placeholder: "Type a word" }), _jsx("button", { onClick: addWord, children: "Add word" })] }), _jsx("div", { className: "recall-list", children: recalled.map((word, index) => _jsxs("button", { onClick: () => setRecalled(current => current.filter((_, i) => i !== index)), children: [word, " x"] }, `${word}-${index}`)) }), _jsxs("button", { className: "primary-action", onClick: () => setStage('pairs'), children: ["Continue to pair game ", _jsx("span", { children: "->" })] })] }), stage === 'pairs' && _jsxs("section", { className: "game-panel", children: [_jsx("h2", { children: "Pair up the color cards" }), _jsx("p", { children: "Flip one card at a time and find all eight pairs." }), _jsx("div", { className: "pair-grid", children: cards.map((card, index) => _jsx("button", { className: `pair-card ${card.open || card.matched ? 'revealed' : ''}`, onClick: () => flip(index), style: card.open || card.matched ? { backgroundColor: card.color } : undefined, children: card.open || card.matched ? '' : '?' }, card.id)) }), _jsxs("p", { className: "game-status", children: ["Pairs found: ", cards.filter(card => card.matched).length / 2, " / 8 \u00B7 Moves: ", moves] })] }), stage === 'numbers' && _jsxs("section", { className: "game-panel", children: [_jsx("h2", { children: "Count from 1 to 25" }), _jsx("p", { children: "Press Start, then select the numbers in order. Stop ends the timer." }), _jsxs("div", { className: "number-actions", children: [_jsx("button", { className: "primary-action", onClick: startNumbers, children: "Start" }), _jsx("button", { className: "secondary-action", onClick: () => started && setStopped(Date.now()), children: "Stop" })] }), _jsx("div", { className: "number-grid", children: grid.map(number => _jsx("button", { className: number < next ? 'number-done' : '', onClick: () => clickNumber(number), children: number }, number)) }), _jsxs("p", { className: "game-status", children: ["Next: ", next > 25 ? 'Complete' : next] }), stopped && _jsxs("button", { className: "primary-action", onClick: startCamera, children: ["Continue to camera session ", _jsx("span", { children: "->" })] })] }), stage === 'camera' && _jsxs("section", { className: "game-panel camera-panel", children: [_jsx("h2", { children: "Camera memory session" }), _jsx("video", { ref: video, autoPlay: true, muted: true, playsInline: true }), cameraPhase === 'memory' && _jsxs("div", { className: "camera-prompt", children: [_jsx("p", { children: "Remember these words and show this number with your fingers." }), _jsx("strong", { children: cameraWords.join(' · ') }), _jsx("b", { children: cameraNumber })] }), cameraPhase === 'colors' && _jsxs("div", { className: "camera-prompt", children: [_jsx("p", { children: "Watch the colors carefully." }), _jsxs("div", { className: "color-flash", children: [_jsx("i", {}), _jsx("i", {}), _jsx("i", {})] })] }), cameraPhase === 'record' && _jsxs("div", { className: "camera-prompt", children: [_jsxs("p", { children: ["Recording now. Say the three words and show ", cameraNumber, " with your fingers."] }), _jsxs("strong", { children: ["Capture time remaining: ", cameraTime, "s"] }), _jsx("span", { children: "Keep your face and hands visible in the camera frame." })] }), cameraPhase === 'done' && _jsxs("div", { className: "camera-prompt", children: [_jsx("p", { children: "Camera and microphone capture complete." }), _jsx("strong", { children: "Captured for verification" }), _jsxs("p", { children: ["Recorded action duration: ", actionStarted && actionEnded ? `${((actionEnded - actionStarted) / 1000).toFixed(1)} seconds` : 'Unavailable'] }), _jsx("p", { children: "The recording will be analyzed against the displayed words and finger-number instruction." }), _jsxs("button", { className: "primary-action", onClick: () => setStage('complete'), children: ["Use captured session ", _jsx("span", { children: "->" })] })] }), _jsx("div", { className: "game-countdown", children: cameraPhase === 'done' ? 'Captured' : `${cameraTime}s` }), cameraError && _jsx("p", { className: "form-error", children: cameraError })] }), stage === 'complete' && _jsxs("section", { className: "game-panel", children: [_jsx("h2", { children: "Cognitive games complete" }), _jsx("p", { children: "Your game results and camera response are ready to submit." }), _jsxs("button", { className: "primary-action", onClick: submit, children: ["Submit cognitive tests ", _jsx("span", { children: "->" })] })] })] });
}
