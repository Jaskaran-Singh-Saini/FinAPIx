// 🔹 Utility: CSRF token getter (safe across templates)
function getCSRFToken() {
    let tokenInput = document.querySelector("[name=csrfmiddlewaretoken]");
    return tokenInput ? tokenInput.value : "";
}

// 🔹 Universal remove stock function
function removeStock(symbol) {
    return fetch(`/watchlist/remove/${symbol}/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCSRFToken(),
            "X-Requested-With": "XMLHttpRequest"
        },
    })
    .then(res => res.json());
}

// 🔹 Sync removal across dashboard + watchlist
document.addEventListener("stockRemoved", function(e) {
    const symbol = e.detail.symbol;

    // Dashboard button/form update
    let removeForm = document.querySelector(`#remove-watchlist-form button[data-symbol="${symbol}"]`);
    if (removeForm) {
        let csrfToken = getCSRFToken();
        let container = removeForm.closest("form");
        container.outerHTML = `
            <form id="add-watchlist-form" method="post" action="/watchlist/add/${symbol}/">
                <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                <button type="submit" data-symbol="${symbol}" style="margin-bottom: 10px;">⭐ Add to Watchlist</button>
            </form>
        `;
    }

    // Watchlist row removal
    let row = document.querySelector(`#watchlist-table tr[data-symbol="${symbol}"]`);
    if (row) {
        row.style.transition = "opacity 0.5s ease";
        row.style.opacity = "0";
        setTimeout(() => row.remove(), 500);
    }
});

// 🔹 Attach remove handlers globally
document.addEventListener("click", function(e) {
    if (e.target.classList.contains("remove-btn")) {
        let symbol = e.target.closest("tr").dataset.symbol;
        removeStock(symbol).then(data => {
            if (data.success) {
                document.dispatchEvent(new CustomEvent("stockRemoved", { detail: { symbol } }));
            } else {
                alert(data.message || "Error removing stock");
            }
        });
    }
});
