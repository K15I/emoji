import argparse
import re
from pathlib import Path

from emoji_assoc import DEFAULT_CSV, V2_FIELDS, join_list, read_rows, rebuild_search_terms, split_list, unique, write_rows


TARGET_CATEGORY = "Travel & Places"

SUBCATEGORY_BASE = {
    "place-map": (["地図", "場所"], ["地球", "線"], ["旅行", "地理", "案内"], ["世界", "方向"], ["実用的"], ["探す"], ["地域"]),
    "place-geographic": (["地形", "自然"], ["山", "空"], ["旅行", "アウトドア", "観光"], ["風景", "自然"], ["爽やか"], ["眺める"], []),
    "place-building": (["建物", "場所"], ["建築", "外観"], ["街", "施設", "外出"], ["暮らし", "都市"], ["落ち着く"], ["訪れる"], []),
    "place-religious": (["宗教施設", "建物"], ["屋根", "象徴"], ["参拝", "観光", "祈り"], ["信仰", "神聖"], ["厳か"], ["祈る"], ["宗教"]),
    "place-other": (["場所", "風景"], ["景色", "空"], ["旅行", "観光", "外出"], ["思い出", "レジャー"], ["楽しい"], ["行く"], []),
    "transport-ground": (["乗り物", "交通"], ["車輪", "道"], ["移動", "通勤", "旅行"], ["速さ", "便利"], ["実用的"], ["走る", "乗る"], []),
    "transport-water": (["船", "水上の乗り物"], ["水", "海"], ["旅行", "港", "海"], ["航海", "移動"], ["爽やか"], ["進む", "乗る"], []),
    "transport-air": (["空の乗り物", "乗り物"], ["空", "翼"], ["旅行", "空港", "移動"], ["飛行", "冒険"], ["わくわく"], ["飛ぶ", "乗る"], []),
    "hotel": (["ホテル", "旅行用品"], ["荷物", "ベル"], ["宿泊", "旅行", "受付"], ["旅支度"], ["実用的"], ["泊まる"], []),
    "time": (["時間", "時計"], ["針", "丸い"], ["予定", "待ち合わせ", "仕事"], ["時刻", "期限"], ["急ぎ"], ["計る", "待つ"], []),
    "sky & weather": (["空", "天気"], ["空模様", "自然"], ["天気予報", "季節", "外出"], ["気象", "宇宙"], ["きれい"], ["変わる"], []),
}

