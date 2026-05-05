const data = window.EMOJI_DATA?.items ?? [];

const state = {
  query: "",
  exactTag: "",
  selected: null,
  relatedFilterTag: "",
  resultRandomSeed: 0,
  relatedRandomSeed: 0,
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
const randomResultsButton = document.querySelector("#randomResultsButton");
const randomRelatedButton = document.querySelector("#randomRelatedButton");
const searchFilter = document.querySelector("#searchFilter");

const presetTags = [
  "笑顔",
  "ありがとう",
  "お祝い",
  "仕事",
  "旅行",
  "動物",
  "食べ物",
  "かわいい",
  "ふわふわ",
  "きらきら",
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

function hasExactTerm(item, term) {
  return allTerms(item).includes(term);
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

function scoreItem(item, terms) {
  if (state.exactTag && !hasExactTerm(item, state.exactTag)) {
    return 0;
  }

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

  if (score === 0) {
    return 0;
  }
  return score + importanceScore(item);
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

  if (score === 0) {
    return 0;
  }
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
    .sort((a, b) => {
      if (state.relatedRandomSeed) {
        return randomScore(a.item.id, state.relatedRandomSeed) - randomScore(b.item.id, state.relatedRandomSeed);
      }
      return b.score - a.score || importanceScore(b.item) - importanceScore(a.item) || a.index - b.index;
    })
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
    state.relatedRandomSeed = 0;
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
      state.relatedRandomSeed = 0;
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
    state.relatedRandomSeed = 0;
    render();
  });
}

function renderSearchFilter() {
  if (!state.exactTag) {
    searchFilter.hidden = true;
    searchFilter.replaceChildren();
    return;
  }

  searchFilter.hidden = false;
  searchFilter.innerHTML = `
    <span>${escapeHtml(state.exactTag)} と一致するタグで検索中</span>
    <button type="button">曖昧検索に戻す</button>
  `;
  searchFilter.querySelector("button").addEventListener("click", () => {
    state.exactTag = "";
    state.resultRandomSeed = 0;
    render();
    searchInput.focus();
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
        state.exactTag = tag;
        state.query = tag;
        searchInput.value = tag;
        state.resultRandomSeed = 0;
        render();
        searchInput.focus();
      });
      return button;
    }),
  );
}

function render() {
  const allFound = searchItems();
  const allRelatedFound = relatedItems();
  const found = allFound.slice(0, 80);
  const relatedFound = allRelatedFound.slice(0, 36);
  resultCount.textContent = String(allFound.length);
  relatedCount.textContent = String(allRelatedFound.length);
  randomResultsButton.disabled = allFound.length < 2;
  randomRelatedButton.disabled = allRelatedFound.length < 2;
  randomResultsButton.classList.toggle("is-active", Boolean(state.resultRandomSeed));
  randomRelatedButton.classList.toggle("is-active", Boolean(state.relatedRandomSeed));
  renderSearchFilter();
  renderList(results, found, state.query ? "一致する絵文字がありません。" : "検索語を入れるか、候補タグを選んでください。");
  renderList(related, relatedFound, state.selected ? "関連する絵文字がありません。" : "絵文字を選ぶと関連候補を表示します。");
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
  state.exactTag = "";
  state.resultRandomSeed = 0;
  render();
});

randomResultsButton.addEventListener("click", () => {
  state.resultRandomSeed = Math.floor(Math.random() * 2 ** 31) + 1;
  render();
});

randomRelatedButton.addEventListener("click", () => {
  state.relatedRandomSeed = Math.floor(Math.random() * 2 ** 31) + 1;
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
