import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "site" / "data" / "emoji.json"
DEFAULT_OUTPUT = ROOT / "data" / "emoji17_from_json.csv"

FIELDS = [
    "id",
    "emoji",
    "codepoints",
    "name_en",
    "name_ja",
    "en_flag",
    "importance",
    "category",
    "category_ja",
    "subcategory",
    "subcategory_ja",
    "unicode_version",
    "abstract_group_id",
    "abstract_group_role",
    "abstract_variant_kind",
    "abstract_is_source",
    "abstract_group_key",
    "direct_ja",
    "visual_ja",
    "context_ja",
    "symbolic_ja",
    "emotion_ja",
    "action_ja",
    "culture_ja",
    "search_ja",
    "meaning_ja",
    "usage_ja",
    "impression_ja",
    "class_ja",
    "hidden_variant",
    "variant_kind",
]


def cell(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return ";".join(str(item).strip() for item in value if str(item).strip())
    return str(value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    source = args.source if args.source.is_absolute() else ROOT / args.source
    output = args.output if args.output.is_absolute() else ROOT / args.output

    payload = json.loads(source.read_text(encoding="utf-8"))
    rows = payload["items"]

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=FIELDS)
        writer.writeheader()
        for item in rows:
            writer.writerow({field: cell(item.get(field, "")) for field in FIELDS})

    print(f"Wrote {len(rows)} rows to {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
