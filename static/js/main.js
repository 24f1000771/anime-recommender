const mediaTypeMap = {
    "ANIME": { type: "ANIME", country: null },
    "MANGA_JP": { type: "MANGA", country: "JP" },
    "MANGA_KR": { type: "MANGA", country: "KR" },
    "MANGA_CN": { type: "MANGA", country: "CN" }
};

let selectedSource = null;
let actualType = null;
let selectedCountry = null;

async function doSearch() {
    const input = document.getElementById("search-input").value.trim();
    const mediaKey = document.getElementById("media-type").value;

    if (!input) return;

    window.location.href = `/browse?search=${encodeURIComponent(input)}&media=${encodeURIComponent(mediaKey)}`;
}

async function selectSource(index) {
    selectedSource = window._searchResults[index];

    const resultsDiv = document.getElementById("search-results");
    const recsDiv = document.getElementById("recommendations");

    resultsDiv.classList.add("hidden");
    recsDiv.classList.remove("hidden");
    recsDiv.innerHTML = '<p class="loading">Fetching recommendations...</p>';

    const response = await fetch("/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            source: selectedSource,
            actual_type: actualType,
            country: selectedCountry,
            n: 12
        })
    });

    const data = await response.json();

    if (data.error) {
        recsDiv.innerHTML = `<p class="loading">Couldn't find recommendations. Try another title.</p>`;
        return;
    }

    recsDiv.innerHTML = `
        <p class="rec-title">Because you searched <span>${selectedSource.title}</span></p>
        <div class="rec-grid">
            ${data.results.map(r => `
                <div class="rec-card">
                    <img src="${r.cover || ''}" onerror="this.style.display='none'" alt="${r.title}">
                    <div class="rec-card-info">
                        <h4>${r.title}</h4>
                        <p>${r.genres.split(',').slice(0, 2).join(', ')}</p>
                        <span class="score-badge">⭐ ${r.average_score || 'N/A'}</span>
                    </div>
                </div>
            `).join('')}
        </div>
        <br>
        <button onclick="resetSearch()" style="background:#1a1a1a;color:#aaa;border:1px solid #333;padding:10px 24px;border-radius:50px;cursor:pointer;font-size:13px;">🔄 Search again</button>
    `;
}

function resetSearch() {
    document.getElementById("search-results").classList.add("hidden");
    document.getElementById("recommendations").classList.add("hidden");
    document.getElementById("search-input").value = "";
    selectedSource = null;
}

document.getElementById("search-input").addEventListener("keydown", function(e) {
    if (e.key === "Enter") doSearch();
});