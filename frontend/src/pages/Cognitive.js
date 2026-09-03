import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import api from '../api';
import { useParams, useNavigate } from 'react-router-dom';
import { MEMORY_WORDS } from '../utils/constants';
export default function Cognitive() {
    const { id } = useParams();
    const [memoryWords, setMemoryWords] = useState(MEMORY_WORDS);
    const [story, setStory] = useState(null);
    const [storyQuestions, setStoryQuestions] = useState([]);
    const [storyQuestionIndex, setStoryQuestionIndex] = useState(0);
    const [storyAnswer, setStoryAnswer] = useState('');
    const [storyAnswers, setStoryAnswers] = useState([]);
    const [sessionNumber, setSessionNumber] = useState(1);
    const [stage, setStage] = useState('memory-display');
    const [timeLeft, setTimeLeft] = useState(10);
    const [recalled, setRecalled] = useState([]);
    const [currentRecall, setCurrentRecall] = useState('');
    const navigate = useNavigate();
    useEffect(() => {
        if (id)
            api.get(`/cognitive/session/${id}`).then(({ data }) => {
                if (Array.isArray(data.memory?.words) && data.memory.words.length === 6)
                    setMemoryWords(data.memory.words);
                if (data.story)
                    setStory(data.story);
                if (Array.isArray(data.story_questions))
                    setStoryQuestions(data.story_questions);
                if (data.session_number)
                    setSessionNumber(data.session_number);
            }).catch(() => { });
    }, [id]);
    // Timer for memory display
    useEffect(() => {
        if (stage === 'memory-display' && timeLeft > 0) {
            const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
            return () => clearTimeout(timer);
        }
        else if (stage === 'memory-display' && timeLeft === 0) {
            setStage('memory-test');
        }
    }, [timeLeft, stage]);
    const handleAddRecalledWord = () => {
        if (currentRecall.trim()) {
            setRecalled([...recalled, currentRecall.trim()]);
            setCurrentRecall('');
        }
    };
    const handleRemoveWord = (index) => {
        setRecalled(recalled.filter((_, i) => i !== index));
    };
    const handleMemoryTestComplete = () => {
        setStage(sessionNumber === 1 && story ? 'story' : storyQuestions.length ? 'story-questions' : 'complete');
    };
    const handleStoryQuestionSubmit = () => {
        if (!storyQuestions.length || storyQuestionIndex >= storyQuestions.length) {
            setStage('complete');
            return;
        }
        const answer = storyAnswer.trim();
        const updated = [...storyAnswers, answer];
        setStoryAnswers(updated);
        setStoryAnswer('');
        const nextIndex = storyQuestionIndex + 1;
        if (nextIndex < storyQuestions.length) {
            setStoryQuestionIndex(nextIndex);
            setStage('story-questions');
            return;
        }
        setStage('complete');
    };
    const submit = async () => {
        const payload = {
            recalled_words: recalled,
            attention_answer: '',
            visual_memory: {},
            pattern_recognition: [],
            orientation: {},
            story_answers: storyAnswers,
        };
        try {
            await api.post(`/cognitive/submit/${id}`, payload);
            navigate(`/assessment/speech/${id}`);
        }
        catch (err) {
            alert(err?.response?.data?.error || 'Failed');
        }
    };
    return (_jsxs("div", { style: { padding: '20px', maxWidth: '800px', margin: '0 auto' }, children: [_jsx("h2", { children: "Cognitive Tests" }), stage === 'memory-display' && (_jsxs("div", { style: {
                    padding: '30px',
                    backgroundColor: '#f0f8ff',
                    borderRadius: '8px',
                    textAlign: 'center',
                    marginBottom: '20px'
                }, children: [_jsx("h3", { children: "Memory Game - Read and Remember" }), _jsxs("p", { style: { fontSize: '18px', color: '#666', marginBottom: '20px' }, children: ["You have ", timeLeft, " seconds to memorize these words:"] }), _jsx("div", { style: {
                            display: 'grid',
                            gridTemplateColumns: 'repeat(2, 1fr)',
                            gap: '15px',
                            marginBottom: '20px'
                        }, children: memoryWords.map((word, idx) => (_jsx("div", { style: {
                                padding: '20px',
                                backgroundColor: '#4CAF50',
                                color: 'white',
                                borderRadius: '8px',
                                fontSize: '20px',
                                fontWeight: 'bold',
                                textTransform: 'uppercase'
                            }, children: word }, idx))) }), _jsxs("div", { style: { fontSize: '24px', fontWeight: 'bold', color: '#ff6b6b' }, children: ["\u23F1\uFE0F ", timeLeft, "s"] })] })), stage === 'memory-test' && (_jsxs("div", { style: {
                    padding: '20px',
                    backgroundColor: '#fff3cd',
                    borderRadius: '8px',
                    marginBottom: '20px'
                }, children: [_jsx("h3", { children: "Memory Test - Recall the Words" }), _jsx("p", { children: "How many words do you remember? Type them one by one and click \"Add Word\"." }), _jsxs("div", { style: { marginBottom: '15px' }, children: [_jsx("input", { type: "text", value: currentRecall, onChange: e => setCurrentRecall(e.target.value), onKeyPress: (e) => {
                                    if (e.key === 'Enter')
                                        handleAddRecalledWord();
                                }, placeholder: "Enter a word...", style: {
                                    width: '70%',
                                    padding: '10px',
                                    marginRight: '10px',
                                    borderRadius: '4px',
                                    border: '1px solid #ddd'
                                } }), _jsx("button", { onClick: handleAddRecalledWord, style: {
                                    padding: '10px 20px',
                                    backgroundColor: '#007bff',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    cursor: 'pointer'
                                }, children: "Add Word" })] }), _jsxs("div", { children: [_jsxs("h4", { children: ["Recalled Words (", recalled.length, "/", memoryWords.length, "):"] }), _jsx("div", { style: {
                                    display: 'flex',
                                    flexWrap: 'wrap',
                                    gap: '8px',
                                    marginBottom: '15px'
                                }, children: recalled.map((word, idx) => (_jsxs("div", { style: {
                                        padding: '8px 12px',
                                        backgroundColor: '#28a745',
                                        color: 'white',
                                        borderRadius: '20px',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '8px'
                                    }, children: [word, _jsx("button", { onClick: () => handleRemoveWord(idx), style: {
                                                background: 'none',
                                                border: 'none',
                                                color: 'white',
                                                cursor: 'pointer',
                                                fontSize: '16px'
                                            }, children: "\u2715" })] }, idx))) })] }), _jsx("button", { onClick: handleMemoryTestComplete, style: {
                            padding: '10px 20px',
                            backgroundColor: '#28a745',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '16px'
                        }, children: sessionNumber === 1 && story ? 'Continue to Story' : storyQuestions.length ? 'Continue to Story Questions' : 'Submit Cognitive Tests' })] })), stage === 'story' && sessionNumber === 1 && story && (_jsxs("div", { style: { padding: '20px', backgroundColor: '#f3e8ff', borderRadius: '8px', marginBottom: '20px' }, children: [_jsx("h3", { children: "Story Recall" }), _jsx("p", { style: { whiteSpace: 'pre-line', lineHeight: '1.8', fontSize: '16px' }, children: story.story }), _jsx("button", { onClick: () => setStage('complete'), style: {
                            padding: '10px 20px',
                            backgroundColor: '#7c3aed',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '16px'
                        }, children: "Submit Cognitive Tests" })] })), stage === 'story-questions' && sessionNumber > 1 && storyQuestions.length > 0 && (_jsxs("div", { style: { padding: '20px', backgroundColor: '#ecfeff', borderRadius: '8px', marginBottom: '20px' }, children: [_jsx("h3", { children: "Story Questions" }), _jsx("p", { style: { fontSize: '18px', marginBottom: '12px' }, children: storyQuestions[storyQuestionIndex].question }), _jsx("input", { value: storyAnswer, onChange: e => setStoryAnswer(e.target.value), placeholder: "Type your answer", style: {
                            width: '100%',
                            padding: '10px',
                            marginBottom: '15px',
                            borderRadius: '4px',
                            border: '1px solid #ddd'
                        } }), _jsx("button", { onClick: handleStoryQuestionSubmit, style: {
                            padding: '10px 20px',
                            backgroundColor: '#0ea5e9',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '16px'
                        }, children: storyQuestionIndex === storyQuestions.length - 1 ? 'Finish Story Questions' : 'Next Question' })] })), stage === 'complete' && (_jsx("div", { style: { marginBottom: '20px' }, children: _jsx("button", { onClick: submit, style: {
                        padding: '10px 20px',
                        backgroundColor: '#28a745',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '16px'
                    }, children: "Submit Cognitive Tests" }) }))] }));
}
