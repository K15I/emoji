const data = window.EMOJI_DATA?.items ?? [];

const SKIN_TONE_REGEX = /:\s*(light|medium-light|medium|medium-dark|dark)\s+skin\s+tone$/i;
const SKIN_TONE_ORDER = ["default", "light", "medium-light", "medium", "medium-dark", "dark"];
const SKIN_TONE_LABELS = {
  default: "標準",
  light: "明るい肌色",
  "medium-light": "やや明るい肌色",
  medium: "中間の肌色",
  "medium-dark": "やや濃い肌色",
  dark: "濃い肌色",
};

const state = {
  query: "",
  searchMode: "fuzzy",
  selectedGroup: null,
  selectedTone: "default",
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
const COPIED_BUTTON_TEXT = "コピーしました";

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

const { groupByItemId } = buildSkinToneGroups(data);

function extractBaseName(name) {
  return name.replace(SKIN_TONE_REGEX, "").trim();
}

function extractSkinTone(name) {
  const match = name.match(SKIN_TONE_REGEX);
  return match ? match[1].toLowerCase() : "default";
}

function buildSkinToneGroups(items) {
  const groupMap = new Map();
  const itemMap = new Map();

  items.forEach((item, index) => {
    const baseName = extractBaseName(item.name_en);
    const key = baseName.toLowerCase();
    const tone = extractSkinTone(item.name_en);
    if (!groupMap.has(key)) {
      groupMap.set(key, {
        id: key,
        baseName,
        baseItem: null,
        firstIndex: index,
        variations: [],
      });
    }
    const group = groupMap.get(key);
    const variation = { item, tone, index };
    group.variations.push(variation);
    itemMap.set(item.id, group);
    if (tone === "default") group.baseItem = item;
  });

  const grouped = [...groupMap.values()].map((group) => {
    group.variations.sort((a, b) => {
      const toneOrder = SKIN_TONE_ORDER.indexOf(a.tone) - SKIN_TONE_ORDER.indexOf(b.tone);
      return toneOrder || a.index - b.index;
    });
    group.baseItem = group.baseItem || group.variations[0].item;
    group.hasSkinToneVariations = group.variations.some((variation) => variation.tone !== "default");
    group.defaultTone = group.variations.some((variation) => variation.tone === "default")
      ? "default"
      : group.variations[0].tone;
    return group;
  });

  return { groups: grouped, groupByItemId: itemMap };
}

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

function groupTerms(group) {
  const seen = new Set();
  const values = [];
  for (const variation of group.variations) {
    for (const term of allTerms(variation.item)) {
      if (!seen.has(term)) {
        seen.add(term);
        values.push(term);
      }
    }
  }
  return values;
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

function searchGroups() {
  const terms = termsFromQuery(state.query);
  const aggregate = new Map();

  data.forEach((item, index) => {
    const score = scoreItem(item, terms);
    if (score <= 0) return;
    const group = groupByItemId.get(item.id);
    const groupScore = score - importanceScore(item) + importanceScore(group.baseItem);
    const current = aggregate.get(group.id);
    if (!current || groupScore > current.score) {
      aggregate.set(group.id, { group, index: group.firstIndex, score: groupScore });
    } else if (current) {
      current.score = Math.max(current.score, groupScore);
      current.index = Math.min(current.index, index);
    }
  });

  return [...aggregate.values()]
    .sort((a, b) => {
      if (state.resultRandomSeed) {
        return randomScore(a.group.id, state.resultRandomSeed) - randomScore(b.group.id, state.resultRandomSeed);
      }
      return b.score - a.score || importanceScore(b.group.baseItem) - importanceScore(a.group.baseItem) || a.index - b.index;
    })
    .map((entry) => entry.group);
}

function selectedItem() {
  if (!state.selectedGroup) return null;
  return itemForTone(state.selectedGroup, state.selectedTone);
}

function itemForTone(group, tone) {
  return group.variations.find((variation) => variation.tone === tone)?.item || group.baseItem;
}

function makeCard(group) {
  const item = group.baseItem;
  const button = document.createElement("button");
  button.type = "button";
  button.className = "emoji-card";
  button.setAttribute("aria-label", `${item.name_ja} ${item.name_en}`);
  if (group.hasSkinToneVariations) button.title = "肌色バリエーションあり";
  if (state.selectedGroup?.id === group.id) button.classList.add("is-selected");
  if (group.hasSkinToneVariations) button.classList.add("has-skin-tones");
  button.innerHTML = `
    <span class="emoji-char">${escapeHtml(item.emoji)}</span>
    <span class="emoji-name">${escapeHtml(item.name_ja)}</span>
    ${group.hasSkinToneVariations ? '<span class="skin-indicator" aria-hidden="true"></span>' : ""}
  `;
  button.addEventListener("click", () => {
    if (state.selectedGroup?.id !== group.id) state.selectedTone = group.defaultTone;
    state.selectedGroup = group;
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

function matchedTermsForGroup(group, terms) {
  if (terms.length === 0) return [];
  return groupTerms(group).filter((value) => {
    const tag = value.toLowerCase();
    if (state.searchMode === "exact") return terms.includes(tag);
    return terms.some((term) => tag === term || tag.includes(term) || term.includes(tag));
  });
}

function renderHitTags(foundGroups) {
  const terms = termsFromQuery(state.query);
  const counts = new Map();
  for (const group of foundGroups) {
    for (const tag of matchedTermsForGroup(group, terms)) {
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
  const item = selectedItem();
  copyButton.disabled = !item;
  copyButton.textContent = item ? `${item.emoji}をコピー` : "絵文字を選んでコピー";
  if (!state.selectedGroup || !item) {
    selectedInline.className = "selected-inline selected-empty";
    selectedInline.textContent = "絵文字を選ぶと、ここに関連語を表示します。";
    return;
  }

  const group = state.selectedGroup;
  const terms = typedTerms(group.baseItem);
  selectedInline.className = "selected-inline";
  selectedInline.innerHTML = `
    <section class="selected-summary">
      <div class="selected-emoji">${escapeHtml(item.emoji)}</div>
      <div class="selected-title">
        <div class="selected-name">${escapeHtml(group.baseItem.name_ja)}</div>
        <div class="selected-en">${escapeHtml(group.baseItem.name_en)}</div>
        ${skinToneSelectorMarkup(group)}
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
  selectedInline.querySelectorAll("[data-skin-tone]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedTone = button.dataset.skinTone;
      render();
    });
    button.addEventListener("keydown", handleSkinToneKeydown);
  });
}

function skinToneSelectorMarkup(group) {
  if (!group.hasSkinToneVariations) return "";
  return `
    <div class="skin-tone-selector" role="radiogroup" aria-label="肌色を選択">
      ${group.variations.map((variation) => skinToneDotMarkup(variation)).join("")}
    </div>
  `;
}

function skinToneDotMarkup(variation) {
  const isSelected = variation.tone === state.selectedTone;
  return `
    <button
      class="skin-tone-dot skin-tone-${variation.tone}"
      type="button"
      data-skin-tone="${escapeHtml(variation.tone)}"
      aria-label="${escapeHtml(SKIN_TONE_LABELS[variation.tone] || variation.tone)}を選択"
      aria-checked="${isSelected}"
      ${isSelected ? 'aria-current="true"' : ""}
      role="radio"
    ></button>
  `;
}

function handleSkinToneKeydown(event) {
  if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Enter", " "].includes(event.key)) return;
  event.preventDefault();
  const buttons = [...selectedInline.querySelectorAll("[data-skin-tone]")];
  const currentIndex = buttons.indexOf(event.currentTarget);
  if (event.key === "Enter" || event.key === " ") {
    state.selectedTone = event.currentTarget.dataset.skinTone;
  } else {
    const offset = event.key === "ArrowLeft" || event.key === "ArrowUp" ? -1 : 1;
    const next = buttons[(currentIndex + offset + buttons.length) % buttons.length];
    state.selectedTone = next.dataset.skinTone;
  }
  render();
  const active = selectedInline.querySelector(`[data-skin-tone="${state.selectedTone}"]`);
  active?.focus();
}

function chipMarkup(value, type) {
  return `<button class="chip chip-button chip-${type}" type="button" data-search-tag="${escapeHtml(value)}">${escapeHtml(value)}</button>`;
}

function render() {
  const allFound = searchGroups();
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
  const item = selectedItem();
  if (!item) return;
  await navigator.clipboard.writeText(item.emoji);
  copyButton.textContent = COPIED_BUTTON_TEXT;
  window.setTimeout(() => {
    copyButton.textContent = `${selectedItem()?.emoji || item.emoji}をコピー`;
  }, 900);
});

renderQuickTags();
render();
