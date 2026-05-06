import argparse
import re
from pathlib import Path

from emoji_assoc import (
    DEFAULT_CSV,
    V2_FIELDS,
    is_skin_tone_variant,
    join_list,
    read_rows,
    rebuild_search_terms,
    split_list,
    unique,
    write_rows,
)


TARGET_CATEGORY = "People & Body"

SUBCATEGORY_BASE = {
    "hand-fingers-open": {
        "direct": ["手", "手のひら"],
        "visual": ["指", "開いた手"],
        "context": ["チャット", "SNS", "リアクション"],
        "symbolic": ["合図", "意思表示"],
        "action": ["示す", "振る"],
    },
    "hand-fingers-partial": {
        "direct": ["手", "指サイン"],
        "visual": ["指", "ジェスチャー"],
        "context": ["チャット", "SNS", "リアクション"],
        "symbolic": ["合図", "意思表示"],
        "action": ["示す", "つまむ"],
    },
    "hand-single-finger": {
        "direct": ["指差し", "指", "手"],
        "visual": ["一本指", "向き"],
        "context": ["案内", "説明", "注目", "チャット"],
        "symbolic": ["方向", "指示", "強調"],
        "action": ["指す", "示す"],
    },
    "hand-fingers-closed": {
        "direct": ["手", "こぶし"],
        "visual": ["握った手", "拳"],
        "context": ["応援", "リアクション", "チャット"],
        "symbolic": ["賛成", "反対", "力"],
        "action": ["握る", "殴る", "応援する"],
    },
    "hands": {
        "direct": ["両手", "手"],
        "visual": ["二つの手", "手のひら"],
        "context": ["挨拶", "お礼", "応援", "チャット"],
        "symbolic": ["協力", "祈り", "祝福"],
        "emotion": ["感謝", "嬉しい", "温かい"],
        "action": ["拍手する", "合わせる", "祈る"],
    },
    "hand-prop": {
        "direct": ["手", "道具"],
        "visual": ["手元", "小物"],
        "context": ["作業", "美容", "写真", "SNS"],
        "symbolic": ["自己表現", "記録"],
        "action": ["書く", "塗る", "撮る"],
    },
    "body-parts": {
        "direct": ["体", "部位"],
        "visual": ["人体", "パーツ"],
        "context": ["健康", "医療", "美容", "説明"],
        "symbolic": ["身体", "感覚"],
        "action": ["見る", "聞く", "話す", "感じる"],
    },
    "person": {
        "direct": ["人", "人物"],
        "visual": ["顔", "上半身"],
        "context": ["プロフィール", "自己紹介", "人物紹介"],
        "symbolic": ["個人", "アイコン"],
        "emotion": ["親しみ"],
    },
    "person-gesture": {
        "direct": ["人", "ジェスチャー"],
        "visual": ["ポーズ", "上半身"],
        "context": ["チャット", "リアクション", "会話", "説明"],
        "symbolic": ["意思表示", "態度"],
        "action": ["示す", "答える"],
    },
    "person-role": {
        "direct": ["人", "職業"],
        "visual": ["制服", "仕事姿"],
        "context": ["仕事", "職場", "専門職", "紹介"],
        "symbolic": ["専門家", "働く人"],
        "action": ["働く"],
    },
    "person-fantasy": {
        "direct": ["人", "空想上の人"],
        "visual": ["衣装", "ファンタジー"],
        "context": ["物語", "ゲーム", "ハロウィン", "創作"],
        "symbolic": ["魔法", "伝説", "非日常"],
        "emotion": ["不思議", "神秘的"],
    },
    "person-activity": {
        "direct": ["人", "活動する人"],
        "visual": ["全身", "動き"],
        "context": ["運動", "趣味", "外出", "日常"],
        "symbolic": ["活動", "挑戦"],
        "action": ["動く"],
    },
    "person-sport": {
        "direct": ["人", "スポーツ"],
        "visual": ["運動", "道具"],
        "context": ["試合", "部活", "応援", "運動会"],
        "symbolic": ["競技", "勝負", "挑戦"],
        "emotion": ["元気", "熱い"],
        "action": ["競う", "運動する"],
        "culture": ["スポーツ"],
    },
    "person-resting": {
        "direct": ["人", "休む人"],
        "visual": ["横になる", "座る"],
        "context": ["休憩", "睡眠", "ホテル", "リラックス"],
        "symbolic": ["休息", "回復"],
        "emotion": ["落ち着く", "眠い"],
        "action": ["休む", "寝る"],
    },
    "family": {
        "direct": ["家族", "人"],
        "visual": ["複数人", "並んだ人"],
        "context": ["家庭", "子育て", "記念写真", "家族紹介"],
        "symbolic": ["絆", "親子", "愛情", "つながり"],
        "emotion": ["温かい", "幸せ", "親しみ"],
        "action": ["暮らす", "支える"],
    },
    "person-symbol": {
        "direct": ["人の記号", "人物アイコン"],
        "visual": ["シルエット", "記号"],
        "context": ["プロフィール", "アカウント", "ユーザー", "名簿"],
        "symbolic": ["匿名", "個人", "グループ"],
        "action": ["登録する", "選ぶ"],
    },
}

