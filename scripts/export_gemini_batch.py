import argparse
import json
from pathlib import Path

from emoji_assoc import (
    DEFAULT_CSV,
    V2_FIELDS,
    association_pool,
    is_skin_tone_variant,
    read_rows,
    search_pool,
    split_list,
)


def row_payload(row):
    payload = {
        "id": row.get("id", ""),
        "emoji": row["emoji"],
        "codepoints": row["codepoints"],
        "name_en": row["name_en"],
        "name_ja": row["name_ja"],
        "category_ja": row.get("category_ja", ""),
        "subcategory": row.get("subcategory", ""),
        "subcategory_ja": row.get("subcategory_ja", ""),
        "association_pool_ja": association_pool(row),
        "search_ja": search_pool(row),
        "en_flag": row.get("en_flag", ""),
        "importance": row.get("importance", ""),
    }
    for field in V2_FIELDS:
        payload[field] = split_list(row.get(field, ""))
    return payload


def lean_row_payload(row):
    payload = {
        "id": row.get("id", ""),
        "emoji": row["emoji"],
        "name_en": row.get("name_en", ""),
        "name_ja": row["name_ja"],
        "category_ja": row.get("category_ja", ""),
        "subcategory": row.get("subcategory", ""),
        "subcategory_ja": row.get("subcategory_ja", ""),
        "importance": row.get("importance", ""),
        "association_pool_ja": association_pool(row),
        "search_ja": search_pool(row),
    }
    for field in V2_FIELDS:
        payload[field] = split_list(row.get(field, ""))
    return payload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--subcategory")
    parser.add_argument("--category")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--include-skin", action="store_true", help="Include skin tone variant rows.")
    parser.add_argument("--lean", action="store_true", help="Output only fields needed for tag cleanup.")
    args = parser.parse_args()

    rows, _ = read_rows(args.csv)
    if not args.include_skin:
        rows = [row for row in rows if not is_skin_tone_variant(row)]
    if args.subcategory:
        rows = [row for row in rows if row.get("subcategory") == args.subcategory]
    if args.category:
        rows = [row for row in rows if row.get("category") == args.category]
    if args.limit:
        rows = rows[: args.limit]

    output = args.output
    if not output:
        name = args.subcategory or args.category or "emoji"
        safe_name = name.replace(" ", "-").replace("&", "and").replace("/", "-")
        output = Path("work") / "batches" / f"{safe_name}.jsonl"

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as fp:
        for row in rows:
            payload = lean_row_payload(row) if args.lean else row_payload(row)
            fp.write(json.dumps(payload, ensure_ascii=False) + "\n")

    print(f"Exported {len(rows)} rows to {output}")


if __name__ == "__main__":
    main()
