import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useEffect, useRef, useState } from "react";
import { FilesetResolver, HandLandmarker } from "@mediapipe/tasks-vision";
import api from "../api";
import { useParams, useNavigate } from "react-router-dom";
import { MEMORY_WORDS } from "../utils/constants";
const COLORS = [
    "#e16f4d",
    "#147d7e",
    "#f1bd48",
    "#6d5aa8",
    "#2c8c5a",
    "#d94f70",
    "#4776b5",
    "#9c6b30",
];
const fisherYates = (items) => {
    const shuffled = [...items];
    for (let index = shuffled.length - 1; index > 0; index -= 1) {
        const swapIndex = Math.floor(Math.random() * (index + 1));
        [shuffled[index], shuffled[swapIndex]] = [
            shuffled[swapIndex],
            shuffled[index],
        ];
    }
    return shuffled;
};
const numberTimeScore = (seconds) => {
    if (seconds == null)
        return 0;
    if (seconds <= 20)
        return 10;
    if (seconds <= 25)
        return 9;
    if (seconds <= 30)
        return 8;
    if (seconds <= 35)
        return 7;
    if (seconds <= 40)
        return 6;
    if (seconds <= 50)
        return 5;
    if (seconds <= 60)
        return 4;
    if (seconds <= 75)
        return 3;
    if (seconds <= 90)
        return 2;
    return 1;
};
const orderedAccuracy = (expected, actual) => {
    if (!expected.length)
        return 0;
    return Math.round((expected.reduce((count, value, index) => count + (actual[index] === value ? 1 : 0), 0) / expected.length) * 1000) / 10;
};
const VISION_WASM = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@1.0.1/wasm";
const HAND_MODEL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task";
const HAND_CONNECTIONS = [
    [0, 1],
    [1, 2],
    [2, 3],
    [3, 4],
    [0, 5],
    [5, 6],
    [6, 7],
    [7, 8],
    [5, 9],
    [9, 10],
    [10, 11],
    [11, 12],
    [9, 13],
    [13, 14],
    [14, 15],
    [15, 16],
    [13, 17],
    [17, 18],
    [18, 19],
    [19, 20],
    [0, 17],
];
export default function Cognitive() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [words, setWords] = useState(MEMORY_WORDS);
    const [stage, setStage] = useState("memory-display");
    const [time, setTime] = useState(15);
    const [recalled, setRecalled] = useState([]);
    const [entry, setEntry] = useState("");
    const [cards, setCards] = useState(() => fisherYates(COLORS.flatMap((color, pair) => [
        { id: pair * 2, color, open: false, matched: false },
        { id: pair * 2 + 1, color, open: false, matched: false },
    ])));
    const [first, setFirst] = useState(null);
    const [moves, setMoves] = useState(0);
    const [pairAttempts, setPairAttempts] = useState(0);
    const [pairCorrectMatches, setPairCorrectMatches] = useState(0);
    const [pairIncorrectAttempts, setPairIncorrectAttempts] = useState(0);
    const [pairCompletionTimeMs, setPairCompletionTimeMs] = useState(null);
    const [grid] = useState(() => fisherYates(Array.from({ length: 25 }, (_, n) => n + 1)));
    const [next, setNext] = useState(1);
    const [started, setStarted] = useState(null);
    const [stopped, setStopped] = useState(null);
    const [numberErrors, setNumberErrors] = useState(0);
    const [numberCompletionMs, setNumberCompletionMs] = useState(null);
    const [numberIntervalsMs, setNumberIntervalsMs] = useState([]);
    const [numberFeedback, setNumberFeedback] = useState("");
    const [cameraPhase, setCameraPhase] = useState("prompt");
    const cameraPhaseRef = useRef("prompt");
    const [cameraTime, setCameraTime] = useState(5);
    const [submitting, setSubmitting] = useState(false);
    const [captureReady, setCaptureReady] = useState(false);
    const [cameraAnalyzed, setCameraAnalyzed] = useState(false);
    const [liveCount, setLiveCount] = useState(null);
    const [handSummary, setHandSummary] = useState([]);
    const [cameraStatus, setCameraStatus] = useState("");
    const [promptedNumbers] = useState(() => fisherYates([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]).slice(0, 3));
    const [acceptedCaptures, setAcceptedCaptures] = useState([]);
    const [capturedNumberRecall, setCapturedNumberRecall] = useState([]);
    const [actionStarted, setActionStarted] = useState(null);
    const [actionEnded, setActionEnded] = useState(null);
    const [praxisTrials, setPraxisTrials] = useState([]);
    const [cameraError, setCameraError] = useState("");
    const video = useRef(null);
    const overlay = useRef(null);
    const stream = useRef(null);
    const recorder = useRef(null);
    const chunks = useRef([]);
    const landmarker = useRef(null);
    const animation = useRef(null);
    const stableCounts = useRef([]);
    const lastVideoTime = useRef(-1);
    const captureWindows = useRef([]);
    const replacementIndexRef = useRef(null);
    const recordingStarted = useRef(0);
    const capturedCount = useRef(0);
    const stableSince = useRef(0);
    const stableValue = useRef(null);
    const pairStartedAt = useRef(null);
    const pairFinished = useRef(false);
    const pairResolving = useRef(false);
    const numberStartedAt = useRef(null);
    const numberLastCorrectAt = useRef(null);
    const numberCompleted = useRef(false);
    const feedbackTimer = useRef(null);
    useEffect(() => {
        if (id)
            api
                .get(`/cognitive/session/${id}`)
                .then(({ data }) => {
                if (data.memory?.words?.length)
                    setWords(data.memory.words);
            })
                .catch(() => { });
    }, [id]);
    useEffect(() => {
        if (stage !== "memory-display" || time <= 0)
            return;
        const timer = window.setTimeout(() => setTime((value) => value - 1), 1000);
        return () => window.clearTimeout(timer);
    }, [stage, time]);
    useEffect(() => {
        if (stage === "memory-display" && time === 0)
            setStage("memory-test");
    }, [stage, time]);
    useEffect(() => {
        if (stage !== "pairs")
            return;
        if (pairStartedAt.current === null)
            pairStartedAt.current = performance.now();
        if (!cards.every((card) => card.matched) || pairFinished.current)
            return;
        pairFinished.current = true;
        const elapsed = performance.now() - (pairStartedAt.current || performance.now());
        setPairCompletionTimeMs(Math.round(elapsed));
        setStage("numbers");
    }, [cards, stage]);
    useEffect(() => {
        if (stage === "camera" && video.current && stream.current) {
            video.current.srcObject = stream.current;
            video.current.play().catch(() => { });
            if (animation.current)
                cancelAnimationFrame(animation.current);
            animation.current = requestAnimationFrame(detectCameraHands);
        }
    }, [stage]);
    useEffect(() => {
        cameraPhaseRef.current = cameraPhase;
    }, [cameraPhase]);
    useEffect(() => {
        if (stage !== "camera" || cameraPhase === "done")
            return;
        if (cameraTime === 0) {
            if (cameraPhase === "prompt") {
                setCameraPhase("wait");
                setCameraTime(5);
            }
            else if (cameraPhase === "wait") {
                setCameraPhase("gesture");
                setCameraTime(0);
                setActionStarted(Date.now());
            }
            else if (cameraPhase === "gesture") {
                return;
            }
            return;
        }
        const timer = window.setTimeout(() => setCameraTime((value) => value - 1), 1000);
        return () => window.clearTimeout(timer);
    }, [stage, cameraPhase, cameraTime]);
    useEffect(() => () => {
        if (animation.current)
            cancelAnimationFrame(animation.current);
        stream.current?.getTracks().forEach((track) => track.stop());
        landmarker.current?.close();
    }, []);
    const addWord = () => {
        if (entry.trim()) {
            setRecalled((current) => [...current, entry.trim()]);
            setEntry("");
        }
    };
    const flip = (index) => {
        if (cards[index].open || cards[index].matched || pairResolving.current)
            return;
        setCards((current) => current.map((card, i) => (i === index ? { ...card, open: true } : card)));
        if (first === null) {
            setFirst(index);
            return;
        }
        setMoves((value) => value + 1);
        const match = cards[first].color === cards[index].color;
        setPairAttempts((value) => value + 1);
        if (match) {
            setPairCorrectMatches((value) => value + 1);
            setCards((current) => current.map((card, i) => i === first || i === index ? { ...card, matched: true } : card));
        }
        else {
            setPairIncorrectAttempts((value) => value + 1);
            pairResolving.current = true;
            window.setTimeout(() => setCards((current) => current.map((card, i) => i === first || i === index ? { ...card, open: false } : card)), 600);
            window.setTimeout(() => {
                pairResolving.current = false;
            }, 600);
        }
        setFirst(null);
    };
    const clickNumber = (value) => {
        if (started === null || stopped !== null || numberCompleted.current)
            return;
        if (value !== next) {
            setNumberErrors((errors) => errors + 1);
            setNumberFeedback(`Incorrect selection. Select ${next}.`);
            if (feedbackTimer.current)
                window.clearTimeout(feedbackTimer.current);
            feedbackTimer.current = window.setTimeout(() => setNumberFeedback(""), 900);
            return;
        }
        const now = performance.now();
        const interval = now - (numberLastCorrectAt.current || numberStartedAt.current || now);
        setNumberIntervalsMs((current) => [...current, Math.round(interval)]);
        numberLastCorrectAt.current = now;
        setNext(next + 1);
        if (value === 25) {
            numberCompleted.current = true;
            setStopped(now);
            setNumberCompletionMs(Math.round(now - (numberStartedAt.current || now)));
        }
    };
    const startNumbers = () => {
        const now = performance.now();
        numberStartedAt.current = now;
        numberLastCorrectAt.current = now;
        numberCompleted.current = false;
        setStarted(now);
        setStopped(null);
        setNext(1);
        setNumberErrors(0);
        setNumberCompletionMs(null);
        setNumberIntervalsMs([]);
        setNumberFeedback("");
    };
    const countHand = (points, _handedness) => {
        const distance = (a, b) => Math.hypot(points[a].x - points[b].x, points[a].y - points[b].y, points[a].z - points[b].z);
        const angle = (first, middle, last) => {
            const a = [
                points[first].x - points[middle].x,
                points[first].y - points[middle].y,
                points[first].z - points[middle].z,
            ];
            const b = [
                points[last].x - points[middle].x,
                points[last].y - points[middle].y,
                points[last].z - points[middle].z,
            ];
            const denominator = Math.max(Math.hypot(...a) * Math.hypot(...b), 1e-6);
            return ((Math.acos(Math.max(-1, Math.min(1, (a[0] * b[0] + a[1] * b[1] + a[2] * b[2]) / denominator))) *
                180) /
                Math.PI);
        };
        const extended = (tip, pip, mcp, dip) => angle(mcp, pip, dip) > 145 &&
            angle(pip, dip, tip) > 145 &&
            distance(tip, 0) > distance(pip, 0) * 1.03;
        const states = {
            thumb: Number(points[4].x < points[5].x),
            index: Number(extended(8, 6, 5, 7)),
            middle: Number(extended(12, 10, 9, 11)),
            ring: Number(extended(16, 14, 13, 15)),
            pinky: Number(extended(20, 18, 17, 19)),
        };
        return {
            ...states,
            count: states.thumb +
                states.index +
                states.middle +
                states.ring +
                states.pinky,
        };
    };
    const drawHands = (result) => {
        const canvas = overlay.current;
        const currentVideo = video.current;
        if (!canvas || !currentVideo)
            return;
        const width = currentVideo.videoWidth || 640;
        const height = currentVideo.videoHeight || 480;
        canvas.width = width;
        canvas.height = height;
        const context = canvas.getContext("2d");
        if (!context)
            return;
        context.clearRect(0, 0, width, height);
        result.landmarks.forEach((points, index) => {
            context.strokeStyle = index ? "#f1bd48" : "#34c759";
            context.fillStyle = context.strokeStyle;
            context.lineWidth = 3;
            HAND_CONNECTIONS.forEach(([from, to]) => {
                context.beginPath();
                context.moveTo((1 - points[from].x) * width, points[from].y * height);
                context.lineTo((1 - points[to].x) * width, points[to].y * height);
                context.stroke();
            });
            points.forEach((point) => {
                context.beginPath();
                context.arc((1 - point.x) * width, point.y * height, 5, 0, Math.PI * 2);
                context.fill();
            });
        });
    };
    const appendOrReplaceCapture = (capture) => {
        const replacementIndex = replacementIndexRef.current;
        const nextCapture = { ...capture };
        setAcceptedCaptures((current) => {
            const next = [...current];
            if (replacementIndex !== null && replacementIndex >= 0 && replacementIndex < next.length) {
                next[replacementIndex] = nextCapture;
            }
            else if (next.length >= promptedNumbers.length) {
                next[next.length - 1] = nextCapture;
            }
            else {
                next.push(nextCapture);
            }
            capturedCount.current = next.length;
            return next;
        });
        setCapturedNumberRecall((current) => {
            const next = [...current];
            if (replacementIndex !== null && replacementIndex >= 0 && replacementIndex < next.length) {
                next[replacementIndex] = nextCapture.detected_number;
            }
            else if (next.length >= promptedNumbers.length) {
                next[next.length - 1] = nextCapture.detected_number;
            }
            else {
                next.push(nextCapture.detected_number);
            }
            return next;
        });
        const nextCaptureWindows = [...captureWindows.current];
        if (replacementIndex !== null && replacementIndex >= 0 && replacementIndex < nextCaptureWindows.length) {
            nextCaptureWindows[replacementIndex] = nextCapture;
        }
        else if (nextCaptureWindows.length >= promptedNumbers.length) {
            nextCaptureWindows[nextCaptureWindows.length - 1] = nextCapture;
        }
        else {
            nextCaptureWindows.push(nextCapture);
        }
        captureWindows.current = nextCaptureWindows;
        replacementIndexRef.current = null;
    };
    const removeCaptureAt = (index) => {
        replacementIndexRef.current = index;
        setAcceptedCaptures((current) => {
            const next = current.filter((_, itemIndex) => itemIndex !== index);
            capturedCount.current = next.length;
            return next;
        });
        setCapturedNumberRecall((current) => current.filter((_, itemIndex) => itemIndex !== index));
        captureWindows.current = captureWindows.current.filter((_, itemIndex) => itemIndex !== index);
    };
    const detectCameraHands = () => {
        const currentVideo = video.current;
        const currentLandmarker = landmarker.current;
        if (!currentVideo || !currentLandmarker)
            return;
        if (currentVideo.readyState >= 2 &&
            currentVideo.currentTime !== lastVideoTime.current) {
            lastVideoTime.current = currentVideo.currentTime;
            const result = currentLandmarker.detectForVideo(currentVideo, performance.now());
            drawHands(result);
            if (!result.landmarks.length) {
                setCameraStatus("No hand detected");
                setLiveCount(null);
                setHandSummary([]);
                stableValue.current = null;
                stableSince.current = 0;
            }
            else {
                const hands = result.landmarks
                    .slice(0, 2)
                    .map((points, index) => {
                    const label = result.handednesses?.[index]?.[0]?.categoryName ||
                        `Hand ${index + 1}`;
                    return { label, ...countHand(points, label) };
                });
                const total = hands.reduce((sum, hand) => sum + hand.count, 0);
                stableCounts.current = [...stableCounts.current.slice(-9), total];
                const counts = stableCounts.current.reduce((map, count) => ({ ...map, [count]: (map[count] || 0) + 1 }), {});
                const stable = Number(Object.entries(counts).sort((a, b) => b[1] - a[1])[0][0]);
                setLiveCount(stable);
                setHandSummary(hands);
                setCameraStatus(hands.length > 1 ? "Two hands detected" : "One hand detected");
                if (cameraPhaseRef.current === "gesture") {
                    if (stable === stableValue.current) {
                        if (!stableSince.current)
                            stableSince.current = performance.now();
                    }
                    else {
                        stableValue.current = stable;
                        stableSince.current = performance.now();
                    }
                    if (stableSince.current &&
                        performance.now() - stableSince.current >= 2500) {
                        const now = performance.now();
                        const start = Math.max(recordingStarted.current, now - 2500);
                        const targetNumber = promptedNumbers[Math.min(capturedCount.current, promptedNumbers.length - 1)];
                        const capture = {
                            target_number: targetNumber,
                            detected_number: stable,
                            accepted: true,
                            response_time_ms: Math.round(now - start),
                            start_seconds: (start - recordingStarted.current) / 1000,
                            end_seconds: (now - recordingStarted.current) / 1000,
                        };
                        appendOrReplaceCapture(capture);
                        setCameraStatus(`Number ${stable} captured automatically`);
                        stableSince.current = 0;
                        stableValue.current = null;
                    }
                }
            }
        }
        animation.current = requestAnimationFrame(detectCameraHands);
    };
    const startCamera = async () => {
        try {
            const current = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: false,
            });
            stream.current = current;
            if (!landmarker.current) {
                const vision = await FilesetResolver.forVisionTasks(VISION_WASM);
                landmarker.current = await HandLandmarker.createFromOptions(vision, {
                    baseOptions: { modelAssetPath: HAND_MODEL },
                    runningMode: "VIDEO",
                    numHands: 2,
                    minHandDetectionConfidence: 0.55,
                    minHandPresenceConfidence: 0.55,
                    minTrackingConfidence: 0.55,
                });
            }
            setCameraError("");
            setCaptureReady(false);
            setCameraAnalyzed(false);
            setAcceptedCaptures([]);
            setCapturedNumberRecall([]);
            capturedCount.current = 0;
            stableSince.current = 0;
            stableValue.current = null;
            captureWindows.current = [];
            recordingStarted.current = performance.now();
            setCameraTime(5);
            setCameraPhase("prompt");
            setStage("camera");
            stableCounts.current = [];
            lastVideoTime.current = -1;
            chunks.current = [];
            if (typeof MediaRecorder !== "undefined") {
                const recording = new MediaRecorder(current);
                recording.ondataavailable = (event) => {
                    if (event.data.size)
                        chunks.current.push(event.data);
                };
                recording.onstop = () => setCaptureReady(true);
                recording.start(250);
                recorder.current = recording;
            }
        }
        catch (error) {
            stream.current?.getTracks().forEach((track) => track.stop());
            stream.current = null;
            setCameraError(error instanceof Error
                ? error.message
                : "Camera access or MediaPipe hand detection is unavailable.");
        }
    };
    const stopRecording = () => {
        if (animation.current)
            cancelAnimationFrame(animation.current);
        if (recorder.current?.state === "recording") {
            recorder.current.stop();
        }
        if (stream.current) {
            stream.current.getTracks().forEach((track) => track.stop());
            stream.current = null;
        }
        if (video.current) {
            video.current.pause();
            video.current.srcObject = null;
        }
    };
    const finishCameraSession = () => {
        setActionEnded(Date.now());
        stopRecording();
        setCameraPhase("done");
    };
    const submit = async () => {
        if (submitting ||
            !captureReady ||
            acceptedCaptures.length !== promptedNumbers.length)
            return;
        setSubmitting(true);
        try {
            const videoBlob = chunks.current.length
                ? new Blob(chunks.current, {
                    type: recorder.current?.mimeType || "video/webm",
                })
                : null;
            if (!videoBlob)
                throw new Error("No camera capture was recorded");
            const finalAcceptedCaptures = acceptedCaptures.length === promptedNumbers.length ? acceptedCaptures : captureWindows.current;
            const finalRecall = capturedNumberRecall.length === promptedNumbers.length ? capturedNumberRecall : finalAcceptedCaptures.map((capture) => capture.detected_number ?? capture);
            const form = new FormData();
            form.append("video", videoBlob, "praxis-capture.webm");
            promptedNumbers.forEach((number) => form.append("prompted_numbers", String(number)));
            form.append("gesture_start_seconds", "10");
            form.append("capture_windows", JSON.stringify(finalAcceptedCaptures));
            const praxis = await api.post(`/cognitive/praxis/analyze/${id}`, form);
            const trials = praxis.data.praxis_trials || [];
            setPraxisTrials(trials);
            const completed = next > 25;
            const elapsedMs = started && stopped ? stopped - started : null;
            const payload = {
                recalled_words: recalled,
                attention_answer: "",
                visual_memory: {},
                pattern_recognition: [],
                orientation: {},
                story_answers: [],
                game_results: {
                    pair_game: {
                        matched_pairs: pairCorrectMatches,
                        attempts: pairAttempts,
                        correct_matches: pairCorrectMatches,
                        incorrect_attempts: pairIncorrectAttempts,
                        completion_time_ms: pairCompletionTimeMs,
                        completion_time_seconds: pairCompletionTimeMs == null ? null : pairCompletionTimeMs / 1000,
                    },
                    number_game: {
                        session_id: id,
                        completed,
                        completion_time_ms: numberCompletionMs,
                        completion_time_seconds: numberCompletionMs == null ? null : numberCompletionMs / 1000,
                        elapsed_ms: elapsedMs,
                        errors: numberErrors,
                        correct_clicks: next > 25 ? 25 : Math.max(0, next - 1),
                        incorrect_clicks: numberErrors,
                        time_score: numberTimeScore(numberCompletionMs == null ? null : numberCompletionMs / 1000),
                        error_penalty: numberErrors * 0.5,
                        final_task_score: Math.max(0, numberTimeScore(numberCompletionMs == null ? null : numberCompletionMs / 1000) - numberErrors * 0.5),
                        grid_layout: grid,
                        intervals_ms: numberIntervalsMs,
                        sequence_score: completed ? 100 : 0,
                    },
                    camera_session: {
                        prompted_numbers: promptedNumbers,
                        accepted_captures: finalAcceptedCaptures,
                        recalled_numbers: finalRecall,
                        praxis_trials: trials,
                        action_duration_ms: finalAcceptedCaptures.reduce((sum, capture) => sum + (capture.response_time_ms || 0), 0),
                        recording_captured: true,
                        capture_verified: true,
                    },
                },
            };
            await api.post(`/cognitive/submit/${id}`, payload);
            setCameraAnalyzed(true);
        }
        catch (error) {
            const detail = error?.response?.data?.error ||
                error?.message ||
                "Failed to submit cognitive tests";
            alert(`Camera analysis failed: ${detail}`);
        }
        finally {
            setSubmitting(false);
        }
    };
    return (_jsxs("div", { className: "cognitive-page", children: [_jsxs("header", { className: "page-intro", children: [_jsx("div", { className: "eyebrow", children: "COGNITIVE ASSESSMENT / STEP 03" }), _jsx("h1", { children: "Memory in motion" }), _jsx("p", { children: "Complete each short challenge. Your responses are recorded as one assessment session." })] }), stage === "memory-display" && (_jsxs("section", { className: "game-panel memory-panel", children: [_jsx("h2", { children: "Remember these words" }), _jsxs("p", { children: ["You have ", time, " seconds."] }), _jsx("div", { className: "memory-word-grid", children: words.map((word) => (_jsx("strong", { children: word }, word))) }), _jsxs("div", { className: "game-countdown", children: [time, "s"] })] })), stage === "memory-test" && (_jsxs("section", { className: "game-panel", children: [_jsx("h2", { children: "Recall the words" }), _jsx("p", { children: "Add each word you remember." }), _jsxs("div", { className: "recall-entry", children: [_jsx("input", { value: entry, onChange: (event) => setEntry(event.target.value), onKeyDown: (event) => event.key === "Enter" && addWord(), placeholder: "Type a word" }), _jsx("button", { onClick: addWord, children: "Add word" })] }), _jsx("div", { className: "recall-list", children: recalled.map((word, index) => (_jsxs("button", { onClick: () => setRecalled((current) => current.filter((_, i) => i !== index)), children: [word, " x"] }, `${word}-${index}`))) }), _jsxs("button", { className: "primary-action", onClick: () => setStage("pairs"), children: ["Continue to pair game ", _jsx("span", { children: "->" })] })] })), stage === "pairs" && (_jsxs("section", { className: "game-panel", children: [_jsx("h2", { children: "Pair up the color cards" }), _jsx("p", { children: "Flip one card at a time and find all eight pairs." }), _jsx("div", { className: "pair-grid", children: cards.map((card, index) => (_jsx("button", { className: `pair-card ${card.open || card.matched ? "revealed" : ""}`, onClick: () => flip(index), style: card.open || card.matched
                                ? { backgroundColor: card.color }
                                : undefined, children: card.open || card.matched ? "" : "?" }, card.id))) }), _jsxs("p", { className: "game-status", children: ["Pairs found: ", cards.filter((card) => card.matched).length / 2, " / 8 \u00B7 Attempts: ", pairAttempts, " \u00B7 Incorrect: ", pairIncorrectAttempts] })] })), stage === "numbers" && (_jsxs("section", { className: "game-panel", children: [_jsx("h2", { children: "Number order and timing" }), _jsx("p", { children: "Select 1 through 25 in sequence as quickly and accurately as possible. The timer starts when you press Start and stops when 25 is selected." }), _jsx("div", { className: "number-actions", children: _jsx("button", { className: "primary-action", onClick: startNumbers, children: "Start" }) }), _jsx("div", { className: "number-grid", children: grid.map((number) => (_jsx("button", { className: `${number < next ? "number-done" : ""} ${numberFeedback && number === next ? "number-error" : ""}`, onClick: () => clickNumber(number), disabled: stopped !== null, children: number }, number))) }), _jsxs("p", { className: "game-status", children: ["Next: ", next > 25 ? "Complete" : next, started && !stopped
                                ? ` · ${((performance.now() - started) / 1000).toFixed(1)}s elapsed`
                                : ""] }), numberFeedback && _jsx("p", { className: "game-status number-feedback", children: numberFeedback }), stopped && (_jsxs("div", { className: "number-result", children: [_jsx("h3", { children: "Cognitive Task Result" }), _jsxs("p", { children: ["Completion Time: ", ((numberCompletionMs || 0) / 1000).toFixed(2), " seconds"] }), _jsxs("p", { children: ["Errors: ", numberErrors] }), _jsxs("p", { children: ["Time Score: ", numberTimeScore((numberCompletionMs || 0) / 1000), "/10"] }), _jsxs("p", { children: ["Error Penalty: ", (numberErrors * 0.5).toFixed(1)] }), _jsx("p", { children: _jsxs("strong", { children: ["Task Performance Score: ", Math.max(0, numberTimeScore((numberCompletionMs || 0) / 1000) - numberErrors * 0.5).toFixed(1), "/10"] }) }), _jsxs("button", { className: "primary-action", onClick: startCamera, children: ["Continue to camera finger session ", _jsx("span", { children: "->" })] })] }))] })), stage === "camera" && (_jsxs("section", { className: "game-panel camera-panel", children: [_jsx("h2", { children: "Finger number assessment" }), _jsx("p", { children: "All three numbers are shown for 5 seconds. After a 5-second wait, show each number steadily until it is captured. After all three are captured, finish the session yourself." }), _jsxs("div", { className: "camera-vision", children: [_jsx("video", { ref: video, autoPlay: true, muted: true, playsInline: true }), _jsx("canvas", { ref: overlay })] }), _jsxs("div", { className: "camera-prompt", children: [_jsx("p", { children: cameraPhase === "prompt"
                                    ? "Memorize these three numbers"
                                    : cameraPhase === "wait"
                                        ? "Get ready to show them"
                                        : cameraPhase === "gesture"
                                            ? `Show the numbers in order · ${acceptedCaptures.length + 1} of ${promptedNumbers.length}`
                                            : "All three numbers captured" }), cameraPhase === "prompt" && _jsx("strong", { children: promptedNumbers.join(" · ") }), _jsx("span", { children: cameraPhase === "prompt"
                                    ? `Visible for ${cameraTime}s`
                                    : cameraPhase === "wait"
                                        ? `Starting in ${cameraTime}s`
                                        : cameraPhase === "gesture"
                                            ? `Show ${promptedNumbers[acceptedCaptures.length]} steadily · no time limit`
                                            : "All three captured · finish the session above" })] }), _jsxs("div", { className: "live-finger-summary", children: [_jsx("span", { children: cameraStatus || "Initializing hand detection" }), _jsxs("strong", { children: ["Detected number: ", liveCount == null ? "Unknown" : liveCount] }), handSummary.map((hand, index) => (_jsxs("small", { children: [hand.label, ": ", hand.count, " fingers (thumb ", hand.thumb, ", index", " ", hand.index, ", middle ", hand.middle, ", ring ", hand.ring, ", pinky", " ", hand.pinky, ")"] }, `${hand.label}-${index}`)))] }), cameraPhase === "gesture" && (_jsxs(_Fragment, { children: [_jsxs("button", { className: "primary-action", onClick: finishCameraSession, children: ["Stop recording ", _jsx("span", { children: "->" })] }), _jsx("div", { className: "camera-no-limit", children: "Each stable detected number is saved automatically. Stop when finished." })] })), cameraPhase === "done" && _jsx("div", { className: "game-countdown", children: "Recording stopped" }), cameraPhase === "done" && (_jsxs("button", { className: "primary-action", onClick: () => setStage("complete"), children: ["Review captured numbers ", _jsx("span", { children: "->" })] })), acceptedCaptures.length > 0 && (_jsxs("div", { className: "camera-number-recall", children: [_jsx("h3", { children: "Numbers captured" }), _jsx("p", { children: "Saved stack compared with the numbers shown on the previous slide." }), _jsx("div", { className: "recall-list", children: capturedNumberRecall.map((number, index) => (_jsxs("button", { onClick: () => removeCaptureAt(index), children: [number, " x"] }, `${number}-${index}`))) }), _jsxs("p", { className: "game-status", children: ["Stack entries: ", capturedNumberRecall.length, " \u00B7 Accuracy: ", orderedAccuracy(promptedNumbers, capturedNumberRecall), "%"] }), _jsx("div", { className: "praxis-trial-list", children: promptedNumbers.map((number, index) => (_jsxs("div", { className: capturedNumberRecall[index] === number ? "praxis-trial correct" : "praxis-trial", children: [_jsxs("span", { children: ["Shown ", number] }), _jsxs("b", { children: ["Saved ", capturedNumberRecall[index] ?? "-"] }), _jsx("small", { children: capturedNumberRecall[index] === number ? "Correct position" : "Incorrect position" })] }, `${number}-${index}`))) })] })), cameraError && _jsx("p", { className: "form-error", children: cameraError })] })), stage === "complete" && (_jsxs("section", { className: "game-panel", children: [_jsx("h2", { children: cameraAnalyzed
                            ? "Camera sequence result"
                            : "Camera recording complete" }), _jsx("p", { children: cameraAnalyzed
                            ? "Computer vision checked the prompted finger numbers in order."
                            : acceptedCaptures.length === promptedNumbers.length
                                ? "The automatic captures and memory stack are ready. Submit them for analysis."
                                : `Only ${acceptedCaptures.length} of ${promptedNumbers.length} prompted numbers were captured. Restart the camera task and try again.` }), cameraAnalyzed && (_jsxs("div", { className: "praxis-results", children: [_jsxs("strong", { children: ["Camera sequence accuracy:", " ", praxisTrials.filter((trial) => trial.is_correct_match).length, " ", "/ ", praxisTrials.length] }), _jsxs("strong", { children: ["Saved stack accuracy: ", orderedAccuracy(promptedNumbers, capturedNumberRecall), "%"] }), praxisTrials.map((trial) => (_jsxs("div", { className: trial.is_correct_match
                                    ? "praxis-trial correct"
                                    : "praxis-trial", children: [_jsxs("span", { children: ["Prompted ", trial.prompted_number] }), _jsxs("b", { children: ["Detected ", trial.gestured_number_detected] }), _jsxs("small", { children: [trial.is_correct_match
                                                ? "Correct match"
                                                : "Does not match", " ", "\u00B7 ", trial.metrics?.frames_with_hand || 0, " hand frames"] })] }, `${trial.prompted_number}-${trial.gestured_number_detected}`))), _jsxs("button", { className: "primary-action", onClick: () => navigate(`/assessment/speech/${id}`), children: ["Continue to speech ", _jsx("span", { children: "->" })] })] })), !cameraAnalyzed &&
                        acceptedCaptures.length === promptedNumbers.length && (_jsxs("button", { className: "primary-action", onClick: submit, disabled: submitting || !captureReady, children: [submitting
                                ? "Analyzing finger sequence..."
                                : captureReady
                                    ? "Submit three automatic captures"
                                    : "Stop recording first", " ", _jsx("span", { children: "->" })] })), !cameraAnalyzed &&
                        acceptedCaptures.length !== promptedNumbers.length && (_jsxs("button", { className: "primary-action", onClick: startCamera, children: ["Restart camera task ", _jsx("span", { children: "->" })] }))] }))] }));
}
