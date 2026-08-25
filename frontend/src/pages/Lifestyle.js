import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import api from '../api';
import { useParams, useNavigate } from 'react-router-dom';
export default function Lifestyle() {
    const { id } = useParams();
    const [questions, setQuestions] = useState([]);
    const [answers, setAnswers] = useState({});
    const navigate = useNavigate();
    useEffect(() => {
        api.get('/lifestyle/questions').then(r => setQuestions(r.data.questions)).catch(() => { });
    }, []);
    const submit = async () => {
        try {
            await api.post(`/lifestyle/submit/${id}`, { answers });
            navigate(`/assessment/cognitive/${id}`);
        }
        catch (err) {
            alert(err?.response?.data?.error || 'Failed');
        }
    };
    return (_jsxs("div", { children: [_jsx("h2", { children: "Lifestyle Questionnaire" }), questions.map(q => (_jsxs("div", { style: { marginBottom: 10 }, children: [_jsx("label", { children: q.text }), q.type === 'radio' ? (q.options.map((o) => (_jsx("div", { children: _jsxs("label", { children: [_jsx("input", { type: "radio", name: q.id, onChange: () => setAnswers({ ...answers, [q.id]: o }) }), " ", o] }) }, o)))) : (_jsx("input", { value: answers[q.id] || '', onChange: e => setAnswers({ ...answers, [q.id]: e.target.value }) }))] }, q.id))), _jsx("button", { onClick: submit, children: "Submit" })] }));
}
