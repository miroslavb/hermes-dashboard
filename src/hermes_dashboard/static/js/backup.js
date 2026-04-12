/* Hermes Dashboard — Backup Panel */
(function () {
    "use strict";

    let refreshTimer = null;

    function esc(t) {
        const d = document.createElement("div");
        d.textContent = t || "";
        return d.innerHTML;
    }

    async function render(container, fetchApi) {
        // Don't render if user navigated away
        if (location.hash !== "#/backup") {
            if (refreshTimer) { clearInterval(refreshTimer); refreshTimer = null; }
            return;
        }
        container.innerHTML = "<p>Loading backup status...</p>";

        let data;
        try {
            data = await fetchApi("/api/backup/status");
        } catch (e) {
            container.innerHTML = `<p class="error">Failed to load: ${esc(e.message)}</p>`;
            return;
        }

        container.innerHTML = "";

        // Header
        const h2 = document.createElement("h2");
        h2.textContent = "💾 Backup";
        container.appendChild(h2);

        // Status bar
        const statusBar = document.createElement("div");
        statusBar.className = "card";
        statusBar.style.cssText = "display:flex;align-items:center;gap:1rem;padding:1rem;";
        if (data.running) {
            statusBar.innerHTML = '<span style="color:var(--green);font-weight:600;">● Backup running...</span>';
            if (!refreshTimer) refreshTimer = setInterval(() => render(container, fetchApi), 10000);
        } else {
            statusBar.innerHTML = `<span style="color:var(--text-secondary);">○ Idle</span> · <span>${data.snapshot_count} snapshot(s)</span>`;
            if (refreshTimer) { clearInterval(refreshTimer); refreshTimer = null; }
        }
        container.appendChild(statusBar);

        // Run button
        const btnRow = document.createElement("div");
        btnRow.style.cssText = "margin:1rem 0;display:flex;gap:0.5rem;";

        const runBtn = document.createElement("button");
        runBtn.className = "btn";
        runBtn.textContent = data.running ? "⏳ Running..." : "▶ Run Backup Now";
        runBtn.disabled = data.running;
        runBtn.style.cssText = "padding:0.5rem 1rem;background:var(--green);color:#000;border:none;border-radius:6px;cursor:pointer;font-weight:600;";
        runBtn.onclick = async () => {
            runBtn.disabled = true;
            runBtn.textContent = "⏳ Starting...";
            try {
                const resp = await fetchApi("/api/backup/run", "POST");
                if (resp.error) {
                    alert("Error: " + resp.error);
                    runBtn.disabled = false;
                    runBtn.textContent = "▶ Run Backup Now";
                    return;
                }
                setTimeout(() => render(container, fetchApi), 2000);
            } catch (e) {
                alert("Error: " + e.message);
                runBtn.disabled = false;
                runBtn.textContent = "▶ Run Backup Now";
            }
        };
        btnRow.appendChild(runBtn);

        const refreshBtn = document.createElement("button");
        refreshBtn.className = "btn";
        refreshBtn.textContent = "🔄 Refresh";
        refreshBtn.style.cssText = "padding:0.5rem 1rem;background:var(--card-bg);color:var(--text);border:1px solid var(--border);border-radius:6px;cursor:pointer;";
        refreshBtn.onclick = () => render(container, fetchApi);
        btnRow.appendChild(refreshBtn);

        container.appendChild(btnRow);

        // Snapshots
        const snapH = document.createElement("h3");
        snapH.textContent = "Snapshots";
        snapH.style.marginTop = "1.5rem";
        container.appendChild(snapH);

        if (data.snapshots && data.snapshots.length && !data.snapshots[0].error) {
            const table = document.createElement("table");
            table.className = "data-table";
            table.innerHTML = '<thead><tr><th>Snapshot</th><th>Size</th><th>Action</th></tr></thead>';
            const tbody = document.createElement("tbody");
            data.snapshots.forEach((s) => {
                const tr = document.createElement("tr");
                tr.innerHTML = `<td>${esc(s.name)}</td><td>${esc(s.size)}</td>`;
                const td = document.createElement("td");
                const btn = document.createElement("button");
                btn.className = "btn";
                btn.textContent = "📋 Restore cmd";
                btn.style.cssText = "padding:0.25rem 0.5rem;font-size:0.8rem;background:var(--card-bg);color:var(--text);border:1px solid var(--border);border-radius:4px;cursor:pointer;";
                btn.onclick = async () => {
                    try {
                        const resp = await fetchApi("/api/backup/restore", "POST", {
                            snapshot: s.name,
                            target: "/",
                        });
                        if (resp.command) {
                            prompt("Restore command (copy & run manually):", resp.command);
                        } else {
                            alert("Error: " + (resp.error || "unknown"));
                        }
                    } catch (e) {
                        alert("Error: " + e.message);
                    }
                };
                td.appendChild(btn);
                tr.appendChild(td);
                tbody.appendChild(tr);
            });
            table.appendChild(tbody);
            container.appendChild(table);
        } else {
            const ph = document.createElement("div");
            ph.className = "placeholder";
            ph.textContent = "No snapshots yet";
            container.appendChild(ph);
        }

        // Log
        const logH = document.createElement("h3");
        logH.textContent = "Log";
        logH.style.marginTop = "1.5rem";
        container.appendChild(logH);

        const logPre = document.createElement("pre");
        logPre.className = "mono";
        logPre.style.cssText = "max-height:400px;overflow:auto;font-size:0.8rem;background:var(--card-bg);padding:1rem;border-radius:6px;";
        logPre.textContent = data.log_tail || "No log yet";
        container.appendChild(logPre);
        logPre.scrollTop = logPre.scrollHeight;
    }

    // Override fetchApi to support POST
    const origFetch = window.fetchApi;
    window.panels = window.panels || {};
    window.panels.backup = function (container, fetchApi) {
        // Wrap fetchApi for POST support
        const wrappedFetch = async function (path, method, body) {
            if (method === "POST") {
                const token = new URLSearchParams(window.location.search).get("token") || "";
                const sep = path.includes("?") ? "&" : "?";
                const url = path + (token ? sep + "token=" + encodeURIComponent(token) : "");
                const resp = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: body ? JSON.stringify(body) : "{}",
                });
                return resp.json();
            }
            return fetchApi(path);
        };
        render(container, wrappedFetch);
    };
})();
