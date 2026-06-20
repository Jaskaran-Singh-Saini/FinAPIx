document.addEventListener("DOMContentLoaded", function () {

    // === Chart Rendering with separate Y axes ===
    const chartDataEl = document.getElementById("chart-data");
    if (chartDataEl) {
        try {
            const chartData = JSON.parse(chartDataEl.textContent);
            if (chartData.labels?.length) {

                // Assign each dataset to its own Y axis
                const axisMap = {
                    0: 'yPrice',   // Close price
                    1: 'yMacd',    // MACD
                    2: 'yRsi',     // RSI
                    3: 'yPrice',   // SMA 14 (same scale as price)
                };
                chartData.datasets.forEach((ds, i) => {
                    ds.yAxisID = axisMap[i] || 'yPrice';
                });

                new Chart(document.getElementById("stockChart"), {
                    type: "line",
                    data: chartData,
                    options: {
                        responsive: true,
                        interaction: { mode: 'index', intersect: false },
                        plugins: {
                            legend: { labels: { color: '#e0e0e0' } },
                            tooltip: { mode: 'index' }
                        },
                        scales: {
                            x: {
                                ticks: { color: '#aaa', maxTicksLimit: 10 },
                                grid: { color: '#2a2d3a' },
                                title: { display: true, text: 'Date', color: '#aaa' }
                            },
                            yPrice: {
                                type: 'linear',
                                position: 'left',
                                ticks: { color: '#4bc0c0' },
                                grid: { color: '#2a2d3a' },
                                title: { display: true, text: 'Price', color: '#4bc0c0' }
                            },
                            yRsi: {
                                type: 'linear',
                                position: 'right',
                                min: 0, max: 100,
                                ticks: { color: '#9966ff' },
                                grid: { drawOnChartArea: false },
                                title: { display: true, text: 'RSI', color: '#9966ff' }
                            },
                            yMacd: {
                                type: 'linear',
                                position: 'right',
                                ticks: { color: '#ff6384' },
                                grid: { drawOnChartArea: false },
                                title: { display: true, text: 'MACD', color: '#ff6384' }
                            },
                        },
                    },
                });
            }
        } catch (err) {
            console.error("Chart render error:", err);
        }
    }

    // === Watchlist Add/Remove AJAX ===
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
                headers: {
                    "X-CSRFToken": csrfToken,
                    "X-Requested-With": "XMLHttpRequest",
                },
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert(`${symbol} ${action === "add" ? "added to" : "removed from"} watchlist`);
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
                    localStorage.setItem("watchlistUpdate", JSON.stringify({ symbol, action, time: Date.now() }));
                } else {
                    alert(data.message || "Something went wrong");
                }
            })
            .catch(err => console.error("Fetch error:", err));
        });
    }

    // === Cross-tab watchlist sync ===
    window.addEventListener("storage", (e) => {
        if (e.key === "watchlistUpdate") {
            const update = JSON.parse(e.newValue);
            if (update.symbol === form?.dataset.symbol) location.reload();
        }
    });
});