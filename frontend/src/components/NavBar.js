import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
export default function NavBar() {
    const { token, logout } = useAuth();
    const [darkMode, setDarkMode] = useState(() => localStorage.getItem('ns_theme') === 'dark');
    useEffect(() => {
        document.documentElement.dataset.theme = darkMode ? 'dark' : 'light';
        localStorage.setItem('ns_theme', darkMode ? 'dark' : 'light');
    }, [darkMode]);
    return (_jsxs("nav", { className: "site-nav", children: [_jsxs("div", { className: "nav-links", children: [_jsx(Link, { to: "/", className: "brand-mark", children: "NeuroSense" }), _jsx(Link, { to: "/knowledge", className: "nav-link", children: "About" })] }), _jsxs("div", { className: "nav-actions", children: [_jsx("button", { type: "button", className: "theme-toggle", onClick: () => setDarkMode(value => !value), "aria-label": darkMode ? 'Use light theme' : 'Use dark theme', title: darkMode ? 'Use light theme' : 'Use dark theme', children: darkMode ? 'Light' : 'Dark' }), token ? (_jsxs(_Fragment, { children: [_jsx(Link, { to: "/dashboard", className: "nav-link nav-link-strong", children: "Dashboard" }), _jsx(Link, { to: "/profile", className: "nav-link", children: "Profile" }), _jsx(Link, { to: "/reports", className: "nav-link", children: "Reports" }), _jsx("button", { onClick: logout, className: "nav-logout", children: "Logout" })] })) : (_jsxs(_Fragment, { children: [_jsx(Link, { to: "/login", className: "nav-link", children: "Login" }), _jsx(Link, { to: "/register", className: "nav-link nav-link-strong", children: "Register" })] }))] })] }));
}
