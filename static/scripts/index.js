const COLORS = {
    Streaming: "#a78bfa",
    Gaming: "#60a5fa",
    Messaging: "#34d399",
    Social: "#fb7185",
    Browsing: "#fbbf24",
};

const ctx = document.getElementById("donut");
const chart = new Chart(ctx, {
    type: "doughnut",
    data: {
        labels: ["No data yet"],
        datasets: [
            {
                data: [1],
                backgroundColor: ["rgba(255,255,255,0.12)"],
                borderColor: ["rgba(255,255,255,0.18)"],
                borderWidth: 1,
                hoverOffset: 6,
            },
        ],
    },
    options: {
        responsive: true,
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: (ctx) => {
                        const label = ctx.label || "";
                        const val = ctx.raw ?? 0;
                        return `${label}: ${val}%`;
                    },
                },
            },
        },
        cutout: "68%",
    },
});

function setText(id, text) {
    document.getElementById(id).textContent = text;
}

function show(el, on) {
    el.style.display = on ? "block" : "none";
}

function renderList(categories) {
    const list = document.getElementById("list");
    list.innerHTML = "";
    if (!categories?.length) {
        const row = document.createElement("div");
        row.className = "row";

        const dot = document.createElement("div");
        dot.className = "dot";
        dot.style.background = "rgba(255,255,255,0.28)";

        const name = document.createElement("div");
        name.className = "name";
        name.textContent = "No categories yet";

        const val = document.createElement("div");
        val.className = "val";
        val.textContent = "Waiting for DNS traffic…";

        row.appendChild(dot);
        row.appendChild(name);
        row.appendChild(val);
        list.appendChild(row);
        return;
    }
    for (const c of categories) {
        const color = COLORS[c.name] || "rgba(255,255,255,0.5)";
        const row = document.createElement("div");
        row.className = "row";

        const dot = document.createElement("div");
        dot.className = "dot";
        dot.style.background = color;

        const name = document.createElement("div");
        name.className = "name";
        name.textContent = c.name;

        const val = document.createElement("div");
        val.className = "val";
        val.textContent = `${c.percent}%  •  ${c.queries} queries`;

        row.appendChild(dot);
        row.appendChild(name);
        row.appendChild(val);
        list.appendChild(row);
    }
}

function updateChart(categories, total) {
    if (!total) {
        chart.data.labels = ["No data yet"];
        chart.data.datasets[0].data = [1];
        chart.data.datasets[0].backgroundColor = ["rgba(255,255,255,0.12)"];
        chart.data.datasets[0].borderColor = ["rgba(255,255,255,0.18)"];
        chart.update();
        return;
    }

    const labels = categories.map((c) => c.name);
    const data = categories.map((c) => c.percent);
    const bg = categories.map((c) => COLORS[c.name] || "rgba(255,255,255,0.5)");

    chart.data.labels = labels;
    chart.data.datasets[0].data = data;
    chart.data.datasets[0].backgroundColor = bg;
    chart.data.datasets[0].borderColor = bg.map(() => "rgba(0,0,0,0)");
    chart.update();
}

function fmtUpdated(iso) {
    try {
        const d = new Date(iso);
        return d.toLocaleString();
    } catch {
        return iso || "—";
    }
}

async function refresh() {
    const err = document.getElementById("err");
    const ok = document.getElementById("ok");
    show(err, false);
    show(ok, false);

    try {
        const res = await fetch("/api/stats", { cache: "no-store" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        setText("updated", `Last updated: ${fmtUpdated(data.updated)}`);
        setText("total", `Total DNS queries: ${data.total_queries}`);

        const cap = data.capture || {};
        const capText = cap.running
            ? `running on ${cap.iface || "?"}`
            : `stopped${cap.iface ? ` (iface ${cap.iface})` : ""}`;
        setText("capture", `Capture: ${capText}`);

        const status = document.getElementById("status");
        if (!data.total_queries) {
            status.textContent = "No data yet — traffic will appear within a minute.";
        } else {
            status.textContent = "Live breakdown (DNS query count).";
        }

        if (cap.last_error) {
            err.textContent = cap.last_error;
            show(err, true);
        } else if (cap.running) {
            ok.textContent = "tcpdump is running.";
            show(ok, true);
        }

        const cats = data.categories || [];
        updateChart(cats, data.total_queries);
        renderList(cats);
    } catch (e) {
        setText("updated", "Last updated: —");
        setText("total", "Total DNS queries: —");
        setText("capture", "Capture: —");
        document.getElementById("status").textContent =
            "Couldn’t reach the backend. Is it running on http://localhost:8080 ?";
        err.textContent = String(e);
        show(err, true);
    }
}

refresh();
setInterval(refresh, 30_000);
