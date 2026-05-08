# Tag Quality Improvement Plan

## Goal

Improve tag quality without making the UI noisy or weakening word search.

The current policy is:

- visible tags should be compact and useful for browsing
- hidden search terms should remain broad enough to catch user wording
- suspicious tag assignments should be audited by rules before manual review

## 1. Separate Visible Tags And Search Terms

Problem:

- If similar person-type emoji show many shared tags, the UI becomes repetitive.
- If those terms are removed entirely, word search becomes weaker.

Policy:

- Keep `search_ja` as a non-visible search vocabulary.
- Use the other seven columns as visible or display-folded tags.
- Do not show every search term in the UI.

Implementation direction:

- Confirm the UI does not render raw `search_ja` as a visible chip.
- Keep `search_ja` in `search_text` and exact/fuzzy matching.
- For person-type emoji, move broad synonyms and helper words to `search_ja` only.

Example:

```text
Visible: 医師, 白衣, 病院, 専門職, 診察する
Search only: 医者, ドクター, 先生, 医療, 治療, 相談
```

## 2. Improve Copy Interaction

Problem:

- Many emoji sites copy the emoji when the user taps the emoji itself.
- This app currently emphasizes the copy button, while card tap is also used for exploration.

Policy:

- Preserve exploration behavior.
- Add direct copy behavior only to the emoji glyph area.

Implementation direction:

- Emoji glyph tap/click: copy that emoji.
- Card body tap/click: select the emoji and show related tags.
- Copy feedback should include the copied emoji, such as `😀をコピーしました`.

This avoids accidental copying while making the main use case faster.

## 3. Light Visible-Tag Compression

Problem:

- Manual tag review for thousands of emoji is too expensive.
- PCA or clustering is heavier than needed for deciding visible words.

Policy:

- Keep `search_ja` broad.
- Compress visible tags with frequency and simple scoring rules.

Suggested rules:

- Keep direct representative terms.
- Keep visual terms that help identify the emoji.
- Keep terms that make useful related searches.
- Move broad, repetitive, synonym, or explanation-like terms to `search_ja` only.
- Prefer visible terms whose total occurrence count is roughly 4-50.
- Terms appearing too broadly, such as generic person words, should usually be hidden search terms.

Implementation direction:

- Add a script that reports candidate visible terms per emoji.
- Do not auto-overwrite the CSV at first.
- Output a review CSV with proposed keep/move decisions.

## 4. Rule-Based Tag Audit

Problem:

- Some tag assignments are plausible by association but feel wrong in browsing.
- Examples: `動物園` on unicorn, `専門家` on student.

Policy:

- Use rule-based auditing to reduce manual review volume.
- Generate warnings, not automatic deletions.

Implementation direction:

- Add `data/tag_audit_rules.csv`.
- Add `scripts/audit_tags.py`.
- Output `data/tag_audit_report.csv`.

Example rule ideas:

```csv
tag,warn_name,warn_category,warn_subcategory,note
動物園,ユニコーン|ドラゴン|妖精,,,"架空・神話寄りは要確認"
専門家,学生|赤ちゃん|子供,,,"職業者ではない人型を確認"
仕事,遊ぶ|ゲーム|スポーツ,,,"仕事タグとして自然か確認"
```

Review flow:

1. Run audit script.
2. Inspect only the warning report.
3. Manually fix clear problems in `data/emoji17.csv`.
4. Rebuild site data.

## Proposed Order

Priority is based on user experience impact and implementation difficulty.

| Priority | Work | User Satisfaction | Code Difficulty | Reason |
| --- | --- | --- | --- | --- |
| 1 | Improve copy interaction | High | Low | Directly improves the main action. Emoji glyph tap can copy while card tap keeps exploration. |
| 2 | Separate visible tags and search terms | High | Medium | Makes the UI cleaner without weakening search. This affects many browsing interactions. |
| 3 | Rule-based tag audit | Medium | Medium | Reduces wrong-feeling tags such as `動物園` on unicorn or `専門家` on student. It mainly improves quality control. |
| 4 | Light visible-tag compression | Medium | High | Useful for reducing repetition, but rules need tuning and can accidentally hide helpful words. |

Recommended order:

1. Implement copy interaction first.
2. Confirm and adjust UI so `search_ja` remains search-only.
3. Add audit tooling and warning reports.
4. Add visible-tag compression after audit rules are stable.
