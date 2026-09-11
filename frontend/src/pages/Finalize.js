import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import api from '../api';
import { useNavigate, useParams } from 'react-router-dom';
export default function Finalize() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [nextLoading, setNextLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const run = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await api.post(`/assessment/${id}/finalize`);
            setResult(res.data.assessment);
        }
        catch (err) {
            setError(err?.response?.data?.error || err?.response?.data?.msg || 'Failed to finalize');
        }
        finally {
            setLoading(false);
        }
    };
    const startNextSession = async () => {
        setNextLoading(true);
        try {
            const res = await api.post(`/assessment/${id}/next`);
            navigate(`/assessment/lifestyle/${res.data.assessment._id}`);
        }
        catch (err) {
            setError(err?.response?.data?.error || 'The next session is not available yet');
        }
        finally {
            setNextLoading(false);
        }
    };
    return (_jsxs("div", { className: "space-y-4", children: [_jsx("h2", { className: "text-2xl font-medium", children: "Finalize Assessment" }), _jsx("p", { children: "When you finalize, the system will fuse available modalities and produce recommendations." }), _jsx("div", { children: _jsx("button", { className: "form-submit", onClick: run, disabled: loading, children: loading ? 'Processing...' : 'Finalize' }) }), error && _jsx("div", { className: "text-red-600", children: error }), result && (_jsxs("div", { className: "finalize-result", children: [_jsxs("div", { className: "result-summary", children: [_jsxs("div", { children: [_jsx("span", { children: "Overall risk" }), _jsx("strong", { children: result.risk_class || 'Not available' }), _jsx("small", { children: formatProbability(result.risk_probability) })] }), _jsxs("div", { children: [_jsx("span", { children: "Modalities used" }), _jsx("strong", { children: result.used_modalities?.length || 0 }), _jsx("small", { children: result.used_modalities?.join(', ') || 'None recorded' })] }), _jsxs("div", { children: [_jsx("span", { children: "Next session date" }), _jsx("strong", { children: result.next_session_date || 'Final session' }), _jsx("small", { children: result.next_session_date ? 'Available on this date' : 'Final session complete' })] })] }), _jsxs("div", { className: "score-visuals", children: [_jsx(ScoreBars, { result: result }), _jsx(ModalityChart, { scores: result.modality_scores })] }), result.next_session_date && (_jsx("button", { className: "form-submit next-session", onClick: startNextSession, disabled: nextLoading, children: nextLoading ? 'Checking date...' : 'Start next session' })), result.next_assessment_suggestion && (_jsxs("div", { className: "assessment-suggestion", children: [_jsx("strong", { children: "Next assessment suggestion" }), _jsx("span", { children: result.next_assessment_suggestion })] })), _jsxs("div", { className: "recommendation-panel", children: [_jsx("h3", { children: "Recommended focus" }), _jsx("p", { children: result.recommendations?.summary || 'Use these focus areas to guide your next steps.' }), _jsxs("div", { className: "recommendation-grid", children: [_jsx(RecommendationList, { title: "Personalized action plan", items: result.recommendations?.personalized_action_plan }), _jsx(RecommendationList, { title: "Recommended exercises", items: result.recommendations?.exercise_recommendations }), _jsx(RecommendationList, { title: "Sleep", items: result.recommendations?.sleep_recommendations }), _jsx(RecommendationList, { title: "Diet", items: result.recommendations?.diet_suggestions }), _jsx(RecommendationList, { title: "Memory strategies", items: result.recommendations?.memory_improvement_tips }), _jsx(RecommendationList, { title: "Stress reduction", items: result.recommendations?.stress_reduction_recommendations }), _jsx(RecommendationList, { title: "Clinical follow-up", items: result.recommendations?.medical_consultation_guidance })] }), result.recommendations?.disclaimer && _jsx("div", { className: "recommendation-disclaimer", children: result.recommendations.disclaimer })] })] }))] }));
}
function RecommendationList({ title, items }) {
    if (!items?.length)
        return null;
    return _jsxs("div", { className: "recommendation-item", children: [_jsx("strong", { children: title }), _jsx("span", { children: items[0] }), _jsxs("small", { children: [items.length, " suggestion", items.length === 1 ? '' : 's'] })] });
}
function formatProbability(value) {
    return value == null ? 'Not available' : `${Math.round(Number(value) * 100)}%`;
}
function formatTimestamp(value, includeTime = false) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime()))
        return value;
    return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', ...(includeTime ? { timeStyle: 'short' } : {}) }).format(date);
}
function ScoreBars({ result }) {
    const scores = [
        ['Lifestyle', result.lifestyle_score],
        ['Clinical concern', result.clinical_concern_score],
        ['Cognitive', result.cognitive_result?.overall_cognitive_score],
        ['Speech risk', result.modality_scores?.speech == null ? null : Number(result.modality_scores.speech) * 100],
    ];
    return _jsxs("section", { className: "visual-card", children: [_jsxs("div", { className: "visual-heading", children: [_jsx("h3", { children: "Assessment profile" }), _jsx("span", { children: "0 to 100" })] }), scores.map(([label, value]) => _jsxs("div", { className: "score-bar", children: [_jsxs("div", { children: [_jsx("span", { children: label }), _jsx("strong", { children: value == null ? 'N/A' : `${Math.round(Number(value))}%` })] }), _jsx("div", { className: "bar-track", children: _jsx("i", { style: { width: `${Math.min(100, Math.max(0, Number(value) || 0))}%` } }) })] }, label))] });
}
function ModalityChart({ scores }) {
    const entries = Object.entries(scores || {}).filter(([, value]) => value != null);
    if (!entries.length)
        return null;
    return _jsxs("section", { className: "visual-card modality-card", children: [_jsxs("div", { className: "visual-heading", children: [_jsx("h3", { children: "Modality signals" }), _jsx("span", { children: "Risk probability" })] }), _jsx("div", { className: "modality-chart", children: entries.map(([label, value]) => _jsxs("div", { className: "modality-column", children: [_jsxs("div", { className: "column-value", children: [Math.round(Number(value) * 100), "%"] }), _jsx("div", { className: "column-track", children: _jsx("i", { style: { height: `${Math.min(100, Math.max(0, Number(value) * 100))}%` } }) }), _jsx("span", { children: label })] }, label)) })] });
}
