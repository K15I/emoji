import argparse
import re
from pathlib import Path

from emoji_assoc import DEFAULT_CSV, V2_FIELDS, join_list, read_rows, rebuild_search_terms, split_list, unique, write_rows


TARGET_CATEGORY = "Activities"

BASE = {
    "event": (["イベント"], ["飾り", "色"], ["お祝い", "季節行事", "パーティー"], ["記念", "祝福"], ["楽しい", "華やか"], ["祝う"], []),
    "award-medal": (["賞", "メダル"], ["金属", "丸い"], ["大会", "表彰", "スポーツ"], ["勝利", "実績"], ["誇らしい"], ["表彰する"], []),
    "sport": (["スポーツ", "競技"], ["道具", "ボール"], ["試合", "部活", "応援"], ["勝負", "運動"], ["熱い", "元気"], ["競う"], ["スポーツ"]),
    "game": (["ゲーム", "遊び"], ["おもちゃ", "記号"], ["遊び", "趣味", "パーティー"], ["運", "戦略"], ["楽しい"], ["遊ぶ"], []),
    "arts & crafts": (["芸術", "工作"], ["道具", "手作り"], ["制作", "趣味", "学校"], ["創作", "表現"], ["楽しい"], ["作る"], []),
}

RULES = {
    "jack-o-lantern": (["ハロウィンかぼちゃ"], ["オレンジ", "顔"], ["ハロウィン", "秋"], ["仮装", "怖い"], ["楽しい"], ["飾る"], ["ハロウィン"]),
    "christmas": (["クリスマスツリー"], ["緑", "星", "飾り"], ["クリスマス", "冬"], ["プレゼント"], ["わくわく"], ["飾る"], ["クリスマス"]),
    "fireworks": (["花火"], ["光", "夜空"], ["夏", "花火大会"], ["祭り"], ["きれい"], ["打ち上げる"], ["日本"]),
    "sparkler": (["線香花火"], ["火花", "手持ち"], ["夏", "花火"], ["儚さ"], ["しんみり"], ["灯す"], ["日本"]),
    "sparkles": (["きらきら"], ["光", "星"], ["装飾", "強調"], ["輝き", "魔法"], ["きれい"], ["光る"], []),
    "balloon": (["風船"], ["丸い", "カラフル"], ["誕生日", "パーティー"], ["子供"], ["楽しい"], ["膨らませる"], []),
    "party": (["クラッカー"], ["紙吹雪", "カラフル"], ["誕生日", "お祝い"], ["祝福"], ["楽しい"], ["祝う"], []),
    "confetti": (["くす玉"], ["紙吹雪", "丸い"], ["お祝い", "発表"], ["祝福"], ["華やか"], ["割る"], []),
    "tanabata": (["七夕"], ["笹", "短冊"], ["七夕", "夏"], ["願いごと", "星"], ["ロマンチック"], ["願う"], ["日本"]),
    "pine decoration": (["門松"], ["竹", "松"], ["正月", "新年"], ["縁起物"], ["めでたい"], ["飾る"], ["日本"]),
    "dolls": (["ひな祭り"], ["人形", "着物"], ["ひな祭り", "春"], ["女の子", "伝統"], ["華やか"], ["飾る"], ["日本"]),
    "carp": (["こいのぼり"], ["魚", "旗"], ["こどもの日", "春"], ["成長", "家族"], ["元気"], ["泳ぐ"], ["日本"]),
    "wind chime": (["風鈴"], ["ガラス", "短冊"], ["夏", "縁側"], ["涼しさ"], ["涼しい"], ["鳴る"], ["日本"]),
    "moon viewing": (["月見"], ["月", "すすき"], ["秋", "十五夜"], ["季節"], ["静か"], ["眺める"], ["日本"]),
    "red envelope": (["赤い封筒"], ["赤", "封筒"], ["正月", "お年玉"], ["縁起", "お金"], ["めでたい"], ["渡す"], ["中華圏"]),
    "ribbon": (["リボン"], ["結び目", "赤"], ["贈り物", "支援"], ["結ぶ", "応援"], ["かわいい"], ["結ぶ"], []),
    "gift": (["プレゼント"], ["箱", "リボン"], ["誕生日", "クリスマス"], ["贈り物", "感謝"], ["嬉しい"], ["贈る"], []),
    "ticket": (["チケット", "入場券"], ["紙", "券"], ["映画", "ライブ", "入場"], ["予約"], ["わくわく"], ["入る"], []),
    "trophy": (["トロフィー"], ["金", "杯"], ["優勝", "大会"], ["勝利", "一番"], ["誇らしい"], ["勝つ"], []),
    "1st": (["金メダル", "1位"], ["金", "丸い"], ["大会", "表彰"], ["優勝"], ["誇らしい"], ["勝つ"], []),
    "2nd": (["銀メダル", "2位"], ["銀", "丸い"], ["大会", "表彰"], ["準優勝"], ["誇らしい"], [], []),
    "3rd": (["銅メダル", "3位"], ["銅", "丸い"], ["大会", "表彰"], ["入賞"], ["誇らしい"], [], []),
    "soccer": (["サッカー"], ["白黒", "ボール"], ["試合", "ワールドカップ"], ["ゴール"], ["熱い"], ["蹴る"], []),
    "baseball": (["野球"], ["白", "ボール"], ["試合", "球場"], ["ホームラン"], ["熱い"], ["投げる"], []),
    "basketball": (["バスケットボール"], ["オレンジ", "ボール"], ["試合", "体育館"], ["シュート"], ["熱い"], ["投げる"], []),
    "rugby": (["ラグビー"], ["楕円", "ボール"], ["試合", "スタジアム"], ["タックル"], ["力強い"], ["走る"], []),
    "tennis": (["テニス"], ["黄色", "ボール"], ["試合", "コート"], ["ラリー"], ["爽やか"], ["打つ"], []),
    "bowling": (["ボウリング"], ["ピン", "ボール"], ["遊び", "デート"], ["ストライク"], ["楽しい"], ["投げる"], []),
    "golf": (["ゴルフ"], ["旗", "穴"], ["コース", "接待"], ["狙う"], ["落ち着く"], ["打つ"], []),
    "fishing": (["釣り"], ["竿", "魚"], ["海", "川", "趣味"], ["待つ"], ["のんびり"], ["釣る"], []),
    "ski": (["スキー"], ["雪", "板"], ["冬", "雪山"], ["スピード"], ["爽快"], ["滑る"], []),
    "target": (["的"], ["赤", "中心"], ["目標", "ゲーム"], ["命中", "集中"], ["楽しい"], ["狙う"], []),
    "crystal": (["水晶玉"], ["丸い", "紫"], ["占い", "未来"], ["予言", "神秘"], ["不思議"], ["占う"], ["占い"]),
    "magic wand": (["魔法の杖"], ["星", "棒"], ["魔法", "創作"], ["変身"], ["わくわく"], ["魔法をかける"], []),
    "video game": (["テレビゲーム"], ["コントローラー"], ["ゲーム", "配信"], ["遊び"], ["楽しい"], ["遊ぶ"], []),
    "die": (["サイコロ"], ["立方体", "数字"], ["ボードゲーム"], ["運", "確率"], ["楽しい"], ["振る"], []),
    "puzzle": (["ジグソーパズル"], ["ピース"], ["遊び", "学習"], ["解決", "組み合わせ"], ["集中"], ["解く"], []),
    "bear": (["テディベア"], ["ぬいぐるみ", "茶色"], ["子供", "プレゼント"], ["安心"], ["かわいい"], ["抱く"], []),
    "heart suit": (["ハート"], ["赤", "カード"], ["トランプ", "恋愛"], ["愛"], ["かわいい"], [], []),
    "mahjong": (["麻雀"], ["牌", "赤"], ["ゲーム", "卓"], ["勝負"], ["集中"], ["打つ"], ["中国"]),
    "flower playing": (["花札"], ["カード", "花"], ["ゲーム", "正月"], ["伝統"], ["渋い"], ["遊ぶ"], ["日本"]),
    "performing": (["舞台芸術"], ["仮面"], ["劇場", "演劇"], ["表現"], ["ドラマチック"], ["演じる"], []),
    "picture": (["額入りの絵"], ["額縁", "絵"], ["美術館", "部屋"], ["芸術"], ["きれい"], ["飾る"], []),
    "palette": (["絵の具パレット"], ["絵の具", "色"], ["絵画", "美術"], ["創作"], ["楽しい"], ["描く"], []),
    "thread": (["糸"], ["細い", "巻き"], ["裁縫", "手芸"], ["つながり"], ["実用的"], ["縫う"], []),
    "needle": (["縫い針"], ["針", "細い"], ["裁縫", "修理"], ["手作り"], ["集中"], ["縫う"], []),
    "yarn": (["毛糸"], ["ふわふわ", "巻き"], ["編み物", "冬"], ["手作り"], ["温かい"], ["編む"], []),
    "knot": (["結び目"], ["ひも", "結び"], ["工作", "ロープ"], ["つながり", "約束"], ["実用的"], ["結ぶ"], []),
}


def has_phrase(text, phrase):
    return bool(re.search(rf"(?<![a-z]){re.escape(phrase.lower())}(?![a-z])", text))


def add(bucket, field, values):
    bucket[field].extend(values)


def make_bucket():
    return {field: [] for field in V2_FIELDS if field != "search_ja"}


def apply_terms(row, bucket):
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
    name_en = row["name_en"].lower()
    for key, values in RULES.items():
        if has_phrase(name_en, key):
            for field, terms in zip(bucket.keys(), values):
                add(bucket, field, terms)


def ensure_minimum(row, bucket):
    expected = {"3": 15, "2": 8, "1": 6}.get(str(row.get("importance", "")).strip(), 8)
    if len(unique(v for values in bucket.values() for v in values)) < expected:
        add(bucket, "symbolic_ja", [row["subcategory_ja"], row["category_ja"], "趣味", "遊び"])


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
        apply_terms(row, bucket)
        ensure_minimum(row, bucket)
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
