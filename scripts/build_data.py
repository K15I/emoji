import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data" / "emoji17.csv"
JSON_OUT = ROOT / "site" / "data" / "emoji.json"
JS_OUT = ROOT / "site" / "data" / "emoji-data.js"

LIST_FIELDS = ("tags_ja", "scenes_ja", "tone_ja")


def split_list(value):
    if not value:
        return []
    return [item.strip() for item in value.replace(",", ";").split(";") if item.strip()]


def clean(value):
    return "" if value is None else str(value).strip()


def normalize_row(row):
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

    for field in LIST_FIELDS:
        item[field] = split_list(row.get(field, ""))

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
        *item["tags_ja"],
        *item["scenes_ja"],
        *item["tone_ja"],
        *item["class_ja"],
    ]
    item["search_text"] = " ".join(searchable).lower()
    return item


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()
    source = args.source
    if not source.is_absolute():
        source = ROOT / source

    with source.open("r", encoding="utf-8-sig", newline="") as fp:
        rows = [normalize_row(row) for row in csv.DictReader(fp)]

    payload = {
        "version": 1,
        "source": str(source.resolve().relative_to(ROOT)).replace("\\", "/"),
        "count": len(rows),
        "items": rows,
    }

    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    JS_OUT.write_text(
        "window.EMOJI_DATA = "
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {payload['count']} emoji to {JSON_OUT.relative_to(ROOT)}")
    print(f"Wrote browser data to {JS_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
