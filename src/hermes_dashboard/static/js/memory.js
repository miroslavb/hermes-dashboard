/* Hermes Dashboard — Memory Panel */
(function () {
    "use strict";

    function formatDate(iso) {
        if (!iso) return "—";
        const d = new Date(iso);
        return d.toLocaleDateString() + " " + d.toLocaleTimeString();
    }

    function buildFileList(files, onSelect) {
        const list = document.createElement("div");
        files.forEach((f) => {
            const row = document.createElement("div");
            row.className = "card";
            row.style.cursor = "pointer";
            row.style.display = "flex";
            row.style.justifyContent = "space-between";
            row.style.alignItems = "center";

            const left = document.createElement("div");
            const name = document.createElement("div");
            name.style.fontWeight = "600";
            name.textContent = "📄 " + f.name;
            const meta = document.createElement("div");
            meta.className = "stat-label";
            meta.textContent = formatDate(f.modified) + " • " + (f.size / 1024).toFixed(1) + " KB";
            left.appendChild(name);
            left.appendChild(meta);

            row.appendChild(left);
            row.addEventListener("click", () => onSelect(f.name));
            list.appendChild(row);
        });
        return list;
    }

    function buildEditor(memFile, onSave, onBack) {
        const container = document.createElement("div");
        const back = document.createElement("button");
        back.textContent = "← Back to memory files";
        back.style.cssText = "background:var(--bg-accent);color:var(--text-primary);border:1px solid var(--border);padding:0.4rem 1rem;border-radius:6px;cursor:pointer;margin-bottom:1rem;";
        back.addEventListener("click", onBack);
        container.appendChild(back);

        const card = document.createElement("div");
        card.className = "card";
        const title = document.createElement("h2");
        title.textContent = "📄 " + memFile.name;
        const meta = document.createElement("div");
        meta.className = "stat-label";
        meta.textContent = formatDate(memFile.modified) + " • " + (memFile.size / 1024).toFixed(1) + " KB";

        const textarea = document.createElement("textarea");
        textarea.value = memFile.content || "";
        textarea.style.cssText = "width:100%;min-height:400px;background:var(--bg-primary);color:var(--text-primary);border:1px solid var(--border);border-radius:6px;padding:0.75rem;font-family:'JetBrains Mono','Fira Code',monospace;font-size:0.85rem;resize:vertical;outline:none;line-height:1.5;";
        textarea.spellcheck = false;

        const btnRow = document.createElement("div");
        btnRow.style.marginTop = "0.75rem";
        btnRow.style.display = "flex";
        btnRow.style.gap = "0.5rem";

        const saveBtn = document.createElement("button");
        saveBtn.textContent = "💾 Save";
        saveBtn.style.cssText = "background:var(--green);color:#000;border:none;padding:0.5rem 1.5rem;border-radius:6px;cursor:pointer;font-weight:600;";
        saveBtn.addEventListener("click", () => onSave(memFile.name, textarea.value, saveBtn));

        const statusEl = document.createElement("span");
        statusEl.className = "stat-label";
        statusEl.style.alignSelf = "center";

        btnRow.appendChild(saveBtn);
        btnRow.appendChild(statusEl);

        card.appendChild(title);
        card.appendChild(meta);
        card.appendChild(textarea);
        card.appendChild(btnRow);
        container.appendChild(card);

        return { container, statusEl };
    }

    window.panels = window.panels || {};
    window.panels.memory = function (app, fetchApi) {
        app.innerHTML = "";

        function showList() {
            app.innerHTML = '<p class="stat-label" style="padding:1rem;">Loading memory files...</p>';
            fetchApi("/api/memory").then((files) => {
                app.innerHTML = "";
                if (!files || files.length === 0) {
                    app.innerHTML = '<div class="card"><p class="stat-label">No memory files found.</p></div>';
                    return;
                }
                app.appendChild(buildFileList(files, showEditor));
            }).catch(() => {
                app.innerHTML = '<div class="card"><p style="color:var(--red);">Failed to load memory files.</p></div>';
            });
        }

        function showEditor(name) {
            app.innerHTML = '<p class="stat-label" style="padding:1rem;">Loading file...</p>';
            fetchApi("/api/memory/" + encodeURIComponent(name)).then((file) => {
                app.innerHTML = "";
                const { container, statusEl } = buildEditor(file, saveFile, showList);
                app.appendChild(container);
            }).catch(() => {
                app.innerHTML = '<div class="card"><p style="color:var(--red);">Failed to load file.</p></div>';
            });
        }

        function saveFile(name, content, btn) {
            btn.disabled = true;
            btn.textContent = "Saving...";
            fetch("/api/memory/" + encodeURIComponent(name), {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ content: content }),
            })
                .then((resp) => {
                    if (!resp.ok) throw new Error("Save failed");
                    btn.textContent = "✓ Saved";
                    btn.style.background = "var(--green)";
                    setTimeout(() => {
                        btn.disabled = false;
                        btn.textContent = "💾 Save";
                    }, 2000);
                })
                .catch(() => {
                    btn.textContent = "✗ Error";
                    btn.style.background = "var(--red)";
                    btn.disabled = false;
                    setTimeout(() => {
                        btn.textContent = "💾 Save";
                        btn.style.background = "var(--green)";
                    }, 2000);
                });
        }

        showList();
    };
})();
