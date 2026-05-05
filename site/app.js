const data = window.EMOJI_DATA?.items ?? [];

const state = {
  query: "",
  selected: null,
  relatedFilterTag: "",
};

const searchInput = document.querySelector("#searchInput");
const quickTags = document.querySelector("#quickTags");
const results = document.querySelector("#results");
const related = document.querySelector("#related");
const resultCount = document.querySelector("#resultCount");
const relatedCount = document.querySelector("#relatedCount");
const relatedTitle = document.querySelector("#relatedTitle");
const relatedFilter = document.querySelector("#relatedFilter");
const selectedDetail = document.querySelector("#selectedDetail");
const copyButton = document.querySelector("#copyButton");

const presetTags = [
  "笑顔",
  "夏",
  "動物",
  "かわいい",
  "ふわふわ",
  "楕円",
  "速い",
  "びっくり",
  "青い旗",
  "三色旗",
];

function termsFromQuery(query) {
  return query.trim().toLowerCase().split(/\s+/).filter(Boolean);
}

function classTerms(item) {
  return item.class_ja ?? [item.category_ja || item.category, item.subcategory_ja || item.subcategory].filter(Boolean);
}

function allTerms(item) {
  return [...item.tags_ja, ...item.scenes_ja, ...item.tone_ja, ...classTerms(item)];
}

function importanceScore(item) {
  const importance = Number.parseInt(item.importance || "2", 10);
  return Number.isFinite(importance) ? importance : 2;
}

function scoreItem(item, terms) {
  if (terms.length === 0) {
    return importanceScore(item);
  }

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

  return score + importanceScore(item);
}

function searchItems() {
  const terms = termsFromQuery(state.query);
  return data
    .map((item, index) => ({ item, index, score: scoreItem(item, terms) }))
    .filter((entry) => entry.score > 0)
    .sort((a, b) => b.score - a.score || importanceScore(b.item) - importanceScore(a.item) || a.index - b.index)
    .map((entry) => entry.item);
}

function overlapScore(base, item) {
  if (!base || base.id === item.id) return 0;

  const baseTags = new Set(base.tags_ja);
  const baseScenes = new Set(base.scenes_ja);
  const baseTone = new Set(base.tone_ja);
  const baseClass = new Set(classTerms(base));
  let score = 0;

  for (const tag of item.tags_ja) {
    if (baseTags.has(tag)) score += 5;
  }
  for (const scene of item.scenes_ja) {
    if (baseScenes.has(scene)) score += 4;
  }
  for (const tone of item.tone_ja) {
    if (baseTone.has(tone)) score += 4;
  }
  for (const className of classTerms(item)) {
    if (baseClass.has(className)) score += 3;
  }
  if (base.category === item.category) score += 1;
  if (base.subcategory === item.subcategory) score += 3;

  return score + importanceScore(item);
}

function relatedItems() {
  if (!state.selected) return [];
  return data
    .map((item, index) => ({ item, index, score: overlapScore(state.selected, item) }))
    .filter((entry) => entry.score > 0)
    .filter((entry) => {
      if (!state.relatedFilterTag) return true;
      return allTerms(entry.item).includes(state.relatedFilterTag);
    })
    .sort((a, b) => b.score - a.score || importanceScore(b.item) - importanceScore(a.item) || a.index - b.index)
    .slice(0, 36)
    .map((entry) => entry.item);
}

function makeCard(item) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "emoji-card";
  if (state.selected?.id === item.id) {
    button.classList.add("is-selected");
  }
  button.innerHTML = `
    <span class="emoji-char">${escapeHtml(item.emoji)}</span>
    <span>
      <span class="emoji-name">${escapeHtml(item.name_ja)}</span>
      <span class="emoji-tags">${escapeHtml([...item.tags_ja, ...item.scenes_ja, ...item.tone_ja].slice(0, 4).join(" / "))}</span>
    </span>
  `;
  button.addEventListener("click", () => {
    state.selected = item;
    state.relatedFilterTag = "";
    render();
  });
  return button;
}

function renderList(container, items) {
  container.replaceChildren(...items.map(makeCard));
}

function renderSelected() {
  copyButton.disabled = !state.selected;
  if (!state.selected) {
    selectedDetail.className = "selected-empty";
    selectedDetail.textContent = "絵文字を選ぶと、同じタグを持つ候補を右に表示します。";
    return;
  }

  const item = state.selected;
  selectedDetail.className = "";
  selectedDetail.innerHTML = `
    <div class="selected-emoji">${escapeHtml(item.emoji)}</div>
    <div class="selected-name">${escapeHtml(item.name_ja)}</div>
    <div class="selected-en">${escapeHtml(item.name_en)}</div>
    <div class="meta-list">
      ${metaBlock("タグ", item.tags_ja)}
      ${metaBlock("場面", item.scenes_ja)}
      ${metaBlock("トーン・見た目", item.tone_ja)}
      ${metaBlock("分類", classTerms(item))}
    </div>
  `;

  selectedDetail.querySelectorAll("[data-related-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      state.relatedFilterTag = button.dataset.relatedFilter;
      render();
    });
  });
}

function metaBlock(title, values) {
  if (!values.length) return "";
  return `
    <section class="meta-block">
      <h3>${escapeHtml(title)}</h3>
      <div class="chips">${values.map((value) => chipMarkup(value)).join("")}</div>
    </section>
  `;
}

function chipMarkup(value) {
  const activeClass = state.relatedFilterTag === value ? " is-active" : "";
  return `<button class="chip chip-button${activeClass}" type="button" data-related-filter="${escapeHtml(value)}">${escapeHtml(value)}</button>`;
}

function renderRelatedFilter() {
  relatedTitle.textContent = state.relatedFilterTag ? "タグ関連" : "関連";
  if (!state.relatedFilterTag) {
    relatedFilter.hidden = true;
    relatedFilter.replaceChildren();
    return;
  }

  relatedFilter.hidden = false;
  relatedFilter.innerHTML = `
    <span>${escapeHtml(state.relatedFilterTag)} で絞り込み中</span>
    <button type="button">解除</button>
  `;
  relatedFilter.querySelector("button").addEventListener("click", () => {
    state.relatedFilterTag = "";
    render();
  });
}

function renderQuickTags() {
  quickTags.replaceChildren(
    ...presetTags.map((tag) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "tag-button";
      button.textContent = tag;
      button.addEventListener("click", () => {
        state.query = tag;
        searchInput.value = tag;
        render();
        searchInput.focus();
      });
      return button;
    }),
  );
}

function render() {
  const found = searchItems().slice(0, 80);
  const relatedFound = relatedItems();
  resultCount.textContent = String(found.length);
  relatedCount.textContent = String(relatedFound.length);
  renderList(results, found);
  renderList(related, relatedFound);
  renderRelatedFilter();
  renderSelected();
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
