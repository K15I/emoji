import argparse
import sys
from collections import Counter
from pathlib import Path

from emoji_assoc import DEFAULT_CSV, V2_FIELDS, is_skin_tone_variant, read_rows, search_pool, split_list


REQUIRED_MIN_SEARCH_TERMS = {
    "3": 12,
    "2": 8,
    "1": 6,
}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--limit", type=int, default=40)
    args = parser.parse_args()

    rows, _ = read_rows(args.csv)
    warnings = []
    usage_counter = Counter()
    impression_counter = Counter()
    v2_empty_counter = Counter()

    for row in rows:
        skin_variant = is_skin_tone_variant(row)
        usage = []
        impression = []
        for field in ("context_ja", "action_ja", "culture_ja"):
            usage.extend(split_list(row.get(field, "")))
        for field in ("visual_ja", "emotion_ja"):
            impression.extend(split_list(row.get(field, "")))
        search_terms = search_pool(row)

        usage_counter.update([";".join(usage)])
        impression_counter.update([";".join(impression)])
        for field in V2_FIELDS:
            if field != "search_ja" and not split_list(row.get(field, "")):
                v2_empty_counter.update([field])

        if row.get("name_ja") == row.get("name_en"):
            warnings.append((row, "name_ja is still English"))
        expected = 0 if skin_variant else REQUIRED_MIN_SEARCH_TERMS.get(str(row.get("importance", "")).strip(), 7)
        if expected and len(search_terms) < expected:
            warnings.append((row, f"search terms are shallow ({len(search_terms)}/{expected})"))
        if split_list(row.get("search_ja", "")) and len(search_terms) != len(set(search_terms)):
            warnings.append((row, "search_ja has duplicate terms"))

    print(f"Rows: {len(rows)}")
    print(f"Warnings: {len(warnings)}")
    for row, reason in warnings[: args.limit]:
        print(f"{row['emoji']} {row['name_en']} / {row.get('name_ja', '')}: {reason}")

    print("\nEmpty v2 fields:")
    for field, count in v2_empty_counter.most_common():
        print(f"{field}: {count}")

    print("\nRepeated usage groups:")
    for value, count in usage_counter.most_common(10):
        if count > 10:
            print(f"{count}: {value}")

    print("\nRepeated impression groups:")
    for value, count in impression_counter.most_common(10):
        if count > 10:
            print(f"{count}: {value}")


if __name__ == "__main__":
    main()
