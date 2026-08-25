import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import api from '../api';
import { useNavigate } from 'react-router-dom';
export default function Register() {
    const [form, setForm] = useState({ name: '', email: '', password: '' });
    const [error, setError] = useState('');
    const navigate = useNavigate();
    const submit = async (e) => {
        e.preventDefault();
        setError('');
        try {
            await api.post('/auth/register', form);
            navigate('/login');
        }
        catch (err) {
            setError(err?.response?.data?.error || 'Registration failed');
        }
    };
    return (_jsxs("div", { style: { maxWidth: 480 }, children: [_jsx("h2", { children: "Register" }), _jsxs("form", { onSubmit: submit, children: [_jsxs("div", { children: [_jsx("label", { children: "Name" }), _jsx("input", { value: form.name, onChange: e => setForm({ ...form, name: e.target.value }) })] }), _jsxs("div", { children: [_jsx("label", { children: "Email" }), _jsx("input", { value: form.email, onChange: e => setForm({ ...form, email: e.target.value }) })] }), _jsxs("div", { children: [_jsx("label", { children: "Password" }), _jsx("input", { type: "password", value: form.password, onChange: e => setForm({ ...form, password: e.target.value }) })] }), error && _jsx("div", { style: { color: 'red' }, children: error }), _jsx("button", { type: "submit", children: "Register" })] })] }));
}
