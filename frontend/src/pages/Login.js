import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import api from '../api';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
export default function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();
    const { login } = useAuth();
    const submit = async (e) => {
        e.preventDefault();
        setError('');
        try {
            const res = await api.post('/auth/login', { email, password });
            const token = res.data.access_token;
            login(token, res.data.user);
            navigate('/dashboard');
        }
        catch (err) {
            setError(err?.response?.data?.error || 'Login failed');
        }
    };
    return (_jsxs("div", { className: "auth-layout", children: [_jsxs("div", { className: "auth-copy", children: [_jsx("div", { className: "eyebrow", children: "A clearer picture of you" }), _jsxs("h1", { children: ["Understand your mind, ", _jsx("span", { className: "auth-accent", children: "gently." })] }), _jsx("p", { children: "NeuroSense brings together meaningful signals to help you notice patterns and make informed next steps." })] }), _jsxs("div", { className: "auth-card", children: [_jsx("h2", { children: "Welcome back" }), _jsxs("form", { onSubmit: submit, children: [_jsxs("div", { className: "form-field", children: [_jsx("label", { children: "Email" }), _jsx("input", { type: "email", value: email, onChange: e => setEmail(e.target.value) })] }), _jsxs("div", { className: "form-field", children: [_jsx("label", { children: "Password" }), _jsx("input", { type: "password", value: password, onChange: e => setPassword(e.target.value) })] }), error && _jsx("div", { className: "form-error", children: error }), _jsx("button", { className: "form-submit", type: "submit", children: "Login" })] })] })] }));
}
