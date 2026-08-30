import { jsx as _jsx } from "react/jsx-runtime";
import { createContext, useContext, useState, useEffect } from 'react';
import api, { setAuthToken } from '../api';
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
    useEffect(() => {
        if (!token) {
            setUser(null);
            return;
        }
        const load = async () => {
            try {
                const res = await api.get('/auth/me');
                setUser(res.data.user);
            }
            catch {
                setUser(null);
            }
        };
        load();
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
    const refreshUser = async () => {
        if (!token)
            return;
        try {
            const res = await api.get('/auth/me');
            setUser(res.data.user);
        }
        catch {
            setUser(null);
        }
    };
    return (_jsx(AuthContext.Provider, { value: { token, user, login, logout, refreshUser }, children: children }));
};
export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx)
        throw new Error('useAuth must be used inside AuthProvider');
    return ctx;
}