KEYWORDS = [
    ("waving", {"direct": ["手を振る"], "context": ["挨拶", "別れ"], "symbolic": ["こんにちは", "さようなら"], "action": ["振る"]}),
    ("raised back", {"direct": ["手の甲"], "visual": ["手の甲"], "action": ["見せる"]}),
    ("fingers splayed", {"direct": ["開いた手"], "visual": ["五本指", "開く"], "action": ["開く"]}),
    ("raised hand", {"direct": ["挙手"], "context": ["授業", "質問", "会議"], "symbolic": ["発言", "参加"], "action": ["手を挙げる"]}),
    ("vulcan", {"direct": ["バルカンの挨拶"], "culture": ["スタートレック", "SF"], "symbolic": ["長寿と繁栄"]}),
    ("rightwards", {"visual": ["右向き", "右"], "symbolic": ["右方向"], "action": ["右を示す"]}),
    ("leftwards", {"visual": ["左向き", "左"], "symbolic": ["左方向"], "action": ["左を示す"]}),
    ("palm down", {"direct": ["下向きの手"], "visual": ["手のひら下"], "symbolic": ["押さえる"], "action": ["下げる"]}),
    ("palm up", {"direct": ["上向きの手"], "visual": ["手のひら上"], "symbolic": ["受け取る", "差し出す"], "action": ["差し出す"]}),
    ("pushing", {"direct": ["押す手"], "symbolic": ["拒む", "ストップ"], "action": ["押す"]}),
    ("OK hand", {"direct": ["OK", "OKサイン"], "context": ["確認", "了承"], "symbolic": ["大丈夫", "合格"], "emotion": ["安心"], "action": ["承認する"]}),
    ("pinched fingers", {"direct": ["すぼめた指"], "visual": ["指先"], "symbolic": ["少し", "細かい"], "action": ["すぼめる"]}),
    ("pinching", {"direct": ["つまむ手"], "visual": ["指先"], "symbolic": ["少し", "小さい"], "action": ["つまむ"]}),
    ("victory", {"direct": ["ピース"], "context": ["写真", "勝利"], "symbolic": ["勝利", "平和"], "emotion": ["嬉しい"], "action": ["ピースする"]}),
    ("crossed fingers", {"direct": ["指をクロス"], "context": ["願掛け"], "symbolic": ["幸運", "祈り"], "action": ["願う"]}),
    ("love-you", {"direct": ["アイラブユー"], "symbolic": ["愛", "好き"], "emotion": ["愛情"], "action": ["愛を伝える"]}),
    ("horns", {"direct": ["角のサイン"], "culture": ["ロック", "ライブ"], "symbolic": ["盛り上がり"], "emotion": ["かっこいい"], "action": ["盛り上げる"]}),
    ("call me", {"direct": ["電話の合図"], "context": ["連絡", "電話"], "symbolic": ["電話して"], "action": ["電話する"]}),
    ("thumbs up", {"direct": ["サムズアップ", "いいね"], "context": ["承認", "応援"], "symbolic": ["賛成", "OK"], "emotion": ["前向き"], "action": ["褒める"]}),
    ("thumbs down", {"direct": ["サムズダウン"], "context": ["評価", "反対"], "symbolic": ["反対", "だめ"], "emotion": ["不満"], "action": ["否定する"]}),
    ("clapping", {"direct": ["拍手"], "context": ["お祝い", "称賛", "発表"], "symbolic": ["称賛"], "emotion": ["嬉しい"], "action": ["拍手する"]}),
    ("raising hands", {"direct": ["バンザイ"], "context": ["成功", "お祝い"], "symbolic": ["喜び", "勝利"], "emotion": ["嬉しい"], "action": ["喜ぶ"]}),
    ("heart hands", {"direct": ["ハートの手"], "visual": ["ハート"], "context": ["推し活", "応援"], "symbolic": ["愛", "感謝"], "emotion": ["好き", "かわいい"], "action": ["愛を伝える"]}),
    ("handshake", {"direct": ["握手"], "context": ["挨拶", "契約", "合意"], "symbolic": ["協力", "信頼"], "action": ["握手する"]}),
    ("folded hands", {"direct": ["合掌", "合わせた手"], "context": ["お願い", "祈り", "お礼"], "symbolic": ["祈願", "感謝", "謝罪"], "emotion": ["ありがたい"], "action": ["祈る", "お願いする"]}),
    ("writing", {"direct": ["書く手"], "context": ["勉強", "仕事", "メモ"], "symbolic": ["記録", "署名"], "action": ["書く"]}),
    ("nail", {"direct": ["マニキュア"], "context": ["美容", "ネイル"], "symbolic": ["おしゃれ"], "emotion": ["きれい"], "action": ["塗る"]}),
    ("selfie", {"direct": ["セルフィー", "自撮り"], "context": ["写真", "SNS", "旅行"], "symbolic": ["記念"], "action": ["撮る"]}),
]

