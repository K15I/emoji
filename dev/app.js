const data = window.EMOJI_DATA?.items ?? [];

const state = {
  query: "",
  searchMode: "fuzzy",
  selected: null,
  resultRandomSeed: 0,
};

const searchInput = document.querySelector("#searchInput");
const fuzzyModeButton = document.querySelector("#fuzzyModeButton");
const exactModeButton = document.querySelector("#exactModeButton");
const quickTags = document.querySelector("#quickTags");
const selectedInline = document.querySelector("#selectedInline");
const results = document.querySelector("#results");
const resultCount = document.querySelector("#resultCount");
const hitTags = document.querySelector("#hitTags");
const copyButton = document.querySelector("#copyButton");
const randomResultsButton = document.querySelector("#randomResultsButton");

const presetTags = [
  "笑顔",
  "ありがとう",
  "お祝い",
  "仕事",
  "旅行",
  "動物",
  "食べ物",
  "ふわふわ",
  "楕円",
  "速い",
  "青い旗",
  "日の丸",
];

function termsFromQuery(query) {
  return query.trim().toLowerCase().split(/\s+/).filter(Boolean);
}

function arrayValue(value) {
  return Array.isArray(value) ? value.filter(Boolean) : [];
}

function classTerms(item) {
  return item.class_ja ?? [item.category_ja || item.category, item.subcategory_ja || item.subcategory].filter(Boolean);
}

function typedTerms(item) {
  return {
    tags: arrayValue(item.tags_ja),
    scenes: arrayValue(item.scenes_ja),
    tones: arrayValue(item.tone_ja),
    classes: classTerms(item),
  };
}

function allTerms(item) {
  const terms = typedTerms(item);
  return [...terms.tags, ...terms.scenes, ...terms.tones, ...terms.classes];
}

function importanceScore(item) {
  const importance = Number.parseInt(item.importance || "2", 10);
  return Number.isFinite(importance) ? importance : 2;
}

function randomScore(id, seed) {
  let hash = seed || 1;
  const text = String(id);
  for (let index = 0; index < text.length; index += 1) {
    hash = Math.imul(hash ^ text.charCodeAt(index), 2654435761);
  }
  return (hash >>> 0) / 4294967295;
}

function hasExactTerm(item, term) {
  return allTerms(item).some((value) => value.toLowerCase() === term);
}

function scoreExactItem(item, terms) {
  if (terms.length === 0) return importanceScore(item);
  return terms.every((term) => hasExactTerm(item, term)) ? 100 + importanceScore(item) : 0;
}

function scoreFuzzyItem(item, terms) {
  if (terms.length === 0) return importanceScore(item);

  let score = 0;
  const nameJa = item.name_ja.toLowerCase();
  const nameEn = item.name_en.toLowerCase();
  const tags = allTerms(item).map((tag) => tag.toLowerCase());

  for (const term of terms) {
    if (item.emoji === term) score += 140;
    if (item.id === term) score += 80;
    if (nameJa === term) score += 80;
    else if (nameJa.includes(term)) score += 45;
    if (nameEn.includes(term)) score += 24;
    for (const tag of tags) {
      if (tag === term) score += 55;
      else if (tag.includes(term) || term.includes(tag)) score += 20;
    }
    if (item.search_text.includes(term)) score += 8;
  }

  return score ? score + importanceScore(item) : 0;
}

function scoreItem(item, terms) {
  return state.searchMode === "exact" ? scoreExactItem(item, terms) : scoreFuzzyItem(item, terms);
}

function searchItems() {
  const terms = termsFromQuery(state.query);
  return data
    .map((item, index) => ({ item, index, score: scoreItem(item, terms) }))
    .filter((entry) => entry.score > 0)
    .sort((a, b) => {
      if (state.resultRandomSeed) {
        return randomScore(a.item.id, state.resultRandomSeed) - randomScore(b.item.id, state.resultRandomSeed);
      }
      return b.score - a.score || importanceScore(b.item) - importanceScore(a.item) || a.index - b.index;
    })
    .map((entry) => entry.item);
}

function makeCard(item) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "emoji-card";
  button.setAttribute("aria-label", `${item.name_ja} ${item.name_en}`);
  if (state.selected?.id === item.id) button.classList.add("is-selected");
  button.innerHTML = `
    <span class="emoji-char">${escapeHtml(item.emoji)}</span>
    <span class="emoji-name">${escapeHtml(item.name_ja)}</span>
  `;
  button.addEventListener("click", () => {
    state.selected = item;
    render();
  });
  return button;
}

function renderList(container, items, emptyText) {
  if (!items.length) {
    const empty = document.createElement("div");
    empty.className = "empty-list";
    empty.textContent = emptyText;
    container.replaceChildren(empty);
    return;
  }
  container.replaceChildren(...items.map(makeCard));
}

