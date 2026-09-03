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
    return (_jsxs("div", { className: "space-y-4", children: [_jsx("h2", { className: "text-2xl font-medium", children: "Finalize Assessment" }), _jsx("p", { children: "When you finalize, the system will fuse available modalities and produce recommendations." }), _jsx("div", { children: _jsx("button", { className: "px-4 py-2 bg-indigo-600 text-white rounded", onClick: run, disabled: loading, children: loading ? 'Processing...' : 'Finalize' }) }), error && _jsx("div", { className: "text-red-600", children: error }), result && (_jsxs("div", { className: "p-4 border rounded", children: [_jsxs("div", { className: "mb-2", children: ["Risk: ", _jsx("strong", { children: result.risk_class }), " (", result.risk_probability, ")"] }), _jsxs("div", { className: "mb-2", children: ["Used modalities: ", result.used_modalities?.join(', ')] }), _jsxs("div", { className: "mb-2", children: [_jsx("strong", { children: "Lifestyle score:" }), " ", result.lifestyle_score ?? 'Not available', " / 100"] }), _jsxs("div", { className: "mb-2", children: [_jsx("strong", { children: "Lifestyle risk probability:" }), " ", formatProbability(result.lifestyle_probability)] }), _jsxs("div", { className: "mb-2", children: [_jsx("strong", { children: "Clinical concern score:" }), " ", result.clinical_concern_score ?? 'Not available', " / 100"] }), _jsxs("div", { className: "mb-2", children: [_jsx("strong", { children: "Cognitive score:" }), " ", result.cognitive_result?.overall_cognitive_score ?? 'Not available', " / 100"] }), _jsxs("div", { className: "mb-2", children: [_jsx("strong", { children: "Speech risk probability:" }), " ", formatProbability(result.modality_scores?.speech)] }), _jsxs("div", { className: "mb-2", children: [_jsx("strong", { children: "Next scheduled session:" }), " ", result.next_session_date || 'This is the final session'] }), result.next_session_date && (_jsx("button", { className: "px-4 py-2 bg-emerald-600 text-white rounded", onClick: startNextSession, disabled: nextLoading, children: nextLoading ? 'Checking date...' : 'Start next session' })), _jsx("div", { className: "mb-2", children: "Integrated modality scores:" }), _jsx("pre", { className: "bg-gray-100 p-2 rounded", children: JSON.stringify(result.modality_scores, null, 2) }), result.next_assessment_suggestion && (_jsxs("div", { className: "mt-3 p-3 rounded bg-amber-50 border border-amber-200 text-amber-900", children: [_jsx("strong", { children: "Next assessment suggestion:" }), " ", result.next_assessment_suggestion] })), _jsxs("div", { className: "mt-2", children: [_jsx("h4", { className: "font-medium", children: "Recommendations" }), _jsxs("div", { className: "mt-1", children: [result.recommendations?.summary ? (_jsx("div", { children: result.recommendations.summary })) : null, result.recommendations?.explanation && _jsx("div", { className: "mt-2 text-sm text-gray-700", children: result.recommendations.explanation })] })] })] }))] }));
}
function formatProbability(value) {
    return value == null ? 'Not available' : `${Math.round(Number(value) * 100)}%`;
}