ROLE_KEYWORDS = {
    "health worker": (["医療従事者", "医師", "看護"], ["病院", "医療", "診察"], ["健康", "治療"], ["診る", "看病する"]),
    "student": (["学生"], ["学校", "授業", "卒業"], ["学び"], ["学ぶ"]),
    "teacher": (["教師", "先生"], ["学校", "授業", "教育"], ["知識"], ["教える"]),
    "judge": (["裁判官"], ["裁判", "法律"], ["正義", "判決"], ["裁く"]),
    "farmer": (["農家"], ["農業", "畑"], ["収穫", "自然"], ["育てる"]),
    "cook": (["料理人", "コック"], ["料理", "レストラン"], ["食事"], ["作る"]),
    "mechanic": (["整備士"], ["修理", "工場"], ["機械"], ["直す"]),
    "factory worker": (["工場労働者"], ["工場", "製造"], ["ものづくり"], ["作る"]),
    "office worker": (["会社員"], ["会社", "仕事", "オフィス"], ["ビジネス"], ["働く"]),
    "scientist": (["科学者"], ["研究", "実験"], ["科学"], ["調べる"]),
    "technologist": (["技術者"], ["IT", "パソコン", "開発"], ["技術"], ["作る"]),
    "singer": (["歌手"], ["音楽", "ライブ"], ["歌"], ["歌う"]),
    "artist": (["芸術家"], ["絵", "制作"], ["アート"], ["描く"]),
    "pilot": (["パイロット"], ["飛行機", "空港"], ["空"], ["操縦する"]),
    "astronaut": (["宇宙飛行士"], ["宇宙", "ロケット"], ["探査"], ["飛ぶ"]),
    "firefighter": (["消防士"], ["消防", "火事"], ["救助"], ["消火する"]),
    "police officer": (["警察官"], ["警察", "防犯"], ["安全"], ["守る"]),
    "detective": (["探偵"], ["調査", "事件"], ["謎"], ["調べる"]),
    "guard": (["警備員"], ["警備", "安全"], ["守る"], ["見張る"]),
    "ninja": (["忍者"], ["和風", "時代劇"], ["隠密"], ["忍ぶ"]),
    "construction worker": (["建設作業員"], ["工事", "建築"], ["現場"], ["作る"]),
    "person with crown": (["王冠の人"], ["王様", "女王"], ["王族"], ["統治する"]),
    "prince": (["王子"], ["王族", "物語"], ["高貴"], ["導く"]),
    "princess": (["姫", "プリンセス"], ["王族", "物語"], ["高貴"], ["微笑む"]),
    "person wearing turban": (["ターバンの人"], ["服装", "文化"], ["伝統"], ["装う"]),
    "person with skullcap": (["帽子の人"], ["服装", "文化"], ["伝統"], ["装う"]),
    "person in tuxedo": (["タキシードの人"], ["結婚式", "式典"], ["正装"], ["着飾る"]),
    "person with veil": (["ベールの人"], ["結婚式", "花嫁"], ["正装"], ["着飾る"]),
    "pregnant": (["妊娠"], ["出産", "家族"], ["命", "母性"], ["育む"]),
    "breast-feeding": (["授乳"], ["育児", "赤ちゃん"], ["子育て", "母性"], ["授乳する"]),
}

