const data = window.EMOJI_DATA?.items ?? [];
const visibleData = data.filter((item) => !item.hidden_variant);

const SKIN_TONE_REGEX = /(?:[:,]\s*)?(light|medium-light|medium|medium-dark|dark)\s+skin\s+tone/i;
const SKIN_TONE_CLEANUP_REGEX = /\b(?:light|medium-light|medium|medium-dark|dark)\s+skin\s+tone\b/gi;
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
  copiedEmoji: "",
  stock: [],
  resultRandomSeed: 0,
};

const searchInput = document.querySelector("#searchInput");
const fuzzyModeButton = document.querySelector("#fuzzyModeButton");
const exactModeButton = document.querySelector("#exactModeButton");
const quickTags = document.querySelector("#quickTags");
const stockWorkbench = document.querySelector("#stockWorkbench");
const selectedInline = document.querySelector("#selectedInline");
const stickyWorkbench = document.querySelector(".sticky-workbench");
const results = document.querySelector("#results");
const resultCount = document.querySelector("#resultCount");
const hitTags = document.querySelector("#hitTags");
const copyButton = document.querySelector("#copyButton");
const randomResultsButton = document.querySelector("#randomResultsButton");

const presetTags = [
  "笑顔",
  "ハート",
  "カフェ",
  "専門職",
  "撮る",
  "白",
  "入力",
  "リラックス",
];

const { groupByItemId } = buildSkinToneGroups(visibleData);

function extractBaseName(name) {
  return name
    .replace(SKIN_TONE_CLEANUP_REGEX, "")
    .replace(/\s*,\s*,/g, ",")
    .replace(/:\s*,\s*/g, ": ")
    .replace(/,\s*:/g, ":")
    .replace(/,\s*$/g, "")
    .replace(/:\s*$/g, "")
    .trim();
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
    meaning: arrayValue(item.meaning_ja),
    usage: arrayValue(item.usage_ja),
    impression: arrayValue(item.impression_ja),
    classes: classTerms(item),
  };
}

