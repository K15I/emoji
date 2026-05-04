import argparse
import sys
from collections import Counter
from pathlib import Path

from emoji_assoc import DEFAULT_CSV, read_rows, split_list


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--limit", type=int, default=40)
    args = parser.parse_args()

    rows, _ = read_rows(args.csv)
    warnings = []
    scene_counter = Counter()
    tone_counter = Counter()

    for row in rows:
        tags = split_list(row.get("tags_ja", ""))
        scenes = split_list(row.get("scenes_ja", ""))
        tones = split_list(row.get("tone_ja", ""))
        assoc = split_list(row.get("assoc_ja", ""))

        scene_counter.update([";".join(scenes)])
        tone_counter.update([";".join(tones)])

        if row.get("name_ja") == row.get("name_en"):
            warnings.append((row, "name_ja is still English"))
        if len(assoc) < 6:
            warnings.append((row, "assoc_ja is shallow"))
        if len(tags) < 4:
            warnings.append((row, "tags_ja is shallow"))
        if len(scenes) < 2:
            warnings.append((row, "scenes_ja is shallow"))
        if len(tones) < 2:
            warnings.append((row, "tone_ja is shallow"))

    print(f"Rows: {len(rows)}")
    print(f"Warnings: {len(warnings)}")
    for row, reason in warnings[: args.limit]:
        print(f"{row['emoji']} {row['name_en']} / {row.get('name_ja', '')}: {reason}")

    print("\nRepeated scenes:")
    for value, count in scene_counter.most_common(10):
        if count > 10:
            print(f"{count}: {value}")

    print("\nRepeated tones:")
    for value, count in tone_counter.most_common(10):
        if count > 10:
            print(f"{count}: {value}")


if __name__ == "__main__":
    main()
