/* Hermes Dashboard — Logs Panel */
(function () {
    "use strict";

    let sse = null;

    function formatDate(ts) {
        if (!ts) return "—";
        const d = typeof ts === "number" ? new Date(ts * 1000) : new Date(ts);
        return d.toLocaleString();
    }

    function buildLogSelector(logs, onSelect) {
        const grid = document.createElement("div");
        grid.className = "grid";
        logs.forEach((log) => {
            const card = document.createElement("div");
            card.className = "card";
            card.style.cursor = "pointer";
            const name = document.createElement("div");
            name.style.fontWeight = "600";
            name.textContent = "📋 " + log.name;
            const meta = document.createElement("div");
            meta.className = "stat-label";
            meta.textContent = (log.size / 1024).toFixed(1) + " KB • " + formatDate(log.modified);
            card.appendChild(name);
            card.appendChild(meta);
            card.addEventListener("click", () => onSelect(log.name));
            grid.appendChild(card);
        });
        return grid;
    }

    function buildLogViewer(logName, logData, onBack, onStream) {
        const container = document.createElement("div");

        // Header with back + stream toggle
        const header = document.createElement("div");
        header.style.cssText = "display:flex;align-items:center;gap:1rem;margin-bottom:1rem;flex-wrap:wrap;";

        const back = document.createElement("button");
        back.textContent = "← All logs";
        back.style.cssText = "background:var(--bg-accent);color:var(--text-primary);border:1px solid var(--border);padding:0.4rem 1rem;border-radius:6px;cursor:pointer;";
        back.addEventListener("click", onBack);

        const title = document.createElement("h2");
        title.textContent = "📋 " + logName;
        title.style.flex = "1";

        const streamBtn = document.createElement("button");
        streamBtn.textContent = "▶ Live Stream";
        streamBtn.style.cssText = "background:var(--green);color:#000;border:none;padding:0.4rem 1rem;border-radius:6px;cursor:pointer;font-weight:600;";
        let streaming = false;
        streamBtn.addEventListener("click", () => {
            streaming = !streaming;
            if (streaming) {
                streamBtn.textContent = "⏹ Stop";
                streamBtn.style.background = "var(--red)";
                streamBtn.style.color = "#fff";
                onStream(true);
            } else {
                streamBtn.textContent = "▶ Live Stream";
                streamBtn.style.background = "var(--green)";
                streamBtn.style.color = "#000";
                onStream(false);
            }
        });

        header.appendChild(back);
        header.appendChild(title);
        header.appendChild(streamBtn);
        container.appendChild(header);

        // Lines info
        const info = document.createElement("div");
        info.className = "stat-label";
        info.textContent = "Showing " + (logData.lines ? logData.lines.length : 0) + " of " + (logData.total_lines || 0) + " lines";
        container.appendChild(info);

        // Log box
        const logBox = document.createElement("div");
        logBox.className = "log-box mono";
        logBox.id = "log-content";
        if (logData.lines) {
            logData.lines.forEach((line) => {
                const div = document.createElement("div");
                div.className = "line";
                div.textContent = line;
                logBox.appendChild(div);
            });
        }
        // Auto-scroll to bottom
        logBox.scrollTop = logBox.scrollHeight;
        container.appendChild(logBox);

        return { container, logBox };
    }

    window.panels = window.panels || {};
    window.panels.logs = function (app, fetchApi) {
        if (sse) { sse.close(); sse = null; }
        app.innerHTML = "";

        function showLogList() {
            if (sse) { sse.close(); sse = null; }
            app.innerHTML = '<p class="stat-label" style="padding:1rem;">Loading log files...</p>';
            fetchApi("/api/logs").then((data) => {
                app.innerHTML = "";
                // Multi-agent: {hermes: {name, files:[...]}, hermes2: {files:[...]}}
                for (const agentId of Object.keys(data)) {
                    const ag = data[agentId];
                    const logs = ag.files || ag.logs || (Array.isArray(ag) ? ag : []);
                    if (logs.length === 0) continue;
                    const h = document.createElement("h3");
                    h.textContent = "🧠 " + (ag.name || agentId);
                    h.style.margin = "1rem 0 0.5rem";
                    app.appendChild(h);
                    app.appendChild(buildLogSelector(logs, (name) => showLog(agentId, name)));
                }
            }).catch((err) => {
                console.error("[Logs] Failed to load:", err);
                app.innerHTML = '<div class="card"><p style="color:var(--red);">Failed to load logs: ' + (err.message || err) + '</p></div>';
            });
        }

        function showLog(agentId, name) {
            app.innerHTML = '<p class="stat-label" style="padding:1rem;">Loading log...</p>';
            const agentQ = agentId ? ("&agent=" + encodeURIComponent(agentId)) : "";
            fetchApi("/api/logs/" + encodeURIComponent(name) + "?lines=200" + agentQ).then((data) => {
                app.innerHTML = "";
                if (!data) {
                    app.innerHTML = '<div class="card"><p class="stat-label">Log not found.</p></div>';
                    return;
                }

                const { container, logBox } = buildLogViewer(name, data, showLogList, (startStream) => {
                    if (startStream) {
                        const streamQ = agentId ? ("?agent=" + encodeURIComponent(agentId)) : "";
                        sse = window.createSSE("/api/logs/" + encodeURIComponent(name) + "/stream" + streamQ, (line) => {
                            const div = document.createElement("div");
                            div.className = "line";
                            div.textContent = typeof line === "string" ? line : JSON.stringify(line);
                            logBox.appendChild(div);
                            // Keep max 2000 lines
                            while (logBox.children.length > 2000) {
                                logBox.removeChild(logBox.firstChild);
                            }
                            logBox.scrollTop = logBox.scrollHeight;
                        });
                    } else {
                        if (sse) { sse.close(); sse = null; }
                    }
                });
                app.appendChild(container);
            }).catch((err) => {
                console.error("[Logs] Failed to load log:", err);
                app.innerHTML = '<div class="card"><p style="color:var(--red);">Failed to load log: ' + (err.message || err) + '</p></div>';
            });
        }

        showLogList();
    };
})();
