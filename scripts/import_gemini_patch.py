import argparse
import json
from pathlib import Path

from emoji_assoc import (
    DEFAULT_CSV,
    V2_FIELDS,
    read_rows,
    rebuild_search_terms,
    join_list,
    split_list,
    unique,
    write_rows,
)


def load_patches(path):
    patches = {}
    with Path(path).open("r", encoding="utf-8-sig") as fp:
        for line_number, line in enumerate(fp, 1):
            line = line.strip()
            if not line:
                continue
            patch = json.loads(line)
            key = patch.get("emoji") or patch.get("codepoints")
            if not key:
                raise ValueError(f"Patch line {line_number} needs emoji or codepoints.")
            patches[key] = patch
    return patches


def is_representative(row):
    return row.get("abstract_is_source", "") == "1" or row.get("abstract_group_role", "") in {"source", "independent"}


def apply_patch(row, patch):
    if patch.get("name_ja"):
        row["name_ja"] = patch["name_ja"].strip()
    if "en_flag" in patch:
        row["en_flag"] = str(patch["en_flag"]).strip()
    if "importance" in patch:
        row["importance"] = str(patch["importance"]).strip()

    changed_non_search = False
    changed_search = False
    for field in V2_FIELDS:
        explicit = (
            f"{field}_set" in patch
            or f"{field}_add" in patch
            or f"{field}_remove" in patch
        )
        if f"{field}_set" in patch:
            values = list(patch.get(f"{field}_set") or [])
        else:
            values = split_list(row.get(field, ""))
        values.extend(patch.get(f"{field}_add", []))
        remove = set(patch.get(f"{field}_remove", []))
        values = [value for value in unique(values) if value not in remove]
        row[field] = join_list(values)
        if explicit and field == "search_ja":
            changed_search = True
        elif explicit:
            changed_non_search = True

    if not changed_search and changed_non_search:
        row["search_ja"] = join_list(rebuild_search_terms(row))
    elif not split_list(row.get("search_ja", "")):
        row["search_ja"] = join_list(rebuild_search_terms(row))

    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("patch_jsonl", type=Path)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-variants", action="store_true")
    args = parser.parse_args()

    rows, fieldnames = read_rows(args.csv)
    patches = load_patches(args.patch_jsonl)
    applied = 0
    skipped_variants = 0
    for row in rows:
        patch = patches.get(row["emoji"]) or patches.get(row["codepoints"])
        if patch:
            if not args.allow_variants and not is_representative(row):
                skipped_variants += 1
                continue
            apply_patch(row, patch)
            applied += 1

    output = args.output or args.csv
    write_rows(output, rows, fieldnames)
    print(f"Applied {applied} patches to {output}")
    if skipped_variants:
        print(f"Skipped {skipped_variants} variant patches; edit representative rows instead.")


if __name__ == "__main__":
    main()
