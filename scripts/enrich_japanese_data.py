import argparse
import csv
import json
import re
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "emoji.csv"
CLDR_FULL_URL = (
    "https://raw.githubusercontent.com/unicode-org/cldr-json/main/"
    "cldr-json/cldr-annotations-full/annotations/ja/annotations.json"
)
CLDR_DERIVED_URL = (
    "https://raw.githubusercontent.com/unicode-org/cldr-json/main/"
    "cldr-json/cldr-annotations-derived-full/annotationsDerived/ja/annotations.json"
)

FIELDNAMES = [
    "emoji",
    "codepoints",
    "name_en",
    "name_ja",
    "category",
    "category_ja",
    "subcategory",
    "subcategory_ja",
    "unicode_version",
    "tags_ja",
    "scenes_ja",
    "tone_ja",
]

CATEGORY_JA = {
    "Smileys & Emotion": "顔文字と感情",
    "People & Body": "人と体",
    "Component": "部品",
    "Animals & Nature": "動物と自然",
    "Food & Drink": "食べ物と飲み物",
    "Travel & Places": "旅行と場所",
    "Activities": "活動",
    "Objects": "物",
    "Symbols": "記号",
    "Flags": "旗",
}

SUBCATEGORY_JA = {
    "face-smiling": "笑顔",
    "face-affection": "愛情の顔",
    "face-tongue": "舌を出す顔",
    "face-hand": "手のある顔",
    "face-neutral-skeptical": "中立・疑いの顔",
    "face-sleepy": "眠い顔",
    "face-unwell": "体調の悪い顔",
    "face-hat": "帽子の顔",
    "face-glasses": "眼鏡の顔",
    "face-concerned": "心配な顔",
    "face-negative": "否定的な顔",
    "face-costume": "仮装の顔",
    "cat-face": "猫の顔",
    "monkey-face": "猿の顔",
    "emotion": "感情",
    "hand-fingers-open": "開いた手",
    "hand-fingers-partial": "部分的な手",
    "hand-single-finger": "一本指",
    "hand-fingers-closed": "閉じた手",
    "hands": "両手",
    "hand-prop": "手と道具",
    "body-parts": "体の部位",
    "person": "人",
    "person-gesture": "人のしぐさ",
    "person-role": "職業の人",
    "person-fantasy": "空想上の人",
    "person-activity": "活動する人",
    "person-sport": "スポーツする人",
    "person-resting": "休む人",
    "family": "家族",
    "person-symbol": "人の記号",
    "skin-tone": "肌の色",
    "hair-style": "髪型",
    "animal-mammal": "哺乳類",
    "animal-bird": "鳥",
    "animal-amphibian": "両生類",
    "animal-reptile": "爬虫類",
    "animal-marine": "海の動物",
    "animal-bug": "虫",
    "plant-flower": "花",
    "plant-other": "植物",
    "food-fruit": "果物",
    "food-vegetable": "野菜",
    "food-prepared": "料理",
    "food-asian": "アジア料理",
    "food-marine": "海の食べ物",
    "food-sweet": "甘い食べ物",
    "drink": "飲み物",
    "dishware": "食器",
    "place-map": "地図",
    "place-geographic": "地形",
    "place-building": "建物",
    "place-religious": "宗教施設",
    "place-other": "その他の場所",
    "transport-ground": "陸の乗り物",
    "transport-water": "水上の乗り物",
    "transport-air": "空の乗り物",
    "hotel": "ホテル",
    "time": "時間",
    "sky & weather": "空と天気",
    "event": "イベント",
    "award-medal": "賞とメダル",
    "sport": "スポーツ",
    "game": "ゲーム",
    "arts & crafts": "芸術と工作",
    "clothing": "服飾",
    "sound": "音",
    "music": "音楽",
    "musical-instrument": "楽器",
    "phone": "電話",
    "computer": "コンピューター",
    "light & video": "光と映像",
    "book-paper": "本と紙",
    "money": "お金",
    "mail": "郵便",
    "writing": "筆記",
    "office": "オフィス",
    "lock": "鍵",
    "tool": "道具",
    "science": "科学",
    "medical": "医療",
    "household": "家庭用品",
    "other-object": "その他の物",
    "transport-sign": "交通標識",
    "warning": "警告",
    "arrow": "矢印",
    "religion": "宗教",
    "zodiac": "星座",
    "av-symbol": "再生記号",
    "gender": "性別",
    "math": "数学",
    "punctuation": "句読点",
    "currency": "通貨",
    "other-symbol": "その他の記号",
    "keycap": "キーキャップ",
    "alphanum": "英数字",
    "geometric": "図形",
    "flag": "旗",
    "country-flag": "国旗",
    "subdivision-flag": "地域の旗",
}