FANTASY_KEYWORDS = {
    "superhero": ["ヒーロー", "正義", "強い"],
    "supervillain": ["悪役", "敵", "ダーク"],
    "mage": ["魔法使い", "魔法", "杖"],
    "fairy": ["妖精", "羽", "ファンタジー"],
    "vampire": ["吸血鬼", "ドラキュラ", "ハロウィン"],
    "merperson": ["人魚", "海", "ファンタジー"],
    "elf": ["エルフ", "耳", "森"],
    "genie": ["ランプの精", "魔法", "願い"],
    "zombie": ["ゾンビ", "ホラー", "不気味"],
}

SPORT_KEYWORDS = {
    "walking": ["歩く", "散歩"],
    "running": ["走る", "ランニング"],
    "dancing": ["踊る", "ダンス"],
    "climbing": ["登る", "クライミング"],
    "lotus": ["座禅", "瞑想", "ヨガ"],
    "bath": ["入浴", "お風呂"],
    "bed": ["寝る", "ベッド"],
    "soccer": ["サッカー"],
    "basketball": ["バスケットボール"],
    "football": ["アメフト"],
    "baseball": ["野球"],
    "softball": ["ソフトボール"],
    "tennis": ["テニス"],
    "volleyball": ["バレーボール"],
    "rugby": ["ラグビー"],
    "billiards": ["ビリヤード"],
    "golfing": ["ゴルフ"],
    "surfing": ["サーフィン"],
    "swimming": ["水泳", "泳ぐ"],
    "water polo": ["水球"],
    "rowing": ["ボート", "漕ぐ"],
    "horse racing": ["競馬", "馬"],
    "biking": ["自転車"],
    "mountain biking": ["マウンテンバイク"],
    "cartwheeling": ["側転"],
    "wrestling": ["レスリング"],
    "juggling": ["ジャグリング"],
}

BODY_PARTS = {
    "brain": ["脳", "頭", "考える"],
    "heart": ["心臓", "ハート", "命"],
    "lungs": ["肺", "呼吸", "息"],
    "tooth": ["歯", "歯医者", "白い"],
    "bone": ["骨", "骸骨", "白い"],
    "eyes": ["目", "見る", "視線"],
    "eye": ["目", "見る", "視線"],
    "tongue": ["舌", "味", "口"],
    "mouth": ["口", "唇", "話す"],
    "ear": ["耳", "聞く", "音"],
    "nose": ["鼻", "におい", "嗅ぐ"],
    "biceps": ["力こぶ", "筋肉", "強い"],
    "leg": ["脚", "歩く", "走る"],
    "foot": ["足", "歩く", "靴"],
}


def add(bucket, key, values):
    bucket[key].extend(values)


def make_bucket():
    return {
        "direct_ja": [],
        "visual_ja": [],
        "context_ja": [],
        "symbolic_ja": [],
        "emotion_ja": [],
        "action_ja": [],
        "culture_ja": [],
    }


