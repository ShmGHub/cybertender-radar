const state = {
  feed: null,
  opportunities: [],
};

const els = {
  totalCount: document.querySelector("#totalCount"),
  highCount: document.querySelector("#highCount"),
  nextDeadline: document.querySelector("#nextDeadline"),
  generatedAt: document.querySelector("#generatedAt"),
  feedStatus: document.querySelector("#feedStatus"),
  opportunityList: document.querySelector("#opportunityList"),
  sourceList: document.querySelector("#sourceList"),
  searchInput: document.querySelector("#searchInput"),
  confidenceFilter: document.querySelector("#confidenceFilter"),
  marketFilter: document.querySelector("#marketFilter"),
  sortSelect: document.querySelector("#sortSelect"),
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatDate(value) {
  if (!value) return "Not specified";
  const date = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}

function deadlineText(item) {
  if (typeof item.deadlineInDays !== "number") return "No deadline";
  if (item.deadlineInDays < 0) return "Closed";
  if (item.deadlineInDays === 0) return "Today";
  if (item.deadlineInDays === 1) return "1 day";
  return `${item.deadlineInDays} days`;
}

function matchesFilters(item) {
  const query = els.searchInput.value.trim().toLowerCase();
  const confidence = els.confidenceFilter.value;
  const market = els.marketFilter.value;
  const haystack = [
    item.title,
    item.buyer,
    item.region,
    item.description,
    item.source,
    ...(item.tags || []),
  ]
    .join(" ")
    .toLowerCase();

  if (query && !haystack.includes(query)) return false;
  if (confidence !== "all" && item.confidence !== confidence) return false;
  if (market !== "all" && item.market !== market) return false;
  return true;
}

function sortItems(items) {
  const mode = els.sortSelect.value;
  return [...items].sort((a, b) => {
    if (mode === "deadline") {
      return (a.deadlineInDays ?? 9999) - (b.deadlineInDays ?? 9999);
    }
    if (mode === "value") {
      return (b.value || 0) - (a.value || 0);
    }
    return (b.matchScore || 0) - (a.matchScore || 0);
  });
}

function renderSummary(feed) {
  els.totalCount.textContent = feed.summary.total;
  els.highCount.textContent = feed.summary.highConfidence;
  els.nextDeadline.textContent =
    typeof feed.summary.nextDeadlineDays === "number"
      ? `${feed.summary.nextDeadlineDays}d`
      : "--";
  els.generatedAt.textContent = `Updated ${new Date(feed.generatedAt).toLocaleString(
    "en-GB",
    { dateStyle: "medium", timeStyle: "short" },
  )}`;
}

function renderMarkets(feed) {
  const markets = feed.summary.markets || [];
  for (const market of markets) {
    const option = document.createElement("option");
    option.value = market;
    option.textContent = market;
    els.marketFilter.append(option);
  }
}

function renderSources(feed) {
  els.sourceList.innerHTML = "";
  for (const source of feed.sources || []) {
    const item = document.createElement("div");
    item.className = "source-item";
    item.innerHTML = `
      <strong>${escapeHtml(source.name)}</strong>
      <span>${escapeHtml(source.status)} &middot; ${escapeHtml(source.fetched)} fetched</span>
    `;
    els.sourceList.append(item);
  }
}

function renderOpportunities() {
  const visible = sortItems(state.opportunities.filter(matchesFilters));
  els.opportunityList.innerHTML = "";
  els.feedStatus.textContent = visible.length
    ? `${visible.length} opportunities shown`
    : "No opportunities match the current filters.";

  for (const item of visible) {
    const card = document.createElement("article");
    card.className = "opportunity-card";
    const tags = (item.tags || [])
      .map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`)
      .join("");
    const sourceLinks = (item.sourceLinks || [])
      .slice(0, 2)
      .map(
        (link, index) =>
          `<a href="${escapeHtml(link)}" target="_blank" rel="noreferrer">Source link ${index + 1}</a>`,
      )
      .join("");
    card.innerHTML = `
      <div>
        <div class="card-meta">
          <span>${escapeHtml(item.source)}</span>
          <span>${escapeHtml(item.market)}</span>
          <span>${escapeHtml(item.valueLabel)}</span>
          <span>${escapeHtml(deadlineText(item))}</span>
        </div>
        <h3>${escapeHtml(item.title)}</h3>
        <p>${escapeHtml(item.buyer || "Unknown buyer")} &middot; ${escapeHtml(item.region || "Region not specified")}</p>
        <p>${escapeHtml(item.whyItMatters)}</p>
        <div class="tags">${tags}</div>
        <div class="card-actions">
          <a href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">Official notice</a>
          ${sourceLinks}
        </div>
      </div>
      <div class="score-box">
        <span>Score</span>
        <strong>${escapeHtml(item.matchScore)}</strong>
        <div class="confidence ${escapeHtml(item.confidence || "").toLowerCase()}">
          ${escapeHtml(item.confidence)}
        </div>
      </div>
    `;
    els.opportunityList.append(card);
  }
}

async function loadFeed() {
  try {
    const response = await fetch("data/opportunities.json", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Feed request failed: ${response.status}`);
    }
    const feed = await response.json();
    state.feed = feed;
    state.opportunities = feed.opportunities || [];
    renderSummary(feed);
    renderMarkets(feed);
    renderSources(feed);
    renderOpportunities();
  } catch (error) {
    els.feedStatus.textContent = "Could not load the opportunity feed.";
    console.error(error);
  }
}

for (const control of [
  els.searchInput,
  els.confidenceFilter,
  els.marketFilter,
  els.sortSelect,
]) {
  control.addEventListener("input", renderOpportunities);
}

loadFeed();
