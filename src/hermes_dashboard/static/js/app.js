/* Hermes Dashboard — App Shell */
(function () {
    "use strict";

    const ROUTES = {
        "#/system": "system",
        "#/sessions": "sessions",
        "#/skills": "skills",
        "#/memory": "memory",
        "#/processes": "processes",
        "#/cron": "cron",
        "#/logs": "logs",
    };

    const NAV_ITEMS = [
        ["#/system", "📊 System"],
        ["#/sessions", "💬 Sessions"],
        ["#/skills", "🛠 Skills"],
        ["#/memory", "🧠 Memory"],
        ["#/processes", "⚡ Processes"],
        ["#/cron", "⏰ Cron"],
        ["#/logs", "📋 Logs"],
    ];

    function initNav() {
        const nav = document.getElementById("nav");
        NAV_ITEMS.forEach(([href, label]) => {
            const a = document.createElement("a");
            a.href = href;
            a.textContent = label;
            nav.appendChild(a);
        });
    }

    async function fetchApi(path) {
        const resp = await fetch(path);
        if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
        return resp.json();
    }

    function onRouteChange() {
        const hash = location.hash || "#/system";
        document.querySelectorAll("nav a").forEach((a) => {
            a.classList.toggle("active", a.getAttribute("href") === hash);
        });
        const app = document.getElementById("app");
        const panel = ROUTES[hash];
        if (panel && window.panels && window.panels[panel]) {
            window.panels[panel](app, fetchApi);
        } else {
            app.innerHTML = '<div class="card"><h2>404</h2><p>Panel not found</p></div>';
        }
    }

    window.addEventListener("DOMContentLoaded", () => {
        initNav();
        onRouteChange();
    });
    window.addEventListener("hashchange", onRouteChange);

    // SSE helper
    window.createSSE = function (url, onData) {
        const es = new EventSource(url);
        es.onmessage = (e) => {
            try { onData(JSON.parse(e.data)); } catch { onData(e.data); }
        };
        es.onerror = () => { es.close(); };
        return es;
    };
    window.fetchApi = fetchApi;
})();
