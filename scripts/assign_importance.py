import argparse
import csv
import re
from pathlib import Path


CSV_PATH = Path("data/emoji_enriched.csv")
IMPORTANCE_FIELD = "importance"

HIGH_SUBCATEGORIES = {
    "face-smiling",
    "face-affection",
    "face-concerned",
    "face-negative",
    "emotion",
    "animal-mammal",
    "animal-bird",
    "animal-marine",
    "plant-flower",
    "food-fruit",
    "food-prepared",
    "food-sweet",
    "drink",
    "sky & weather",
    "event",
}

HIGH_NAME_KEYWORDS = {
    "heart",
    "party",
    "birthday",
    "sun",
    "moon",
    "star",
    "flower",
    "dog",
    "cat",
    "lion",
    "tiger",
    "rabbit",
    "panda",
    "dolphin",
    "watermelon",
    "sushi",
    "coffee",
    "beer",
    "airplane",
    "house",
    "light bulb",
    "crystal ball",
}

LOW_CATEGORIES = {"Flags", "Symbols", "Component"}

LOW_SUBCATEGORIES = {
    "skin-tone",
    "hair-style",
    "keycap",
    "alphanum",
    "geometric",
    "arrow",
    "av-symbol",
    "gender",
    "punctuation",
    "currency",
}

SKIN_TONE_RE = re.compile(
    r": (?P<tones>.*(?:light skin tone|medium-light skin tone|medium skin tone|medium-dark skin tone|dark skin tone).*)$"
)


def base_name(name_en):
    return name_en.split(":", 1)[0].replace(" facing right", "").strip()


def has_skin_tone(name_en):
    return bool(SKIN_TONE_RE.search(name_en))


def preferred_japanese_skin_tone(name_en):
    # For image-generation display, keep one natural-looking skin-tone variant and downrank the rest.
    return "medium-light skin tone" in name_en


def name_has_keyword(name_en, keywords):
    lowered = name_en.lower()
    return any(keyword in lowered for keyword in keywords)


def has_plain_base(row, base_names):
    return base_name(row["name_en"]) in base_names


def initial_importance(row):
    category = row.get("category", "")
    subcategory = row.get("subcategory", "")
    name_en = row.get("name_en", "")

    if category in LOW_CATEGORIES or subcategory in LOW_SUBCATEGORIES:
        score = 1
    elif subcategory in HIGH_SUBCATEGORIES or name_has_keyword(name_en, HIGH_NAME_KEYWORDS):
        score = 3
    else:
        score = 2

    if "flag:" in name_en:
        score = 1
    if "button" in name_en or "symbol" in name_en:
        score = min(score, 1)
    if "face" in name_en and subcategory.startswith("face-"):
        score = max(score, 3)
    return score


def assign_importance(rows):
    plain_bases = {base_name(row["name_en"]) for row in rows if not has_skin_tone(row["name_en"])}

    for row in rows:
        name_en = row.get("name_en", "")
        score = initial_importance(row)

        if has_skin_tone(name_en):
            if preferred_japanese_skin_tone(name_en):
                score = 2
            else:
                score = 1

        row[IMPORTANCE_FIELD] = str(max(1, min(3, score)))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=CSV_PATH)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    with args.csv.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    if IMPORTANCE_FIELD not in fieldnames:
        fieldnames.append(IMPORTANCE_FIELD)

    rows = assign_importance(rows)
    output = args.output or args.csv
    with output.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    counts = {str(level): 0 for level in (1, 2, 3)}
    for row in rows:
        counts[row[IMPORTANCE_FIELD]] = counts.get(row[IMPORTANCE_FIELD], 0) + 1
    print(f"Assigned importance to {len(rows)} emoji in {output}")
    print(f"importance counts: {counts}")


if __name__ == "__main__":
    main()
