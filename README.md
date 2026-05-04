# 連想絵文字検索

CSVを正本にして、静的サイト用のJSON/JSを生成する絵文字検索MVPです。

## 使い方

1. `data/emoji.csv` を編集する
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
data/emoji.csv
  -> scripts/build_data.py
  -> site/data/emoji.json
  -> site/data/emoji-data.js
  -> site/index.html
```

## CSVの区切り

`tags_ja`、`scenes_ja`、`tone_ja` は `;` 区切りです。

```csv
emoji,name_ja,tags_ja,scenes_ja,tone_ja
🍉,スイカ,"夏;果物;暑い","夏休み;暑中見舞い","明るい;季節感"
```
