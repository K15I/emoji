# 絵文字辞典

読み方を知らなくても、言葉や気持ちから絵文字を引けるWebアプリです。

IME変換では、絵文字の正式名称や読み方を知らないと目的の絵文字にたどり着きにくいことがあります。このアプリでは、「笑顔」「夏」「動物」「ふわふわ」「嬉しい」「青い旗」のような思いつきの言葉から検索できるようにします。

## 構成

```text
data/emoji17.csv          編集元CSV
site/                     本体アプリ
site/data/emoji.json      本番用データ
site/data/emoji-data.js   本番用ブラウザ読み込みデータ
dev/data/emoji.json       試作用データ
dev/data/emoji-data.js    試作用ブラウザ読み込みデータ
dev/                      UI試作用コピー
scripts/build_data.py     CSVからJSON/JSを生成する
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

編集元は `data/emoji17.csv` です。

現在の基本列:

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
importance
```

タグ作業で追加する列:

```text
direct_ja
visual_ja
context_ja
symbolic_ja
emotion_ja
action_ja
culture_ja
search_ja
```

旧 `tags_ja`、`scenes_ja`、`tone_ja` はCSV編集列にもサイト用JSONにも使いません。サイト表示用には、`scripts/build_data.py` が8分類から色数を抑えたチップ用データを生成します。

折りたたみ方:

```text
direct_ja + symbolic_ja             -> meaning_ja
context_ja + action_ja + culture_ja -> usage_ja
visual_ja + emotion_ja              -> impression_ja
category_ja + subcategory_ja        -> class_ja
```

## サイト用データ生成

CSVを変更した後、サイト用JSON/JSを生成します。

```powershell
python scripts/build_data.py
```

生成されるファイル:

```text
site/data/emoji.json
site/data/emoji-data.js
```

`dev/data/` は試作用コピーです。`scripts/build_data.py` は `site/data/` と `dev/data/` の両方を同時に更新します。

## 検索仕様

検索モードは2種類です。

```text
あいまい検索 : 手入力向け。部分一致や包含一致を許可する。
一致検索     : タグや関連語チップ向け。完全一致した語で絞り込む。
```

検索結果は重要度とマッチスコアで並びます。ランダムボタンは解除トグルではなく、押すたびにヒット候補をランダムに並べ替えます。

## 肌色バリエーション

肌色違いの絵文字は、一覧ではベース絵文字の1カードに集約します。

例:

```text
waving hand
waving hand: light skin tone
waving hand: medium-light skin tone
waving hand: medium skin tone
waving hand: medium-dark skin tone
waving hand: dark skin tone
```

一覧では1枚のカードとして表示し、詳細内で肌色を選べます。コピーされる絵文字は現在選択中の肌色を反映します。

2人分の肌色を組み合わせる派生絵文字は、検索結果と肌色候補からは非表示にします。例として、握手、手をつなぐ、キスするカップル、ハートのカップルなどの `light skin tone, medium skin tone` 形式の派生は `scripts/build_data.py` が `hidden_variant: true` を付け、UIは表示対象から外します。`importance` は表示可否には使わず、順位付けの意味だけに保ちます。

タグ作業では、肌色違いの各行にベース絵文字と同じ検索語を複製しません。ベース絵文字に検索タグを厚く付け、肌色違いは詳細欄の選択UIで扱います。

`scripts/export_codex_batch.py` は、標準では肌色違いの行を出力しません。タグ作業はベース絵文字だけを対象にします。`scripts/build_data.py` はサイト用データ生成時に、肌色違いへベース絵文字のタグを出力上だけ引き継ぎます。CSV上で肌色違いのタグを手で考える必要はありません。

## タグ作業

今回のタグ修正はCodexで行います。外部AIへ一括依頼しません。

参照する作業資料:

```text
test/00_tag_rules.md
test/01_abstract_words.md
test/02_batch_workflow.md
test/2026-0506-0815タグ作成.md
test/2026-0506-1947作業指示.md
```

補助スクリプト:

```text
scripts/export_codex_batch.py
scripts/import_codex_patch.py
scripts/audit_emoji_data.py
```

対象を小分けにJSONL化する例:

```powershell
python scripts/export_codex_batch.py --subcategory face-smiling --lean --output work/batches/face-smiling.jsonl
```

肌色違いも含めて確認したい特殊な場合だけ `--include-skin` を付けます。

JSONLパッチをCSVへ反映する例:

```powershell
python scripts/import_codex_patch.py work/results/face-smiling.patch.jsonl --csv data/emoji17.csv
```

監査:

```powershell
python scripts/audit_emoji_data.py --limit 40
```

CSVはBOM付きUTF-8で扱います。

## 注意

`test/emoji17_0505.csv` は過去版の退避です。今回の編集元にはしません。

タグがまだ空の段階で `scripts/build_data.py` を実行すると、空タグのサイト用データで `site/data` を上書きします。タグ投入後に実行します。
