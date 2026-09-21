import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import api from '../api';
import { useAuth } from '../context/AuthContext';
export default function Profile() {
    const { user, refreshUser } = useAuth();
    const [form, setForm] = useState({
        name: '',
        age: '',
        gender: '',
        phone: '',
        education: '',
        occupation: '',
        guardian_email: '',
        guardian_phone: '',
        consent_share: false,
        email_notifications: true,
    });
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState('');
    useEffect(() => {
        if (!user)
            return;
        setForm({
            name: user.name || '',
            age: user.age ?? '',
            gender: user.gender || '',
            phone: user.phone || '',
            education: user.education || '',
            occupation: user.occupation || '',
            guardian_email: user.guardian_email || '',
            guardian_phone: user.guardian_phone || '',
            consent_share: !!user.consent_share,
            email_notifications: user.email_notifications !== false,
        });
    }, [user]);
    const save = async () => {
        setSaving(true);
        setMessage('');
        try {
            await api.put('/auth/me', form);
            await refreshUser();
            setMessage('Profile saved successfully.');
        }
        catch (err) {
            setMessage(err?.response?.data?.error || 'Unable to save profile.');
        }
        finally {
            setSaving(false);
        }
    };
    return (_jsxs("div", { className: "profile-page", children: [_jsxs("div", { className: "page-intro", children: [_jsx("div", { className: "eyebrow", children: "Your profile" }), _jsx("h1", { children: "Personal details" }), _jsx("p", { children: "Keep your contact information current so your assessment updates and guardian alerts can reach the right people." })] }), _jsxs("div", { className: "profile-panel", children: [_jsxs("div", { className: "profile-grid", children: [_jsxs("div", { className: "form-field", children: [_jsx("label", { children: "Name" }), _jsx("input", { value: form.name, onChange: e => setForm({ ...form, name: e.target.value }) })] }), _jsxs("div", { className: "form-field", children: [_jsx("label", { children: "Email" }), _jsx("input", { value: user?.email || '', readOnly: true })] }), _jsxs("div", { className: "form-field", children: [_jsx("label", { children: "Age" }), _jsx("input", { type: "number", value: form.age, onChange: e => setForm({ ...form, age: e.target.value }) })] }), _jsxs("div", { className: "form-field", children: [_jsx("label", { htmlFor: "profile-gender", children: "Gender" }), _jsxs("select", { id: "profile-gender", value: form.gender, onChange: e => setForm({ ...form, gender: e.target.value }), children: [_jsx("option", { value: "", children: "Select gender" }), _jsx("option", { value: "Female", children: "Female" }), _jsx("option", { value: "Male", children: "Male" }), _jsx("option", { value: "Non-binary", children: "Non-binary" }), _jsx("option", { value: "Prefer not to say", children: "Prefer not to say" })] })] }), _jsxs("div", { className: "form-field", children: [_jsx("label", { children: "Phone number" }), _jsx("input", { value: form.phone, onChange: e => setForm({ ...form, phone: e.target.value }) })] }), _jsxs("div", { className: "form-field", children: [_jsx("label", { children: "Education" }), _jsx("input", { value: form.education, onChange: e => setForm({ ...form, education: e.target.value }) })] }), _jsxs("div", { className: "form-field", children: [_jsx("label", { children: "Occupation" }), _jsx("input", { value: form.occupation, onChange: e => setForm({ ...form, occupation: e.target.value }) })] }), _jsxs("div", { className: "form-field", children: [_jsx("label", { children: "Guardian email" }), _jsx("input", { type: "email", value: form.guardian_email, onChange: e => setForm({ ...form, guardian_email: e.target.value }) })] }), _jsxs("div", { className: "form-field", children: [_jsx("label", { children: "Guardian phone" }), _jsx("input", { value: form.guardian_phone, onChange: e => setForm({ ...form, guardian_phone: e.target.value }) })] })] }), _jsxs("section", { className: "notification-preferences", children: [_jsx("h2", { children: "Notification Preferences" }), _jsxs("label", { className: "consent-box", children: [_jsx("input", { type: "checkbox", checked: form.email_notifications, onChange: e => setForm({ ...form, email_notifications: e.target.checked }) }), "Email Notifications"] }), _jsxs("p", { className: "profile-note", children: ["Email: ", user?.email || 'Not available'] })] }), _jsxs("label", { className: "consent-box", children: [_jsx("input", { type: "checkbox", checked: form.consent_share, onChange: e => setForm({ ...form, consent_share: e.target.checked }) }), "I consent to share my assessment reports with my guardian by email."] }), _jsx("button", { className: "form-submit", onClick: save, disabled: saving, children: saving ? 'Saving...' : 'Save profile' }), message && _jsx("div", { className: "form-message", children: message })] })] }));
}
