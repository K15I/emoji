# 連想絵文字検索

日本語の連想語から絵文字を探すための静的Webアプリです。

通常のIME変換では、絵文字の正式な読み方や名前を知らないと探しにくいことがあります。このアプリでは、`笑顔`、`夏`、`動物`、`ふわふわ`、`楕円`、`青い旗` のような言葉から絵文字を検索できます。

## 現在の完成データ

完成版CSVは次のファイルです。

```text
data/emoji17.csv
```

件数は3944件です。Unicode Emojiのデータに、日本語名、分類、検索用タグ、場面、トーン・見た目、重要度を付与しています。

## アプリを表示する

ローカルで確認する場合:

```powershell
python -m http.server 5173 --directory site
```

ブラウザで開きます。

```text
http://127.0.0.1:5173
```

`site/index.html` は相対パスで `site/data/emoji-data.js` を読み込みます。

## データを再生成する

CSVからサイト用JSON/JSを作ります。

```powershell
python scripts/build_data.py --source data/emoji17.csv
```

生成されるファイル:

```text
site/data/emoji.json
site/data/emoji-data.js
```

## CSV列

`data/emoji17.csv` の主な列:

```text
id
emoji
codepoints
name_en
name_ja
category
category_ja
subcategory
subcategory_ja
unicode_version
tags_ja
scenes_ja
tone_ja
importance
```

リスト列は `;` 区切りです。

分類の考え方:

```text
tags_ja   : 物を特定する語、分類、固有名、部品
scenes_ja : 場面、用途、行動、場所、文化圏
tone_ja   : 感情、雰囲気、感覚、見た目、形、色、質感
```

`assoc_ja` は完成版CSVから外しています。サイト側では `tags_ja`、`scenes_ja`、`tone_ja`、`category_ja`、`subcategory_ja` を検索対象にします。

## 重要度

`importance` は検索結果や関連候補の並び順に使います。

```text
3: よく使う、画像生成向き、代表性が高い
2: 通常候補
1: 色違い、記号、旗、細かいバリエーションなど優先度が低い
```

通常表示では、マッチスコアが同じ場合に重要度が高いものを上に出します。

## 検索仕様

検索ボックスへの手入力は曖昧検索です。

例:

```text
びっくり
a
青い旗
```

部分一致・包含一致を許容して、探索しやすさを優先しています。

上部の候補タグをクリックした場合は、タグ完全一致検索です。たとえば `三色旗` の候補タグを押した場合、`旗` 全般ではなく `三色旗` タグを持つものだけを表示します。

絵文字を選ぶと中央に詳細が表示されます。中央のタグ、場面、トーン、分類のチップをクリックすると、右側の関連候補をその語で絞り込みます。

## UX機能

- 左側: 検索結果
- 中央: 選択中の絵文字詳細
- 右側: 関連候補
- 左右それぞれにランダム表示ボタン
- ランダム表示は、マッチした候補の中だけを並べ替えます
- マッチしていないものは表示しません

## 開発メモ

JavaScriptの構文確認:

```powershell
node --check site/app.js
```

データ件数確認:

```powershell
python -c "import json; p=json.load(open('site/data/emoji.json', encoding='utf-8')); print(p['source'], p['count'])"
```

## 主要スクリプト

```text
scripts/build_data.py
```

CSVから `site/data/emoji.json` と `site/data/emoji-data.js` を生成します。

```text
scripts/import_unicode_emoji.py
scripts/enrich_japanese_data.py
scripts/assign_importance.py
```

Unicode Emojiデータの取り込み、日本語名・分類補助、重要度付けに使ったスクリプトです。

```text
scripts/generate_assoc.py
scripts/split_assoc_columns.py
```

連想語生成と、`tags_ja`、`scenes_ja`、`tone_ja` への分割に使ったスクリプトです。

```text
scripts/export_gemini_batch.py
scripts/import_gemini_patch.py
```

外部AIに小分け作業を渡すためのJSONL入出力補助です。
