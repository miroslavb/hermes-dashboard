/* Hermes Dashboard — Cron Panel */
(function () {
    "use strict";

    function formatDate(iso) {
        if (!iso) return "—";
        return new Date(iso).toLocaleString();
    }

    function buildJobList(jobs, onSelect) {
        const list = document.createElement("div");
        jobs.forEach((job) => {
            const row = document.createElement("div");
            row.className = "card";
            row.style.cursor = "pointer";

            const header = document.createElement("div");
            header.style.cssText = "display:flex;justify-content:space-between;align-items:center;";
            const name = document.createElement("div");
            name.style.fontWeight = "600";
            name.textContent = "⏰ " + (job.name || job.id);
            const status = document.createElement("span");
            status.textContent = job.status || "unknown";
            status.style.cssText = "padding:0.2rem 0.6rem;border-radius:10px;font-size:0.75rem;font-weight:600;" +
                (job.status === "active" ? "background:rgba(0,212,170,0.2);color:var(--green);" : "background:rgba(255,107,107,0.2);color:var(--red);");
            header.appendChild(name);
            header.appendChild(status);

            const schedule = document.createElement("div");
            schedule.className = "stat-label";
            schedule.textContent = "Schedule: " + (job.schedule || "—");

            const prompt = document.createElement("div");
            prompt.className = "mono";
            prompt.style.cssText = "margin-top:0.5rem;font-size:0.8rem;color:var(--text-secondary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:100%;";
            prompt.textContent = job.prompt || "";

            const lastRun = document.createElement("div");
            lastRun.className = "stat-label";
            lastRun.textContent = "Last run: " + formatDate(job.last_run);

            row.appendChild(header);
            row.appendChild(schedule);
            row.appendChild(prompt);
            row.appendChild(lastRun);

            list.appendChild(row);
        });
        return list;
    }

    function buildOutputViewer(outputs) {
        const card = document.createElement("div");
        card.className = "card";
        const title = document.createElement("h2");
        title.textContent = "📄 Recent Output";
        card.appendChild(title);

        if (!outputs || outputs.length === 0) {
            const empty = document.createElement("div");
            empty.className = "stat-label";
            empty.textContent = "No output files.";
            card.appendChild(empty);
            return card;
        }

        outputs.forEach((o) => {
            const row = document.createElement("div");
            row.style.cssText = "margin-bottom:0.75rem;padding-bottom:0.75rem;border-bottom:1px solid var(--border);";
            const header = document.createElement("div");
            header.style.cssText = "display:flex;justify-content:space-between;";
            const name = document.createElement("span");
            name.className = "mono";
            name.textContent = o.file;
            const meta = document.createElement("span");
            meta.className = "stat-label";
            meta.textContent = (o.size / 1024).toFixed(1) + " KB • " + Math.floor(o.age_seconds / 60) + "m ago";
            header.appendChild(name);
            header.appendChild(meta);
            row.appendChild(header);

            if (o.preview) {
                const preview = document.createElement("pre");
                preview.className = "mono log-box";
                preview.style.maxHeight = "150px";
                preview.style.fontSize = "0.75rem";
                preview.textContent = o.preview;
                row.appendChild(preview);
            }
            card.appendChild(row);
        });
        return card;
    }

    window.panels = window.panels || {};
    window.panels.cron = function (app, fetchApi) {
        app.innerHTML = '<p class="stat-label" style="padding:1rem;">Loading...</p>';

        Promise.all([
            fetchApi("/api/cron").catch(() => []),
            fetchApi("/api/cron/output").catch(() => []),
        ]).then(([jobs, outputs]) => {
            app.innerHTML = "";

            const jobsCard = document.createElement("div");
            jobsCard.className = "card";
            const jobsTitle = document.createElement("h2");
            jobsTitle.textContent = "Scheduled Jobs";
            jobsCard.appendChild(jobsTitle);

            if (!jobs || jobs.length === 0) {
                const empty = document.createElement("div");
                empty.className = "stat-label";
                empty.textContent = "No cron jobs configured.";
                jobsCard.appendChild(empty);
            }
            app.appendChild(jobsCard);

            if (jobs && jobs.length > 0) {
                app.appendChild(buildJobList(jobs));
            }
            app.appendChild(buildOutputViewer(outputs));
        }).catch(() => {
            app.innerHTML = '<div class="card"><p style="color:var(--red);">Failed to load cron data.</p></div>';
        });
    };
})();