def apply_base(row, bucket):
    name_en = row.get("name_en", "").lower()
    if row["subcategory"] == "person-role" and ("pregnant" in name_en or "breast-feeding" in name_en):
        base = SUBCATEGORY_BASE["person"]
    else:
        base = SUBCATEGORY_BASE.get(row["subcategory"], {})
    mapping = {
        "direct": "direct_ja",
        "visual": "visual_ja",
        "context": "context_ja",
        "symbolic": "symbolic_ja",
        "emotion": "emotion_ja",
        "action": "action_ja",
        "culture": "culture_ja",
    }
    for key, field in mapping.items():
        add(bucket, field, base.get(key, []))


def add_name_terms(row, bucket):
    name_ja = row.get("name_ja", "").strip()
    if name_ja:
        add(bucket, "direct_ja", [name_ja.replace(":", " ").strip()])

    name_en = row.get("name_en", "").lower()
    if has_word(name_en, "man") or has_word(name_en, "male") or has_word(name_en, "boy") or has_word(name_en, "father") or "merman" in name_en:
        add(bucket, "direct_ja", ["男性"])
        add(bucket, "visual_ja", ["男"])
    if has_word(name_en, "woman") or has_word(name_en, "female") or has_word(name_en, "girl") or has_word(name_en, "mother") or "mermaid" in name_en:
        add(bucket, "direct_ja", ["女性"])
        add(bucket, "visual_ja", ["女"])
    if has_word(name_en, "boy"):
        add(bucket, "direct_ja", ["男の子", "子供"])
        add(bucket, "context_ja", ["子育て"])
    if has_word(name_en, "girl"):
        add(bucket, "direct_ja", ["女の子", "子供"])
        add(bucket, "context_ja", ["子育て"])
    if has_word(name_en, "baby"):
        add(bucket, "direct_ja", ["赤ちゃん", "赤ん坊"])
        add(bucket, "context_ja", ["育児", "出産"])
        add(bucket, "emotion_ja", ["かわいい"])
    if "child" in name_en:
        add(bucket, "direct_ja", ["子供"])
        add(bucket, "context_ja", ["学校", "子育て"])
    if "older" in name_en or "old " in name_en:
        add(bucket, "direct_ja", ["高齢者", "お年寄り"])
        add(bucket, "context_ja", ["介護", "家族"])
    for word, ja in [("blond", "金髪"), ("red hair", "赤毛"), ("curly hair", "巻き毛"), ("white hair", "白髪"), ("bald", "はげ頭"), ("beard", "ひげ")]:
        if word in name_en:
            add(bucket, "direct_ja", [ja])
            add(bucket, "visual_ja", [ja, "髪型"])


