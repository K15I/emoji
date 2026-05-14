import argparse
import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MASTER = ROOT / "data" / "abstract_ja_master.jsonl"
DEFAULT_EMOJI_JSON = ROOT.parents[1] / "emojify" / "data" / "emoji.json"
DEFAULT_OUTPUT = ROOT / "work" / "reports" / "abstract_coverage.csv"
SEARCH_FIELDS = (
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
)


def load_jsonl(path):
    rows = []
    with path.open("r", encoding="utf-8") as fp:
        for line_number, line in enumerate(fp, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSONL") from exc
    return rows


def item_terms(item):
    terms = {
        item.get("emoji", ""),
        item.get("id", ""),
        item.get("name_ja", ""),
        item.get("name_en", ""),
        item.get("category_ja", ""),
        item.get("subcategory_ja", ""),
        item.get("category", ""),
        item.get("subcategory", ""),
    }
    for field in SEARCH_FIELDS:
        value = item.get(field)
        if isinstance(value, list):
            terms.update(str(term).strip() for term in value if str(term).strip())
        elif value:
            terms.add(str(value).strip())
    return {term for term in terms if term}


def visible_items(payload):
    return [item for item in payload.get("items", []) if not item.get("hidden_variant")]


def representative_items(payload):
    return [
        item
        for item in visible_items(payload)
        if item.get("abstract_is_source") == "1"
        or item.get("abstract_group_role") in {"source", "independent"}
    ]


def group_key(item):
    return item.get("abstract_group_id") or item.get("id") or item.get("emoji", "")


def unique_groups(items):
    seen = set()
    result = []
    for item in items:
        key = group_key(item)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def coverage_row(abstract, items):
    term = str(abstract["abstract_ja"]).strip()
    exact = []
    fuzzy = []
    for item in items:
        terms = item_terms(item)
        if term in terms:
            exact.append(item)
        elif term and term.lower() in str(item.get("search_text", "")).lower():
            fuzzy.append(item)

    exact_groups = unique_groups(exact)
    fuzzy_groups = unique_groups([item for item in fuzzy if group_key(item) not in {group_key(exact_item) for exact_item in exact}])
    expected_min = int(abstract.get("expected_min") or 0)
    exact_count = len(exact_groups)
    fuzzy_count = exact_count + len(fuzzy_groups)
    status = "ok" if exact_count >= expected_min else "gap"
    return {
        "abstract_ja": term,
        "category": abstract.get("category", ""),
        "priority": abstract.get("priority", ""),
        "expected_min": expected_min,
        "exact_count": exact_count,
        "fuzzy_count": fuzzy_count,
        "gap": max(expected_min - exact_count, 0),
        "status": status,
        "exact_emojis": "".join(item.get("emoji", "") for item in exact_groups[:16]),
        "fuzzy_extra_emojis": "".join(item.get("emoji", "") for item in fuzzy_groups[:16]),
        "notes": abstract.get("notes", ""),
    }


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "abstract_ja",
        "category",
        "priority",
        "expected_min",
        "exact_count",
        "fuzzy_count",
        "gap",
        "status",
        "exact_emojis",
        "fuzzy_extra_emojis",
        "notes",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser()
    parser.add_argument("--master", type=Path, default=DEFAULT_MASTER)
    parser.add_argument("--emoji-json", type=Path, default=DEFAULT_EMOJI_JSON)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()

    master = args.master if args.master.is_absolute() else ROOT / args.master
    emoji_json = args.emoji_json if args.emoji_json.is_absolute() else ROOT / args.emoji_json
    output = args.output if args.output.is_absolute() else ROOT / args.output

    abstracts = load_jsonl(master)
    payload = json.loads(emoji_json.read_text(encoding="utf-8"))
    items = representative_items(payload)
    rows = [coverage_row(abstract, items) for abstract in abstracts]
    rows.sort(key=lambda row: (-row["gap"], row["priority"], row["category"], row["abstract_ja"]))
    write_csv(output, rows)

    gaps = [row for row in rows if row["status"] == "gap"]
    print(f"Abstract terms: {len(rows)}")
    print(f"Representative emoji: {len(items)}")
    print(f"Gaps: {len(gaps)}")
    print(f"Wrote {output.relative_to(ROOT)}")
    for row in gaps[: args.limit]:
        print(
            f"{row['abstract_ja']} [{row['category']}/{row['priority']}]: "
            f"{row['exact_count']}/{row['expected_min']} exact, "
            f"{row['fuzzy_count']} fuzzy"
        )


if __name__ == "__main__":
    main()
