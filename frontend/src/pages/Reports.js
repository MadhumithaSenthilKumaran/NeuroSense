import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import api from '../api';
export default function Reports() {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(false);
    useEffect(() => {
        api.get('/reports/history').then(r => setHistory(r.data.history)).catch(() => { });
    }, []);
    const generate = async (assessment_id) => {
        setLoading(true);
        try {
            console.log('Generating report for assessment:', assessment_id);
            const res = await api.post(`/reports/generate/${assessment_id}`);
            console.log('Generate response:', res.data);
            if (!res.data.download_url) {
                alert('Failed to generate report: No download URL returned');
                return;
            }
            // Remove /api prefix if it exists in download_url since axios already has it as baseURL
            let downloadUrl = res.data.download_url;
            if (downloadUrl.startsWith('/api/')) {
                downloadUrl = downloadUrl.substring(4); // Remove '/api' prefix
            }
            const fileRes = await api.get(downloadUrl, {
                responseType: 'blob',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('ns_token')}` }
            });
            if (!fileRes.data || fileRes.data.size === 0) {
                alert('Failed to download report: Empty file received');
                return;
            }
            const blob = new Blob([fileRes.data], { type: 'application/pdf' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `NeuroSense_Report_${assessment_id}.pdf`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
            alert('Report downloaded successfully!');
        }
        catch (err) {
            console.error('Report generation error:', err);
            const errorMsg = err?.response?.data?.error || err?.message || 'Failed to generate or download report';
            alert(errorMsg);
        }
        finally {
            setLoading(false);
        }
    };
    return (_jsxs("div", { className: "report-page", children: [_jsxs("div", { className: "page-intro", children: [_jsx("div", { className: "eyebrow", children: "Assessment archive" }), _jsx("h1", { children: "Reports and summaries" }), _jsx("p", { children: "Your screening reports, risk history, and recent insights are kept here for easy review." })] }), _jsxs("div", { className: "report-list", children: [history.length === 0 && _jsx("div", { className: "empty-state", children: "No completed assessments yet." }), history.map((h, idx) => (_jsxs("div", { className: "report-card", children: [_jsxs("div", { children: [_jsx("div", { className: "report-date", children: h.date ? new Date(h.date).toLocaleString() : 'Unknown date' }), _jsxs("div", { className: "report-risk", children: ["Risk: ", _jsx("strong", { children: h.risk_class || 'Pending' }), " (", h.risk_probability != null ? `${Math.round(Number(h.risk_probability) * 100)}%` : 'n/a', ")"] })] }), _jsx("button", { className: "form-submit small", onClick: () => generate(h.assessment_id || h._id), disabled: loading, children: "Download PDF" })] }, idx)))] })] }));
}
