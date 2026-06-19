document.addEventListener("DOMContentLoaded", function () {
    // === Chart Rendering ===
    const chartDataEl = document.getElementById("chart-data");
    if (chartDataEl) {
        try {
            const chartData = JSON.parse(chartDataEl.textContent);
            if (chartData.labels?.length) {
                new Chart(document.getElementById("stockChart"), {
                    type: "line",
                    data: chartData,
                    options: {
                        responsive: true,
                        scales: {
                            x: { title: { display: true, text: "Date" } },
                            y: { title: { display: true, text: "Close Price" } },
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

                    // Update button UI
                    if (action === "add") {
                        form.dataset.action = "remove";
                        form.action = `/watchlist/remove/${symbol}/`;
                        form.innerHTML = `<input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                            <button type="submit" class="btn btn-danger btn-sm">❌ Remove from Watchlist</button>`;
                    } else {
                        form.dataset.action = "add";
                        form.action = `/watchlist/add/${symbol}/`;
                        form.innerHTML = `<input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                            <button type="submit" class="btn btn-success btn-sm">⭐ Add to Watchlist</button>`;
                    }

                    // 🔥 Cross-tab sync
                    localStorage.setItem("watchlistUpdate", JSON.stringify({
                        symbol: symbol,
                        action: action,
                        time: Date.now()
                    }));
                } else {
                    alert(data.message || "Something went wrong");
                }
            })
            .catch(err => console.error("Fetch error:", err));
        });
    }

    // === Listen for changes from Watchlist page ===
    window.addEventListener("storage", (e) => {
        if (e.key === "watchlistUpdate") {
            const update = JSON.parse(e.newValue);
            if (update.symbol === form?.dataset.symbol) {
                location.reload(); // simple sync for now
            }
        }
    });
});