def apply_keyword_rules(row, bucket):
    name_en = row.get("name_en", "").lower()
    name_ja = row.get("name_ja", "")

    for keyword, values in KEYWORDS:
        if keyword.lower() in name_en:
            for key, terms in values.items():
                add(bucket, f"{key}_ja", terms)

    if row["subcategory"] == "body-parts":
        for keyword, terms in BODY_PARTS.items():
            if has_word(name_en, keyword):
                add(bucket, "direct_ja", terms[:2])
                add(bucket, "visual_ja", terms[:2])
                add(bucket, "context_ja", ["健康", "医療"])
                add(bucket, "symbolic_ja", terms[2:])
                add(bucket, "action_ja", terms[1:])

    if row["subcategory"] == "person-role":
        for keyword, (direct, context, symbolic, action) in ROLE_KEYWORDS.items():
            if keyword in name_en:
                add(bucket, "direct_ja", direct)
                add(bucket, "context_ja", context)
                add(bucket, "symbolic_ja", symbolic)
                add(bucket, "action_ja", action)

    if row["subcategory"] == "person-fantasy":
        for keyword, terms in FANTASY_KEYWORDS.items():
            if keyword in name_en:
                add(bucket, "direct_ja", terms[:1])
                add(bucket, "visual_ja", terms[2:])
                add(bucket, "symbolic_ja", terms[1:])
                add(bucket, "culture_ja", ["ファンタジー"])

    if row["subcategory"] in {"person-activity", "person-sport", "person-resting"}:
        for keyword, terms in SPORT_KEYWORDS.items():
            if keyword in name_en:
                add(bucket, "direct_ja", terms)
                add(bucket, "action_ja", terms)
                add(bucket, "context_ja", terms)

    if row["subcategory"] == "family":
        if "couple" in name_en:
            add(bucket, "direct_ja", ["カップル", "恋人"])
            add(bucket, "context_ja", ["デート", "恋愛"])
            add(bucket, "symbolic_ja", ["愛情", "パートナー"])
        if "kiss" in name_en:
            add(bucket, "direct_ja", ["キス"])
            add(bucket, "context_ja", ["恋愛", "記念日"])
            add(bucket, "symbolic_ja", ["愛情"])
            add(bucket, "action_ja", ["キスする"])
        if "heart" in name_en:
            add(bucket, "visual_ja", ["ハート"])
            add(bucket, "symbolic_ja", ["愛"])
        if "family" in name_en:
            add(bucket, "direct_ja", ["家族"])
            add(bucket, "context_ja", ["家庭", "親子"])
        if "holding hands" in name_en:
            add(bucket, "direct_ja", ["手をつなぐ"])
            add(bucket, "action_ja", ["手をつなぐ"])
            add(bucket, "symbolic_ja", ["仲良し"])

    if "deaf" in name_en or "耳の不自由" in name_ja:
        add(bucket, "direct_ja", ["耳の不自由な人"])
        add(bucket, "context_ja", ["福祉", "アクセシビリティ"])
        add(bucket, "symbolic_ja", ["多様性"])
    if "wheelchair" in name_en:
        add(bucket, "direct_ja", ["車椅子"])
        add(bucket, "context_ja", ["福祉", "バリアフリー"])
        add(bucket, "symbolic_ja", ["アクセシビリティ"])
    if "white cane" in name_en:
        add(bucket, "direct_ja", ["白杖"])
        add(bucket, "context_ja", ["福祉", "バリアフリー"])
        add(bucket, "symbolic_ja", ["アクセシビリティ"])


def ensure_minimum(row, bucket):
    search = unique(v for field in bucket.values() for v in field)
    expected = {"3": 15, "2": 8, "1": 6}.get(str(row.get("importance", "")).strip(), 8)
    if len(search) >= expected:
        return

    fallback = [
        row.get("subcategory_ja", ""),
        row.get("category_ja", ""),
        "絵文字",
    ]
    if row["subcategory"].startswith("hand"):
        fallback.extend(["ハンドサイン", "合図", "リアクション"])
    elif row["subcategory"].startswith("person"):
        fallback.extend(["人物", "人間", "アイコン"])
    elif row["subcategory"] == "family":
        fallback.extend(["人物", "家庭", "人間関係"])
    elif row["subcategory"] == "body-parts":
        fallback.extend(["人体", "からだ", "健康"])
    add(bucket, "symbolic_ja", fallback)


def has_word(text, word):
    return bool(re.search(rf"(?<![a-z]){re.escape(word)}(?![a-z])", text))


def build_terms(row):
    bucket = make_bucket()
    apply_base(row, bucket)
    add_name_terms(row, bucket)
    apply_keyword_rules(row, bucket)
    ensure_minimum(row, bucket)
    return {field: unique(values) for field, values in bucket.items()}


def should_fill(row):
    return (
        row.get("category") == TARGET_CATEGORY
        and not is_skin_tone_variant(row)
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Regenerate existing People & Body rows too.")
    args = parser.parse_args()

    rows, fieldnames = read_rows(args.csv)
    changed = 0
    for row in rows:
        if not should_fill(row) or (split_list(row.get("search_ja", "")) and not args.force):
            continue
        terms = build_terms(row)
        for field in V2_FIELDS:
            if field == "search_ja":
                continue
            row[field] = join_list(terms.get(field, []))
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
