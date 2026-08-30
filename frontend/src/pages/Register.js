import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import api from '../api';
import { useNavigate } from 'react-router-dom';
const emptyForm = {
    name: '',
    email: '',
    password: '',
    age: '',
    gender: '',
    phone: '',
    education: '',
    occupation: '',
    guardian_email: '',
    guardian_phone: '',
    consent_share: false,
};
export default function Register() {
    const [form, setForm] = useState(emptyForm);
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
    return (_jsxs("div", { className: "auth-layout", children: [_jsxs("div", { className: "auth-copy", children: [_jsx("div", { className: "eyebrow", children: "Begin your journey" }), _jsxs("h1", { children: ["Small steps, ", _jsx("span", { className: "auth-accent", children: "better insight." })] }), _jsx("p", { children: "Create a private NeuroSense account and build a personal picture of the signals that shape your wellbeing." })] }), _jsxs("div", { className: "auth-card auth-card-wide", children: [_jsx("h2", { children: "Create account" }), _jsxs("form", { onSubmit: submit, className: "auth-form-grid", children: [_jsxs("div", { className: "form-field", children: [_jsx("label", { children: "Name" }), _jsx("input", { value: form.name, onChange: e => setForm({ ...form, name: e.target.value }) })] }), _jsxs("div", { className: "form-field", children: [_jsx("label", { children: "Email" }), _jsx("input", { type: "email", value: form.email, onChange: e => setForm({ ...form, email: e.target.value }) })] }), _jsxs("div", { className: "form-field", children: [_jsx("label", { children: "Password" }), _jsx("input", { type: "password", value: form.password, onChange: e => setForm({ ...form, password: e.target.value }) })] }), _jsxs("div", { className: "form-field", children: [_jsx("label", { children: "Age" }), _jsx("input", { type: "number", value: form.age, onChange: e => setForm({ ...form, age: e.target.value }) })] }), _jsxs("div", { className: "form-field", children: [_jsx("label", { children: "Gender" }), _jsx("input", { value: form.gender, onChange: e => setForm({ ...form, gender: e.target.value }) })] }), _jsxs("div", { className: "form-field", children: [_jsx("label", { children: "Phone number" }), _jsx("input", { value: form.phone, onChange: e => setForm({ ...form, phone: e.target.value }) })] }), _jsxs("div", { className: "form-field", children: [_jsx("label", { children: "Education" }), _jsx("input", { value: form.education, onChange: e => setForm({ ...form, education: e.target.value }) })] }), _jsxs("div", { className: "form-field", children: [_jsx("label", { children: "Occupation" }), _jsx("input", { value: form.occupation, onChange: e => setForm({ ...form, occupation: e.target.value }) })] }), _jsxs("div", { className: "form-field", children: [_jsx("label", { children: "Guardian email" }), _jsx("input", { type: "email", value: form.guardian_email, onChange: e => setForm({ ...form, guardian_email: e.target.value }) })] }), _jsxs("div", { className: "form-field", children: [_jsx("label", { children: "Guardian phone" }), _jsx("input", { value: form.guardian_phone, onChange: e => setForm({ ...form, guardian_phone: e.target.value }) })] }), _jsxs("label", { className: "consent-box consent-box-inline", children: [_jsx("input", { type: "checkbox", checked: form.consent_share, onChange: e => setForm({ ...form, consent_share: e.target.checked }) }), "I consent to share assessment updates with my guardian."] }), error && _jsx("div", { className: "form-error", children: error }), _jsx("button", { className: "form-submit", type: "submit", children: "Register" })] })] })] }));
}
