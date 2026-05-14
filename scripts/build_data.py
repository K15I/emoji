import argparse
import csv
import json
import re
from pathlib import Path

from emoji_assoc import is_skin_tone_variant, skin_tone_base_name


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data" / "emoji17.csv"
OUTPUT_DIRS = (
    ROOT / "site" / "data",
    ROOT / "dev" / "data",
)

V2_FIELDS = (
    "direct_ja",
    "visual_ja",
    "context_ja",
    "symbolic_ja",
    "emotion_ja",
    "action_ja",
    "culture_ja",
    "search_ja",
)
LIST_FIELDS = V2_FIELDS
ABSTRACT_GROUP_FIELDS = (
    "abstract_group_id",
    "abstract_group_role",
    "abstract_variant_kind",
    "abstract_is_source",
    "abstract_group_key",
)
SKIN_TONE_WORD_RE = re.compile(
    r"\b(?:light|medium-light|medium|medium-dark|dark)\s+skin\s+tone\b",
    re.I,
)


def split_list(value):
    if not value:
        return []
    return [item.strip() for item in value.replace(",", ";").split(";") if item.strip()]


def clean(value):
    return "" if value is None else str(value).strip()


def unique(values):
    seen = set()
    result = []
    for value in values:
        value = clean(value)
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def base_match_key(name):
    name = SKIN_TONE_WORD_RE.sub("", clean(name).lower())
    name = re.sub(r"[^a-z0-9]+", " ", name)
    return " ".join(name.split())


def skin_tone_count(name):
    return len(SKIN_TONE_WORD_RE.findall(clean(name)))


def is_hidden_variant(row):
    return skin_tone_count(row.get("name_en", "")) >= 2


def normalize_row(row):
    lists = {field: split_list(row.get(field, "")) for field in LIST_FIELDS}
    if not lists["search_ja"]:
        search = []
        for field in V2_FIELDS:
            if field != "search_ja":
                search.extend(lists[field])
        lists["search_ja"] = unique(search)

    meaning = unique([*lists["direct_ja"], *lists["symbolic_ja"]])
    usage = unique([*lists["context_ja"], *lists["action_ja"], *lists["culture_ja"]])
    impression = unique([*lists["visual_ja"], *lists["emotion_ja"]])

    item = {
        "id": clean(row.get("id", "")),
        "emoji": clean(row["emoji"]),
        "codepoints": [part.strip() for part in clean(row["codepoints"]).split() if part.strip()],
        "name_en": clean(row["name_en"]),
        "name_ja": clean(row["name_ja"]),
        "en_flag": clean(row.get("en_flag", "")),
        "importance": clean(row.get("importance", "")),
        "category": clean(row["category"]),
        "category_ja": clean(row.get("category_ja", "")),
        "subcategory": clean(row["subcategory"]),
        "subcategory_ja": clean(row.get("subcategory_ja", "")),
        "unicode_version": clean(row["unicode_version"]),
    }
    for field in ABSTRACT_GROUP_FIELDS:
        item[field] = clean(row.get(field, ""))
    if is_hidden_variant(row):
        item["hidden_variant"] = True
        item["variant_kind"] = "multi_skin"

    for field in LIST_FIELDS:
        item[field] = lists[field]

    item["meaning_ja"] = meaning
    item["usage_ja"] = usage
    item["impression_ja"] = impression
    item["class_ja"] = [
        value
        for value in (item["category_ja"] or item["category"], item["subcategory_ja"] or item["subcategory"])
        if value
    ]

    searchable = [
        item["emoji"],
        item["id"],
        item["name_en"],
        item["name_ja"],
        item["en_flag"],
        item["importance"],
        item["category"],
        item["category_ja"],
        item["subcategory"],
        item["subcategory_ja"],
        *item["meaning_ja"],
        *item["usage_ja"],
        *item["impression_ja"],
        *item["direct_ja"],
        *item["visual_ja"],
        *item["context_ja"],
        *item["symbolic_ja"],
        *item["emotion_ja"],
        *item["action_ja"],
        *item["culture_ja"],
        *item["search_ja"],
        *item["class_ja"],
    ]
    item["search_text"] = " ".join(searchable).lower()
    return item


def source_row_by_group(rows):
    sources = {}
    for row in rows:
        group_id = clean(row.get("abstract_group_id", ""))
        if not group_id:
            continue
        if clean(row.get("abstract_is_source", "")) == "1":
            sources[group_id] = row
    return sources


def copy_source_tags_to_variants(rows):
    sources = source_row_by_group(rows)
    copied = []
    for row in rows:
        row = dict(row)
        group_id = clean(row.get("abstract_group_id", ""))
        source = sources.get(group_id)
        if not source or clean(row.get("abstract_is_source", "")) == "1":
            copied.append(row)
            continue

        for field in V2_FIELDS:
            if not split_list(row.get(field, "")):
                row[field] = source.get(field, "")
        copied.append(row)
    return copied


def copy_base_tags_to_skin_variants(rows):
    base_by_name = {
        base_match_key(row.get("name_en", "")): row
        for row in rows
        if not is_skin_tone_variant(row)
    }
    copied = []
    for row in rows:
        row = dict(row)
        if not is_skin_tone_variant(row):
            copied.append(row)
            continue

        base = base_by_name.get(base_match_key(row.get("name_en", ""))) or base_by_name.get(
            base_match_key(skin_tone_base_name(row))
        )
        if not base:
            copied.append(row)
            continue

        for field in V2_FIELDS:
            if not split_list(row.get(field, "")):
                row[field] = base.get(field, "")
        copied.append(row)
    return copied


def copy_representative_tags_to_variants(rows):
    return copy_base_tags_to_skin_variants(copy_source_tags_to_variants(rows))


def write_payload(payload, output_dir):
    json_out = output_dir / "emoji.json"
    js_out = output_dir / "emoji-data.js"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    js_out.write_text(
        "window.EMOJI_DATA = "
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {payload['count']} emoji to {json_out.relative_to(ROOT)}")
    print(f"Wrote browser data to {js_out.relative_to(ROOT)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()
    source = args.source
    if not source.is_absolute():
        source = ROOT / source

    with source.open("r", encoding="utf-8-sig", newline="") as fp:
        source_rows = copy_representative_tags_to_variants(list(csv.DictReader(fp)))
        rows = [normalize_row(row) for row in source_rows]

    payload = {
        "version": 1,
        "source": str(source.resolve().relative_to(ROOT)).replace("\\", "/"),
        "count": len(rows),
        "items": rows,
    }

    for output_dir in OUTPUT_DIRS:
        write_payload(payload, output_dir)


if __name__ == "__main__":
    main()
