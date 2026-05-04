import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "emoji.csv"
JSON_OUT = ROOT / "site" / "data" / "emoji.json"
JS_OUT = ROOT / "site" / "data" / "emoji-data.js"

LIST_FIELDS = ("tags_ja", "scenes_ja", "tone_ja")


def split_list(value):
    if not value:
        return []
    return [item.strip() for item in value.replace(",", ";").split(";") if item.strip()]


def normalize_row(row):
    item = {
        "emoji": row["emoji"].strip(),
        "codepoints": [part.strip() for part in row["codepoints"].split() if part.strip()],
        "name_en": row["name_en"].strip(),
        "name_ja": row["name_ja"].strip(),
        "category": row["category"].strip(),
        "subcategory": row["subcategory"].strip(),
        "unicode_version": row["unicode_version"].strip(),
    }

    for field in LIST_FIELDS:
        item[field] = split_list(row.get(field, ""))

    searchable = [
        item["emoji"],
        item["name_en"],
        item["name_ja"],
        item["category"],
        item["subcategory"],
        *item["tags_ja"],
        *item["scenes_ja"],
        *item["tone_ja"],
    ]
    item["search_text"] = " ".join(searchable).lower()
    return item


def main():
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as fp:
        rows = [normalize_row(row) for row in csv.DictReader(fp)]

    payload = {
        "version": 1,
        "source": "data/emoji.csv",
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
