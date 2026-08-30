import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
export default function NavBar() {
    const { token, logout } = useAuth();
    return (_jsxs("nav", { className: "site-nav", children: [_jsxs("div", { className: "nav-links", children: [_jsx(Link, { to: "/", className: "brand-mark", children: "NeuroSense" }), _jsx(Link, { to: "/knowledge", className: "nav-link", children: "About" }), _jsx(Link, { to: "/health", className: "nav-link", children: "Health" })] }), _jsx("div", { className: "nav-actions", children: token ? (_jsxs(_Fragment, { children: [_jsx(Link, { to: "/dashboard", className: "nav-link nav-link-strong", children: "Dashboard" }), _jsx(Link, { to: "/profile", className: "nav-link", children: "Profile" }), _jsx(Link, { to: "/reports", className: "nav-link", children: "Reports" }), _jsx(Link, { to: "/admin/dashboard", className: "nav-link", children: "Admin" }), _jsx("button", { onClick: logout, className: "nav-logout", children: "Logout" })] })) : (_jsxs(_Fragment, { children: [_jsx(Link, { to: "/login", className: "nav-link", children: "Login" }), _jsx(Link, { to: "/register", className: "nav-link nav-link-strong", children: "Register" })] })) })] }));
}
