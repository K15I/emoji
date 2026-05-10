# Codex Working Rules

This file is the project-level operating guide for Codex work in this repository.

## Source Of Truth

- Treat `instruction/` as the current local specification.
- Do not treat `archive/` or `test/` as current instructions.
- Use `archive/` only for old proposals, completed handoffs, external AI prompts, and historical notes.
- Use `record/` for chronological work records and decisions.

## Emoji Data Rules

- The active CSV source is `data/emoji17.csv`.
- The site data is generated from CSV into `site/data/emoji.json`, `site/data/emoji-data.js`, `dev/data/emoji.json`, and `dev/data/emoji-data.js`.
- Keep paths relative so the app can be checked locally by opening HTML.
- CSV files intended for spreadsheet editing should be written as UTF-8 with BOM.

## Tag Rules

- Use the current 8-column tag model:
  - `direct_ja`
  - `visual_ja`
  - `context_ja`
  - `symbolic_ja`
  - `emotion_ja`
  - `action_ja`
  - `culture_ja`
  - `search_ja`
- Do not reintroduce old `tags_ja`, `scenes_ja`, or `tone_ja` as active source columns.
- `search_ja` is the integrated search vocabulary. It may include important terms from the other seven columns.
- The display model may fold the 8 columns into fewer UI groups, but the CSV editing model remains 8 columns.

## Skin Tone Rules

- Skin tone variants should inherit searchable associations from their base emoji.
- Skin tone words should not be added as normal search tags.
- Mixed skin tone variants are hidden from the main result list and handled through variant selection where possible.

## Work Records

- When a task changes project rules, data flow, or tagging policy, add a short dated record in `record/`.
- Before committing, confirm that old instructions were moved to `archive/` and only current rules remain in `instruction/`.
