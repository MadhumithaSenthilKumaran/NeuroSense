import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import api from '../api';
export default function Knowledge() {
    const [articles, setArticles] = useState([]);
    useEffect(() => {
        api.get('/knowledge/articles').then(r => setArticles(r.data.articles)).catch(() => { });
    }, []);
    const grouped = articles.reduce((acc, article) => {
        const topic = article.tags?.[0] || 'general';
        const existing = acc[topic] || [];
        acc[topic] = [...existing, article];
        return acc;
    }, {});
    return (_jsxs("div", { className: "knowledge-page", children: [_jsxs("div", { className: "page-intro", children: [_jsx("div", { className: "eyebrow", children: "Evidence-based guidance" }), _jsx("h1", { children: "Brain health knowledge base" }), _jsx("p", { children: "Clear, practical information about habits that may support memory, resilience, and healthy aging." })] }), _jsx("div", { className: "knowledge-grid", children: Object.entries(grouped).map(([topic, items]) => (_jsxs("section", { className: "knowledge-card", children: [_jsx("div", { className: "knowledge-header", children: _jsx("span", { className: "knowledge-tag", children: topic.replace(/_/g, ' ') }) }), items.map((a) => (_jsxs("article", { className: "knowledge-article", children: [_jsx("h3", { children: a.title || 'Brain health update' }), _jsx("p", { children: a.summary || a.text }), _jsxs("div", { className: "knowledge-meta", children: [_jsx("span", { children: a.source }), a.tags?.slice(0, 3).map((tag) => (_jsx("span", { className: "mini-pill", children: tag.replace(/_/g, ' ') }, tag)))] })] }, a.id || a.title || a.source)))] }, topic))) })] }));
}
