/* Hermes Dashboard — Sessions Panel */
(function () {
    "use strict";

    function formatDate(ts) {
        if (!ts) return "—";
        const d = typeof ts === "number" ? new Date(ts * 1000) : new Date(ts);
        return d.toLocaleDateString() + " " + d.toLocaleTimeString();
    }

    function buildSessionList(sessions) {
        const list = document.createElement("div");
        sessions.forEach((s) => {
            const row = document.createElement("div");
            row.className = "card";
            row.style.cursor = "pointer";
            row.style.display = "flex";
            row.style.justifyContent = "space-between";
            row.style.alignItems = "center";

            const left = document.createElement("div");
            const idEl = document.createElement("div");
            idEl.style.fontWeight = "600";
            idEl.textContent = "Session " + s.id.slice(0, 8);
            const meta = document.createElement("div");
            meta.className = "stat-label";
            meta.textContent = formatDate(s.started_at) + " • " + (s.channel || "unknown");
            left.appendChild(idEl);
            left.appendChild(meta);

            const right = document.createElement("div");
            right.style.textAlign = "right";
            const msgs = document.createElement("div");
            msgs.style.color = "var(--green)";
            msgs.style.fontWeight = "600";
            msgs.textContent = s.message_count + " msgs";
            const size = document.createElement("div");
            size.className = "stat-label";
            size.textContent = s.file_size ? (s.file_size / 1024).toFixed(1) + " KB" : "";
            right.appendChild(msgs);
            right.appendChild(size);

            row.appendChild(left);
            row.appendChild(right);

            row.addEventListener("click", () => loadTranscript(s.id));
            list.appendChild(row);
        });
        return list;
    }

    function buildTranscript(messages, onBack) {
        const container = document.createElement("div");
        const back = document.createElement("button");
        back.textContent = "← Back to sessions";
        back.style.cssText = "background:var(--bg-accent);color:var(--text-primary);border:1px solid var(--border);padding:0.4rem 1rem;border-radius:6px;cursor:pointer;margin-bottom:1rem;";
        back.addEventListener("click", onBack);
        container.appendChild(back);

        messages.forEach((m) => {
            const card = document.createElement("div");
            card.className = "card mono";
            const role = document.createElement("div");
            role.style.fontWeight = "700";
            role.style.color = m.role === "assistant" ? "var(--green)" : "var(--blue)";
            role.textContent = m.role.toUpperCase();
            const content = document.createElement("div");
            content.style.whiteSpace = "pre-wrap";
            content.style.marginTop = "0.5rem";
            content.textContent = m.content;
            const ts = document.createElement("div");
            ts.className = "stat-label";
            ts.textContent = formatDate(m.timestamp);
            card.appendChild(role);
            card.appendChild(content);
            card.appendChild(ts);
            container.appendChild(card);
        });
        return container;
    }

    let searchTimer = null;

    window.panels = window.panels || {};
    window.panels.sessions = function (app, fetchApi) {
        app.innerHTML = "";

        // Search bar
        const searchWrap = document.createElement("div");
        searchWrap.className = "card";
        const input = document.createElement("input");
        input.type = "text";
        input.placeholder = "Search sessions...";
        input.style.cssText = "width:100%;padding:0.5rem;background:var(--bg-primary);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);font-size:0.9rem;outline:none;";
        searchWrap.appendChild(input);
        app.appendChild(searchWrap);

        const content = document.createElement("div");
        app.appendChild(content);

        function loadSessions(url) {
            url = url || "/api/sessions";
            content.innerHTML = '<p class="stat-label" style="padding:1rem;">Loading...</p>';
            fetchApi(url).then((sessions) => {
                content.innerHTML = "";
                if (!sessions || sessions.length === 0) {
                    content.innerHTML = '<div class="card"><p class="stat-label">No sessions found.</p></div>';
                    return;
                }
                content.appendChild(buildSessionList(sessions));
            }).catch(() => {
                content.innerHTML = '<div class="card"><p style="color:var(--red);">Failed to load sessions.</p></div>';
            });
        }

        function loadTranscript(sessionId) {
            content.innerHTML = '<p class="stat-label" style="padding:1rem;">Loading transcript...</p>';
            fetchApi("/api/sessions/" + sessionId).then((data) => {
                content.innerHTML = "";
                if (!data || !data.messages) {
                    content.innerHTML = '<div class="card"><p class="stat-label">No messages found.</p></div>';
                    return;
                }
                content.appendChild(buildTranscript(data.messages, () => loadSessions()));
            }).catch(() => {
                content.innerHTML = '<div class="card"><p style="color:var(--red);">Failed to load transcript.</p></div>';
            });
        }

        // Expose for inline clicks
        window._loadTranscript = loadTranscript;

        input.addEventListener("input", () => {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(() => {
                const q = input.value.trim();
                if (q.length === 0) {
                    loadSessions();
                } else {
                    loadSessions("/api/sessions/search?q=" + encodeURIComponent(q));
                }
            }, 300);
        });

        loadSessions();
    };
})();
