document.addEventListener("DOMContentLoaded", function () {
    const table = document.getElementById("watchlist-table");

    // Attach remove handler to all existing buttons
    document.querySelectorAll(".remove-btn").forEach(button => {
        attachRemoveHandler(button);
    });

    // === Listen for Dashboard updates ===
    window.addEventListener("storage", (e) => {
        if (e.key === "watchlistUpdate") {
            const update = JSON.parse(e.newValue);

            if (update.action === "remove") {
                document.getElementById(`watchlist-row-${update.symbol}`)?.remove();

                // ✅ If no rows left, re-add placeholder
                if (table.querySelectorAll("tbody tr").length === 0) {
                    table.querySelector("tbody").innerHTML =
                        `<tr id="empty-row"><td colspan="2" class="px-6 py-4 text-center text-gray-500 italic">No stocks in your watchlist.</td></tr>`;
                }
            } 
            else if (update.action === "add") {
                if (!document.getElementById(`watchlist-row-${update.symbol}`)) {
                    // ✅ Remove placeholder row if exists
                    const emptyRow = document.getElementById("empty-row");
                    if (emptyRow) emptyRow.remove();

                    // ✅ Insert stock row
                    table.querySelector("tbody").insertAdjacentHTML("beforeend", `
                        <tr id="watchlist-row-${update.symbol}" class="border-t hover:bg-gray-50 transition">
                            <td class="px-6 py-4 font-medium text-gray-800 align-middle">${update.symbol}</td>
                            <td class="px-6 py-4 text-center align-middle">
                                <button
                                    class="remove-btn inline-flex items-center justify-center bg-red-500 hover:bg-red-600 text-white text-sm px-3 py-1.5 rounded transition"
                                    data-symbol="${update.symbol}"
                                    data-url="/watchlist/remove/${update.symbol}/">
                                    Remove
                                </button>
                            </td>
                        </tr>
                    `);

                    // ✅ Re-attach event listener to new button
                    const newBtn = document.querySelector(`#watchlist-row-${update.symbol} .remove-btn`);
                    if (newBtn) attachRemoveHandler(newBtn);
                }
            }
        }
    });

    // === Helper to attach remove logic to a button ===
    function attachRemoveHandler(button) {
        button.addEventListener("click", function () {
            const symbol = this.dataset.symbol;
            const url = this.dataset.url;

            fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCSRFToken(),
                    "X-Requested-With": "XMLHttpRequest"
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    document.getElementById(`watchlist-row-${symbol}`)?.remove();

                    // ✅ Show placeholder again if no rows left
                    if (table.querySelectorAll("tbody tr").length === 0) {
                        table.querySelector("tbody").innerHTML =
                            `<tr id="empty-row"><td colspan="2" class="px-6 py-4 text-center text-gray-500 italic">No stocks in your watchlist.</td></tr>`;
                    }

                    //  Sync with other tabs
                    localStorage.setItem("watchlistUpdate", JSON.stringify({
                        symbol: symbol,
                        action: "remove",
                        time: Date.now()
                    }));
                } else {
                    alert(data.message || "Error removing");
                }
            })
            .catch(err => console.error("Error:", err));
        });
    }
});

// Helper to grab CSRF token
function getCSRFToken() {
    return document.querySelector("[name=csrfmiddlewaretoken]")?.value;
}
