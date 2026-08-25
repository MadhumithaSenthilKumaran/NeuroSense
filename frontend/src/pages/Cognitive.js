import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import api from '../api';
import { useParams, useNavigate } from 'react-router-dom';
import { MEMORY_WORDS } from '../utils/constants';
export default function Cognitive() {
    const { id } = useParams();
    const [recalled, setRecalled] = useState('');
    const [reaction, setReaction] = useState('');
    const navigate = useNavigate();
    const submit = async () => {
        const payload = {
            recalled_words: recalled.split(',').map(s => s.trim()),
            reaction_times_ms: reaction.split(',').map(s => parseFloat(s.trim())).filter(Boolean),
            attention_answer: '',
            visual_memory: {},
            pattern_recognition: [],
            orientation: {},
        };
        try {
            await api.post(`/cognitive/submit/${id}`, payload);
            navigate(`/assessment/speech/${id}`);
        }
        catch (err) {
            alert(err?.response?.data?.error || 'Failed');
        }
    };
    return (_jsxs("div", { children: [_jsx("h2", { children: "Cognitive Tests" }), _jsxs("div", { children: [_jsx("h4", { children: "Memory words (read, then enter recalled words comma-separated)" }), _jsx("div", { children: MEMORY_WORDS.join(', ') }), _jsx("input", { value: recalled, onChange: e => setRecalled(e.target.value) })] }), _jsxs("div", { children: [_jsx("h4", { children: "Reaction times (ms) - comma separated" }), _jsx("input", { value: reaction, onChange: e => setReaction(e.target.value) })] }), _jsx("button", { onClick: submit, children: "Submit cognitive" })] }));
}
