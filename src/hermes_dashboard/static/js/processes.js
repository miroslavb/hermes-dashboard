/* Hermes Dashboard — Processes Panel */
(function () {
    "use strict";

    function formatTime(ts) {
        if (!ts) return "—";
        return new Date(ts * 1000).toLocaleTimeString();
    }

    function formatAge(seconds) {
        if (seconds < 60) return Math.floor(seconds) + "s";
        if (seconds < 3600) return Math.floor(seconds / 60) + "m";
        return Math.floor(seconds / 3600) + "h";
    }

    function buildProcessTable(procs) {
        const card = document.createElement("div");
        card.className = "card";
        card.style.overflowX = "auto";
        const title = document.createElement("h2");
        title.textContent = "⚡ Top Processes";
        card.appendChild(title);

        const table = document.createElement("table");
        table.style.cssText = "width:100%;border-collapse:collapse;font-size:0.85rem;";
        const thead = document.createElement("thead");
        thead.innerHTML = '<tr style="text-align:left;border-bottom:1px solid var(--border);"><th style="padding:0.4rem;">PID</th><th style="padding:0.4rem;">Name</th><th style="padding:0.4rem;">CPU %</th><th style="padding:0.4rem;">Mem MB</th><th style="padding:0.4rem;">Started</th></tr>';
        table.appendChild(thead);
        const tbody = document.createElement("tbody");
        procs.forEach((p) => {
            const tr = document.createElement("tr");
            tr.style.borderBottom = "1px solid var(--border)";
            tr.innerHTML = '<td class="mono" style="padding:0.4rem;">' + p.pid +
                '</td><td style="padding:0.4rem;">' + p.name +
                '</td><td style="padding:0.4rem;color:' + (p.cpu_percent > 50 ? 'var(--red)' : 'var(--green)') + ';">' + p.cpu_percent.toFixed(1) +
                '%</td><td style="padding:0.4rem;">' + (p.memory_mb || 0).toFixed(1) +
                '</td><td class="stat-label" style="padding:0.4rem;">' + formatTime(p.create_time) + '</td>';
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        card.appendChild(table);
        return card;
    }

    function buildActiveSessions(active) {
        const card = document.createElement("div");
        card.className = "card";
        const title = document.createElement("h2");
        title.textContent = "📁 Active Session Files";
        card.appendChild(title);

        if (!active || active.length === 0) {
            const empty = document.createElement("div");
            empty.className = "stat-label";
            empty.textContent = "No active session files.";
            card.appendChild(empty);
            return card;
        }

        active.forEach((a) => {
            const row = document.createElement("div");
            row.style.cssText = "display:flex;justify-content:space-between;padding:0.3rem 0;border-bottom:1px solid var(--border);";
            const name = document.createElement("span");
            name.className = "mono";
            name.textContent = a.file;
            const meta = document.createElement("span");
            meta.className = "stat-label";
            meta.textContent = (a.size / 1024).toFixed(1) + " KB • " + formatAge(a.age_seconds) + " ago";
            row.appendChild(name);
            row.appendChild(meta);
            card.appendChild(row);
        });
        return card;
    }

    let sseSource = null;

    window.panels = window.panels || {};
    window.panels.processes = function (app, fetchApi) {
        app.innerHTML = '<p class="stat-label" style="padding:1rem;">Loading...</p>';

        // Close previous SSE if any
        if (sseSource) { sseSource.close(); sseSource = null; }

        // Container refs for live updates
        let procsContainer = null;
        let activeContainer = null;

        function render(procs, active) {
            app.innerHTML = "";
            if (!procs || procs.length === 0) {
                app.innerHTML = '<div class="card"><p class="stat-label">No process data available.</p></div>';
                return;
            }
            procsContainer = buildProcessTable(procs);
            activeContainer = buildActiveSessions(active);
            app.appendChild(procsContainer);
            app.appendChild(activeContainer);
        }

        function updateProcs(procs) {
            if (!procsContainer || !app.contains(procsContainer)) return;
            const newTable = buildProcessTable(procs);
            procsContainer.replaceWith(newTable);
            procsContainer = newTable;
        }

        // Initial load
        Promise.all([
            fetchApi("/api/processes").catch(() => []),
            fetchApi("/api/processes/active").catch(() => []),
        ]).then(([procs, active]) => {
            render(procs, active);

            // Connect SSE for live process updates
            const token = new URLSearchParams(window.location.search).get("token") || "";
            const sseUrl = "/api/processes/stream" + (token ? "?token=" + encodeURIComponent(token) : "");
            sseSource = new EventSource(sseUrl);
            sseSource.onmessage = function (e) {
                try {
                    const data = JSON.parse(e.data);
                    if (Array.isArray(data)) {
                        updateProcs(data);
                    }
                } catch (_) { /* ignore parse errors */ }
            };
            sseSource.onerror = function () {
                // SSE will auto-reconnect
            };
        }).catch(() => {
            app.innerHTML = '<div class="card"><p style="color:var(--red);">Failed to load processes.</p></div>';
        });
    };
})();
