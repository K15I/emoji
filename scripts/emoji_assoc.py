import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = ROOT / "data" / "emoji17.csv"
SKIN_TONE_RE = re.compile(r":\s*(light|medium-light|medium|medium-dark|dark)\s+skin\s+tone", re.I)

V2_FIELDS = [
    "direct_ja",
    "visual_ja",
    "context_ja",
    "symbolic_ja",
    "emotion_ja",
    "action_ja",
    "culture_ja",
    "search_ja",
]

BASE_FIELDNAMES = [
    "id",
    "emoji",
    "codepoints",
    "name_en",
    "name_ja",
    "category",
    "category_ja",
    "subcategory",
    "subcategory_ja",
    "unicode_version",
    "importance",
    *V2_FIELDS,
]

SCENE_WORDS = {
    "挨拶", "雑談", "会話", "リアクション", "返事", "お礼", "謝罪", "謝る", "お願い",
    "誕生日", "お祝い", "成功", "応援", "発表", "リリース", "記念日", "パーティー",
    "旅行", "外出", "移動", "通勤", "出張", "帰省", "遠出", "ドライブ",
    "夏休み", "暑中見舞い", "海水浴", "花火大会", "夏祭り", "バーベキュー",
    "食事", "外食", "昼食", "夜食", "休憩", "乾杯", "飲み会", "仕事終わり",
    "動物園", "サファリ", "水族館", "ペット", "散歩", "癒し",
    "占い", "星座占い", "動物占い", "性格診断", "運勢", "願いごと",
    "推し活", "デート", "ライブ", "趣味", "試合", "部活", "学習", "作業",
    "看病", "病院", "体調不良", "寝る前", "深夜", "退勤",
}

TONE_WORDS = {
    "明るい", "暗い", "楽しい", "嬉しい", "悲しい", "寂しい", "しんみり", "感情的",
    "かわいい", "かっこいい", "きれい", "上品", "華やか", "にぎやか", "静か",
    "やさしい", "温かい", "冷たい", "涼しい", "爽やか", "穏やか", "落ち着き",
    "堂々", "力強い", "勇ましい", "王者", "ワイルド", "神秘的", "不思議",
    "幻想的", "怪しい", "不穏", "公式", "中立", "実用的", "日常", "親しみ",
    "くだけた", "軽い", "強い", "控えめ", "素直", "前向き", "活動的", "期待",
    "季節感", "レトロ", "ゆるい", "けだるい", "リラックス", "無気力",
}

CLASSIFICATION_TAGS = {
    "顔文字と感情", "人と体", "動物と自然", "食べ物と飲み物", "旅行と場所", "活動",
    "物", "記号", "旗", "笑顔", "愛情の顔", "哺乳類", "鳥", "虫", "花", "果物",
    "野菜", "料理", "飲み物", "イベント", "スポーツ", "国旗",
}


def split_list(value):
    if not value:
        return []
    return [item.strip() for item in value.replace(",", ";").split(";") if item.strip()]


def unique(values):
    seen = set()
    result = []
    for value in values:
        value = str(value).strip()
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def join_list(values):
    return ";".join(unique(values))


def is_skin_tone_variant(row):
    return bool(SKIN_TONE_RE.search(row.get("name_en", "")))


def skin_tone_base_name(row):
    return SKIN_TONE_RE.sub("", row.get("name_en", "")).strip()


def normalized_fieldnames(fieldnames):
    result = list(fieldnames or [])
    for field in BASE_FIELDNAMES:
        if field not in result:
            result.append(field)
    return result


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        fieldnames = normalized_fieldnames(reader.fieldnames)
        return [normalize_row(row, fieldnames) for row in reader], fieldnames


def normalize_row(row, fieldnames):
    return {field: row.get(field, "") for field in fieldnames}


def write_rows(path, rows, fieldnames):
    fieldnames = normalized_fieldnames(fieldnames)
    with Path(path).open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fieldnames} for row in rows)


def association_pool(row):
    values = []
    for field in V2_FIELDS:
        values.extend(split_list(row.get(field, "")))
    return unique(values)


def search_pool(row):
    values = split_list(row.get("search_ja", ""))
    if values:
        return unique(values)
    values = []
    for field in V2_FIELDS:
        if field != "search_ja":
            values.extend(split_list(row.get(field, "")))
    return unique(values)


def rebuild_search_terms(row):
    values = []
    for field in V2_FIELDS:
        if field != "search_ja":
            values.extend(split_list(row.get(field, "")))
    return unique(values)


def derive_compat_fields(row):
    """Compatibility shim for older callers; only rebuilds the search field now."""
    if not split_list(row.get("search_ja", "")):
        row["search_ja"] = join_list(rebuild_search_terms(row))
    return row


def classify_associations(row):
    return derive_compat_fields(row)
