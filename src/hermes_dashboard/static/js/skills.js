/* Hermes Dashboard — Skills Panel */
(function () {
    "use strict";

    function buildCategoryGrid(categories, onSelect) {
        const grid = document.createElement("div");
        grid.className = "grid";
        categories.forEach((cat) => {
            const card = document.createElement("div");
            card.className = "card";
            card.style.cursor = "pointer";
            const title = document.createElement("h2");
            title.textContent = "📁 " + cat.name;
            const desc = document.createElement("div");
            desc.className = "stat-label";
            desc.textContent = cat.description || "";
            const count = document.createElement("div");
            count.style.marginTop = "0.5rem";
            count.style.color = "var(--green)";
            count.textContent = cat.skill_count + " skill(s)";
            card.appendChild(title);
            card.appendChild(desc);
            card.appendChild(count);
            card.addEventListener("click", () => onSelect(cat.name));
            grid.appendChild(card);
        });
        return grid;
    }

    function buildSkillList(skills, category, onSelect, onBack) {
        const container = document.createElement("div");
        const back = document.createElement("button");
        back.textContent = "← All categories";
        back.style.cssText = "background:var(--bg-accent);color:var(--text-primary);border:1px solid var(--border);padding:0.4rem 1rem;border-radius:6px;cursor:pointer;margin-bottom:1rem;";
        back.addEventListener("click", onBack);
        container.appendChild(back);

        const title = document.createElement("h2");
        title.textContent = category;
        title.style.marginBottom = "1rem";
        container.appendChild(title);

        const grid = document.createElement("div");
        grid.className = "grid";
        skills.forEach((sk) => {
            const card = document.createElement("div");
            card.className = "card";
            card.style.cursor = "pointer";
            const name = document.createElement("div");
            name.style.fontWeight = "600";
            name.textContent = "🔧 " + sk.name;
            const desc = document.createElement("div");
            desc.className = "stat-label";
            desc.textContent = sk.description || "";
            card.appendChild(name);
            card.appendChild(desc);
            if (sk.tags && sk.tags.length) {
                const tags = document.createElement("div");
                tags.style.marginTop = "0.5rem";
                sk.tags.forEach((t) => {
                    const badge = document.createElement("span");
                    badge.textContent = t;
                    badge.style.cssText = "display:inline-block;background:var(--bg-accent);color:var(--blue);padding:0.15rem 0.5rem;border-radius:10px;font-size:0.75rem;margin-right:0.3rem;";
                    tags.appendChild(badge);
                });
                card.appendChild(tags);
            }
            card.addEventListener("click", () => onSelect(category, sk.name));
            grid.appendChild(card);
        });
        container.appendChild(grid);
        return container;
    }

    function buildSkillViewer(skill, onBack) {
        const container = document.createElement("div");
        const back = document.createElement("button");
        back.textContent = "← Back to skills";
        back.style.cssText = "background:var(--bg-accent);color:var(--text-primary);border:1px solid var(--border);padding:0.4rem 1rem;border-radius:6px;cursor:pointer;margin-bottom:1rem;";
        back.addEventListener("click", onBack);
        container.appendChild(back);

        const card = document.createElement("div");
        card.className = "card";
        const title = document.createElement("h2");
        title.textContent = "🔧 " + skill.name;
        const meta = document.createElement("div");
        meta.className = "stat-label";
        meta.textContent = "Category: " + skill.category;
        const content = document.createElement("pre");
        content.className = "mono log-box";
        content.style.maxHeight = "600px";
        content.textContent = skill.content || "(empty)";
        card.appendChild(title);
        card.appendChild(meta);
        card.appendChild(content);
        container.appendChild(card);
        return container;
    }

    window.panels = window.panels || {};
    window.panels.skills = function (app, fetchApi) {
        app.innerHTML = "";
        let activeAgent = "";

        function showCategories() {
            app.innerHTML = '<p class="stat-label" style="padding:1rem;">Loading categories...</p>';
            fetchApi("/api/skills").then((data) => {
                app.innerHTML = "";
                // Multi-agent: {hermes: {name, categories:[...]}, hermes2: {...}}
                const agentIds = Object.keys(data);
                if (!agentIds || agentIds.length === 0) {
                    app.innerHTML = '<div class="card"><p class="stat-label">No skills found.</p></div>';
                    return;
                }
                for (const agentId of agentIds) {
                    const ag = data[agentId];
                    const cats = ag.categories || [];
                    if (cats.length === 0) continue;
                    // Agent header
                    const h = document.createElement("h3");
                    h.textContent = "🧠 " + ag.name;
                    h.style.margin = "1rem 0 0.5rem";
                    app.appendChild(h);
                    // Wrap showSkillList per agent
                    const grid = buildCategoryGrid(cats, (catName) => showSkillList(agentId, catName));
                    app.appendChild(grid);
                }
            }).catch((err) => {
                console.error("[Skills] Failed to load:", err);
                app.innerHTML = '<div class="card"><p style="color:var(--red);">Failed to load skills: ' + (err.message || err) + '</p></div>';
            });
        }

        function showSkillList(agentId, category) {
            app.innerHTML = '<p class="stat-label" style="padding:1rem;">Loading skills...</p>';
            const agentQ = agentId ? ("?agent=" + encodeURIComponent(agentId)) : "";
            fetchApi("/api/skills/" + encodeURIComponent(category) + agentQ).then((skills) => {
                app.innerHTML = "";
                if (!skills || skills.length === 0) {
                    app.innerHTML = '<div class="card"><p class="stat-label">No skills in this category.</p></div>';
                    return;
                }
                app.appendChild(buildSkillList(skills, category, (cat, name) => showSkillDetail(agentId, cat, name), showCategories));
            }).catch((err) => {
                console.error("[Skills] Failed to load category:", err);
                app.innerHTML = '<div class="card"><p style="color:var(--red);">Failed to load skills: ' + (err.message || err) + '</p></div>';
            });
        }

        function showSkillDetail(agentId, category, name) {
            app.innerHTML = '<p class="stat-label" style="padding:1rem;">Loading skill...</p>';
            const agentQ = agentId ? ("?agent=" + encodeURIComponent(agentId)) : "";
            fetchApi("/api/skills/" + encodeURIComponent(category) + "/" + encodeURIComponent(name) + agentQ).then((skill) => {
                app.innerHTML = "";
                app.appendChild(buildSkillViewer(skill, () => showSkillList(agentId, category)));
            }).catch((err) => {
                console.error("[Skills] Failed to load skill:", err);
                app.innerHTML = '<div class="card"><p style="color:var(--red);">Failed to load skill: ' + (err.message || err) + '</p></div>';
            });
        }

        showCategories();
    };
})();
