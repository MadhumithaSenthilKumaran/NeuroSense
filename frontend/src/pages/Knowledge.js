import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import api from '../api';
export default function Knowledge() {
    const [articles, setArticles] = useState([]);
    useEffect(() => {
        api.get('/knowledge/articles').then(r => setArticles(r.data.articles)).catch(() => { });
    }, []);
    return (_jsxs("div", { children: [_jsx("h2", { children: "Knowledge base" }), articles.map(a => (_jsxs("div", { style: { border: '1px solid #eee', padding: 10, marginBottom: 8 }, children: [_jsx("h3", { children: a.title }), _jsx("div", { children: a.summary }), _jsxs("div", { style: { fontSize: 12, color: '#666' }, children: ["Source: ", a.source] })] }, a.title)))] }));
}