function renderQuickTags() {
  quickTags.replaceChildren(
    ...presetTags.map((tag) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "tag-button";
      button.textContent = tag;
      button.addEventListener("click", () => {
        applySearch(tag, "exact");
      });
      return button;
    }),
  );
}

function applySearch(query, mode = state.searchMode) {
  state.query = query;
  state.searchMode = mode;
  state.resultRandomSeed = 0;
  searchInput.value = query;
  render();
  searchInput.focus();
}

function setSearchMode(mode) {
  state.searchMode = mode;
  state.resultRandomSeed = 0;
  render();
  searchInput.focus();
}

function renderSearchMode() {
  fuzzyModeButton.classList.toggle("is-active", state.searchMode === "fuzzy");
  exactModeButton.classList.toggle("is-active", state.searchMode === "exact");
  fuzzyModeButton.setAttribute("aria-pressed", String(state.searchMode === "fuzzy"));
  exactModeButton.setAttribute("aria-pressed", String(state.searchMode === "exact"));
}

function matchedTermsForItem(item, terms) {
  if (terms.length === 0) return [];
  return allTerms(item).filter((value) => {
    const tag = value.toLowerCase();
    if (state.searchMode === "exact") return terms.includes(tag);
    return terms.some((term) => tag === term || tag.includes(term) || term.includes(tag));
  });
}

function renderHitTags(foundItems) {
  const terms = termsFromQuery(state.query);
  const counts = new Map();
  for (const item of foundItems) {
    for (const tag of matchedTermsForItem(item, terms)) {
      counts.set(tag, (counts.get(tag) || 0) + 1);
    }
  }

  const tags = [...counts.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], "ja"))
    .slice(0, 8)
    .map(([tag]) => tag);

  const label = document.createElement("span");
  label.className = "hit-tags-label";
  label.textContent = "ヒットしたタグ";

  if (!tags.length) {
    hitTags.replaceChildren(label);
    return;
  }

  hitTags.replaceChildren(
    label,
    ...tags.map((tag) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "hit-tag-button";
      button.textContent = tag;
      button.addEventListener("click", () => {
        applySearch(tag, "exact");
      });
      return button;
    }),
  );
}

function renderSelectedInline() {
  copyButton.disabled = !state.selected;
  if (!state.selected) {
    selectedInline.className = "selected-inline selected-empty";
    selectedInline.textContent = "絵文字を選ぶと、ここに関連語を表示します。";
    return;
  }

  const item = state.selected;
  const terms = typedTerms(item);
  selectedInline.className = "selected-inline";
  selectedInline.innerHTML = `
    <section class="selected-summary">
      <div class="selected-emoji">${escapeHtml(item.emoji)}</div>
      <div class="selected-title">
        <div class="selected-name">${escapeHtml(item.name_ja)}</div>
        <div class="selected-en">${escapeHtml(item.name_en)}</div>
      </div>
    </section>
    <div class="chips merged-chips">
      ${terms.tags.map((value) => chipMarkup(value, "tag")).join("")}
      ${terms.scenes.map((value) => chipMarkup(value, "scene")).join("")}
      ${terms.tones.map((value) => chipMarkup(value, "tone")).join("")}
      ${terms.classes.map((value) => chipMarkup(value, "class")).join("")}
    </div>
  `;
  selectedInline.querySelectorAll("[data-search-tag]").forEach((button) => {
    button.addEventListener("click", () => {
      applySearch(button.dataset.searchTag, "exact");
    });
  });
}

function chipMarkup(value, type) {
  return `<button class="chip chip-button chip-${type}" type="button" data-search-tag="${escapeHtml(value)}">${escapeHtml(value)}</button>`;
}

function render() {
  const allFound = searchItems();
  const found = allFound.slice(0, 120);
  resultCount.textContent = `${allFound.length}個`;
  randomResultsButton.disabled = allFound.length < 2;
  renderSearchMode();
  renderHitTags(allFound);
  renderSelectedInline();
  renderList(results, found, state.query ? "一致する絵文字がありません。" : "検索語を入れるか、候補タグを選んでください。");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

searchInput.addEventListener("input", (event) => {
  state.query = event.target.value;
  state.resultRandomSeed = 0;
  render();
});

fuzzyModeButton.addEventListener("click", () => {
  setSearchMode("fuzzy");
});

exactModeButton.addEventListener("click", () => {
  setSearchMode("exact");
});

randomResultsButton.addEventListener("click", () => {
  state.resultRandomSeed = Math.floor(Math.random() * 2 ** 31) + 1;
  render();
});

copyButton.addEventListener("click", async () => {
  if (!state.selected) return;
  await navigator.clipboard.writeText(state.selected.emoji);
  copyButton.textContent = "コピー済み";
  window.setTimeout(() => {
    copyButton.textContent = "コピー";
  }, 900);
});

renderQuickTags();
render();
