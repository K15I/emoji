import argparse
import csv
import re
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "emoji.csv"
DEFAULT_URL = "https://unicode.org/Public/emoji/latest/emoji-test.txt"
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

LINE_RE = re.compile(
    r"^(?P<codepoints>[0-9A-F ]+)\s*;\s*fully-qualified\s*#\s*"
    r"(?P<emoji>\S+)\s+E(?P<version>[0-9.]+)\s+(?P<name>.+)$"
)

GROUP_TAGS = {
    "Smileys & Emotion": ["顔", "表情", "感情"],
    "People & Body": ["人", "体", "手"],
    "Component": ["部品"],
    "Animals & Nature": ["動物", "自然"],
    "Food & Drink": ["食べ物", "飲み物"],
    "Travel & Places": ["旅行", "場所", "乗り物"],
    "Activities": ["活動", "イベント", "遊び"],
    "Objects": ["物", "道具"],
    "Symbols": ["記号"],
    "Flags": ["旗", "国"],
}

SUBGROUP_TAGS = {
    "face-smiling": ["笑顔", "嬉しい"],
    "face-affection": ["好き", "愛", "かわいい"],
    "face-tongue": ["冗談", "楽しい"],
    "face-hand": ["顔", "手"],
    "face-neutral-skeptical": ["中立", "考える"],
    "face-sleepy": ["眠い", "疲れ"],
    "face-unwell": ["体調", "つらい"],
    "face-hat": ["顔"],
    "face-glasses": ["顔", "眼鏡"],
    "face-concerned": ["悲しい", "心配"],
    "face-negative": ["怒り", "不満"],
    "face-costume": ["仮装", "顔"],
    "emotion": ["感情", "気持ち"],
    "hand-fingers-open": ["手", "指"],
    "hand-fingers-partial": ["手", "指"],
    "hand-single-finger": ["手", "指"],
    "hand-fingers-closed": ["手", "了解"],
    "hands": ["手", "お願い", "感謝"],
    "person": ["人"],
    "person-gesture": ["人", "しぐさ"],
    "person-role": ["人", "仕事"],
    "person-fantasy": ["人", "ファンタジー"],
    "person-activity": ["人", "活動"],
    "person-sport": ["スポーツ", "人"],
    "person-resting": ["休む", "人"],
    "family": ["家族"],
    "animal-mammal": ["動物", "哺乳類"],
    "animal-bird": ["動物", "鳥"],
    "animal-amphibian": ["動物"],
    "animal-reptile": ["動物", "爬虫類"],
    "animal-marine": ["動物", "海"],
    "animal-bug": ["動物", "虫"],
    "plant-flower": ["花", "植物"],
    "plant-other": ["植物", "自然"],
    "food-fruit": ["食べ物", "果物"],
    "food-vegetable": ["食べ物", "野菜"],
    "food-prepared": ["食べ物", "料理"],
    "food-asian": ["食べ物", "日本", "料理"],
    "food-marine": ["食べ物", "海"],
    "food-sweet": ["食べ物", "甘い"],
    "drink": ["飲み物"],
    "dishware": ["食器"],
    "place-map": ["地図", "場所"],
    "place-geographic": ["場所", "自然"],
    "place-building": ["建物", "場所"],
    "place-religious": ["場所", "宗教"],
    "place-other": ["場所"],
    "transport-ground": ["乗り物", "移動"],
    "transport-water": ["乗り物", "海"],
    "transport-air": ["乗り物", "空"],
    "hotel": ["宿泊", "旅行"],
    "time": ["時間"],
    "sky & weather": ["天気", "空"],
    "event": ["イベント", "お祝い"],
    "award-medal": ["賞", "お祝い"],
    "sport": ["スポーツ"],
    "game": ["ゲーム", "遊び"],
    "arts & crafts": ["芸術", "道具"],
    "clothing": ["服"],
    "sound": ["音"],
    "music": ["音楽"],
    "musical-instrument": ["音楽", "楽器"],
    "phone": ["電話", "道具"],
    "computer": ["コンピューター", "道具"],
    "light & video": ["光", "映像"],
    "book-paper": ["本", "紙"],
    "money": ["お金"],
    "mail": ["メール"],
    "writing": ["書く", "道具"],
    "office": ["仕事", "道具"],
    "lock": ["鍵", "安全"],
    "tool": ["道具"],
    "science": ["科学"],
    "medical": ["医療"],
    "household": ["家", "道具"],
    "other-object": ["物"],
    "transport-sign": ["標識", "移動"],
    "warning": ["注意", "記号"],
    "arrow": ["矢印", "記号"],
    "religion": ["宗教", "記号"],
    "zodiac": ["星座", "記号"],
    "av-symbol": ["記号"],
    "gender": ["性別", "記号"],
    "math": ["数学", "記号"],
    "punctuation": ["記号"],
    "currency": ["お金", "記号"],
    "other-symbol": ["記号"],
    "keycap": ["キー", "記号"],
    "alphanum": ["文字", "記号"],
    "geometric": ["図形", "記号"],
    "flag": ["旗", "国"],
    "country-flag": ["旗", "国"],
    "subdivision-flag": ["旗", "地域"],
}

