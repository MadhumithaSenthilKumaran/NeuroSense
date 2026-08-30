import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import api from '../api';
import { useParams } from 'react-router-dom';
export default function Finalize() {
    const { id } = useParams();
    const [loading, setLoading] = useState(false);
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
    return (_jsxs("div", { className: "space-y-4", children: [_jsx("h2", { className: "text-2xl font-medium", children: "Finalize Assessment" }), _jsx("p", { children: "When you finalize, the system will fuse available modalities and produce recommendations." }), _jsx("div", { children: _jsx("button", { className: "px-4 py-2 bg-indigo-600 text-white rounded", onClick: run, disabled: loading, children: loading ? 'Processing...' : 'Finalize' }) }), error && _jsx("div", { className: "text-red-600", children: error }), result && (_jsxs("div", { className: "p-4 border rounded", children: [_jsxs("div", { className: "mb-2", children: ["Risk: ", _jsx("strong", { children: result.risk_class }), " (", result.risk_probability, ")"] }), _jsxs("div", { className: "mb-2", children: ["Used modalities: ", result.used_modalities?.join(', ')] }), _jsx("div", { className: "mb-2", children: "Modality scores:" }), _jsx("pre", { className: "bg-gray-100 p-2 rounded", children: JSON.stringify(result.modality_scores, null, 2) }), _jsxs("div", { className: "mt-2", children: [_jsx("h4", { className: "font-medium", children: "Recommendations" }), _jsxs("div", { className: "mt-1", children: [result.recommendations?.summary ? (_jsx("div", { children: result.recommendations.summary })) : null, result.recommendations?.explanation && _jsx("div", { className: "mt-2 text-sm text-gray-700", children: result.recommendations.explanation })] })] })] }))] }));
}
