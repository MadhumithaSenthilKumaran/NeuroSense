import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import StartAssessment from './pages/StartAssessment';
import Lifestyle from './pages/Lifestyle';
import Cognitive from './pages/Cognitive';
import SpeechUpload from './pages/SpeechUpload';
import Finalize from './pages/Finalize';
import Reports from './pages/Reports';
import Knowledge from './pages/Knowledge';
import Health from './pages/Health';
import AdminDashboard from './pages/AdminDashboard';
import NavBar from './components/NavBar';
import { AuthProvider, useAuth } from './context/AuthContext';
function PrivateRoute({ children }) {
    const { token } = useAuth();
    return token ? children : _jsx(Navigate, { to: "/login" });
}
export default function App() {
    return (_jsxs(AuthProvider, { children: [_jsx(NavBar, {}), _jsx("main", { style: { padding: 20 }, children: _jsxs(Routes, { children: [_jsx(Route, { path: "/", element: _jsx(Navigate, { to: "/dashboard", replace: true }) }), _jsx(Route, { path: "/health", element: _jsx(Health, {}) }), _jsx(Route, { path: "/knowledge", element: _jsx(Knowledge, {}) }), _jsx(Route, { path: "/login", element: _jsx(Login, {}) }), _jsx(Route, { path: "/register", element: _jsx(Register, {}) }), _jsx(Route, { path: "/dashboard", element: _jsx(PrivateRoute, { children: _jsx(Dashboard, {}) }) }), _jsx(Route, { path: "/assessment/start", element: _jsx(PrivateRoute, { children: _jsx(StartAssessment, {}) }) }), _jsx(Route, { path: "/assessment/lifestyle/:id", element: _jsx(PrivateRoute, { children: _jsx(Lifestyle, {}) }) }), _jsx(Route, { path: "/assessment/cognitive/:id", element: _jsx(PrivateRoute, { children: _jsx(Cognitive, {}) }) }), _jsx(Route, { path: "/assessment/speech/:id", element: _jsx(PrivateRoute, { children: _jsx(SpeechUpload, {}) }) }), _jsx(Route, { path: "/assessment/finalize/:id", element: _jsx(PrivateRoute, { children: _jsx(Finalize, {}) }) }), _jsx(Route, { path: "/reports", element: _jsx(PrivateRoute, { children: _jsx(Reports, {}) }) }), _jsx(Route, { path: "/admin/dashboard", element: _jsx(PrivateRoute, { children: _jsx(AdminDashboard, {}) }) })] }) })] }));
}