GENERATED_CLASS_TAGS = {
    "顔", "表情", "感情", "人", "体", "手", "部品", "自然", "場所", "活動", "物", "道具",
    "記号", "国", "哺乳類", "鳥", "爬虫類", "虫", "植物", "果物", "野菜", "料理", "飲み物",
    "食器", "地図", "建物", "時間", "天気", "空", "イベント", "賞", "ゲーム", "芸術", "服",
    "音", "音楽", "電話", "本", "紙", "お金", "メール", "仕事", "鍵", "安全", "科学", "医療",
    "家", "注意", "矢印", "宗教", "星座", "性別", "数学", "図形", "旗", "地域",
}

KEYWORD_SCENES = {
    "笑顔": ["挨拶", "雑談"],
    "泣く": ["悲報", "共感"],
    "悲しい": ["別れ", "失敗"],
    "怒り": ["不満", "注意"],
    "愛": ["愛情表現", "お礼"],
    "動物": ["動物園", "癒し"],
    "猫": ["ペット", "癒し"],
    "犬": ["ペット", "散歩"],
    "鳥": ["自然", "朝"],
    "海": ["旅行", "夏"],
    "花": ["季節", "お祝い"],
    "食べ物": ["食事", "外食"],
    "飲み物": ["休憩", "乾杯"],
    "旅行": ["移動", "遠出"],
    "乗り物": ["移動", "旅行"],
    "スポーツ": ["試合", "応援"],
    "音楽": ["ライブ", "趣味"],
    "お祝い": ["誕生日", "成功"],
    "旗": ["国", "地域"],
    "仕事": ["作業", "連絡"],
    "医療": ["体調", "病院"],
    "天気": ["外出", "季節"],
}

KEYWORD_TONES = {
    "笑顔": ["明るい", "親しみ"],
    "嬉しい": ["明るい", "前向き"],
    "かわいい": ["かわいい", "やさしい"],
    "愛": ["温かい", "好意"],
    "泣く": ["感情的", "素直"],
    "悲しい": ["しんみり", "弱い"],
    "怒り": ["強い", "否定的"],
    "動物": ["かわいい", "親しみ"],
    "自然": ["穏やか", "季節感"],
    "花": ["きれい", "やさしい"],
    "食べ物": ["日常", "親しみ"],
    "飲み物": ["日常", "落ち着き"],
    "旅行": ["活動的", "期待"],
    "スポーツ": ["元気", "活動的"],
    "音楽": ["楽しい", "にぎやか"],
    "お祝い": ["祝福", "明るい"],
    "記号": ["実用的", "中立"],
    "仕事": ["実用的", "中立"],
}

CATEGORY_SCENES = {
    "Smileys & Emotion": ["会話", "リアクション"],
    "People & Body": ["会話", "自己紹介"],
    "Animals & Nature": ["自然", "癒し"],
    "Food & Drink": ["食事", "休憩"],
    "Travel & Places": ["旅行", "移動"],
    "Activities": ["イベント", "趣味"],
    "Objects": ["作業", "日常"],
    "Symbols": ["案内", "整理"],
    "Flags": ["国", "地域"],
}

CATEGORY_TONES = {
    "Smileys & Emotion": ["感情的", "会話向き"],
    "People & Body": ["親しみ", "会話向き"],
    "Animals & Nature": ["親しみ", "自然"],
    "Food & Drink": ["日常", "親しみ"],
    "Travel & Places": ["活動的", "実用的"],
    "Activities": ["楽しい", "にぎやか"],
    "Objects": ["実用的", "中立"],
    "Symbols": ["実用的", "中立"],
    "Flags": ["公式", "中立"],
}

SHORT_NAME_OVERRIDES = {
    "grinning face": "にっこり笑顔",
    "grinning face with big eyes": "大きな目の笑顔",
    "grinning face with smiling eyes": "目を細めた笑顔",
    "beaming face with smiling eyes": "満面の笑顔",
    "grinning squinting face": "目を閉じた笑顔",
    "grinning face with sweat": "汗笑い",
    "rolling on the floor laughing": "転げるほど笑う顔",
    "face with tears of joy": "嬉し泣き笑い",
    "slightly smiling face": "少し笑う顔",
    "smiling face with smiling eyes": "ほほえみ",
    "smiling face with heart-eyes": "ハート目の笑顔",
    "smiling face with hearts": "ハートに囲まれた笑顔",
    "crying face": "泣き顔",
    "loudly crying face": "大泣き",
    "folded hands": "合わせた手",
    "thumbs up": "サムズアップ",
    "clapping hands": "拍手",
    "red heart": "赤いハート",
    "party popper": "クラッカー",
    "birthday cake": "誕生日ケーキ",
    "cherry blossom": "桜",
    "sunflower": "ひまわり",
    "watermelon": "スイカ",
    "dog face": "犬の顔",
    "cat face": "猫の顔",
    "rabbit face": "うさぎの顔",
    "panda": "パンダ",
    "fish": "魚",
    "dolphin": "イルカ",
    "steaming bowl": "ラーメン",
    "sushi": "寿司",
    "beer mug": "ビール",
    "hot beverage": "コーヒー",
    "automobile": "車",
    "airplane": "飛行機",
    "house": "家",
    "light bulb": "電球",
    "magnifying glass tilted left": "虫眼鏡",
}

