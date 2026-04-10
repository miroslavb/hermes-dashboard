/* Hermes Dashboard — System Panel */
(function () {
    "use strict";

    const HISTORY_LEN = 60;
    let cpuHistory = [];
    let ramHistory = [];
    let chart = null;
    let sse = null;

    function createGauge(label, value, unit, color) {
        const card = document.createElement("div");
        card.className = "card";
        const val = document.createElement("div");
        val.className = "stat-value";
        val.style.color = color;
        val.textContent = value + unit;
        const lbl = document.createElement("div");
        lbl.className = "stat-label";
        lbl.textContent = label;
        card.appendChild(val);
        card.appendChild(lbl);
        return { card, val };
    }

    function createProgressBar(label, value, total, unit, color) {
        const card = document.createElement("div");
        card.className = "card";
        const title = document.createElement("div");
        title.className = "stat-label";
        title.textContent = label;
        const val = document.createElement("div");
        val.className = "stat-value";
        val.style.color = color;
        val.textContent = value + " / " + total + " " + unit;
        const bar = document.createElement("div");
        bar.className = "progress-bar";
        const fill = document.createElement("div");
        fill.className = "fill";
        fill.style.background = color;
        fill.style.width = "0%";
        bar.appendChild(fill);
        card.appendChild(title);
        card.appendChild(val);
        card.appendChild(bar);
        return { card, fill, val };
    }

    function buildChart(canvas) {
        const ctx = canvas.getContext("2d");
        chart = new Chart(ctx, {
            type: "line",
            data: {
                labels: Array(HISTORY_LEN).fill(""),
                datasets: [
                    {
                        label: "CPU %",
                        data: [],
                        borderColor: "#00d4aa",
                        backgroundColor: "rgba(0,212,170,0.1)",
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3,
                        pointRadius: 0,
                    },
                    {
                        label: "RAM %",
                        data: [],
                        borderColor: "#4ea8de",
                        backgroundColor: "rgba(78,168,222,0.1)",
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3,
                        pointRadius: 0,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 300 },
                scales: {
                    x: { display: false },
                    y: {
                        min: 0,
                        max: 100,
                        ticks: { color: "#a0a0a0", stepSize: 25 },
                        grid: { color: "rgba(255,255,255,0.05)" },
                    },
                },
                plugins: {
                    legend: {
                        labels: { color: "#e0e0e0", usePointStyle: true, pointStyle: "line" },
                    },
                },
            },
        });
    }

    function updateData(data, gauges) {
        // CPU
        gauges.cpuVal.textContent = data.cpu_percent.toFixed(1) + "%";
        gauges.cpuBar.val.textContent = data.cpu_percent.toFixed(1) + "% (" + data.cpu_count + " cores)";
        gauges.cpuBar.fill.style.width = data.cpu_percent + "%";
        if (data.cpu_percent > 80) gauges.cpuBar.fill.style.background = "var(--red)";
        else if (data.cpu_percent > 50) gauges.cpuBar.fill.style.background = "var(--yellow)";
        else gauges.cpuBar.fill.style.background = "var(--green)";

        // RAM
        gauges.ramVal.textContent = data.ram_percent.toFixed(1) + "%";
        gauges.ramBar.val.textContent = data.ram_used_gb.toFixed(1) + " / " + data.ram_total_gb.toFixed(1) + " GB";
        gauges.ramBar.fill.style.width = data.ram_percent + "%";
        if (data.ram_percent > 80) gauges.ramBar.fill.style.background = "var(--red)";
        else if (data.ram_percent > 50) gauges.ramBar.fill.style.background = "var(--yellow)";
        else gauges.ramBar.fill.style.background = "var(--blue)";

        // Disk
        gauges.diskBar.val.textContent = data.disk_used_gb.toFixed(1) + " / " + data.disk_total_gb.toFixed(1) + " GB";
        gauges.diskBar.fill.style.width = data.disk_percent + "%";
        if (data.disk_percent > 80) gauges.diskBar.fill.style.background = "var(--red)";
        else gauges.diskBar.fill.style.background = "var(--green)";

        // Network
        gauges.netVal.textContent = "↑" + data.net_sent_mb.toFixed(1) + " MB  ↓" + data.net_recv_mb.toFixed(1) + " MB";

        // Uptime
        const days = Math.floor(data.uptime_seconds / 86400);
        const hrs = Math.floor((data.uptime_seconds % 86400) / 3600);
        const mins = Math.floor((data.uptime_seconds % 3600) / 60);
        gauges.uptimeVal.textContent = days + "d " + hrs + "h " + mins + "m";

        // Info
        gauges.infoCard.textContent = data.hostname + " | " + data.os + " | Python " + data.python_version;

        // Chart history
        cpuHistory.push(data.cpu_percent);
        ramHistory.push(data.ram_percent);
        if (cpuHistory.length > HISTORY_LEN) cpuHistory.shift();
        if (ramHistory.length > HISTORY_LEN) ramHistory.shift();
        if (chart) {
            chart.data.datasets[0].data = cpuHistory;
            chart.data.datasets[1].data = ramHistory;
            chart.update("none");
        }
    }

    window.panels = window.panels || {};
    window.panels.system = function (app, fetchApi) {
        cpuHistory = [];
        ramHistory = [];
        if (sse) { sse.close(); sse = null; }

        app.innerHTML = "";

        const gauges = {};

        // Row 1: CPU + RAM + Disk gauges
        const row1 = document.createElement("div");
        row1.className = "grid";
        gauges.cpuBar = createProgressBar("CPU", "0", "", "%", "var(--green)");
        gauges.ramBar = createProgressBar("RAM", "0", "", "GB", "var(--blue)");
        gauges.diskBar = createProgressBar("Disk", "0", "", "GB", "var(--green)");
        row1.appendChild(gauges.cpuBar.card);
        row1.appendChild(gauges.ramBar.card);
        row1.appendChild(gauges.diskBar.card);

        // Row 2: Network + Uptime + Info
        const row2 = document.createElement("div");
        row2.className = "grid";
        const netGauge = createGauge("Network", "↑0 MB  ↓0 MB", "", "var(--yellow)");
        gauges.netVal = netGauge.val;
        const upGauge = createGauge("Uptime", "0d 0h 0m", "", "var(--green)");
        gauges.uptimeVal = upGauge.val;
        const infoCard = document.createElement("div");
        infoCard.className = "card mono";
        gauges.infoCard = infoCard;
        row2.appendChild(netGauge.card);
        row2.appendChild(upGauge.card);
        row2.appendChild(infoCard);

        // Row 3: Chart
        const chartCard = document.createElement("div");
        chartCard.className = "card";
        const chartTitle = document.createElement("h2");
        chartTitle.textContent = "CPU / RAM History";
        const chartWrap = document.createElement("div");
        chartWrap.style.height = "200px";
        const canvas = document.createElement("canvas");
        chartWrap.appendChild(canvas);
        chartCard.appendChild(chartTitle);
        chartCard.appendChild(chartWrap);

        // Stub val references for CPU/RAM percentage display
        gauges.cpuVal = gauges.cpuBar.val;
        gauges.ramVal = gauges.ramBar.val;

        app.appendChild(row1);
        app.appendChild(row2);
        app.appendChild(chartCard);

        buildChart(canvas);

        // Initial fetch
        fetchApi("/api/system/status").then((data) => updateData(data, gauges)).catch(() => {});

        // SSE live update
        sse = window.createSSE("/api/system/stream", (data) => {
            if (data && typeof data.cpu_percent === "number") {
                updateData(data, gauges);
            }
        });
    };
})();
