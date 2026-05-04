import argparse
import json
from pathlib import Path

from emoji_assoc import DEFAULT_CSV, association_pool, read_rows, split_list


def row_payload(row):
    return {
        "id": row.get("id", ""),
        "emoji": row["emoji"],
        "codepoints": row["codepoints"],
        "name_en": row["name_en"],
        "name_ja": row["name_ja"],
        "category_ja": row.get("category_ja", ""),
        "subcategory": row.get("subcategory", ""),
        "subcategory_ja": row.get("subcategory_ja", ""),
        "assoc_ja": association_pool(row),
        "tags_ja": split_list(row.get("tags_ja", "")),
        "scenes_ja": split_list(row.get("scenes_ja", "")),
        "tone_ja": split_list(row.get("tone_ja", "")),
        "en_flag": row.get("en_flag", ""),
        "importance": row.get("importance", ""),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--subcategory")
    parser.add_argument("--category")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    rows, _ = read_rows(args.csv)
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
            fp.write(json.dumps(row_payload(row), ensure_ascii=False) + "\n")

    print(f"Exported {len(rows)} rows to {output}")


if __name__ == "__main__":
    main()
