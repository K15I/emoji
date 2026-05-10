import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data" / "emoji17.csv"

ABSTRACT_FIELDS = [
    "abstract_group_id",
    "abstract_group_role",
    "abstract_variant_kind",
    "abstract_is_source",
    "abstract_group_key",
]

SKIN_TONE_RE = re.compile(r"\b(?:light|medium-light|medium|medium-dark|dark)\s+skin\s+tone\b", re.I)
COLOR_RE = re.compile(
    r"^(?:red|pink|orange|yellow|green|light blue|blue|purple|brown|black|grey|gray|white)\s+",
    re.I,
)
GENDER_PREFIX_RE = re.compile(r"^(?:man|woman|person)\s+", re.I)
GENDER_WORD_RE = re.compile(r"\b(?:man|woman|person|men|women|people)\b", re.I)

SPECIAL_GROUPS = [
    (re.compile(r"^(?:people|women|men|woman and man)\s+holding hands$", re.I), "holding hands"),
    (re.compile(r"^kiss(?::.*)?$", re.I), "kiss"),
    (re.compile(r"^couple with heart(?::.*)?$", re.I), "couple with heart"),
]


def clean_name(name):
    name = SKIN_TONE_RE.sub("", name or "")
    name = re.sub(r"\s*,\s*,", ",", name)
    name = re.sub(r":\s*,\s*", ": ", name)
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"\s*,\s*$", "", name)
    name = re.sub(r":\s*$", "", name)
    return name.strip().lower()


def strip_gender(name):
    name = GENDER_PREFIX_RE.sub("", name)
    if ":" in name:
        head, tail = name.split(":", 1)
        parts = [part.strip() for part in tail.split(",")]
        parts = [part for part in parts if part and not GENDER_WORD_RE.fullmatch(part)]
        name = head if not parts else f"{head}: {', '.join(parts)}"
    return re.sub(r"\s+", " ", name).strip()


def strip_color(name):
    return COLOR_RE.sub("", name).strip()


def special_key(name):
    for pattern, key in SPECIAL_GROUPS:
        if pattern.match(name):
            return key
    return ""


def base_key(row):
    name = clean_name(row.get("name_en", ""))
    key = special_key(name) or strip_gender(name)
    return key


def color_key(row):
    name = base_key(row)
    stripped = strip_color(name)
    return stripped if stripped != name else ""


def variant_kind(row, group_key):
    name = clean_name(row.get("name_en", ""))
    skin_count = len(SKIN_TONE_RE.findall(row.get("name_en", "")))
    without_skin = clean_name(row.get("name_en", ""))
    without_gender = strip_gender(without_skin)
    without_color = strip_color(without_gender)

    if skin_count >= 2:
        return "mixed_skin"
    if skin_count == 1 and without_skin != without_gender and without_gender == group_key:
        return "skin_gender"
    if skin_count == 1 and without_gender == group_key:
        return "skin_tone"
    if without_gender == group_key and without_skin != without_gender:
        return "gender"
    if without_color == group_key and without_gender != without_color:
        return "color"
    if name != group_key:
        return "derived"
    return "base"


def int_id(row):
    try:
        return int(row.get("id", "0"))
    except ValueError:
        return 0


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        return list(reader), list(reader.fieldnames or [])


def write_rows(path, rows, fieldnames):
    output_fields = list(fieldnames)
    for field in ABSTRACT_FIELDS:
        if field not in output_fields:
            output_fields.append(field)

    with path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=output_fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in output_fields} for row in rows)


def assign_groups(rows):
    provisional = defaultdict(list)
    for row in rows:
        provisional[base_key(row)].append(row)

    color_candidates = defaultdict(list)
    for key, group_rows in provisional.items():
        for row in group_rows:
            key_without_color = color_key(row)
            if key_without_color:
                color_candidates[(row.get("subcategory", ""), key_without_color)].append(row)

    color_group_keys = {}
    for (_, stripped), group_rows in color_candidates.items():
        if len(group_rows) < 2:
            continue
        ids = {row.get("id", "") for row in group_rows}
        if len(ids) >= 2:
            for row in group_rows:
                color_group_keys[row.get("id", "")] = stripped

    grouped = defaultdict(list)
    for row in rows:
        row_key = color_group_keys.get(row.get("id", "")) or base_key(row)
        grouped[(row.get("subcategory", ""), row_key)].append(row)

    for (_, key), group_rows in grouped.items():
        source = min(group_rows, key=int_id)
        source_id = source.get("id", "")
        group_size = len(group_rows)
        for row in group_rows:
            is_source = row.get("id", "") == source_id
            row["abstract_group_id"] = source_id
            row["abstract_group_key"] = key
            row["abstract_is_source"] = "1" if is_source else "0"
            row["abstract_group_role"] = "independent" if group_size == 1 else ("source" if is_source else "variant")
            row["abstract_variant_kind"] = "independent" if group_size == 1 else variant_kind(row, key)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()

    source = args.source if args.source.is_absolute() else ROOT / args.source
    rows, fieldnames = read_rows(source)
    assign_groups(rows)
    write_rows(source, rows, fieldnames)

    grouped_count = len({row["abstract_group_id"] for row in rows})
    source_count = sum(1 for row in rows if row["abstract_is_source"] == "1")
    variant_count = sum(1 for row in rows if row["abstract_group_role"] == "variant")
    independent_count = sum(1 for row in rows if row["abstract_group_role"] == "independent")
    print(f"Wrote {len(rows)} rows to {source.relative_to(ROOT)}")
    print(f"Groups: {grouped_count}, sources: {source_count}, variants: {variant_count}, independent: {independent_count}")


if __name__ == "__main__":
    main()
