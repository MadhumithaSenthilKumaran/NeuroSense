import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import api from '../api';
import { useNavigate } from 'react-router-dom';
export default function StartAssessment() {
    const navigate = useNavigate();
    const [schedule, setSchedule] = useState([]);
    const [loading, setLoading] = useState(false);
    const start = async () => {
        setLoading(true);
        try {
            const res = await api.post('/assessment/start');
            const id = res.data.assessment._id;
            setSchedule(res.data.assessment.cycle_schedule || []);
            navigate(`/assessment/lifestyle/${id}`);
        }
        catch (err) {
            alert(err?.response?.data?.error || 'Failed to start');
        }
        finally {
            setLoading(false);
        }
    };
    return (_jsxs("div", { children: [_jsx("h2", { children: "Start Assessment" }), _jsx("p", { children: "This will create the first session. The follow-up sessions are available only on their scheduled dates." }), _jsx("button", { onClick: start, disabled: loading, children: loading ? 'Starting...' : 'Start Session 1' }), schedule.length > 0 && _jsx("ul", { children: schedule.map(item => _jsxs("li", { children: ["Session ", item.session_number, ": ", item.scheduled_for] }, item.session_number)) })] }));
}
