import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Link } from 'react-router-dom';
export default function Dashboard() {
    return (_jsxs("div", { children: [_jsx("h2", { children: "Dashboard" }), _jsxs("ul", { children: [_jsx("li", { children: _jsx(Link, { to: "/assessment/start", children: "Start new assessment" }) }), _jsx("li", { children: _jsx(Link, { to: "/reports", children: "Reports" }) }), _jsx("li", { children: _jsx(Link, { to: "/knowledge", children: "Knowledge base" }) })] })] }));
}
