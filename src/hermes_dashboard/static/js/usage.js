/* Hermes Dashboard — Usage/Tokens Panel */
(function () {
    "use strict";

    function fmt(n) {
        if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
        if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
        return String(n);
    }

    function fmtCost(usd) {
        if (!usd) return "$0.00";
        if (usd < 0.01) return "$" + usd.toFixed(4);
        return "$" + usd.toFixed(2);
    }

    function fmtDate(ts) {
        if (!ts) return "—";
        var d = typeof ts === "number" ? new Date(ts * 1000) : new Date(ts);
        return d.toLocaleDateString() + " " + d.toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"});
    }

    function card(label, value, color) {
        var el = document.createElement("div");
        el.className = "card";
        el.style.cssText = "text-align:center;padding:0.8rem;";
        el.innerHTML = '<div style="font-size:1.5rem;font-weight:700;color:' + (color||"var(--green)") + ';">' + value + '</div><div class="stat-label">' + label + '</div>';
        return el;
    }

    function table(headers, rows) {
        var t = document.createElement("table");
        t.style.cssText = "width:100%;border-collapse:collapse;font-size:0.85rem;";
        var thtml = "<thead><tr>";
        headers.forEach(function(h) { thtml += '<th style="text-align:left;padding:0.4rem 0.6rem;border-bottom:1px solid var(--border);color:var(--text-secondary);font-weight:600;">' + h + '</th>'; });
        thtml += "</tr></thead><tbody>";
        rows.forEach(function(r) {
            thtml += '<tr style="border-bottom:1px solid var(--border);">';
            r.forEach(function(c) { thtml += '<td style="padding:0.4rem 0.6rem;">' + c + '</td>'; });
            thtml += "</tr>";
        });
        thtml += "</tbody>";
        t.innerHTML = thtml;
        return t;
    }

    function section(title) {
        var h = document.createElement("h3");
        h.style.cssText = "margin:1.2rem 0 0.6rem;font-size:1rem;";
        h.textContent = title;
        return h;
    }

    var timer = null;

    window.panels = window.panels || {};
    window.panels.usage = function (app, fetchApi) {
        app.innerHTML = "";

        /* --- Filter bar --- */
        var bar = document.createElement("div");
        bar.className = "card";
        bar.style.cssText = "display:flex;gap:0.8rem;flex-wrap:wrap;align-items:center;";

        function makeInput(type, placeholder) {
            var inp = document.createElement("input");
            inp.type = type;
            inp.placeholder = placeholder;
            inp.style.cssText = "padding:0.3rem 0.5rem;background:var(--bg-primary);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);font-size:0.85rem;";
            return inp;
        }

        function makeSelect() {
            var sel = document.createElement("select");
            sel.style.cssText = "padding:0.3rem 0.5rem;background:var(--bg-primary);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);font-size:0.85rem;";
            return sel;
        }

        var dateFrom = makeInput("date", "From");
        var dateTo = makeInput("date", "To");
        var provSel = makeSelect();
        var modelSel = makeSelect();

        function addFilter(lbl, el) {
            var s = document.createElement("span");
            s.className = "stat-label";
            s.textContent = lbl;
            bar.appendChild(s);
            bar.appendChild(el);
        }
        addFilter("From:", dateFrom);
        addFilter("To:", dateTo);
        addFilter("Provider:", provSel);
        addFilter("Model:", modelSel);
        app.appendChild(bar);

        var content = document.createElement("div");
        app.appendChild(content);

        function loadData() {
            content.innerHTML = '<p class="stat-label" style="padding:1rem;">Loading...</p>';
            var p = new URLSearchParams();
            if (dateFrom.value) p.set("date_from", dateFrom.value);
            if (dateTo.value) p.set("date_to", dateTo.value);
            if (provSel.value) p.set("provider", provSel.value);
            if (modelSel.value) p.set("model", modelSel.value);
            var qs = p.toString();
            fetchApi("/api/usage" + (qs ? "?" + qs : "")).then(function (d) {
                content.innerHTML = "";
                if (!d || !d.totals) { content.innerHTML = '<div class="card"><p class="stat-label">No data.</p></div>'; return; }

                /* populate dropdowns once */
                if (provSel.options.length <= 1 && d.providers) {
                    provSel.innerHTML = '<option value="">All Providers</option>';
                    d.providers.forEach(function(v) { provSel.innerHTML += '<option value="'+v+'">'+v+'</option>'; });
                }
                if (modelSel.options.length <= 1 && d.models) {
                    modelSel.innerHTML = '<option value="">All Models</option>';
                    d.models.forEach(function(v) {
                        var label = v.length > 50 ? v.slice(0,47)+"..." : v;
                        modelSel.innerHTML += '<option value="'+v+'">'+label+'</option>';
                    });
                }

                var t = d.totals;
                var row = document.createElement("div");
                row.style.cssText = "display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:0.5rem;margin-bottom:1rem;";
                row.appendChild(card("Sessions", fmt(t.sessions), "var(--blue)"));
                row.appendChild(card("Input", fmt(t.input_tokens), "var(--green)"));
                row.appendChild(card("Output", fmt(t.output_tokens), "var(--yellow)"));
                row.appendChild(card("Total", fmt(t.total_tokens)));
                row.appendChild(card("Tools", fmt(t.tool_calls), "var(--blue)"));
                row.appendChild(card("Messages", fmt(t.messages), "var(--text-secondary)"));
                row.appendChild(card("Cost", fmtCost(t.estimated_cost_usd), "var(--green)"));
                content.appendChild(row);

                if (d.calendar && d.calendar.length) {
                    content.appendChild(section("Daily Breakdown"));
                    content.appendChild(table(["Date","Sessions","In","Out","Total","Cost"],
                        d.calendar.map(function(c) { return [c.date,fmt(c.sessions),fmt(c.input_tokens),fmt(c.output_tokens),fmt(c.total_tokens),fmtCost(c.estimated_cost_usd)]; })
                    ));
                }

                if (d.top_sessions && d.top_sessions.length) {
                    content.appendChild(section("Top Sessions"));
                    content.appendChild(table(["Session","Agent","Model","Provider","In","Out","Total","Tools","Cost"],
                        d.top_sessions.map(function(s) {
                            var sid = s.id.length>16 ? s.id.slice(0,14)+".." : s.id;
                            var m = (s.model||"?").split("/").pop();
                            if (m.length>20) m = m.slice(0,17)+"...";
                            return [sid, s.agent_name||"?", m, s.provider||"?", fmt(s.input_tokens), fmt(s.output_tokens), fmt(s.total_tokens), s.tool_calls, fmtCost(s.estimated_cost_usd)];
                        })
                    ));
                }
            }).catch(function(err) {
                console.error("[Usage]", err);
                content.innerHTML = '<div class="card"><p style="color:var(--red);">Failed: '+(err.message||err)+'</p></div>';
            });
        }

        function onChange() { clearTimeout(timer); timer = setTimeout(loadData, 300); }
        dateFrom.addEventListener("change", onChange);
        dateTo.addEventListener("change", onChange);
        provSel.addEventListener("change", onChange);
        modelSel.addEventListener("change", onChange);

        loadData();
    };
})();
