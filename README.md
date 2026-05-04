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