RULES = {
    "globe": (["地球"], ["丸い", "青"], ["世界", "海外"], ["グローバル"], ["壮大"], [], ["世界"]),
    "japan": (["日本"], ["地図"], ["国内旅行"], ["日本列島"], ["親しみ"], [], ["日本"]),
    "compass": (["コンパス", "方位磁針"], ["針", "方角"], ["登山", "道案内"], ["方向", "目的地"], ["実用的"], ["案内する"], []),
    "mountain": (["山"], ["高い", "岩"], ["登山", "旅行"], ["自然", "挑戦"], ["雄大"], ["登る"], []),
    "fuji": (["富士山"], ["山", "雪"], ["日本旅行", "初夢"], ["日本", "象徴"], ["美しい"], ["眺める"], ["日本"]),
    "beach": (["ビーチ", "砂浜"], ["海", "砂", "傘"], ["夏", "海水浴", "旅行"], ["リゾート"], ["爽やか"], ["休む"], []),
    "desert": (["砂漠"], ["砂", "暑い"], ["冒険", "旅行"], ["乾燥", "孤独"], ["暑い"], ["歩く"], []),
    "island": (["島", "無人島"], ["海", "ヤシ"], ["旅行", "リゾート"], ["南国"], ["のんびり"], ["休む"], []),
    "park": (["公園"], ["緑", "景色"], ["散歩", "ピクニック"], ["自然"], ["穏やか"], ["歩く"], []),
    "house": (["家", "住宅"], ["屋根", "窓"], ["暮らし", "帰宅", "家族"], ["家庭", "安心"], ["温かい"], ["住む"], []),
    "hospital": (["病院"], ["十字", "建物"], ["医療", "診察"], ["健康", "治療"], ["不安"], ["受診する"], []),
    "bank": (["銀行"], ["建物", "お金"], ["手続き", "貯金"], ["金融"], ["実用的"], ["預ける"], []),
    "school": (["学校"], ["校舎"], ["授業", "勉強"], ["教育"], ["まじめ"], ["学ぶ"], []),
    "castle": (["城"], ["塔", "石"], ["観光", "歴史"], ["王様", "物語"], ["立派"], ["訪れる"], []),
    "wedding": (["結婚式"], ["教会", "ハート"], ["結婚", "お祝い"], ["愛", "誓い"], ["幸せ"], ["祝う"], []),
    "tower": (["タワー"], ["高い", "赤"], ["観光", "東京"], ["ランドマーク"], ["わくわく"], ["眺める"], ["日本"]),
    "liberty": (["自由の女神"], ["像", "たいまつ"], ["ニューヨーク", "観光"], ["自由", "アメリカ"], ["壮大"], ["訪れる"], ["アメリカ"]),
    "church": (["教会"], ["十字架"], ["結婚式", "祈り"], ["キリスト教"], ["厳か"], ["祈る"], ["キリスト教"]),
    "mosque": (["モスク"], ["ドーム", "月"], ["礼拝", "観光"], ["イスラム教"], ["神聖"], ["祈る"], ["イスラム教"]),
    "temple": (["寺院"], ["屋根"], ["参拝", "観光"], ["信仰"], ["厳か"], ["祈る"], ["宗教"]),
    "shrine": (["神社"], ["鳥居", "赤"], ["参拝", "初詣"], ["神道", "願い"], ["厳か"], ["祈る"], ["日本", "神道"]),
    "kaaba": (["カーバ"], ["黒", "立方体"], ["巡礼", "礼拝"], ["イスラム教"], ["神聖"], ["祈る"], ["イスラム教"]),
    "sunrise": (["日の出", "朝日"], ["太陽", "空"], ["朝", "旅行"], ["始まり", "希望"], ["美しい"], ["昇る"], []),
    "sunset": (["夕日", "夕焼け"], ["赤い空", "太陽"], ["夕方", "帰り道"], ["終わり"], ["しんみり"], ["沈む"], []),
    "hot springs": (["温泉"], ["湯気", "水"], ["旅行", "入浴"], ["癒し", "和風"], ["ほっとする"], ["浸かる"], ["日本"]),
    "train": (["電車", "鉄道"], ["レール", "車両"], ["通勤", "旅行"], ["移動"], ["実用的"], ["走る"], []),
    "shinkansen": (["新幹線"], ["白", "速い"], ["旅行", "出張"], ["高速", "日本"], ["わくわく"], ["走る"], ["日本"]),
    "bus": (["バス"], ["車輪", "大きい"], ["通勤", "通学"], ["公共交通"], ["実用的"], ["乗る"], []),
    "ambulance": (["救急車"], ["赤色灯", "白"], ["救急", "病院"], ["命", "緊急"], ["不安"], ["運ぶ"], []),
    "fire engine": (["消防車"], ["赤", "サイレン"], ["消防", "火事"], ["救助", "緊急"], ["頼もしい"], ["消火する"], []),
    "police": (["パトカー", "警察"], ["赤色灯"], ["防犯", "緊急"], ["安全"], ["緊張"], ["守る"], []),
    "taxi": (["タクシー"], ["車", "黄色"], ["移動", "街"], ["便利"], ["実用的"], ["乗る"], []),
    "automobile": (["車", "自動車"], ["車輪", "正面"], ["ドライブ", "通勤"], ["移動"], ["便利"], ["走る"], []),
    "truck": (["トラック"], ["荷台", "車輪"], ["配送", "引っ越し"], ["物流"], ["実用的"], ["運ぶ"], []),
    "bicycle": (["自転車"], ["二輪", "ペダル"], ["通学", "散歩"], ["エコ", "運動"], ["爽やか"], ["こぐ"], []),
    "traffic light": (["信号"], ["赤", "青", "黄色"], ["道路", "運転"], ["交通安全"], ["実用的"], ["止まる"], []),
    "airplane": (["飛行機"], ["翼", "白"], ["空港", "海外旅行"], ["旅", "遠く"], ["わくわく"], ["飛ぶ"], []),
    "departure": (["離陸"], ["上向き"], ["出発", "空港"], ["旅立ち"], ["わくわく"], ["出発する"], []),
    "arrival": (["着陸"], ["下向き"], ["到着", "空港"], ["帰着"], ["安心"], ["到着する"], []),
    "rocket": (["ロケット"], ["炎", "宇宙"], ["宇宙", "打ち上げ"], ["挑戦", "未来"], ["わくわく"], ["飛ぶ"], []),
    "saucer": (["空飛ぶ円盤", "UFO"], ["円盤", "宇宙"], ["SF", "宇宙"], ["未知", "宇宙人"], ["不思議"], ["飛ぶ"], []),
    "moon": (["月"], ["黄色", "夜"], ["夜", "空"], ["月相", "神秘"], ["静か"], ["満ち欠けする"], []),
    "sun": (["太陽"], ["黄色", "光"], ["昼", "夏"], ["明るさ", "元気"], ["明るい"], ["照らす"], []),
    "star": (["星"], ["黄色", "きらきら"], ["夜空", "願い"], ["夢", "評価"], ["きれい"], ["光る"], []),
    "rain": (["雨"], ["水滴", "雲"], ["梅雨", "外出"], ["潤い"], ["しっとり"], ["降る"], []),
    "snow": (["雪"], ["白", "結晶"], ["冬", "寒い日"], ["寒さ"], ["きれい"], ["降る"], []),
    "lightning": (["雷"], ["稲妻", "黄色"], ["嵐", "停電"], ["衝撃", "危険"], ["怖い"], ["光る"], []),
    "cloud": (["雲"], ["白", "もくもく"], ["空", "天気"], ["曇り"], ["穏やか"], ["浮かぶ"], []),
    "rainbow": (["虹"], ["七色", "弧"], ["雨上がり", "空"], ["希望", "多様性"], ["きれい"], ["かかる"], []),
    "umbrella": (["傘"], ["柄", "雨具"], ["雨", "外出"], ["雨よけ"], ["実用的"], ["差す"], []),
    "fire": (["火", "炎"], ["赤", "熱い"], ["料理", "焚き火"], ["情熱", "危険"], ["熱い"], ["燃える"], []),
    "wave": (["波"], ["青", "水"], ["海", "夏"], ["勢い"], ["爽やか"], ["揺れる"], []),
}


