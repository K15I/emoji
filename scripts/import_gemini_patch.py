import argparse
import json
from pathlib import Path

from emoji_assoc import (
    DEFAULT_CSV,
    classify_associations,
    read_rows,
    split_list,
    unique,
    write_rows,
)


def load_patches(path):
    patches = {}
    with Path(path).open("r", encoding="utf-8") as fp:
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


def apply_patch(row, patch):
    if patch.get("name_ja"):
        row["name_ja"] = patch["name_ja"].strip()
    if "en_flag" in patch:
        row["en_flag"] = str(patch["en_flag"]).strip()
    if "importance" in patch:
        row["importance"] = str(patch["importance"]).strip()

    assoc = split_list(row.get("assoc_ja", ""))
    assoc.extend(patch.get("assoc_ja_add", []))
    assoc.extend(patch.get("associations_ja_add", []))
    assoc.extend(patch.get("tags_ja_add", []))
    assoc.extend(patch.get("scenes_ja_add", []))
    assoc.extend(patch.get("tone_ja_add", []))

    remove = set(patch.get("assoc_ja_remove", []))
    remove.update(patch.get("remove", []))
    assoc = [value for value in unique(assoc) if value not in remove]
    row["assoc_ja"] = ";".join(assoc)
    return classify_associations(row)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("patch_jsonl", type=Path)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    rows, fieldnames = read_rows(args.csv)
    patches = load_patches(args.patch_jsonl)
    applied = 0
    for row in rows:
        patch = patches.get(row["emoji"]) or patches.get(row["codepoints"])
        if patch:
            apply_patch(row, patch)
            applied += 1

    output = args.output or args.csv
    write_rows(output, rows, fieldnames)
    print(f"Applied {applied} patches to {output}")


if __name__ == "__main__":
    main()