const DISPLAY_UNIQUE_TRIM_THRESHOLD = 8;
const DISPLAY_TERM_COUNTS = buildDisplayTermCounts(visibleData);
const COMMON_DISPLAY_STOP_TAGS = new Set(["人"]);
const OCCUPATION_DISPLAY_STOP_TAGS = new Set([
  "職業",
  "制服",
  "仕事姿",
  "仕事",
  "職場",
  "専門職",
  "紹介",
  "専門家",
  "働く人",
  "働く",
  "医師",
  "診る",
  "診察",
]);
const SUBCATEGORY_DISPLAY_STOP_TAGS = {
  国旗: [
    "旗",
    "国旗",
    "国",
    "地域",
    "代表",
    "所属",
    "掲げる",
  ],
  哺乳類: [
    "哺乳類",
    "生き物",
    "生命",
    "野生",
    "毛",
    "しっぽ",
    "動物園",
  ],
  "空と天気": [
    "空",
    "天気",
    "空模様",
    "気象",
    "天気予報",
    "季節",
    "外出",
    "変わる",
  ],
  陸の乗り物: [
    "乗り物",
    "交通",
    "移動",
    "便利",
    "速さ",
    "走る",
    "乗る",
    "車輪",
    "道",
    "実用的",
  ],
  時間: [
    "時間",
    "時計",
    "時刻",
    "針",
    "文字盤",
    "丸い",
    "計る",
  ],
  英数字: [
    "英数字記号",
    "ボタン",
    "ラベル",
    "状態",
    "入力",
    "表示",
    "示す",
    "文字",
    "四角",
    "実用的",
  ],
  再生記号: [
    "再生記号",
    "操作ボタン",
    "操作",
    "メディア",
    "操作する",
    "三角",
    "ボタン",
    "実用的",
  ],
  その他の記号: [
    "記号",
    "マーク",
    "意味",
    "サイン",
    "表示",
    "案内",
    "示す",
    "形",
    "印",
    "実用的",
  ],
  料理: [
    "料理",
    "食べ物",
    "食事",
    "ごはん",
    "食べる",
    "皿",
    "焼き色",
  ],
  飲み物: [
    "飲み物",
    "ドリンク",
    "水分",
    "飲む",
    "コップ",
    "液体",
    "食事",
  ],
  果物: [
    "果物",
    "フルーツ",
    "食べる",
    "色",
  ],
  野菜: [
    "野菜",
    "食材",
    "料理",
    "食事",
    "食べる",
    "調理する",
    "形",
  ],
  道具: [
    "道具",
    "工具",
    "金属",
    "持ち手",
    "実用的",
  ],
  家庭用品: [
    "家庭用品",
    "生活用品",
    "生活",
    "使う",
    "道具",
    "実用的",
  ],
  人: [
    "人物",
    "個人",
    "アイコン",
    "プロフィール",
    "自己紹介",
    "人物紹介",
    "顔",
    "上半身",
  ],
  活動する人: [
    "活動する人",
    "活動",
    "挑戦",
    "運動",
    "趣味",
    "外出",
    "日常",
    "動く",
    "全身",
    "動き",
  ],
  スポーツする人: [
    "人",
    "競技",
    "勝負",
    "挑戦",
    "試合",
    "部活",
    "応援",
    "運動会",
    "競う",
    "運動する",
    "運動",
  ],
  スポーツ: [
    "競技",
    "勝負",
    "運動",
    "試合",
    "部活",
    "応援",
    "競う",
    "道具",
    "ボール",
  ],
  服飾: [
    "服飾",
    "身につける物",
    "装い",
    "ファッション",
    "身支度",
    "着る",
    "布",
    "形",
  ],
  笑顔: [
    "笑顔",
    "顔",
    "チャット",
    "返信",
    "雑談",
    "SNS",
    "黄色",
  ],
  愛情の顔: [
    "顔",
    "チャット",
    "返信",
    "SNS",
    "黄色",
  ],
  舌を出す顔: [
    "舌",
    "顔",
    "チャット",
    "返信",
    "SNS",
    "黄色",
    "舌を出す",
  ],
  手のある顔: [
    "手",
    "顔",
    "チャット",
    "返信",
    "SNS",
    "黄色",
  ],
  "中立・疑いの顔": [
    "顔",
    "チャット",
    "返信",
    "SNS",
    "黄色",
  ],
  眠い顔: [
    "顔",
    "チャット",
    "返信",
    "SNS",
    "黄色",
  ],
  体調の悪い顔: [
    "顔",
    "返信",
    "チャット",
    "SNS",
    "黄色",
  ],
  帽子の顔: [
    "顔",
    "チャット",
    "SNS",
    "黄色",
    "帽子",
  ],
  眼鏡の顔: [
    "顔",
    "チャット",
    "SNS",
    "黄色",
    "メガネ",
  ],
  心配な顔: [
    "顔",
    "チャット",
    "返信",
    "SNS",
    "黄色",
  ],
  否定的な顔: [
    "顔",
    "チャット",
    "返信",
    "SNS",
  ],
  仮装の顔: [
    "顔",
    "チャット",
    "SNS",
    "仮装",
  ],
  猫の顔: [
    "猫",
    "顔",
    "チャット",
    "返信",
    "SNS",
    "猫好き",
    "ペット",
    "猫耳",
    "ひげ",
    "黄色",
  ],
  猿の顔: [
    "猿",
    "顔",
    "チャット",
    "SNS",
    "三猿",
  ],
  感情: [
    "チャット",
    "SNS",
    "漫画表現",
    "メッセージ",
    "吹き出し",
    "会話",
    "コメント",
  ],
  開いた手: [
    "開いた手",
    "手",
    "手のひら",
    "合図",
    "意思表示",
    "チャット",
    "SNS",
    "リアクション",
    "示す",
    "指",
  ],
  部分的な手: [
    "手",
    "指サイン",
    "合図",
    "意思表示",
    "チャット",
    "SNS",
    "リアクション",
    "示す",
    "指",
    "ジェスチャー",
  ],
  一本指: [
    "指差し",
    "指",
    "手",
    "方向",
    "指示",
    "案内",
    "説明",
    "注目",
    "チャット",
    "示す",
  ],
  閉じた手: [
    "手",
    "こぶし",
    "リアクション",
    "チャット",
    "握る",
    "握った手",
  ],
  両手: [
    "両手",
    "手",
    "協力",
    "チャット",
    "合わせる",
  ],
  手と道具: [
    "手",
    "道具",
    "自己表現",
    "記録",
    "作業",
    "SNS",
    "手元",
  ],
  体の部位: [
    "体",
    "部位",
    "身体",
    "感覚",
    "説明",
  ],
  人のしぐさ: [
    "人",
    "ジェスチャー",
    "意思表示",
    "態度",
    "チャット",
    "リアクション",
    "会話",
    "説明",
    "示す",
    "答える",
    "ポーズ",
    "上半身",
  ],
  空想上の人: [
    "人",
    "空想上の人",
    "伝説",
    "非日常",
    "物語",
    "創作",
    "衣装",
  ],
  休む人: [
    "人",
    "休む人",
    "休息",
    "回復",
    "休憩",
    "睡眠",
    "リラックス",
  ],
  家族: [
    "家族",
    "人",
    "つながり",
    "家庭",
    "記念写真",
    "家族紹介",
  ],
  人の記号: [
    "人の記号",
    "人物アイコン",
    "匿名",
    "個人",
    "グループ",
    "プロフィール",
    "アカウント",
    "ユーザー",
    "名簿",
  ],
  鳥: [
    "鳥",
    "羽",
    "自然",
    "飛翔",
    "空",
    "観察",
    "飛ぶ",
    "くちばし",
  ],
  爬虫類: [
    "爬虫類",
    "野生",
    "自然",
    "動物園",
    "うろこ",
    "しっぽ",
  ],
  海の動物: [
    "海の生き物",
    "海洋",
    "生命",
    "水族館",
    "泳ぐ",
    "水中",
  ],
  虫: [
    "虫",
    "小さな生き物",
    "自然",
    "観察",
    "動く",
    "小さい",
    "脚",
  ],
  花: [
    "花",
    "季節",
    "庭",
    "咲く",
    "花びら",
    "色",
  ],
  植物: [
    "植物",
    "自然",
    "季節",
    "成長",
    "生命",
    "庭",
    "観葉植物",
    "育つ",
    "緑",
    "葉",
  ],
  アジア料理: [
    "料理",
    "アジア料理",
    "ごはん",
    "定番",
    "食事",
    "外食",
    "食べる",
    "日本",
    "アジア",
    "器",
  ],
  甘い食べ物: [
    "甘い食べ物",
    "スイーツ",
    "ご褒美",
    "甘さ",
    "おやつ",
    "デザート",
    "カフェ",
    "差し入れ",
    "食べる",
    "甘い",
    "色",
  ],
  食器: [
    "食器",
    "道具",
    "準備",
    "暮らし",
    "食事",
    "料理",
    "台所",
    "使う",
    "金属",
    "器",
    "実用的",
  ],
  地図: [
    "地図",
    "場所",
    "方向",
    "地理",
    "案内",
    "探す",
    "地域",
    "線",
    "実用的",
  ],
  地形: [
    "地形",
    "自然",
    "風景",
    "旅行",
    "アウトドア",
    "観光",
    "眺める",
    "空",
  ],
  建物: [
    "建物",
    "場所",
    "都市",
    "街",
    "施設",
    "外出",
    "訪れる",
    "建築",
    "外観",
    "暮らし",
  ],
  宗教施設: [
    "宗教施設",
    "建物",
    "信仰",
    "参拝",
    "観光",
    "祈り",
    "祈る",
    "宗教",
    "屋根",
  ],
  その他の場所: [
    "場所",
    "風景",
    "思い出",
    "レジャー",
    "旅行",
    "観光",
    "外出",
    "行く",
    "景色",
    "空",
  ],
  水上の乗り物: [
    "船",
    "水上の乗り物",
    "航海",
    "移動",
    "旅行",
    "港",
    "進む",
    "乗る",
    "水",
  ],
  空の乗り物: [
    "空の乗り物",
    "乗り物",
    "飛行",
    "旅行",
    "空港",
    "移動",
    "飛ぶ",
    "乗る",
    "空",
    "翼",
  ],
  イベント: [
    "イベント",
    "記念",
    "祝福",
    "お祝い",
    "季節行事",
    "パーティー",
    "祝う",
    "飾り",
    "色",
  ],
  賞とメダル: [
    "賞",
    "メダル",
    "勝利",
    "実績",
    "大会",
    "表彰",
    "スポーツ",
    "表彰する",
    "金属",
    "丸い",
  ],
  ゲーム: [
    "ゲーム",
    "遊び",
    "運",
    "戦略",
    "趣味",
    "パーティー",
    "遊ぶ",
    "おもちゃ",
    "記号",
  ],
  芸術と工作: [
    "工作",
    "芸術",
    "創作",
    "表現",
    "制作",
    "趣味",
    "学校",
    "作る",
    "道具",
  ],
  音: [
    "音",
    "音響",
    "知らせ",
    "通知",
    "アナウンス",
    "鳴る",
    "記号",
  ],
  音楽: [
    "音楽",
    "機材",
    "表現",
    "リズム",
    "録音",
    "配信",
    "聴く",
    "機械",
  ],
  楽器: [
    "楽器",
    "音楽",
    "表現",
    "演奏",
    "ライブ",
    "練習",
    "演奏する",
    "木",
    "金属",
  ],
  電話: [
    "電話",
    "通信",
    "つながり",
    "連絡",
    "仕事",
    "会話",
    "電話する",
    "機械",
    "実用的",
  ],
  コンピューター: [
    "コンピューター",
    "IT",
    "記録",
    "仕事",
    "勉強",
    "デジタル",
    "使う",
    "画面",
    "部品",
    "実用的",
  ],
  光と映像: [
    "光",
    "映像",
    "記録",
    "撮影",
    "映画",
    "配信",
    "撮る",
    "レンズ",
  ],
  本と紙: [
    "本",
    "紙",
    "ページ",
    "知識",
    "記録",
    "読書",
    "勉強",
    "書類",
    "読む",
    "四角",
  ],
  お金: [
    "お金",
    "価値",
    "資産",
    "買い物",
    "会計",
    "仕事",
    "払う",
    "紙幣",
    "金属",
    "実用的",
  ],
  郵便: [
    "郵便",
    "メール",
    "メッセージ",
    "届ける",
    "連絡",
    "配送",
    "仕事",
    "送る",
    "箱",
    "実用的",
  ],
  筆記: [
    "筆記具",
    "書く道具",
    "記録",
    "表現",
    "勉強",
    "仕事",
    "メモ",
    "書く",
    "線",
  ],
  オフィス: [
    "オフィス用品",
    "文具",
    "管理",
    "記録",
    "仕事",
    "学校",
    "整理",
    "整理する",
    "紙",
    "道具",
    "実用的",
  ],
  鍵: [
    "鍵",
    "ロック",
    "安全",
    "防犯",
    "ログイン",
    "保管",
    "開ける",
    "閉める",
    "金属",
  ],
  科学: [
    "科学",
    "実験道具",
    "知識",
    "発見",
    "研究",
    "実験",
    "観察",
    "調べる",
    "ガラス",
    "機械",
  ],
  医療: [
    "医療",
    "治療道具",
    "治療",
    "回復",
    "病院",
    "健康",
    "手当て",
    "治す",
    "白",
    "赤",
  ],
  その他の物: [
    "物",
    "その他の物",
    "象徴",
    "印",
    "生活",
    "儀式",
    "表示",
    "置く",
    "形",
    "素材",
  ],
  交通標識: [
    "案内記号",
    "施設記号",
    "案内",
    "公共",
    "駅",
    "示す",
    "四角",
    "標識",
    "実用的",
  ],
  警告: [
    "注意",
    "警告記号",
    "禁止記号",
    "危険",
    "禁止",
    "道路",
    "ルール",
    "止める",
    "赤",
    "斜線",
  ],
  矢印: [
    "矢印",
    "方向",
    "移動",
    "案内",
    "操作",
    "説明",
    "示す",
    "向き",
    "線",
    "実用的",
  ],
  宗教: [
    "宗教記号",
    "象徴",
    "信仰",
    "神聖",
    "宗教",
    "祈り",
    "文化",
    "祈る",
    "記号",
    "形",
  ],
  星座: [
    "星座",
    "占い",
    "運勢",
    "性格診断",
    "誕生日",
    "占う",
    "記号",
    "線",
  ],
  性別: [
    "性別記号",
    "性別",
    "ジェンダー",
    "プロフィール",
    "多様性",
    "表す",
    "丸",
    "線",
  ],
  数学: [
    "数学記号",
    "数式",
    "比較",
    "計算",
    "勉強",
    "計算する",
    "線",
    "記号",
  ],
  句読点: [
    "句読点",
    "記号",
    "疑問",
    "驚き",
    "文章",
    "チャット",
    "強調",
    "強調する",
  ],
  キーキャップ: [
    "キーキャップ",
    "数字キー",
    "ボタン",
    "入力",
    "番号",
    "入力する",
    "四角",
    "文字",
    "実用的",
  ],
  図形: [
    "図形",
    "形",
    "色分け",
    "シンプル",
    "デザイン",
    "分類",
    "目印",
    "示す",
    "色",
    "幾何学",
  ],
  旗: [
    "旗",
    "合図",
    "所属",
    "目印",
    "応援",
    "イベント",
    "掲げる",
    "布",
  ],
  地域の旗: [
    "旗",
    "国旗",
    "国",
    "地域",
    "代表",
    "所属",
    "掲げる",
  ],
};