def has_phrase(text, phrase):
    return bool(re.search(rf"(?<![a-z]){re.escape(phrase.lower())}(?![a-z])", text))


def add(bucket, field, values):
    bucket[field].extend(values)


def make_bucket():
    return {field: [] for field in V2_FIELDS if field != "search_ja"}


def apply_base(row, bucket):
    direct, visual, context, symbolic, emotion, action, culture = SUBCATEGORY_BASE[row["subcategory"]]
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


def apply_specific(row, bucket):
    name_en = row["name_en"].lower()
    add(bucket, "direct_ja", [row["name_ja"]])
    if row["subcategory"] == "time":
        digits = re.findall(r"\d+", row["name_ja"])
        add(bucket, "direct_ja", digits)
        add(bucket, "visual_ja", ["文字盤"])
        if "半" in row["name_ja"] or "thirty" in name_en:
            add(bucket, "direct_ja", ["半"])
            add(bucket, "symbolic_ja", ["30分"])
    for key, values in RULES.items():
        if has_phrase(name_en, key):
            direct, visual, context, symbolic, emotion, action, culture = values
            for field, terms in [
                ("direct_ja", direct),
                ("visual_ja", visual),
                ("context_ja", context),
                ("symbolic_ja", symbolic),
                ("emotion_ja", emotion),
                ("action_ja", action),
                ("culture_ja", culture),
            ]:
                add(bucket, field, terms)


def ensure_minimum(row, bucket):
    expected = {"3": 15, "2": 8, "1": 6}.get(str(row.get("importance", "")).strip(), 8)
    if len(unique(v for values in bucket.values() for v in values)) >= expected:
        return
    add(bucket, "symbolic_ja", [row["subcategory_ja"], row["category_ja"], "場所", "移動"])


def build_terms(row):
    bucket = make_bucket()
    apply_base(row, bucket)
    apply_specific(row, bucket)
    ensure_minimum(row, bucket)
    return {field: unique(values) for field, values in bucket.items()}


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
        terms = build_terms(row)
        for field in V2_FIELDS:
            if field == "search_ja":
                continue
            row[field] = join_list(terms[field])
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
