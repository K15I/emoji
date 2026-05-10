import argparse
import re
from pathlib import Path

from emoji_assoc import DEFAULT_CSV, V2_FIELDS, join_list, read_rows, rebuild_search_terms, split_list, unique, write_rows


TARGET_CATEGORY = "Symbols"

BASE = {
    "transport-sign": (["案内記号", "施設記号"], ["四角", "標識"], ["駅", "空港", "施設"], ["案内", "公共"], ["実用的"], ["示す"], []),
    "warning": (["警告記号", "禁止記号"], ["赤", "斜線"], ["道路", "注意", "ルール"], ["危険", "禁止"], ["注意"], ["止める"], []),
    "arrow": (["矢印"], ["向き", "線"], ["案内", "操作", "説明"], ["方向", "移動"], ["実用的"], ["示す"], []),
    "religion": (["宗教記号", "象徴"], ["記号", "形"], ["宗教", "祈り", "文化"], ["信仰", "神聖"], ["厳か"], ["祈る"], ["宗教"]),
    "zodiac": (["星座", "占い"], ["記号", "線"], ["占い", "誕生日"], ["運勢", "性格診断"], ["神秘的"], ["占う"], ["星座", "占い"]),
    "av-symbol": (["操作ボタン", "再生記号"], ["三角", "ボタン"], ["音楽", "動画", "再生"], ["操作", "メディア"], ["実用的"], ["操作する"], []),
    "gender": (["性別記号"], ["丸", "線"], ["プロフィール", "多様性"], ["性別", "ジェンダー"], ["中立"], ["表す"], []),
    "math": (["数学記号"], ["線", "記号"], ["計算", "勉強"], ["数式", "比較"], ["まじめ"], ["計算する"], []),
    "punctuation": (["句読点", "記号"], ["赤", "白"], ["文章", "チャット", "強調"], ["疑問", "驚き"], ["びっくり"], ["強調する"], []),
    "currency": (["通貨記号"], ["お金", "記号"], ["両替", "買い物"], ["価格", "金融"], ["実用的"], ["払う"], []),
    "other-symbol": (["記号", "マーク"], ["形", "印"], ["表示", "案内", "チャット"], ["意味", "サイン"], ["実用的"], ["示す"], []),
    "keycap": (["キーキャップ", "数字キー"], ["四角", "文字"], ["入力", "番号"], ["数字", "ボタン"], ["実用的"], ["入力する"], []),
    "alphanum": (["英数字記号", "ボタン"], ["文字", "四角"], ["入力", "案内", "表示"], ["ラベル", "状態"], ["実用的"], ["示す"], []),
    "geometric": (["図形", "形"], ["色", "幾何学"], ["デザイン", "分類", "目印"], ["色分け", "シンプル"], ["中立"], ["示す"], []),
}

COLOR_WORDS = {
    "red": "赤", "orange": "オレンジ", "yellow": "黄色", "green": "緑", "blue": "青",
    "purple": "紫", "brown": "茶色", "black": "黒", "white": "白",
}