function uniqueTerms(values) {
  const seen = new Set();
  return values.filter((value) => {
    if (seen.has(value)) return false;
    seen.add(value);
    return true;
  });
}

function displayStopTags(item) {
  const result = new Set(COMMON_DISPLAY_STOP_TAGS);
  if (classTerms(item).includes("職業の人")) {
    OCCUPATION_DISPLAY_STOP_TAGS.forEach((value) => result.add(value));
  }
  for (const value of SUBCATEGORY_DISPLAY_STOP_TAGS[item.subcategory_ja] || []) {
    result.add(value);
  }
  return result;
}

function displayTerms(item) {
  const terms = typedTerms(item);
  const stopTags = displayStopTags(item);
  const filter = (values) => uniqueTerms(values).filter((value) => !stopTags.has(value));
  return trimLowSignalUniqueTerms(item, {
    meaning: filter(terms.meaning),
    usage: filter(terms.usage),
    impression: filter(terms.impression),
    classes: terms.classes,
  });
}

function allTerms(item) {
  const terms = typedTerms(item);
  return [...terms.meaning, ...terms.usage, ...terms.impression, ...terms.classes];
}

function buildDisplayTermCounts(items) {
  const counts = new Map();
  for (const item of items) {
    const terms = typedTerms(item);
    const values = uniqueTerms([...terms.meaning, ...terms.usage, ...terms.impression]);
    for (const value of values) {
      counts.set(value, (counts.get(value) || 0) + 1);
    }
  }
  return counts;
}

