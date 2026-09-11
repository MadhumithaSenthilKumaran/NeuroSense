import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import api from '../api';
export default function Reports() {
    const [history, setHistory] = useState([]);
    const [finalReports, setFinalReports] = useState([]);
    const [loading, setLoading] = useState(false);
    useEffect(() => {
        api.get('/reports/history').then(r => { setHistory(r.data.history || []); setFinalReports(r.data.final_reports || []); }).catch(() => { });
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
    return (_jsxs("div", { className: "report-page", children: [_jsxs("div", { className: "page-intro", children: [_jsx("div", { className: "eyebrow", children: "Assessment archive" }), _jsx("h1", { children: "Reports and summaries" }), _jsx("p", { children: "Your screening reports, risk history, and recent insights are kept here for easy review." })] }), _jsxs("div", { className: "report-list", children: [finalReports.map(report => (_jsxs("div", { className: "report-card final-report-card", children: [_jsxs("div", { children: [_jsx("div", { className: "report-date", children: "Final three-session report" }), _jsxs("div", { className: "report-risk", children: [report.session_count, " sessions \u00B7 generated ", report.generated_at ? formatTimestamp(report.generated_at) : 'Unknown date'] })] }), _jsx("button", { className: "form-submit small", onClick: () => downloadReport(report.report_id, `NeuroSense_Final_Report_${report.cycle_id || report.report_id}.pdf`), disabled: loading, children: "Download PDF" })] }, report.report_id))), history.length === 0 && finalReports.length === 0 && _jsx("div", { className: "empty-state", children: "No completed assessments yet." }), history.map((h, idx) => (_jsxs("div", { className: "report-card", children: [_jsxs("div", { children: [_jsxs("div", { className: "report-date", children: [h.session_label || `Session ${h.session_number || '?'}`, " \u00B7 ", h.scheduled_for || 'Date unavailable'] }), _jsxs("div", { className: "report-risk", children: ["Risk: ", _jsx("strong", { children: h.risk_class || 'Pending' }), " (", h.risk_probability != null ? `${Math.round(Number(h.risk_probability) * 100)}%` : 'n/a', ")"] }), _jsxs("div", { className: "report-risk", children: ["Completed ", h.completed_at ? formatTimestamp(h.completed_at) : 'Unknown time'] })] }), _jsx("button", { className: "form-submit small", onClick: () => generate(h.assessment_id || h._id), disabled: loading, children: "Download PDF" })] }, idx)))] })] }));
}
async function downloadReport(reportId, filename) {
    const fileRes = await api.get(`/reports/download/${reportId}`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([fileRes.data], { type: 'application/pdf' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    window.URL.revokeObjectURL(url);
}
function formatTimestamp(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime()))
        return value;
    return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}
