import argparse
from pathlib import Path

from emoji_assoc import DEFAULT_CSV, classify_associations, read_rows, write_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    rows, fieldnames = read_rows(args.csv)
    rows = [classify_associations(row) for row in rows]
    output = args.output or args.csv
    write_rows(output, rows, fieldnames)
    print(f"Classified associations for {len(rows)} emoji into {output}")


if __name__ == "__main__":
    main()
