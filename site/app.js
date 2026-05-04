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

const presetTags = ["笑顔", "夏", "動物", "食べ物", "謝罪", "お祝い", "旅行", "かわいい", "落ち着き"];

function termsFromQuery(query) {
  return query
    .trim()
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean);
}

function scoreItem(item, terms) {
  if (terms.length === 0) {
    return 1;
  }

  let score = 0;
  const nameJa = item.name_ja.toLowerCase();
  const nameEn = item.name_en.toLowerCase();
  const tagSet = [...item.tags_ja, ...item.scenes_ja, ...item.tone_ja].map((tag) => tag.toLowerCase());

  for (const term of terms) {
    if (item.emoji === term) score += 100;
    if (nameJa === term) score += 60;
    if (nameJa.includes(term)) score += 35;
    if (nameEn.includes(term)) score += 20;
    for (const tag of tagSet) {
      if (tag === term) score += 45;
      else if (tag.includes(term) || term.includes(tag)) score += 18;
    }
    if (item.search_text.includes(term)) score += 8;
  }

  return score;
}

function searchItems() {
  const terms = termsFromQuery(state.query);
  return data
    .map((item, index) => ({ item, index, score: scoreItem(item, terms) }))
    .filter((entry) => entry.score > 0)
    .sort((a, b) => b.score - a.score || a.index - b.index)
    .map((entry) => entry.item);
}

function overlapScore(base, item) {
  if (!base || base.emoji === item.emoji) return 0;
  const baseTags = new Set([...base.tags_ja, ...base.scenes_ja, ...base.tone_ja]);
  let score = 0;

  for (const tag of item.tags_ja) {
    if (baseTags.has(tag)) score += 4;
  }
  for (const scene of item.scenes_ja) {
    if (baseTags.has(scene)) score += 3;
  }
  for (const tone of item.tone_ja) {
    if (baseTags.has(tone)) score += 2;
  }
  if (base.category === item.category) score += 1;
  if (base.subcategory === item.subcategory) score += 2;

  return score;
}

function allRelatedTerms(item) {
  return [...item.tags_ja, ...item.scenes_ja, ...item.tone_ja];
}

function relatedItems() {
  if (!state.selected) return [];
  return data
    .map((item, index) => ({ item, index, score: overlapScore(state.selected, item) }))
    .filter((entry) => entry.score > 0)
    .filter((entry) => {
      if (!state.relatedFilterTag) return true;
      return allRelatedTerms(entry.item).includes(state.relatedFilterTag);
    })
    .sort((a, b) => b.score - a.score || a.index - b.index)
    .slice(0, 24)
    .map((entry) => entry.item);
}

function makeCard(item) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "emoji-card";
  if (state.selected?.emoji === item.emoji) {
    button.classList.add("is-selected");
  }
  button.innerHTML = `
    <span class="emoji-char">${item.emoji}</span>
    <span>
      <span class="emoji-name">${item.name_ja}</span>
      <span class="emoji-tags">${item.tags_ja.slice(0, 3).join(" / ")}</span>
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
    selectedDetail.textContent = "絵文字を選ぶと、同じタグを持つ候補が表示されます。";
    return;
  }

  const item = state.selected;
  selectedDetail.className = "";
  selectedDetail.innerHTML = `
    <div class="selected-emoji">${item.emoji}</div>
    <div class="selected-name">${item.name_ja}</div>
    <div class="selected-en">${item.name_en}</div>
    <div class="meta-list">
      ${metaBlock("タグ", item.tags_ja)}
      ${metaBlock("場面", item.scenes_ja)}
      ${metaBlock("トーン", item.tone_ja)}
      ${metaBlock("分類", [item.category, item.subcategory])}
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
  const isClickable = title !== "分類";
  return `
    <section class="meta-block">
      <h3>${title}</h3>
      <div class="chips">${values.map((value) => chipMarkup(value, isClickable)).join("")}</div>
    </section>
  `;
}

function chipMarkup(value, isClickable) {
  if (!isClickable) {
    return `<span class="chip">${value}</span>`;
  }
  const activeClass = state.relatedFilterTag === value ? " is-active" : "";
  return `<button class="chip chip-button${activeClass}" type="button" data-related-filter="${value}">${value}</button>`;
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
    <span>${state.relatedFilterTag} で絞り込み中</span>
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
  const found = searchItems().slice(0, 60);
  const relatedFound = relatedItems();
  resultCount.textContent = String(found.length);
  relatedCount.textContent = String(relatedFound.length);
  renderList(results, found);
  renderList(related, relatedFound);
  renderRelatedFilter();
  renderSelected();
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
