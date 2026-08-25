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
    return (_jsxs("div", { style: { maxWidth: 480 }, children: [_jsx("h2", { children: "Login" }), _jsxs("form", { onSubmit: submit, children: [_jsxs("div", { children: [_jsx("label", { children: "Email" }), _jsx("input", { value: email, onChange: e => setEmail(e.target.value) })] }), _jsxs("div", { children: [_jsx("label", { children: "Password" }), _jsx("input", { type: "password", value: password, onChange: e => setPassword(e.target.value) })] }), error && _jsx("div", { style: { color: 'red' }, children: error }), _jsx("button", { type: "submit", children: "Login" })] })] }));
}
