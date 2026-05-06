# 連想絵文字検索

日本語の連想語から絵文字を探すための静的Webアプリです。

IME変換では、絵文字の正式名や読み方を知らないと目的の絵文字にたどり着きにくいことがあります。このアプリでは、`笑顔`、`夏`、`動物`、`ふわふわ`、`楕円`、`青い旗` のような思いつきの言葉から絵文字を検索できます。

## 現在の構成

```text
data/emoji17.csv          編集元の完成版CSV
site/                     本体アプリ
site/data/emoji.json      サイト用データ
site/data/emoji-data.js   ブラウザ読み込み用データ
dev/                      UI試作用コピー
scripts/build_data.py     CSVからJSON/JSを再生成するスクリプト
```

`site/` と `dev/` は相対パスで動くようにしています。ローカル確認や静的ホスティングでは、フォルダごと配置して表示できます。

## ローカル表示

本体を確認する場合:

```powershell
python -m http.server 5173 --directory site
```

ブラウザで開きます。

```text
http://127.0.0.1:5173
```

試作版を確認する場合:

```powershell
python -m http.server 5174 --directory dev
```

## データ運用

編集元は `data/emoji17.csv` です。次のタグ見直し作業でも、基本的にはこのCSVを編集します。

CSVを変更したら、サイト用JSON/JSを再生成します。

```powershell
python scripts/build_data.py
```

明示する場合:

```powershell
python scripts/build_data.py --source data/emoji17.csv
```

生成されるファイル:

```text
site/data/emoji.json
site/data/emoji-data.js
```

`dev/data/` は試作用コピーです。本体データを更新したあと、devでも同じデータを確認したい場合は `site/data/` からコピーしてください。

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

`tags_ja`、`scenes_ja`、`tone_ja` は `;` 区切りです。

分類の目安:

```text
tags_ja   : 物を特定する語、分類、固有名、部品
scenes_ja : 場面、用途、行動、場所、文化圏
tone_ja   : 感情、雰囲気、感覚、見た目、形、色、質感
```

`assoc_ja` は完成版CSVから外しています。サイト側では `tags_ja`、`scenes_ja`、`tone_ja`、`category_ja`、`subcategory_ja` を検索と関連語表示に使います。

## 検索仕様

検索モードは2種類です。

```text
あいまい検索 : 手入力向け。部分一致や包含一致を許容する。
一致検索     : タグや関連語チップ向け。完全一致した語だけで絞り込む。
```

上部の候補タグ、選択中絵文字の関連語、ヒット欄のタグを押した場合は、一致検索に切り替わります。たとえば `三色旗` を押した場合、`旗` 全般ではなく `三色旗` タグを持つ候補だけを表示します。

検索結果は重要度とマッチスコアで並びます。`ランダム` ボタンは解除トグルではなく、押すたびにヒットした候補をランダムに並べ替えます。

## 肌色集約

肌色違いの絵文字は、一覧ではベース絵文字1枚に集約します。

例:

```text
waving hand
waving hand: light skin tone
waving hand: medium-light skin tone
waving hand: medium skin tone
waving hand: medium-dark skin tone
waving hand: dark skin tone
```

上記は一覧では1枚のカードとして表示されます。カード右下の小さなインジケーターは、肌色バリエーションがあることを示します。

絵文字を選択すると、詳細欄で肌色ドットを選べます。コピーされる絵文字は、現在選択中の肌色を反映します。

## 重要度

`importance` は検索結果の並び順に使います。

```text
3: よく使う、画像生成向き、代表性が高い
2: 通常候補
1: 色違い、記号、旗、細かいバリエーションなど優先度が低い
```

肌色集約後は、グループ単位で並び替えます。重要度は代表絵文字のものを使います。

## 動作確認

JavaScript構文確認:

```powershell
node --check site/app.js
```

データ件数確認:

```powershell
python -c "import json; p=json.load(open('site/data/emoji.json', encoding='utf-8')); print(p['source'], p['count'])"
```

CSVから再生成できるか確認:

```powershell
python scripts/build_data.py
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
scripts/classify_associations.py
```

連想語生成と、`tags_ja`、`scenes_ja`、`tone_ja` への分割に使ったスクリプトです。

```text
scripts/export_gemini_batch.py
scripts/import_gemini_patch.py
```

外部AIに小分け作業を渡すためのJSONL入出力補助です。
