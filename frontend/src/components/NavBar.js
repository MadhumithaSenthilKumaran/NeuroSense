import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
export default function NavBar() {
    const { token, logout } = useAuth();
    return (_jsxs("nav", { className: "flex items-center justify-between px-4 py-3 bg-white shadow-sm", children: [_jsxs("div", { className: "space-x-4", children: [_jsx(Link, { to: "/", className: "font-semibold", children: "NeuroSense" }), _jsx(Link, { to: "/knowledge", className: "text-sm text-gray-600", children: "About" }), _jsx(Link, { to: "/health", className: "text-sm text-gray-600", children: "Health" })] }), _jsx("div", { children: token ? (_jsxs("div", { className: "space-x-3", children: [_jsx(Link, { to: "/dashboard", className: "text-sm", children: "Dashboard" }), _jsx(Link, { to: "/admin/dashboard", className: "text-sm", children: "Admin" }), _jsx("a", { href: "#", onClick: (e) => { e.preventDefault(); logout(); }, className: "text-sm text-red-600", children: "Logout" })] })) : (_jsxs("div", { className: "space-x-3", children: [_jsx(Link, { to: "/login", className: "text-sm", children: "Login" }), _jsx(Link, { to: "/register", className: "text-sm", children: "Register" })] })) })] }));
}
