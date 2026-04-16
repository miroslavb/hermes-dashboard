/* Hermes Dashboard — RLM Visualizer Panel */
(function () {
    "use strict";

    function formatTime(seconds) {
        if (seconds == null) return "—";
        if (seconds < 60) return seconds.toFixed(1) + "s";
        const m = Math.floor(seconds / 60);
        const s = (seconds % 60).toFixed(0);
        return m + "m " + s + "s";
    }

    function formatSize(bytes) {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
        return (bytes / (1024 * 1024)).toFixed(1) + " MB";
    }

    function escapeHtml(str) {
        if (!str) return "";
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    function buildStatsBar(summary) {
        const bar = document.createElement("div");
        bar.style.cssText = "display:flex;gap:1.5rem;flex-wrap:wrap;margin:0.5rem 0;";

        const stats = [
            ["🔄 Iterations", summary.iterations || 0],
            ["📝 Code Blocks", summary.code_blocks || 0],
            ["🧠 Sub-LM Calls", summary.sub_lm_calls || 0],
            ["⏱ Time", formatTime(summary.execution_time)],
        ];

        if (summary.has_errors) {
            stats.push(["⚠️ Errors", "Yes"]);
        }

        stats.forEach(([label, value]) => {
            const item = document.createElement("div");
            item.style.cssText = "text-align:center;";
            const val = document.createElement("div");
            val.style.cssText = "font-size:1.3rem;font-weight:700;color:var(--green);";
            val.textContent = value;
            const lbl = document.createElement("div");
            lbl.className = "stat-label";
            lbl.textContent = label;
            item.appendChild(val);
            item.appendChild(lbl);
            bar.appendChild(item);
        });

        return bar;
    }

    function buildCodeBlock(block, blockIdx) {
        const container = document.createElement("div");
        container.style.cssText = "margin-bottom:1rem;border:1px solid var(--border);border-radius:6px;overflow:hidden;";

        // Header
        const header = document.createElement("div");
        header.style.cssText = "display:flex;justify-content:space-between;align-items:center;padding:0.4rem 0.8rem;background:var(--bg-accent);cursor:pointer;";
        const title = document.createElement("span");
        title.style.fontWeight = "600";
        title.textContent = "📝 Code Block " + (blockIdx + 1);
        header.appendChild(title);

        const result = block.result || {};
        const execTime = result.execution_time;
        if (execTime != null) {
            const timeSpan = document.createElement("span");
            timeSpan.className = "stat-label";
            timeSpan.textContent = formatTime(execTime);
            header.appendChild(timeSpan);
        }
        container.appendChild(header);

        // Code
        const codeEl = document.createElement("pre");
        codeEl.className = "mono";
        codeEl.style.cssText = "background:#0d1117;padding:0.8rem;margin:0;overflow-x:auto;font-size:0.8rem;line-height:1.5;max-height:300px;overflow-y:auto;";
        codeEl.textContent = block.code || "";
        container.appendChild(codeEl);

        // stdout
        if (result.stdout) {
            const stdoutHeader = document.createElement("div");
            stdoutHeader.style.cssText = "padding:0.3rem 0.8rem;background:rgba(0,212,170,0.1);font-size:0.8rem;font-weight:600;color:var(--green);";
            stdoutHeader.textContent = "📤 stdout";
            container.appendChild(stdoutHeader);

            const stdoutEl = document.createElement("pre");
            stdoutEl.className = "mono log-box";
            stdoutEl.style.cssText = "margin:0;border-radius:0;font-size:0.78rem;max-height:200px;";
            stdoutEl.textContent = result.stdout;
            container.appendChild(stdoutEl);
        }

        // stderr
        if (result.stderr) {
            const stderrHeader = document.createElement("div");
            stderrHeader.style.cssText = "padding:0.3rem 0.8rem;background:rgba(255,107,107,0.1);font-size:0.8rem;font-weight:600;color:var(--red);";
            stderrHeader.textContent = "⚠️ stderr";
            container.appendChild(stderrHeader);

            const stderrEl = document.createElement("pre");
            stderrEl.className = "mono";
            stderrEl.style.cssText = "background:#1a0000;padding:0.8rem;margin:0;border-radius:0;font-size:0.78rem;color:var(--red);max-height:150px;overflow-y:auto;";
            stderrEl.textContent = result.stderr;
            container.appendChild(stderrEl);
        }

        // Sub-LM calls
        const rlmCalls = result.rlm_calls || [];
        if (rlmCalls.length > 0) {
            const callsHeader = document.createElement("div");
            callsHeader.style.cssText = "padding:0.3rem 0.8rem;background:rgba(78,168,222,0.1);font-size:0.8rem;font-weight:600;color:var(--blue);";
            callsHeader.textContent = "🧠 Sub-LM Calls (" + rlmCalls.length + ")";
            container.appendChild(callsHeader);

            rlmCalls.forEach((call, i) => {
                const callDiv = document.createElement("div");
                callDiv.style.cssText = "padding:0.5rem 0.8rem;border-top:1px solid var(--border);font-size:0.78rem;";

                const callMeta = document.createElement("div");
                callMeta.className = "stat-label";
                callMeta.textContent = "Call " + (i + 1) + " — " + (call.prompt_tokens || 0) + "→" + (call.completion_tokens || 0) + " tokens, " + formatTime(call.execution_time);
                callDiv.appendChild(callMeta);

                if (call.prompt) {
                    const promptDiv = document.createElement("div");
                    promptDiv.style.cssText = "margin-top:0.3rem;color:var(--text-secondary);";
                    const promptStr = typeof call.prompt === "string" ? call.prompt : JSON.stringify(call.prompt);
                    promptDiv.textContent = promptStr.slice(0, 300) + (promptStr.length > 300 ? "..." : "");
                    callDiv.appendChild(promptDiv);
                }

                if (call.response) {
                    const respDiv = document.createElement("div");
                    respDiv.style.cssText = "margin-top:0.3rem;color:var(--green);";
                    respDiv.textContent = call.response.slice(0, 300) + (call.response.length > 300 ? "..." : "");
                    callDiv.appendChild(respDiv);
                }

                container.appendChild(callDiv);
            });
        }

        // Locals (collapsed)
        const locals = result.locals || {};
        const localKeys = Object.keys(locals).filter(k => k !== "__builtins__");
        if (localKeys.length > 0) {
            const localsDiv = document.createElement("details");
            localsDiv.style.cssText = "border-top:1px solid var(--border);";
            const localsSummary = document.createElement("summary");
            localsSummary.style.cssText = "padding:0.3rem 0.8rem;font-size:0.8rem;cursor:pointer;color:var(--text-secondary);";
            localsSummary.textContent = "📦 Variables (" + localKeys.length + ")";
            localsDiv.appendChild(localsSummary);

            const localsContent = document.createElement("pre");
            localsContent.className = "mono";
            localsContent.style.cssText = "background:#0d1117;padding:0.5rem 0.8rem;margin:0;font-size:0.75rem;max-height:150px;overflow-y:auto;";
            const localsObj = {};
            localKeys.forEach(k => {
                const v = locals[k];
                localsObj[k] = typeof v === "string" ? (v.length > 100 ? v.slice(0, 100) + "..." : v) : typeof v;
            });
            localsContent.textContent = JSON.stringify(localsObj, null, 2);
            localsDiv.appendChild(localsContent);
            container.appendChild(localsDiv);
        }

        return container;
    }

    function buildIterationCard(iter) {
        const card = document.createElement("div");
        card.className = "card";

        // Header
        const header = document.createElement("div");
        header.style.cssText = "display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem;";

        const title = document.createElement("h2");
        title.textContent = "🔄 Iteration " + iter.iteration;
        header.appendChild(title);

        if (iter.iteration_time != null) {
            const timeBadge = document.createElement("span");
            timeBadge.style.cssText = "padding:0.2rem 0.6rem;border-radius:10px;font-size:0.75rem;font-weight:600;background:rgba(0,212,170,0.2);color:var(--green);";
            timeBadge.textContent = formatTime(iter.iteration_time);
            header.appendChild(timeBadge);
        }

        card.appendChild(header);

        // Prompt (collapsed)
        if (iter.prompt && iter.prompt.length > 0) {
            const promptDetails = document.createElement("details");
            promptDetails.style.marginBottom = "0.75rem";
            const promptSummary = document.createElement("summary");
            promptSummary.style.cssText = "font-size:0.85rem;cursor:pointer;color:var(--blue);font-weight:600;";
            promptSummary.textContent = "💬 Prompt (" + iter.prompt.length + " messages)";
            promptDetails.appendChild(promptSummary);

            const promptContent = document.createElement("div");
            promptContent.style.cssText = "margin-top:0.5rem;";
            iter.prompt.forEach((msg) => {
                const msgDiv = document.createElement("div");
                msgDiv.style.cssText = "margin-bottom:0.5rem;padding:0.5rem;border-radius:4px;font-size:0.78rem;";
                const roleColors = {
                    system: "background:rgba(78,168,222,0.1);border-left:3px solid var(--blue);",
                    user: "background:rgba(255,217,61,0.1);border-left:3px solid var(--yellow);",
                    assistant: "background:rgba(0,212,170,0.1);border-left:3px solid var(--green);",
                };
                msgDiv.style.cssText += roleColors[msg.role] || "";

                const roleLabel = document.createElement("div");
                roleLabel.style.cssText = "font-weight:600;font-size:0.75rem;color:var(--text-secondary);margin-bottom:0.2rem;";
                roleLabel.textContent = msg.role;
                msgDiv.appendChild(roleLabel);

                const content = document.createElement("pre");
                content.className = "mono";
                content.style.cssText = "white-space:pre-wrap;word-break:break-word;margin:0;font-size:0.75rem;max-height:200px;overflow-y:auto;";
                content.textContent = msg.content || "";
                msgDiv.appendChild(content);

                promptContent.appendChild(msgDiv);
            });
            promptDetails.appendChild(promptContent);
            card.appendChild(promptDetails);
        }

        // Response
        if (iter.response) {
            const respHeader = document.createElement("div");
            respHeader.style.cssText = "font-size:0.85rem;font-weight:600;color:var(--green);margin-bottom:0.3rem;";
            respHeader.textContent = "🤖 Response";
            card.appendChild(respHeader);

            const respEl = document.createElement("pre");
            respEl.className = "mono";
            respEl.style.cssText = "background:#0d1117;padding:0.8rem;border-radius:6px;font-size:0.78rem;max-height:300px;overflow-y:auto;white-space:pre-wrap;word-break:break-word;";
            respEl.textContent = iter.response;
            card.appendChild(respEl);
        }

        // Code blocks
        const codeBlocks = iter.code_blocks || [];
        if (codeBlocks.length > 0) {
            const cbHeader = document.createElement("div");
            cbHeader.style.cssText = "font-size:0.85rem;font-weight:600;margin:0.75rem 0 0.5rem;color:var(--text-primary);";
            cbHeader.textContent = "📝 Code Blocks (" + codeBlocks.length + ")";
            card.appendChild(cbHeader);

            codeBlocks.forEach((block, i) => {
                card.appendChild(buildCodeBlock(block, i));
            });
        }

        // Final answer
        if (iter.final_answer) {
            const faDiv = document.createElement("div");
            faDiv.style.cssText = "margin-top:0.75rem;padding:0.8rem;background:rgba(0,212,170,0.1);border:1px solid var(--green);border-radius:6px;";
            const faLabel = document.createElement("div");
            faLabel.style.cssText = "font-weight:700;color:var(--green);margin-bottom:0.3rem;font-size:0.85rem;";
            faLabel.textContent = "✅ Final Answer";
            faDiv.appendChild(faLabel);

            const faText = document.createElement("pre");
            faText.className = "mono";
            faText.style.cssText = "white-space:pre-wrap;word-break:break-word;margin:0;font-size:0.8rem;";
            const answer = Array.isArray(iter.final_answer) ? iter.final_answer[1] : iter.final_answer;
            faText.textContent = answer;
            faDiv.appendChild(faText);
            card.appendChild(faDiv);
        }

        return card;
    }

    function buildRunDetail(data) {
        const container = document.createElement("div");

        // Summary header
        const summaryCard = document.createElement("div");
        summaryCard.className = "card";
        const summaryTitle = document.createElement("h2");
        summaryTitle.textContent = "📊 Run Summary";
        summaryCard.appendChild(summaryTitle);

        // Config metadata
        const meta = data.metadata || {};
        if (meta.root_model || meta.backend) {
            const configDiv = document.createElement("div");
            configDiv.style.cssText = "margin-bottom:0.75rem;font-size:0.8rem;color:var(--text-secondary);";
            const parts = [];
            if (meta.root_model) parts.push("Model: " + meta.root_model);
            if (meta.backend) parts.push("Backend: " + meta.backend);
            if (meta.max_depth) parts.push("Depth: " + meta.max_depth);
            if (meta.max_iterations) parts.push("Max iter: " + meta.max_iterations);
            if (meta.environment_type) parts.push("Env: " + meta.environment_type);
            configDiv.textContent = parts.join(" • ");
            summaryCard.appendChild(configDiv);
        }

        summaryCard.appendChild(buildStatsBar(data.summary));

        // Final answer in summary
        if (data.summary.final_answer) {
            const faDiv = document.createElement("div");
            faDiv.style.cssText = "margin-top:0.75rem;padding:0.6rem;background:rgba(0,212,170,0.1);border-radius:4px;font-size:0.85rem;";
            faDiv.innerHTML = '<strong style="color:var(--green);">Final:</strong> ' + escapeHtml(data.summary.final_answer);
            summaryCard.appendChild(faDiv);
        }

        container.appendChild(summaryCard);

        // Iterations
        const iterations = data.iterations || [];
        iterations.forEach((iter) => {
            container.appendChild(buildIterationCard(iter));
        });

        if (iterations.length === 0) {
            const empty = document.createElement("div");
            empty.className = "card";
            empty.innerHTML = '<p class="stat-label">No iterations recorded in this run.</p>';
            container.appendChild(empty);
        }

        return container;
    }

    function buildRunList(runs, onSelect) {
        const list = document.createElement("div");

        if (!runs || runs.length === 0) {
            list.innerHTML = '<div class="card"><p class="stat-label">No RLM runs found. RLM trajectory logs appear here after rlm_repl tool calls.</p></div>';
            return list;
        }

        runs.forEach((run) => {
            const row = document.createElement("div");
            row.className = "card";
            row.style.cursor = "pointer";
            row.style.transition = "border-color 0.2s";
            row.addEventListener("mouseenter", () => { row.style.borderColor = "var(--green)"; });
            row.addEventListener("mouseleave", () => { row.style.borderColor = "var(--border)"; });

            // Top row: filename + time
            const topRow = document.createElement("div");
            topRow.style.cssText = "display:flex;justify-content:space-between;align-items:center;";

            const name = document.createElement("div");
            name.style.fontWeight = "600";
            name.textContent = "🔄 " + run.file;
            topRow.appendChild(name);

            const meta = document.createElement("span");
            meta.className = "stat-label";
            const ageMin = Math.floor(run.age_seconds / 60);
            meta.textContent = formatSize(run.size) + " • " + (ageMin < 60 ? ageMin + "m ago" : Math.floor(ageMin / 60) + "h ago");
            topRow.appendChild(meta);
            row.appendChild(topRow);

            // Context question
            if (run.context_question) {
                const question = document.createElement("div");
                question.style.cssText = "margin-top:0.3rem;font-size:0.8rem;color:var(--text-secondary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;";
                question.textContent = "📋 " + run.context_question;
                row.appendChild(question);
            }

            // Stats row
            const statsRow = document.createElement("div");
            statsRow.style.cssText = "display:flex;gap:1rem;margin-top:0.5rem;font-size:0.8rem;";
            const items = [
                "🔄 " + run.iterations + " iter",
                "📝 " + run.code_blocks + " blocks",
                "🧠 " + run.sub_lm_calls + " sub-calls",
                "⏱ " + formatTime(run.execution_time),
            ];
            if (run.has_errors) items.push("⚠️ errors");
            statsRow.textContent = items.join(" • ");
            row.appendChild(statsRow);

            // Model info
            if (run.metadata && run.metadata.root_model) {
                const modelDiv = document.createElement("div");
                modelDiv.className = "stat-label";
                modelDiv.textContent = "Model: " + run.metadata.root_model;
                row.appendChild(modelDiv);
            }

            row.addEventListener("click", () => onSelect(run.file));
            list.appendChild(row);
        });

        return list;
    }

    window.panels = window.panels || {};
    window.panels.rlm = function (app, fetchApi) {
        app.innerHTML = '<p class="stat-label" style="padding:1rem;">Loading RLM runs...</p>';

        let currentView = "list"; // "list" or "detail"
        let currentFile = null;

        function showList() {
            currentView = "list";
            currentFile = null;
            app.innerHTML = '<p class="stat-label" style="padding:1rem;">Loading RLM runs...</p>';

            fetchApi("/api/rlm").then((runs) => {
                app.innerHTML = "";

                const header = document.createElement("div");
                header.style.cssText = "display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;";
                const title = document.createElement("h2");
                title.style.cssText = "font-size:1.2rem;color:var(--green);margin:0;";
                title.textContent = "🔄 RLM Trajectories";
                header.appendChild(title);

                const count = document.createElement("span");
                count.className = "stat-label";
                count.textContent = runs.length + " runs";
                header.appendChild(count);
                app.appendChild(header);

                app.appendChild(buildRunList(runs, showDetail));
            }).catch((err) => {
                console.error("[RLM] Failed:", err);
                app.innerHTML = '<div class="card"><p style="color:var(--red);">Failed to load RLM runs: ' + escapeHtml(err.message || err) + '</p></div>';
            });
        }

        function showDetail(filename) {
            currentView = "detail";
            currentFile = filename;
            app.innerHTML = '<p class="stat-label" style="padding:1rem;">Loading run details...</p>';

            fetchApi("/api/rlm/" + encodeURIComponent(filename)).then((data) => {
                app.innerHTML = "";

                // Back button
                const backBtn = document.createElement("button");
                backBtn.textContent = "← Back to runs";
                backBtn.style.cssText = "background:var(--bg-accent);color:var(--text-primary);border:1px solid var(--border);border-radius:6px;padding:0.4rem 0.8rem;cursor:pointer;font-size:0.85rem;margin-bottom:1rem;";
                backBtn.addEventListener("click", showList);
                app.appendChild(backBtn);

                app.appendChild(buildRunDetail(data));
            }).catch((err) => {
                console.error("[RLM] Detail error:", err);
                app.innerHTML = '<div class="card"><p style="color:var(--red);">Failed to load run: ' + escapeHtml(err.message || err) + '</p></div>' +
                    '<button onclick="window.panels.rlm(document.getElementById(\'app\'), window.fetchApi)" style="background:var(--bg-accent);color:var(--text-primary);border:1px solid var(--border);border-radius:6px;padding:0.4rem 0.8rem;cursor:pointer;">← Back</button>';
            });
        }

        showList();
    };
})();
