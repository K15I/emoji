import argparse
import csv
from pathlib import Path


DEFAULT_INPUT = Path("data/emoji_enriched_divcodex.csv")
DEFAULT_OUTPUT = Path("data/emoji_enriched_divcodex_split.csv")


TONE_TERMS = {
    "嬉しい", "楽しい", "明るい", "かわいい", "面白い", "好き", "愛", "感謝", "不思議",
    "悲しい", "心配", "不安", "怒り", "不満", "否定", "強い", "怖い", "困惑",
    "にっこり", "ほほえみ", "笑う", "爆笑", "泣く", "涙", "感情", "気持ち",
    "雰囲気", "感覚", "恋愛", "反応", "強調", "きれい", "爽やか", "静か",
    "暑い", "寒い", "涼しい", "熱い", "冷たい", "軽い", "重い", "柔らかい", "硬い",
    "白い", "黒い", "赤い", "青い", "黄色", "緑", "紫", "茶色", "カラフル",
    "赤白", "赤白青", "青白赤", "緑白赤", "黒赤黄", "白青赤", "青黄",
    "白", "黒", "赤", "青", "黄", "緑", "紫", "オレンジ", "水色", "赤青",
    "青白", "赤黄赤", "緑白オレンジ", "黒黄赤", "赤白水色", "白赤", "青い旗",
    "赤い旗", "白地", "赤い丸", "黄色い丸", "青い丸", "黄色い星", "白十字",
    "青い十字", "黄色い十字", "青い旗", "ダビデの星", "三日月", "星条旗",
    "ユニオンジャック", "三色旗", "縦縞", "横縞", "縞模様", "日の丸",
    "太極", "Y字", "アショーカチャクラ", "紋章", "カエデ",
    "丸", "円", "楕円", "四角", "四角い", "三角", "三角形", "ひし形",
    "長い", "細長い", "小さい", "大きい", "高い", "平たい", "広がる",
    "形", "素材", "色", "見た目", "明るさ", "毛", "足跡", "カード",
    "動き", "ポーズ", "肌色違い", "バリエーション", "薄い肌色", "やや薄い肌色",
    "中間の肌色", "やや濃い肌色", "濃い肌色", "左向き", "右向き", "上向き", "下向き",
    "ふわふわ", "きらきら", "ぐるぐる", "ざぶざぶ", "そよそよ", "めらめら",
    "りんりん", "ぽろぽろ", "しくしく", "ぷんぷん", "いらいら", "すやすや",
    "あせあせ", "ぴかぴか", "しっとり", "さらさら", "つるつる", "とげとげ",
    "とろける", "ぽこぽこ", "ぺろぺろ", "あっかんべー", "ちゅっ", "ドキドキ",
    "すっぱい", "甘い", "苦い", "しょっぱい", "新鮮", "透明", "光", "輝き",
}

SCENE_TERMS = {
    "挨拶", "雑談", "SNS", "チャット", "返信", "スタンプ", "推し活", "会話",
    "仕事", "作業", "学校", "学習", "記録", "研究", "実験", "専門", "通勤",
    "旅行", "出張", "外出", "おでかけ", "観光", "地図", "街", "場所", "道路",
    "駅", "交通", "移動", "遠出", "旅", "乗る", "運ぶ", "ドライブ",
    "食事", "料理", "昼食", "夕食", "朝食", "おやつ", "食卓", "外食", "店",
    "メニュー", "カフェ", "乾杯", "飲み会", "休憩", "生活", "使う", "持つ",
    "置く", "保管", "用途", "便利",
    "イベント", "お祝い", "パーティー", "誕生日", "クリスマス", "ハロウィーン",
    "バレンタイン", "休日", "行事", "参加", "写真",
    "スポーツ", "試合", "応援", "運動", "部活", "練習", "ゲーム", "遊び", "勝負",
    "趣味", "ライブ", "音楽", "演奏", "映画", "動画", "メディア",
    "家", "庭", "公園", "病院", "寺院", "水族館", "動物園", "サファリ", "海",
    "空", "屋外", "自然", "季節", "春", "夏休み", "秋", "冬", "朝", "夜",
    "買い物", "支払い", "予約", "受付", "申し込み", "申請", "確認", "提示",
    "入力", "表示", "変換", "操作", "通知", "再生", "停止", "連絡", "案内",
    "注意", "禁止", "許可", "安全", "保護", "ケア", "健康", "体調", "祈り",
    "ジェスチャー", "合図", "OK", "了解", "お願い", "感謝", "拍手", "指差し",
    "ピース", "電話", "応援", "挨拶",
    "信仰", "占い", "運勢", "動物占い", "星座占い", "国際", "海外",
    "景色", "アジア", "中東", "ヨーロッパ", "アフリカ", "北アメリカ", "南アメリカ",
    "オセアニア", "南極", "日本", "インド", "イスラエル", "アメリカ",
    "フランス", "スウェーデン", "ブラジル", "カナダ", "中国", "韓国",
    "仏教", "ユダヤ教", "宗教", "文化", "歴史", "代表",
}

