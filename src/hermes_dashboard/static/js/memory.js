/* Hermes Dashboard — Memory Panel (multi-agent) */
(function () {
    "use strict";

    function formatDate(ts) {
        if (!ts) return "—";
        const d = typeof ts === "number" ? new Date(ts * 1000) : new Date(ts);
        return d.toLocaleDateString() + " " + d.toLocaleTimeString();
    }

    function buildAgentSection(agentId, agentData, fetchApi, app) {
        const section = document.createElement("div");
        section.className = "card";
        section.style.marginBottom = "1rem";

        const header = document.createElement("h3");
        header.textContent = "🧠 " + agentData.name;
        section.appendChild(header);

        if (!agentData.files || agentData.files.length === 0) {
            const empty = document.createElement("div");
            empty.className = "stat-label";
            empty.textContent = "No memory files.";
            section.appendChild(empty);
            app.appendChild(section);
            return;
        }

        // File list
        agentData.files.forEach((f) => {
            const row = document.createElement("div");
            row.style.cssText = "display:flex;justify-content:space-between;align-items:center;padding:0.5rem 0;border-bottom:1px solid var(--border);cursor:pointer;";
            row.addEventListener("click", () => showEditor(f, agentId, fetchApi, app));

            const left = document.createElement("div");
            const name = document.createElement("div");
            name.style.fontWeight = "600";
            name.textContent = (f.name === "SOUL.md" ? "🔒 " : "📄 ") + f.name;
            const meta = document.createElement("div");
            meta.className = "stat-label";
            meta.textContent = formatDate(f.modified) + " • " + (f.size / 1024).toFixed(1) + " KB";
            left.appendChild(name);
            left.appendChild(meta);

            const right = document.createElement("div");
            if (f.name === "SOUL.md") {
                const badge = document.createElement("span");
                badge.textContent = "Read-only";
                badge.style.cssText = "padding:0.15rem 0.5rem;border-radius:4px;font-size:0.75rem;background:rgba(255,107,107,0.2);color:var(--red);";
                right.appendChild(badge);
            }

            row.appendChild(left);
            row.appendChild(right);
            section.appendChild(row);
        });

        app.appendChild(section);
    }

    function showEditor(file, agentId, fetchApi, app) {
        app.innerHTML = "";

        const back = document.createElement("button");
        back.textContent = "← Back to memory files";
        back.style.cssText = "background:var(--bg-accent);color:var(--text-primary);border:1px solid var(--border);padding:0.4rem 1rem;border-radius:6px;cursor:pointer;margin-bottom:1rem;";
        back.addEventListener("click", () => window.panels.memory(app, fetchApi));
        app.appendChild(back);

        const card = document.createElement("div");
        card.className = "card";

        const title = document.createElement("h2");
        title.textContent = "📄 " + file.name;
        const meta = document.createElement("div");
        meta.className = "stat-label";
        meta.textContent = formatDate(file.modified) + " • " + (file.size / 1024).toFixed(1) + " KB" + (agentId ? " • Agent: " + agentId : "");

        const textarea = document.createElement("textarea");
        textarea.value = file.content || "";
        textarea.style.cssText = "width:100%;min-height:400px;background:var(--bg-primary);color:var(--text-primary);border:1px solid var(--border);border-radius:6px;padding:0.75rem;font-family:'JetBrains Mono','Fira Code',monospace;font-size:0.85rem;resize:vertical;outline:none;line-height:1.5;";
        textarea.spellcheck = false;
        if (file.name === "SOUL.md") textarea.readOnly = true;

        card.appendChild(title);
        card.appendChild(meta);
        card.appendChild(textarea);

        if (file.name !== "SOUL.md") {
            const btnRow = document.createElement("div");
            btnRow.style.marginTop = "0.75rem";
            const saveBtn = document.createElement("button");
            saveBtn.textContent = "💾 Save";
            saveBtn.style.cssText = "background:var(--green);color:#000;border:none;padding:0.5rem 1.5rem;border-radius:6px;cursor:pointer;font-weight:600;";
            saveBtn.addEventListener("click", () => {
                saveBtn.disabled = true;
                saveBtn.textContent = "Saving...";
                fetch(window.apiPath("/api/memory/" + encodeURIComponent(file.name)), {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ content: textarea.value }),
                })
                    .then((r) => {
                        if (!r.ok) throw new Error("Save failed");
                        saveBtn.textContent = "✓ Saved";
                        saveBtn.style.background = "var(--green)";
                        setTimeout(() => { saveBtn.disabled = false; saveBtn.textContent = "💾 Save"; }, 2000);
                    })
                    .catch(() => {
                        saveBtn.textContent = "✗ Error";
                        saveBtn.style.background = "var(--red)";
                        saveBtn.disabled = false;
                    });
            });
            btnRow.appendChild(saveBtn);
            card.appendChild(btnRow);
        }

        app.appendChild(card);
    }

    window.panels = window.panels || {};
    window.panels.memory = function (app, fetchApi) {
        app.innerHTML = '<p class="stat-label" style="padding:1rem;">Loading memory files...</p>';

        fetchApi("/api/memory")
            .then((data) => {
                app.innerHTML = "";
                if (!data || Object.keys(data).length === 0) {
                    app.innerHTML = '<div class="card"><p class="stat-label">No memory files found.</p></div>';
                    return;
                }
                for (const agentId of Object.keys(data)) {
                    try {
                        buildAgentSection(agentId, data[agentId], fetchApi, app);
                    } catch (e) {
                        console.error("[Memory] Error building section for", agentId, ":", e, "data:", data[agentId]);
                        const errDiv = document.createElement("div");
                        errDiv.className = "card";
                        errDiv.innerHTML = '<p style="color:var(--red);">Error rendering agent "' + agentId + '": ' + e.message + '</p>';
                        app.appendChild(errDiv);
                    }
                }
            })
            .catch((err) => {
                console.error("[Memory] Failed to load:", err);
                app.innerHTML = '<div class="card"><p style="color:var(--red);">Failed to load memory files: ' + (err.message || err) + '</p><p class="stat-label">Check browser console for details.</p></div>';
            });
    };
})();