function protectedDisplayTerms(item) {
  return new Set([item.name_ja, item.name_ja?.replace(/（.+$/, "")].filter(Boolean));
}

function trimLowSignalUniqueTerms(item, terms) {
  const displayCount = terms.meaning.length + terms.usage.length + terms.impression.length;
  if (displayCount < DISPLAY_UNIQUE_TRIM_THRESHOLD) return terms;

  const protectedTerms = protectedDisplayTerms(item);
  return {
    ...terms,
    impression: terms.impression.filter((value) => {
      if (protectedTerms.has(value)) return true;
      return (DISPLAY_TERM_COUNTS.get(value) || 0) > 1;
    }),
  };
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

  visibleData.forEach((item, index) => {
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

async function copyEmoji(item) {
  if (!item) return;
  await navigator.clipboard.writeText(item.emoji);
  state.copiedEmoji = item.emoji;
  copyButton.textContent = `${item.emoji}をコピーしました`;
}

function itemForTone(group, tone) {
  return group.variations.find((variation) => variation.tone === tone)?.item || group.baseItem;
}

function selectGroup(group, options = {}) {
  if (state.selectedGroup?.id !== group.id) state.selectedTone = group.defaultTone;
  state.selectedGroup = group;
  render();
  if (options.scrollToTop) {
    window.requestAnimationFrame(() => {
      scrollSelectedIntoView();
    });
  }
}

function scrollSelectedIntoView() {
  const scrollingElement = document.scrollingElement || document.documentElement;
  const stickyHeight = stickyWorkbench?.getBoundingClientRect().height || 0;
  const targetTop = selectedInline.getBoundingClientRect().top + scrollingElement.scrollTop - stickyHeight - 8;
  scrollingElement.scrollTo({
    top: Math.max(0, targetTop),
    behavior: "smooth",
  });
}

function addSelectedToStock() {
  const item = selectedItem();
  if (!item) return;
  state.stock = [...state.stock, item.emoji].slice(-20);
  render();
}

function removeStockAt(index) {
  state.stock = state.stock.filter((_, itemIndex) => itemIndex !== index);
  render();
}

async function copyStock(event) {
  if (!state.stock.length) return;
  await navigator.clipboard.writeText(state.stock.join(""));
  copyButton.textContent = "ストックをコピーしました";
  if (event?.currentTarget) event.currentTarget.textContent = "コピーしました";
}

function clearStock() {
  state.stock = [];
  render();
}

function makeCard(group) {
  const item = group.baseItem;
  const isStocked = group.variations.some((variation) => state.stock.includes(variation.item.emoji));
  const button = document.createElement("button");
  button.type = "button";
  button.className = "emoji-card";
  button.setAttribute("aria-label", `${item.name_ja} ${item.name_en}`);
  if (group.hasSkinToneVariations) button.title = "肌色バリエーションあり";
  if (state.selectedGroup?.id === group.id) button.classList.add("is-selected");
  if (group.hasSkinToneVariations) button.classList.add("has-skin-tones");
  if (isStocked) button.classList.add("is-stocked");
  button.innerHTML = `
    <span class="emoji-char">${escapeHtml(item.emoji)}</span>
    <span class="emoji-name">${escapeHtml(item.name_ja)}</span>
    ${group.hasSkinToneVariations ? '<span class="skin-indicator" aria-hidden="true"></span>' : ""}
    ${isStocked ? '<span class="stocked-indicator" aria-hidden="true">✓</span>' : ""}
  `;
  button.addEventListener("click", async (event) => {
    if (event.target.closest(".emoji-char")) {
      selectGroup(group, { scrollToTop: true });
      await copyEmoji(selectedItem() || item);
      return;
    }
    selectGroup(group, { scrollToTop: true });
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

function applySearch(query, mode = state.searchMode, options = {}) {
  state.query = query;
  state.searchMode = mode;
  state.resultRandomSeed = 0;
  searchInput.value = query;
  render();
  if (options.focus) searchInput.focus();
}

function setSearchMode(mode) {
  state.searchMode = mode;
  state.resultRandomSeed = 0;
  render();
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

function renderStockWorkbench() {
  if (!state.stock.length) {
    stockWorkbench.className = "stock-workbench stock-empty";
    stockWorkbench.textContent = "＋ストックでまとめてコピー用に追加";
    return;
  }

  stockWorkbench.className = "stock-workbench";
  stockWorkbench.innerHTML = `
    <div class="stock-items" aria-label="ストックした絵文字">
      ${state.stock
        .map(
          (emoji, index) =>
            `<button class="stock-emoji" type="button" data-stock-index="${index}" aria-label="${escapeHtml(emoji)}をストックから削除"><span>${escapeHtml(emoji)}</span><span class="stock-remove-mark" aria-hidden="true">×</span></button>`,
        )
        .join("")}
    </div>
    <div class="stock-actions">
      <button class="stock-copy-button" type="button" data-copy-stock>まとめてコピー</button>
      <button class="stock-clear-button" type="button" data-clear-stock>クリア</button>
    </div>
  `;

  stockWorkbench.querySelector("[data-copy-stock]")?.addEventListener("click", copyStock);
  stockWorkbench.querySelector("[data-clear-stock]")?.addEventListener("click", clearStock);
  stockWorkbench.querySelectorAll("[data-stock-index]").forEach((button) => {
    button.addEventListener("click", () => {
      removeStockAt(Number.parseInt(button.dataset.stockIndex, 10));
    });
  });
}
function renderSelectedInline() {
  const item = selectedItem();
  copyButton.disabled = !item;
  copyButton.textContent = item
    ? item.emoji === state.copiedEmoji
      ? `${item.emoji}をコピーしました`
      : `${item.emoji}をコピー`
    : "絵文字を選んでコピー";
  if (!state.selectedGroup || !item) {
    selectedInline.className = "selected-inline selected-empty";
    selectedInline.textContent = "絵文字を選ぶと、ここに関連語を表示します。";
    return;
  }

  const group = state.selectedGroup;
  const terms = displayTerms(group.baseItem);
  selectedInline.className = "selected-inline";
  selectedInline.innerHTML = `
    <section class="selected-summary">
      <div class="selected-emoji">${escapeHtml(item.emoji)}</div>
      <div class="selected-title">
        <div class="selected-name">${escapeHtml(group.baseItem.name_ja)}</div>
        <div class="selected-en">${escapeHtml(group.baseItem.name_en)}</div>
        ${skinToneSelectorMarkup(group)}
      </div>
      <button class="stock-add-button" type="button" data-add-stock>＋ストック</button>
    </section>
    <div class="chips merged-chips">
      ${terms.meaning.map((value) => chipMarkup(value, "meaning")).join("")}
      ${terms.usage.map((value) => chipMarkup(value, "usage")).join("")}
      ${terms.impression.map((value) => chipMarkup(value, "impression")).join("")}
      ${terms.classes.map((value) => chipMarkup(value, "class")).join("")}
    </div>
  `;

  selectedInline.querySelectorAll("[data-search-tag]").forEach((button) => {
    button.addEventListener("click", () => {
      applySearch(button.dataset.searchTag, "exact");
    });
  });
  selectedInline.querySelector("[data-add-stock]")?.addEventListener("click", addSelectedToStock);
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
  renderStockWorkbench();
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
  await copyEmoji(item);
});

renderQuickTags();
render();

