# 連想絵文字検索

CSVを正本にして、静的サイト用のJSON/JSを生成する絵文字検索MVPです。

## 使い方

1. `data/emoji_enriched.csv` を編集する
2. JSON/JSを再生成する

```powershell
python scripts/build_data.py
```

3. `site/index.html` をブラウザで開く

サイト内の参照は相対パスです。`file://` で直接開いても動くように、サイトは `site/data/emoji-data.js` を読み込みます。`site/data/emoji.json` は後で別用途に使える検索DBです。

## Unicode公式データを取り込む

Unicode公式の `emoji-test.txt` から `fully-qualified` 絵文字を取り込み、既存CSVの日本語名・タグを残したまま行を増やせます。

```powershell
python scripts/import_unicode_emoji.py
python scripts/build_data.py
```

日本語名、分類名、連想タグ、場面、トーンをCLDR日本語アノテーションなどで補強する場合は、取り込み後に以下を実行します。

```powershell
python scripts/enrich_japanese_data.py
python scripts/build_data.py
```

## Geminiで連想語を補強する

GeminiにはCSV全体を直接編集させず、subcategory単位などでJSONLを書き出して、`assoc_ja` のパッチを返してもらいます。

```powershell
python scripts/export_gemini_batch.py --subcategory animal-mammal
```

`work/batches/animal-mammal.jsonl` と `gemini.md` をGeminiに渡し、JSONLパッチを `work/results/animal-mammal.patch.jsonl` に保存します。

```powershell
python scripts/import_gemini_patch.py work/results/animal-mammal.patch.jsonl
python scripts/classify_associations.py
python scripts/build_data.py
```

品質確認:

```powershell
python scripts/audit_emoji_data.py
```

取り込み元の既定値は以下です。

```text
https://unicode.org/Public/emoji/latest/emoji-test.txt
```

ネットワークを使わない場合は、事前に保存した `emoji-test.txt` を指定できます。

```powershell
python scripts/import_unicode_emoji.py --input path\to\emoji-test.txt
python scripts/build_data.py
```

## データの流れ

```text
data/emoji_enriched.csv
  -> scripts/build_data.py
  -> site/data/emoji.json
  -> site/data/emoji-data.js
  -> site/index.html
```

## CSVの区切り

`tags_ja`、`scenes_ja`、`tone_ja`、`assoc_ja` は `;` 区切りです。`importance` は関連表示や検索順位の重みに使うための1から3の数値です。

```csv
emoji,name_ja,tags_ja,scenes_ja,tone_ja,assoc_ja
🍉,スイカ,"スイカ;水分","夏休み;暑中見舞い","涼しい;季節感","夏;果物;暑い;海;スイカ;水分;涼しい;夏休み;暑中見舞い"
```

## 重要度

`importance` は画像生成や関連検索で優先したい絵文字を上に出すための列です。

```text
3: よく使われる、画像生成向き、代表性が高い
2: 通常候補
1: 色違い、記号、旗、細かいバリエーションなど優先度が低い
```

自動付与:

```powershell
python scripts/assign_importance.py
python scripts/build_data.py
```

肌色違いは `medium-light skin tone` を日本人の肌色寄りの代表として `2`、それ以外の肌色違いを `1` にします。
