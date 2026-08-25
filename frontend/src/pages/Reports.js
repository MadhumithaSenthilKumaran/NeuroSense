import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import api from '../api';
export default function Reports() {
    const [history, setHistory] = useState([]);
    useEffect(() => {
        api.get('/reports/history').then(r => setHistory(r.data.history)).catch(() => { });
    }, []);
    const generate = async (assessment_id) => {
        try {
            const res = await api.post(`/reports/generate/${assessment_id}`);
            alert('Report generation started; use download link from response or history');
        }
        catch (err) {
            alert(err?.response?.data?.error || 'Failed');
        }
    };
    return (_jsxs("div", { children: [_jsx("h2", { children: "Reports / History" }), _jsxs("div", { children: [history.length === 0 && _jsx("div", { children: "No completed assessments yet." }), history.map((h, idx) => (_jsxs("div", { style: { border: '1px solid #eee', padding: 10, marginBottom: 8 }, children: [_jsxs("div", { children: ["Date: ", h.date] }), _jsxs("div", { children: ["Risk: ", h.risk_class, " (", h.risk_probability, ")"] })] }, idx)))] })] }));
}
