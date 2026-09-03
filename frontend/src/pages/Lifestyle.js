import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import React, { useEffect, useState } from 'react';
import api from '../api';
import { useParams, useNavigate } from 'react-router-dom';
export default function Lifestyle() {
    const { id } = useParams();
    const [questions, setQuestions] = useState([]);
    const [answers, setAnswers] = useState({});
    const [concernAnswers, setConcernAnswers] = useState({});
    const [concernQuestions, setConcernQuestions] = useState([]);
    const [concernScale, setConcernScale] = useState([]);
    const [stage, setStage] = useState('lifestyle');
    const navigate = useNavigate();
    useEffect(() => {
        api.get('/lifestyle/questions').then(r => setQuestions(r.data.questions)).catch(() => { });
        api.get('/lifestyle/concern-questions').then(r => {
            setConcernQuestions(r.data.questions);
            setConcernScale(r.data.scale);
        }).catch(() => { });
    }, []);
    const handleLifestyleNext = () => {
        setStage('concerns');
    };
    const submit = async () => {
        try {
            await api.post(`/lifestyle/submit/${id}`, { answers, concern_answers: concernAnswers });
            navigate(`/assessment/cognitive/${id}`);
        }
        catch (err) {
            alert(err?.response?.data?.error || 'Failed');
        }
    };
    const getSliderLabel = (question, value) => {
        if (!value && value !== 0)
            return '';
        if (question.id === 'exercise_days')
            return `${value} days/week`;
        if (question.id === 'sleep_hours')
            return `${value} hours/night`;
        if (question.id === 'stress_level')
            return `${value}/10`;
        if (question.id === 'age')
            return `${value} years`;
        if (question.id === 'education_years')
            return `${value} years`;
        if (question.id === 'bmi')
            return `${value}`;
        if (question.id === 'medication_count')
            return `${value} medications`;
        return value;
    };
    return (_jsxs("div", { style: { padding: '20px', maxWidth: '900px', margin: '0 auto' }, children: [_jsx("h2", { children: "Lifestyle Assessment" }), stage === 'lifestyle' && (_jsxs("div", { children: [_jsx("h3", { children: "Lifestyle Questionnaire" }), _jsx("p", { style: { color: '#666', marginBottom: '20px' }, children: "Please answer the following questions about your lifestyle and health." }), questions.map((q, idx) => (_jsxs("div", { style: {
                            marginBottom: '25px',
                            padding: '15px',
                            backgroundColor: '#f9f9f9',
                            borderRadius: '8px',
                            borderLeft: '4px solid #007bff'
                        }, children: [_jsxs("label", { style: { fontWeight: 'bold', display: 'block', marginBottom: '10px' }, children: [idx + 1, ". ", q.text] }), q.type === 'radio' ? (_jsx("div", { style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '8px' }, children: q.options.map((option) => (_jsxs("label", { style: { display: 'flex', alignItems: 'center', gap: '8px' }, children: [_jsx("input", { type: "radio", name: q.id, value: option, checked: answers[q.id] === option, onChange: () => setAnswers({ ...answers, [q.id]: option }), style: { cursor: 'pointer' } }), _jsx("span", { children: option })] }, option))) })) : q.type === 'slider' ? (_jsxs("div", { children: [_jsx("input", { type: "range", min: q.min, max: q.max, value: answers[q.id] || q.min, onChange: (e) => setAnswers({ ...answers, [q.id]: parseFloat(e.target.value) }), style: {
                                            width: '100%',
                                            height: '6px',
                                            cursor: 'pointer',
                                            accentColor: '#007bff'
                                        } }), _jsxs("div", { style: {
                                            marginTop: '8px',
                                            display: 'flex',
                                            justifyContent: 'space-between',
                                            fontSize: '12px',
                                            color: '#666'
                                        }, children: [_jsx("span", { children: q.min }), _jsx("span", { style: { fontWeight: 'bold', color: '#007bff' }, children: getSliderLabel(q, answers[q.id]) }), _jsx("span", { children: q.max })] })] })) : q.type === 'number' ? (_jsx("input", { type: "number", value: answers[q.id] || '', onChange: (e) => setAnswers({ ...answers, [q.id]: e.target.value }), placeholder: `Enter ${q.text.toLowerCase()}`, style: {
                                    padding: '10px',
                                    borderRadius: '4px',
                                    border: '1px solid #ddd',
                                    width: '200px',
                                    fontSize: '14px'
                                } })) : (_jsx("input", { type: "text", value: answers[q.id] || '', onChange: (e) => setAnswers({ ...answers, [q.id]: e.target.value }), placeholder: `Enter ${q.text.toLowerCase()}`, style: {
                                    padding: '10px',
                                    borderRadius: '4px',
                                    border: '1px solid #ddd',
                                    width: '100%',
                                    fontSize: '14px'
                                } }))] }, q.id))), _jsx("button", { onClick: handleLifestyleNext, style: {
                            padding: '12px 30px',
                            backgroundColor: '#28a745',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '16px',
                            marginTop: '20px'
                        }, children: "Continue to Concerns Assessment" })] })), stage === 'concerns' && (_jsxs("div", { children: [_jsx("h3", { children: "Self-Reported Cognitive Concerns" }), _jsx("p", { style: { color: '#666', marginBottom: '20px' }, children: "Rate how often you experience each of the following:" }), _jsx("div", { style: { overflowX: 'auto', marginBottom: '20px' }, children: _jsxs("div", { style: {
                                display: 'grid',
                                gridTemplateColumns: `250px repeat(${concernScale.length}, 85px)`,
                                gap: '0',
                                minWidth: '100%'
                            }, children: [_jsx("div", { style: {
                                        padding: '12px',
                                        backgroundColor: '#007bff',
                                        color: 'white',
                                        fontWeight: 'bold',
                                        borderBottom: '2px solid #0d47a1',
                                        minHeight: '50px',
                                        display: 'flex',
                                        alignItems: 'center'
                                    }, children: "Concern" }), concernScale.map((scale) => (_jsx("div", { style: {
                                        padding: '12px',
                                        backgroundColor: '#007bff',
                                        color: 'white',
                                        fontWeight: 'bold',
                                        textAlign: 'center',
                                        fontSize: '12px',
                                        borderBottom: '2px solid #0d47a1',
                                        minHeight: '50px',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center'
                                    }, children: scale }, `header-${scale}`))), concernQuestions.map((q, qIdx) => (_jsxs(React.Fragment, { children: [_jsxs("div", { style: {
                                                padding: '12px',
                                                backgroundColor: qIdx % 2 === 0 ? '#f9f9f9' : '#fff',
                                                borderBottom: '1px solid #eee',
                                                fontWeight: '500',
                                                fontSize: '13px',
                                                display: 'flex',
                                                alignItems: 'center'
                                            }, children: [qIdx + 1, ". ", q.text] }), concernScale.map((scale) => (_jsx("div", { style: {
                                                padding: '12px',
                                                backgroundColor: qIdx % 2 === 0 ? '#f9f9f9' : '#fff',
                                                borderBottom: '1px solid #eee',
                                                display: 'flex',
                                                justifyContent: 'center',
                                                alignItems: 'center',
                                                minHeight: '50px'
                                            }, children: _jsx("label", { style: {
                                                    display: 'flex',
                                                    justifyContent: 'center',
                                                    alignItems: 'center',
                                                    cursor: 'pointer',
                                                    width: '100%'
                                                }, children: _jsx("input", { type: "radio", name: q.id, value: scale, checked: concernAnswers[q.id] === scale, onChange: () => setConcernAnswers({ ...concernAnswers, [q.id]: scale }), style: { cursor: 'pointer', width: '18px', height: '18px' } }) }) }, `${q.id}-${scale}`)))] }, q.id)))] }) }), _jsxs("div", { style: { display: 'flex', gap: '10px', marginTop: '20px' }, children: [_jsx("button", { onClick: () => setStage('lifestyle'), style: {
                                    padding: '12px 30px',
                                    backgroundColor: '#6c757d',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    cursor: 'pointer',
                                    fontSize: '16px'
                                }, children: "Back" }), _jsx("button", { onClick: submit, style: {
                                    padding: '12px 30px',
                                    backgroundColor: '#28a745',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    cursor: 'pointer',
                                    fontSize: '16px'
                                }, children: "Submit Assessment" })] })] }))] }));
}
