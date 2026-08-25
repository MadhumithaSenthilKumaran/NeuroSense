import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import api from '../api';
export default function AdminDashboard() {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);
    useEffect(() => {
        api.get('/admin/dashboard').then(r => setData(r.data)).catch((err) => {
            if (err?.response?.status === 403)
                setError('Access denied (admin only)');
            else
                setError(err?.response?.data?.error || 'Failed to load');
        });
    }, []);
    if (error)
        return _jsx("div", { className: "text-red-600", children: error });
    if (!data)
        return _jsx("div", { children: "Loading..." });
    return (_jsxs("div", { children: [_jsx("h2", { className: "text-2xl font-medium", children: "Admin Dashboard" }), _jsxs("div", { className: "grid grid-cols-3 gap-4 mt-4", children: [_jsxs("div", { className: "p-4 border rounded", children: ["Users", _jsx("br", {}), _jsx("strong", { className: "text-xl", children: data.total_users })] }), _jsxs("div", { className: "p-4 border rounded", children: ["Assessments", _jsx("br", {}), _jsx("strong", { className: "text-xl", children: data.total_assessments })] }), _jsxs("div", { className: "p-4 border rounded", children: ["Completed", _jsx("br", {}), _jsx("strong", { className: "text-xl", children: data.completed_assessments })] })] }), _jsxs("div", { className: "mt-6", children: [_jsx("h3", { className: "font-medium", children: "Risk breakdown" }), _jsx("div", { className: "mt-2", children: data.risk_breakdown && Object.keys(data.risk_breakdown).length > 0 ? (_jsxs("table", { className: "w-full text-left border-collapse", children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "Class" }), _jsx("th", { children: "Count" })] }) }), _jsx("tbody", { children: Object.entries(data.risk_breakdown).map(([k, v]) => (_jsxs("tr", { className: "border-t", children: [_jsx("td", { className: "py-2", children: k }), _jsx("td", { className: "py-2", children: v })] }, k))) })] })) : (_jsx("div", { children: "No completed assessments yet." })) })] })] }));
}
