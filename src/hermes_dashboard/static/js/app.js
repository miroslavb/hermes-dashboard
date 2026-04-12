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
        "#/backup": "backup",
        "#/logs": "logs",
    };

    const NAV_ITEMS = [
        ["#/system", "📊 System"],
        ["#/sessions", "💬 Sessions"],
        ["#/skills", "🛠 Skills"],
        ["#/memory", "🧠 Memory"],
        ["#/processes", "⚡ Processes"],
        ["#/cron", "⏰ Cron"],
        ["#/backup", "💾 Backup"],
        ["#/logs", "📋 Logs"],
    ];

    let currentAgent = ""; // empty = all agents
    let agentsList = [];

    function initNav() {
        const nav = document.getElementById("nav");

        // Agent selector
        const agentSel = document.createElement("select");
        agentSel.id = "agent-select";
        agentSel.style.cssText = "margin-bottom:0.5rem;padding:0.3rem 0.5rem;background:var(--card-bg);color:var(--text-primary);border:1px solid var(--border);border-radius:4px;font-size:0.8rem;";
        agentSel.innerHTML = '<option value="">All agents</option>';
        agentSel.addEventListener("change", () => {
            currentAgent = agentSel.value;
            onRouteChange();
        });
        nav.appendChild(agentSel);

        // Load agents
        fetchApi("/api/agents").then((data) => {
            agentsList = data.agents || [];
            agentsList.forEach((a) => {
                const opt = document.createElement("option");
                opt.value = a.id;
                opt.textContent = a.name + ` (${a.session_count}💬 ${a.skill_count}🛠 ${a.cron_count}⏰)`;
                agentSel.appendChild(opt);
            });
        }).catch(() => {});

        // Nav links
        NAV_ITEMS.forEach(([href, label]) => {
            const a = document.createElement("a");
            a.href = href;
            a.textContent = label;
            nav.appendChild(a);
        });
    }

    function getToken() {
        return new URLSearchParams(window.location.search).get("token") || "";
    }

    function agentParam() {
        return currentAgent ? (currentAgent.includes("?") ? "&" : "?") + "agent=" + currentAgent : "";
    }

    function apiPath(path) {
        const token = getToken();
        let result = path;
        // Add agent param
        if (currentAgent) {
            const sep = result.includes("?") ? "&" : "?";
            result += sep + "agent=" + encodeURIComponent(currentAgent);
        }
        // Add token
        if (token) {
            const sep = result.includes("?") ? "&" : "?";
            result += sep + "token=" + encodeURIComponent(token);
        }
        return result;
    }

    async function fetchApi(path) {
        const resp = await fetch(apiPath(path));
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
        const es = new EventSource(apiPath(url));
        es.onmessage = (e) => {
            try { onData(JSON.parse(e.data)); } catch { onData(e.data); }
        };
        es.onerror = () => { es.close(); };
        return es;
    };
    window.fetchApi = fetchApi;
    window.apiPath = apiPath;
})();