CLDR_NOISE = {
    "U",
    "絵文字",
    "顔",
}

NAME_TAG_EXCLUSIONS = {
    "lion": {"しし座", "星座"},
    "watermelon": {"野菜"},
}


def split_list(value):
    if not value:
        return []
    return [item.strip() for item in value.replace(",", ";").split(";") if item.strip()]


def unique(values):
    seen = set()
    result = []
    for value in values:
        value = value.strip()
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def join_list(values):
    return ";".join(unique(values))


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def load_cldr(full_path=None, derived_path=None):
    if full_path:
        full = json.loads(Path(full_path).read_text(encoding="utf-8"))
    else:
        full = fetch_json(CLDR_FULL_URL)

    if derived_path:
        derived = json.loads(Path(derived_path).read_text(encoding="utf-8"))
    else:
        derived = fetch_json(CLDR_DERIVED_URL)

    annotations = {}
    annotations.update(full["annotations"]["annotations"])
    annotations.update(derived["annotationsDerived"]["annotations"])
    return annotations


def clean_tts(value):
    value = value.replace("：", ":").strip()
    if value.startswith("旗: "):
        return f"{value[3:]}の旗"
    value = value.replace(": 薄い肌色", "（薄い肌色）")
    value = value.replace(": やや薄い肌色", "（やや薄い肌色）")
    value = value.replace(": 中間の肌色", "（中間の肌色）")
    value = value.replace(": やや濃い肌色", "（やや濃い肌色）")
    value = value.replace(": 濃い肌色", "（濃い肌色）")
    return value


def japanese_name(row, annotation):
    existing = row.get("name_ja", "").strip()
    name_en = row["name_en"].strip()
    if name_en in SHORT_NAME_OVERRIDES:
        return SHORT_NAME_OVERRIDES[name_en]
    if existing and existing != name_en:
        return existing
    if annotation and annotation.get("tts"):
        return clean_tts(annotation["tts"][0])
    return name_en


def cldr_tags(annotation):
    if not annotation:
        return []
    values = annotation.get("default", [])
    return [value for value in values if value not in CLDR_NOISE and len(value) <= 16]


def filtered_tags(row, tags):
    exclusions = NAME_TAG_EXCLUSIONS.get(row["name_en"], set())
    return [tag for tag in tags if tag not in exclusions]


def generated_scenes(row, tags):
    scenes = []
    for tag in tags:
        scenes.extend(KEYWORD_SCENES.get(tag, []))
    scenes.extend(CATEGORY_SCENES.get(row["category"], []))
    return scenes[:8]


def generated_tones(row, tags):
    tones = []
    for tag in tags:
        tones.extend(KEYWORD_TONES.get(tag, []))
    tones.extend(CATEGORY_TONES.get(row["category"], []))
    return tones[:8]


def should_drop_old_tag(tag, annotation_tags):
    if tag in annotation_tags:
        return False
    return tag in GENERATED_CLASS_TAGS


def enrich_row(row, annotations):
    annotation = annotations.get(row["emoji"], {})
    annotation_tags = filtered_tags(row, cldr_tags(annotation))
    old_tags = [
        tag for tag in split_list(row.get("tags_ja", ""))
        if not should_drop_old_tag(tag, annotation_tags)
    ]
    tags = filtered_tags(row, unique([*old_tags, *annotation_tags]))
    scenes = unique([*split_list(row.get("scenes_ja", "")), *generated_scenes(row, tags)])
    tones = unique([*split_list(row.get("tone_ja", "")), *generated_tones(row, tags)])

    return {
        "emoji": row["emoji"],
        "codepoints": row["codepoints"],
        "name_en": row["name_en"],
        "name_ja": japanese_name(row, annotation),
        "category": row["category"],
        "category_ja": CATEGORY_JA.get(row["category"], row["category"]),
        "subcategory": row["subcategory"],
        "subcategory_ja": SUBCATEGORY_JA.get(row["subcategory"], row["subcategory"]),
        "unicode_version": row["unicode_version"],
        "tags_ja": join_list(tags),
        "scenes_ja": join_list(scenes),
        "tone_ja": join_list(tones),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=CSV_PATH)
    parser.add_argument("--cldr-full", type=Path)
    parser.add_argument("--cldr-derived", type=Path)
    args = parser.parse_args()

    annotations = load_cldr(args.cldr_full, args.cldr_derived)
    with args.csv.open("r", encoding="utf-8-sig", newline="") as fp:
        rows = [enrich_row(row, annotations) for row in csv.DictReader(fp)]

    with args.csv.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Enriched {len(rows)} emoji with Japanese names, categories, tags, scenes, and tones.")


if __name__ == "__main__":
    main()
