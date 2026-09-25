// Store charts
let charts = {};

// Destroy old charts
function destroyCharts() {
    for (let key in charts) {
        charts[key].destroy();
    }
    charts = {};
}

// Render all charts
function renderCharts(data) {
    destroyCharts();

    // BAR
    charts.bar = new Chart(document.getElementById("barChart"), {
        type: "bar",
        data: {
            labels: data.bar.labels,
            datasets: [{
                label: "Bar Data",
                data: data.bar.data,
                backgroundColor: "#38bdf8"
            }]
        }
    });

    // LINE
    charts.line = new Chart(document.getElementById("lineChart"), {
        type: "line",
        data: {
            labels: data.line.labels,
            datasets: [{
                label: "Trend",
                data: data.line.data,
                borderColor: "#22c55e",
                fill: false
            }]
        }
    });

    // PIE
    charts.pie = new Chart(document.getElementById("pieChart"), {
        type: "pie",
        data: {
            labels: data.pie.labels,
            datasets: [{
                data: data.pie.data,
                backgroundColor: [
                    "#38bdf8", "#f43f5e", "#22c55e", "#eab308", "#a855f7"
                ]
            }]
        }
    });

    // HEATMAP (correlation)
    charts.heatmap = new Chart(document.getElementById("heatmapChart"), {
        type: "bar", // still simple version
        data: {
            labels: data.heatmap.labels,
            datasets: [{
                label: "Correlation",
                data: data.heatmap.data,
                backgroundColor: "#f97316"
            }]
        }
    });
}

// Upload CSV
async function upload() {
    let file = document.getElementById("file").files[0];
    let formData = new FormData();
    formData.append("file", file);

    let res = await fetch("/upload", {
        method: "POST",
        body: formData
    });

    let data = await res.json();

    // ✅ UPDATE STATS CARDS
    document.getElementById("rows").innerText = "Rows: " + data.rows;
    document.getElementById("cols").innerText = "Columns: " + data.columns;
    document.getElementById("num").innerText = "Numeric: " + data.numeric;

    // Dynamic filters
    let filterDiv = document.getElementById("filters");
    filterDiv.innerHTML = "";

    for (let col in data.filters) {
        let select = document.createElement("select");
        select.id = col;

        select.onchange = applyFilters; // 🔥 AUTO APPLY

        let defaultOption = document.createElement("option");
        defaultOption.value = "";
        defaultOption.text = "All " + col;
        select.appendChild(defaultOption);

        data.filters[col].forEach(val => {
            let opt = document.createElement("option");
            opt.value = val;
            opt.text = val;
            select.appendChild(opt);
        });

        filterDiv.appendChild(select);
    }

    loadCharts();
}

// Load charts initially
async function loadCharts() {
    let res = await fetch("/charts");
    let data = await res.json();

    renderCharts(data.charts);

    // 🔥 Show report
    //document.getElementById("response").innerText = data.report;
    document.getElementById("response").innerHTML = formatReport(data.report);
}

function formatReport(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, "<h2>$1</h2>")   // bold → heading
        .replace(/### (.*?)/g, "<h3>$1</h3>")       // ### → subheading
        .replace(/\* (.*?)/g, "<li>$1</li>")        // bullets
        .replace(/\n/g, "<br>");                   // new lines
}

// Apply filters
async function applyFilters() {
    let selects = document.querySelectorAll("#filters select");

    let filters = {};
    selects.forEach(s => {
        if (s.value) {
            filters[s.id] = s.value;
        }
    });

    let res = await fetch("/filter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(filters)
    });

    let data = await res.json();

    // 🔥 Update charts
    renderCharts(data.charts);

    // 🔥 Update report
    document.getElementById("response").innerText = data.report;
}

// Ask question
async function ask() {
    let question = document.getElementById("query").value;

    let res = await fetch("/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question })
    });

    let data = await res.json();

    document.getElementById("response").innerText =
        data.explanation + "\nResult: " + data.result;
}