TAG_HINT_TERMS = {
    "顔", "笑顔", "表情", "リアクション", "顔文字", "人", "体", "手", "指", "目", "口",
    "ハート", "星", "月", "太陽", "雲", "雨", "雪", "雷", "火", "水", "波", "風",
    "動物", "生き物", "哺乳類", "鳥", "虫", "魚", "植物", "花", "葉", "緑", "果物",
    "野菜", "食べ物", "飲み物", "道具", "物", "持ち物", "日用品", "服", "ファッション",
    "文房具", "本", "紙", "お金", "メール", "スマホ", "パソコン", "医療", "宗教",
    "記号", "マーク", "シンボル", "数字", "文字", "英字", "日本語", "ボタン", "キー",
    "国", "地域", "国旗", "旗", "星座", "干支", "十字",
    "車輪", "歯車", "カード", "素材", "形", "色", "見た目",
    "都会",
}

SCENE_SUFFIXES = (
    "するとき", "向き", "用", "場面", "場所", "旅行", "仕事", "学校", "店", "会",
)
TONE_SUFFIXES = ("い", "しい", "たい", "やか", "っぽい")


def split_values(value):
    return [item.strip() for item in str(value or "").split(";") if item.strip()]


def add_unique(target, value):
    if value and value not in target:
        target.append(value)


def classify_term(term):
    if term in SCENE_TERMS:
        return "scenes"
    if term in TONE_TERMS:
        return "tone"
    if term in TAG_HINT_TERMS:
        return "tags"
    if term.endswith(SCENE_SUFFIXES):
        return "scenes"
    if term.endswith(TONE_SUFFIXES) and len(term) <= 6:
        return "tone"
    if any(part in term for part in ("入力", "旅行", "仕事", "通勤", "予約", "店", "学校", "病院", "宗教", "占い")):
        return "scenes"
    if any(part in term for part in ("笑", "泣", "怒", "かわ", "好き", "怖", "暑", "寒", "速い", "ゆっくり", "丸", "縞")):
        return "tone"
    return "tags"


def rebalance(tags, scenes, tone):
    # Keep at least two scene/tone terms when the source has enough associative breadth.
    while len(scenes) < 2:
        for i, term in enumerate(tags):
            if term in {"SNS", "チャット", "仕事", "旅行", "食事", "写真", "入力", "表示", "外出", "場所", "店", "学校", "家", "海外", "国際", "文化", "宗教", "仏教", "インド", "アジア", "中東", "ヨーロッパ", "代表", "生活", "使う", "持つ", "置く", "保管", "用途", "便利", "確認", "ジェスチャー", "合図", "OK", "了解", "お願い", "感謝", "拍手", "応援", "挨拶"}:
                add_unique(scenes, term)
                tags.pop(i)
                break
        else:
            break
    while len(tone) < 2:
        for i, term in enumerate(tags):
            if term in {"かわいい", "楽しい", "明るい", "白い", "白", "赤い", "青い", "青い旗", "丸い", "丸", "円", "楕円", "三色旗", "縦縞", "横縞", "縞模様", "速い", "ふわふわ", "きらきら", "好き", "ダビデの星", "日の丸", "赤い丸", "緑", "オレンジ", "形", "素材", "色", "見た目", "カード", "動き", "ポーズ", "肌色違い", "バリエーション", "薄い肌色", "やや薄い肌色", "中間の肌色", "やや濃い肌色", "濃い肌色", "左向き", "右向き", "上向き", "下向き"}:
                add_unique(tone, term)
                tags.pop(i)
                break
        else:
            break
    return tags, scenes, tone


def split_row(row):
    tags = []
    scenes = []
    tone = []
    for term in split_values(row.get("assoc_ja")):
        bucket = classify_term(term)
        if bucket == "scenes":
            add_unique(scenes, term)
        elif bucket == "tone":
            add_unique(tone, term)
        else:
            add_unique(tags, term)
    tags, scenes, tone = rebalance(tags, scenes, tone)
    row["tags_ja"] = ";".join(tags)
    row["scenes_ja"] = ";".join(scenes)
    row["tone_ja"] = ";".join(tone)
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    for required in ("tags_ja", "scenes_ja", "tone_ja"):
        if required not in fieldnames:
            fieldnames.append(required)

    rows = [split_row(row) for row in rows]

    with args.output.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
