import { jsx as _jsx } from "react/jsx-runtime";
import { createContext, useContext, useState, useEffect } from 'react';
import { setAuthToken } from '../api';
const AuthContext = createContext(undefined);
export const AuthProvider = ({ children }) => {
    const [token, setToken] = useState(localStorage.getItem('ns_token'));
    const [user, setUser] = useState(null);
    useEffect(() => {
        setAuthToken(token);
        if (token) {
            localStorage.setItem('ns_token', token);
        }
        else {
            localStorage.removeItem('ns_token');
        }
    }, [token]);
    const login = (t, u) => {
        setToken(t);
        if (u)
            setUser(u);
    };
    const logout = () => {
        setToken(null);
        setUser(null);
    };
    return (_jsx(AuthContext.Provider, { value: { token, user, login, logout }, children: children }));
};
export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx)
        throw new Error('useAuth must be used inside AuthProvider');
    return ctx;
}