EXTRA = {
    "ATM": ["ATM", "銀行", "現金"],
    "wheelchair": ["車椅子", "バリアフリー", "福祉"],
    "restroom": ["トイレ", "化粧室", "施設"],
    "passport": ["パスポート", "出入国", "空港"],
    "customs": ["税関", "入国", "空港"],
    "baggage": ["手荷物", "荷物", "空港"],
    "no smoking": ["禁煙", "たばこ禁止", "禁止"],
    "no bicycles": ["自転車禁止", "自転車", "禁止"],
    "radioactive": ["放射能", "危険", "警告"],
    "biohazard": ["バイオハザード", "感染", "危険"],
    "David": ["ダビデの星", "ユダヤ教", "イスラエル"],
    "dharma": ["法輪", "仏教", "インド"],
    "yin yang": ["陰陽", "道教", "バランス"],
    "cross": ["十字架", "キリスト教", "教会"],
    "crescent": ["三日月", "イスラム教", "星"],
    "peace": ["平和", "ピース", "反戦"],
    "Aries": ["おひつじ座", "牡羊座", "牡羊"],
    "Taurus": ["おうし座", "牡牛座", "牡牛"],
    "Gemini": ["ふたご座", "双子"],
    "Cancer": ["かに座", "蟹座", "蟹"],
    "Leo": ["しし座", "獅子座", "ライオン"],
    "Virgo": ["おとめ座", "乙女"],
    "Libra": ["てんびん座", "天秤"],
    "Scorpio": ["さそり座", "蠍"],
    "Sagittarius": ["いて座", "弓"],
    "Capricorn": ["やぎ座", "山羊"],
    "Aquarius": ["みずがめ座", "水瓶"],
    "Pisces": ["うお座", "魚"],
    "Ophiuchus": ["へびつかい座", "蛇"],
    "play": ["再生", "スタート", "動画"],
    "pause": ["一時停止", "止める", "動画"],
    "stop": ["停止", "ストップ", "動画"],
    "record": ["録音", "録画", "記録"],
    "question": ["疑問符", "はてな", "？"],
    "exclamation": ["感嘆符", "びっくり", "！"],
    "check": ["チェック", "確認", "OK"],
    "cross mark": ["バツ", "NG", "だめ"],
    "copyright": ["著作権", "コピーライト", "権利"],
    "trade": ["商標", "ブランド", "権利"],
}


def add(bucket, field, values):
    bucket[field].extend(values)


def make_bucket():
    return {field: [] for field in V2_FIELDS if field != "search_ja"}


def apply_base(row, bucket):
    direct, visual, context, symbolic, emotion, action, culture = BASE[row["subcategory"]]
    for field, values in [
        ("direct_ja", direct),
        ("visual_ja", visual),
        ("context_ja", context),
        ("symbolic_ja", symbolic),
        ("emotion_ja", emotion),
        ("action_ja", action),
        ("culture_ja", culture),
    ]:
        add(bucket, field, values)
    add(bucket, "direct_ja", [row["name_ja"]])


def apply_specific(row, bucket):
    name_en = row["name_en"]
    lower = name_en.lower()
    for en, ja in COLOR_WORDS.items():
        if en in lower:
            add(bucket, "visual_ja", [ja])
            add(bucket, "direct_ja", [ja])
    for shape in ["circle", "square", "triangle", "diamond"]:
        if shape in lower:
            add(bucket, "visual_ja", [{"circle": "丸", "square": "四角", "triangle": "三角", "diamond": "ひし形"}[shape]])
    for direction, ja in [("up", "上"), ("down", "下"), ("left", "左"), ("right", "右")]:
        if direction in lower:
            add(bucket, "direct_ja", [ja])
            add(bucket, "symbolic_ja", [f"{ja}方向"])
    for token, terms in EXTRA.items():
        if token.lower() in lower or token in name_en:
            add(bucket, "direct_ja", terms)
            add(bucket, "symbolic_ja", terms)
    digits = re.findall(r"\d+", row["name_ja"])
    if digits:
        add(bucket, "direct_ja", digits)
        add(bucket, "visual_ja", ["数字"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    rows, fieldnames = read_rows(args.csv)
    changed = 0
    for row in rows:
        if row.get("category") != TARGET_CATEGORY or (split_list(row.get("search_ja", "")) and not args.force):
            continue
        bucket = make_bucket()
        apply_base(row, bucket)
        apply_specific(row, bucket)
        if len(unique(v for values in bucket.values() for v in values)) < 6:
            add(bucket, "symbolic_ja", [row["subcategory_ja"], row["category_ja"]])
        for field in V2_FIELDS:
            if field == "search_ja":
                continue
            row[field] = join_list(unique(bucket[field]))
        row["search_ja"] = join_list(rebuild_search_terms(row))
        changed += 1

    if args.dry_run:
        print(f"Would fill {changed} {TARGET_CATEGORY} rows")
        return
    output = args.output or args.csv
    write_rows(output, rows, fieldnames)
    print(f"Filled {changed} {TARGET_CATEGORY} rows into {output}")


if __name__ == "__main__":
    main()