NAME_TAGS = {
    "grinning": ["笑顔"],
    "smiling": ["笑顔"],
    "smile": ["笑顔"],
    "laughing": ["笑う"],
    "joy": ["嬉しい"],
    "heart": ["ハート", "愛"],
    "love": ["愛", "好き"],
    "crying": ["泣く", "悲しい"],
    "tear": ["涙"],
    "angry": ["怒り"],
    "sad": ["悲しい"],
    "sleep": ["眠い"],
    "sweat": ["汗", "焦る"],
    "cat": ["猫", "動物"],
    "dog": ["犬", "動物"],
    "bird": ["鳥", "動物"],
    "fish": ["魚", "海"],
    "flower": ["花"],
    "sun": ["太陽", "晴れ"],
    "moon": ["月", "夜"],
    "star": ["星", "きらきら"],
    "fire": ["火", "熱い"],
    "water": ["水"],
    "wave": ["波", "海"],
    "rain": ["雨", "天気"],
    "snow": ["雪", "冬"],
    "party": ["お祝い", "パーティー"],
    "birthday": ["誕生日", "お祝い"],
    "cake": ["ケーキ", "甘い"],
    "gift": ["プレゼント", "お祝い"],
    "beer": ["ビール", "乾杯"],
    "coffee": ["コーヒー", "休憩"],
    "tea": ["お茶", "休憩"],
    "car": ["車", "乗り物"],
    "train": ["電車", "乗り物"],
    "airplane": ["飛行機", "旅行"],
    "house": ["家"],
    "school": ["学校"],
    "office": ["仕事"],
    "book": ["本"],
    "search": ["検索", "探す"],
    "magnifying": ["検索", "探す"],
    "flag": ["旗"],
}


def split_list(value):
    if not value:
        return []
    return [item.strip() for item in value.replace(",", ";").split(";") if item.strip()]


def join_list(values):
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return ";".join(result)


def read_existing(path):
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as fp:
        return {row["emoji"]: row for row in csv.DictReader(fp)}


def fetch_text(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode("utf-8")


def parse_emoji_test(text):
    group = ""
    subgroup = ""
    rows = []
    for line in text.splitlines():
        if line.startswith("# group:"):
            group = line.split(":", 1)[1].strip()
            continue
        if line.startswith("# subgroup:"):
            subgroup = line.split(":", 1)[1].strip()
            continue
        match = LINE_RE.match(line)
        if not match:
            continue
        rows.append(
            {
                "emoji": match.group("emoji"),
                "codepoints": " ".join(match.group("codepoints").split()),
                "name_en": match.group("name"),
                "category": group,
                "subcategory": subgroup,
                "unicode_version": match.group("version"),
            }
        )
    return rows


def generated_tags(row):
    tags = [*GROUP_TAGS.get(row["category"], []), *SUBGROUP_TAGS.get(row["subcategory"], [])]
    name_words = re.findall(r"[a-z]+", row["name_en"].lower())
    for word in name_words:
        tags.extend(NAME_TAGS.get(word, []))
    return tags


def merge_row(imported, existing):
    old = existing.get(imported["emoji"], {})
    tags = [*split_list(old.get("tags_ja", "")), *generated_tags(imported)]
    return {
        "emoji": imported["emoji"],
        "codepoints": imported["codepoints"],
        "name_en": imported["name_en"],
        "name_ja": old.get("name_ja") or imported["name_en"],
        "category": imported["category"],
        "category_ja": old.get("category_ja", ""),
        "subcategory": imported["subcategory"],
        "subcategory_ja": old.get("subcategory_ja", ""),
        "unicode_version": imported["unicode_version"],
        "tags_ja": join_list(tags),
        "scenes_ja": join_list(split_list(old.get("scenes_ja", ""))),
        "tone_ja": join_list(split_list(old.get("tone_ja", ""))),
    }


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--input", type=Path, help="Use a local emoji-test.txt instead of downloading.")
    parser.add_argument("--output", type=Path, default=CSV_PATH)
    args = parser.parse_args()

    text = args.input.read_text(encoding="utf-8") if args.input else fetch_text(args.url)
    imported = parse_emoji_test(text)
    existing = read_existing(args.output)
    rows = [merge_row(row, existing) for row in imported]
    write_csv(args.output, rows)
    print(f"Imported {len(rows)} fully-qualified emoji into {args.output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
