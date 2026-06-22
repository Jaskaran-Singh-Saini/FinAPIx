document.addEventListener("DOMContentLoaded", function () {

    const chartDataEl = document.getElementById("chart-data");
    if (!chartDataEl) return;

    let chartData;
    try {
        chartData = JSON.parse(chartDataEl.textContent);
    } catch (e) {
        console.error("Chart JSON parse error:", e);
        return;
    }
    if (!chartData.labels?.length) return;

    const labels   = chartData.labels;
    const closes   = chartData.closes;
    const sma14    = chartData.sma14;
    const bbUpper  = chartData.bb_upper;
    const bbLower  = chartData.bb_lower;
    const rsi      = chartData.rsi;
    const macd     = chartData.macd;
    const darkGrid = "#2a2d3a";
    const darkTick = "#888";

    const zoomPlugin = {
        zoom: {
            wheel: { enabled: true },
            pinch: { enabled: true },
            mode: 'x',
        },
        pan: {
            enabled: true,
            mode: 'x',
        },
    };

    // ── PANEL 1: Price + SMA + BB ─────────────────────────────────────────
    const priceChart = new Chart(document.getElementById("priceChart"), {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "Close",
                    data: closes,
                    borderColor: "#4bc0c0",
                    backgroundColor: "rgba(75,192,192,0.08)",
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false,
                    tension: 0.2,
                },
                {
                    label: "SMA 14",
                    data: sma14,
                    borderColor: "#ffe066",
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: false,
                    tension: 0.2,
                    borderDash: [4, 3],
                },
                {
                    label: "BB Upper",
                    data: bbUpper,
                    borderColor: "rgba(180,100,255,0.6)",
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: false,
                    tension: 0.2,
                    borderDash: [2, 3],
                },
                {
                    label: "BB Lower",
                    data: bbLower,
                    borderColor: "rgba(180,100,255,0.6)",
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: "-1",
                    backgroundColor: "rgba(180,100,255,0.06)",
                    tension: 0.2,
                },
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: { labels: { color: "#ccc", boxWidth: 14 } },
                title: { display: true, text: "Price & Bollinger Bands", color: "#aaa" },
                zoom: zoomPlugin,
            },
            scales: {
                x: { ticks: { color: darkTick, maxTicksLimit: 8 }, grid: { color: darkGrid } },
                y: { ticks: { color: "#4bc0c0" }, grid: { color: darkGrid },
                     title: { display: true, text: "Price (USD)", color: "#4bc0c0" } }
            }
        }
    });

    // ── PANEL 2: RSI ──────────────────────────────────────────────────────
    const rsiChart = new Chart(document.getElementById("rsiChart"), {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "RSI (14)",
                    data: rsi,
                    borderColor: "#9966ff",
                    backgroundColor: "rgba(153,102,255,0.1)",
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: true,
                    tension: 0.2,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: { labels: { color: "#ccc" } },
                title: { display: true, text: "RSI (14)  —  overbought >70  /  oversold <30", color: "#aaa" },
                zoom: zoomPlugin,
            },
            scales: {
                x: { ticks: { color: darkTick, maxTicksLimit: 8 }, grid: { color: darkGrid } },
                y: {
                    min: 0, max: 100,
                    ticks: {
                        color: "#9966ff",
                        callback: (v) => {
                            if (v === 70) return '70 ⚠️';
                            if (v === 30) return '30 ✅';
                            return v;
                        }
                    },
                    grid: {
                        color: (ctx) => {
                            if (ctx.tick.value === 70) return "rgba(255,80,80,0.4)";
                            if (ctx.tick.value === 30) return "rgba(80,200,80,0.4)";
                            return darkGrid;
                        }
                    },
                    title: { display: true, text: "RSI", color: "#9966ff" }
                }
            }
        }
    });

    // ── PANEL 3: MACD ─────────────────────────────────────────────────────
    const macdChart = new Chart(document.getElementById("macdChart"), {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "MACD",
                    data: macd,
                    borderColor: "#ff6384",
                    backgroundColor: "rgba(255,99,132,0.08)",
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: true,
                    tension: 0.2,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: { labels: { color: "#ccc" } },
                title: { display: true, text: "MACD (12,26,9)", color: "#aaa" },
                zoom: zoomPlugin,
            },
            scales: {
                x: { ticks: { color: darkTick, maxTicksLimit: 8 }, grid: { color: darkGrid } },
                y: { ticks: { color: "#ff6384" }, grid: { color: darkGrid },
                     title: { display: true, text: "MACD", color: "#ff6384" } }
            }
        }
    });

    // ── Reset zoom buttons ────────────────────────────────────────────────
    document.getElementById("resetPrice")?.addEventListener("click", () => priceChart.resetZoom());
    document.getElementById("resetRsi")?.addEventListener("click",   () => rsiChart.resetZoom());
    document.getElementById("resetMacd")?.addEventListener("click",  () => macdChart.resetZoom());

    // ── Watchlist AJAX ────────────────────────────────────────────────────
    const form = document.getElementById("watchlist-form");
    if (form) {
        form.addEventListener("submit", function (e) {
            e.preventDefault();
            const url = form.action;
            const symbol = form.dataset.symbol;
            const csrfToken = form.querySelector("[name=csrfmiddlewaretoken]").value;
            const action = form.dataset.action;

            fetch(url, {
                method: "POST",
                headers: { "X-CSRFToken": csrfToken, "X-Requested-With": "XMLHttpRequest" },
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    if (action === "add") {
                        form.dataset.action = "remove";
                        form.action = `/watchlist/remove/${symbol}/`;
                        form.innerHTML = `<input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                            <button type="submit" class="btn btn-danger w-100">❌ Remove from Watchlist</button>`;
                    } else {
                        form.dataset.action = "add";
                        form.action = `/watchlist/add/${symbol}/`;
                        form.innerHTML = `<input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                            <button type="submit" class="btn btn-success w-100">⭐ Add to Watchlist</button>`;
                    }
                }
            })
            .catch(err => console.error("Fetch error:", err));
        });
    }
});