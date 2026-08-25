import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import api from '../api';
import { useNavigate } from 'react-router-dom';
export default function StartAssessment() {
    const navigate = useNavigate();
    const start = async () => {
        try {
            const res = await api.post('/assessment/start');
            const id = res.data.assessment._id;
            navigate(`/assessment/lifestyle/${id}`);
        }
        catch (err) {
            alert(err?.response?.data?.error || 'Failed to start');
        }
    };
    return (_jsxs("div", { children: [_jsx("h2", { children: "Start Assessment" }), _jsx("p", { children: "This will create a new assessment and take you through the modules." }), _jsx("button", { onClick: start, children: "Start" })] }));
}
