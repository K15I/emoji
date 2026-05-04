import argparse
import csv
import re
from pathlib import Path


CSV_PATH = Path("data/emoji_enriched.csv")

EXACT_NAMES = {
    "A button (blood type)": "A型ボタン",
    "B button (blood type)": "B型ボタン",
    "O button (blood type)": "O型ボタン",
    "P button": "Pボタン",
    "SOS button": "SOSボタン",
    "BACK arrow": "戻る矢印",
    "END arrow": "終了矢印",
    "ON! arrow": "ON矢印",
    "SOON arrow": "もうすぐ矢印",
    "Japanese “congratulations” button": "祝ボタン",
    "Japanese “monthly amount” button": "月ボタン",
    "Japanese “secret” button": "秘ボタン",
    "Japanese “service charge” button": "サービスボタン",
    "admission tickets": "入場券",
    "alembic": "蒸留器",
    "atom symbol": "原子記号",
    "balance scale": "天秤",
    "ballot box with ballot": "投票箱",
    "beach with umbrella": "ビーチパラソル",
    "bed": "ベッド",
    "bellhop bell": "ベル",
    "biohazard": "バイオハザード",
    "black medium square": "黒い四角",
    "black small square": "小さい黒四角",
    "black nib": "ペン先",
    "broken chain": "切れた鎖",
    "building construction": "工事中の建物",
    "camping": "キャンプ",
    "candle": "ろうそく",
    "card file box": "カードボックス",
    "card index dividers": "カード見出し",
    "chains": "鎖",
    "check box with check": "チェックボックス",
    "check mark": "チェックマーク",
    "chess pawn": "チェスの駒",
    "chipmunk": "シマリス",
    "circled M": "丸囲みM",
    "cityscape": "街並み",
    "clamp": "クランプ",
    "classical building": "古典的な建物",
    "cloud": "雲",
    "cloud with lightning": "雷雲",
    "cloud with lightning and rain": "雷雨",
    "cloud with rain": "雨雲",
    "cloud with snow": "雪雲",
    "club suit": "クラブ",
    "coffin": "棺",
    "comet": "彗星",
    "computer mouse": "マウス",
    "control knobs": "操作つまみ",
    "copyright": "著作権マーク",
    "couch and lamp": "ソファとランプ",
    "crossed swords": "交差した剣",
    "dagger": "短剣",
    "down arrow": "下矢印",
    "down-left arrow": "左下矢印",
    "down-right arrow": "右下矢印",
    "fog": "霧",
    "gear": "歯車",
    "hammer and pick": "ハンマーとつるはし",
    "hammer and wrench": "ハンマーとレンチ",
    "information": "案内",
    "left arrow": "左矢印",
    "left arrow curving right": "右へ曲がる左矢印",
    "left-right arrow": "左右矢印",
    "pick": "つるはし",
    "polar bear": "シロクマ",
    "right arrow": "右矢印",
    "right arrow curving down": "下へ曲がる右矢印",
    "right arrow curving left": "左へ曲がる右矢印",
    "right arrow curving up": "上へ曲がる右矢印",
    "shield": "盾",
    "snowflake": "雪の結晶",
    "snowman": "雪だるま",
    "sun behind large cloud": "太陽と大きな雲",
    "sun behind rain cloud": "太陽と雨雲",
    "sun behind small cloud": "太陽と小さな雲",
    "thermometer": "温度計",
    "tornado": "竜巻",
    "umbrella": "傘",
    "umbrella on ground": "ビーチパラソル",
    "up arrow": "上矢印",
    "up-down arrow": "上下矢印",
    "up-left arrow": "左上矢印",
    "up-right arrow": "右上矢印",
    "wind face": "風の顔",
    "shamrock": "クローバー",
    "shinto shrine": "神社",
    "shopping bags": "買い物袋",
    "skier": "スキー",
    "skull and crossbones": "ドクロ",
    "small airplane": "小型飛行機",
    "smiling face": "ほほえみ",
    "snow-capped mountain": "雪山",
    "spade suit": "スペード",
    "sparkle": "きらめき",
    "speaking head": "話す人",
    "spider": "クモ",
    "spider web": "クモの巣",
    "spiral calendar": "リングカレンダー",
    "spiral notepad": "リングメモ",
    "stadium": "スタジアム",
    "star and crescent": "星と三日月",
    "star of David": "ダビデの星",
    "stop button": "停止ボタン",
    "stopwatch": "ストップウォッチ",
    "studio microphone": "スタジオマイク",
    "sunglasses": "サングラス",
    "telephone": "電話",
    "timer clock": "タイマー",
    "trackball": "トラックボール",
    "trade mark": "商標",
    "transgender flag": "トランスジェンダーの旗",
    "transgender symbol": "トランスジェンダー記号",
    "victory hand": "ピース",
    "warning": "警告",
    "wastebasket": "ごみ箱",
    "wavy dash": "波線",
    "wheel of dharma": "法輪",
    "white flag": "白旗",
    "white medium square": "白い四角",
    "white small square": "小さい白四角",
    "world map": "世界地図",
    "writing hand": "書く手",
    "yin yang": "陰陽",
    "crayon": "クレヨン",
    "derelict house": "廃屋",
    "desert": "砂漠",
    "desert island": "無人島",
    "desktop computer": "デスクトップPC",
    "diamond suit": "ダイヤ",
    "double exclamation mark": "二重感嘆符",
    "dove": "ハト",
    "eight-pointed star": "八芒星",
    "eight-spoked asterisk": "アスタリスク",
    "eject button": "取り出しボタン",
    "envelope": "封筒",
    "exclamation question mark": "感嘆疑問符",
    "eye": "目",
    "eye in speech bubble": "吹き出しの目",
    "face in clouds": "雲の中の顔",
    "female sign": "女性記号",
    "ferry": "フェリー",
    "file cabinet": "ファイルキャビネット",
    "film frames": "フィルム",
    "film projector": "映写機",
    "fleur-de-lis": "フルール・ド・リス",
    "fork and knife with plate": "皿とナイフとフォーク",
    "fountain pen": "万年筆",
    "framed picture": "額入りの絵",
    "frowning face": "しかめ顔",
    "funeral urn": "骨壺",
    "hand with fingers splayed": "開いた手",
    "head shaking horizontally": "首を横に振る顔",
    "head shaking vertically": "うなずく顔",
    "heart exclamation": "ハート感嘆符",
    "heart on fire": "燃えるハート",
    "heart suit": "ハート",
    "hole": "穴",
    "hot pepper": "唐辛子",
    "hot springs": "温泉",
    "houses": "住宅街",
    "ice skate": "アイススケート",
    "index pointing up": "上を指す手",
    "infinity": "無限大",
    "joystick": "ジョイスティック",
    "keyboard": "キーボード",
    "label": "ラベル",
    "last track button": "前の曲ボタン",
    "latin cross": "十字架",
    "left speech bubble": "左吹き出し",
    "level slider": "音量スライダー",
    "linked paperclips": "つながったクリップ",
    "male sign": "男性記号",
    "mantelpiece clock": "置き時計",
    "medical symbol": "医療記号",
    "mending heart": "修復中のハート",
    "mermaid": "人魚",
    "merman": "人魚",
    "military medal": "勲章",
    "motor boat": "モーターボート",
    "motorcycle": "バイク",
    "motorway": "高速道路",
    "mountain": "山",
    "multiply": "掛け算",
    "national park": "国立公園",
    "next track button": "次の曲ボタン",
    "oil drum": "ドラム缶",
    "old key": "古い鍵",
    "om": "オーム",
    "orthodox cross": "正教会の十字架",
    "paintbrush": "絵筆",
    "part alternation mark": "庵点",
    "passenger ship": "客船",
    "pause button": "一時停止ボタン",
    "peace symbol": "ピースマーク",
    "pen": "ペン",
    "pencil": "鉛筆",
    "pirate flag": "海賊旗",
    "play button": "再生ボタン",
    "play or pause button": "再生一時停止ボタン",
    "printer": "プリンター",
    "racing car": "レーシングカー",
    "radioactive": "放射能",
    "railway track": "線路",
    "rainbow flag": "虹色の旗",
    "record button": "録音ボタン",
    "recycling symbol": "リサイクルマーク",
    "registered": "登録商標",
    "reminder ribbon": "リボン",
    "rescue worker’s helmet": "救助ヘルメット",
    "reverse button": "逆再生ボタン",
    "right anger bubble": "怒りの吹き出し",
    "rolled-up newspaper": "丸めた新聞",
    "rosette": "ロゼット",
    "satellite": "人工衛星",
    "scissors": "はさみ",
}

PHRASE_NAMES = {
    "couple with heart": "ハートのカップル",
    "kiss": "キスするカップル",
    "family": "家族",
    "health worker": "医療従事者",
    "judge": "裁判官",
    "construction worker": "建設作業員",
    "detective": "探偵",
    "police officer": "警察官",
    "guard": "警備員",
    "ninja": "忍者",
    "farmer": "農家",
    "cook": "料理人",
    "student": "学生",
    "singer": "歌手",
    "artist": "アーティスト",
    "teacher": "教師",
    "factory worker": "工場作業員",
    "technologist": "技術者",
    "office worker": "会社員",
    "mechanic": "整備士",
    "scientist": "科学者",
    "astronaut": "宇宙飛行士",
    "firefighter": "消防士",
    "pilot": "パイロット",
    "climbing": "クライミング",
    "getting haircut": "ヘアカット",
    "getting massage": "マッサージ",
    "in manual wheelchair": "車椅子",
    "in motorized wheelchair": "電動車椅子",
    "walking": "歩く人",
    "running": "走る人",
    "kneeling": "ひざまずく人",
    "with white cane": "白杖の人",
    "deaf": "耳の不自由な人",
    "bowing": "お辞儀",
    "facepalming": "頭を抱える人",
    "frowning": "困った顔の人",
    "gesturing NO": "NGジェスチャー",
    "gesturing OK": "OKジェスチャー",
    "pouting": "不満そうな人",
    "raising hand": "手を挙げる人",
    "shrugging": "肩をすくめる人",
    "tipping hand": "案内する人",
    "in steamy room": "サウナ",
    "in tuxedo": "タキシードの人",
    "standing": "立つ人",
    "wearing turban": "ターバンの人",
    "with veil": "ベールの人",
    "beard": "ひげの人",
    "blond hair": "金髪の人",
    "with bunny ears": "バニーの人",
    "wrestling": "レスリング",
    "in suit levitating": "浮かぶスーツの人",
    "biking": "自転車",
    "bouncing ball": "ボール遊び",
    "cartwheeling": "側転",
    "golfing": "ゴルフ",
    "handball": "ハンドボール",
    "juggling": "ジャグリング",
    "lifting weights": "重量挙げ",
    "mountain biking": "マウンテンバイク",
    "playing water polo": "水球",
    "rowing boat": "ボート",
    "surfing": "サーフィン",
    "swimming": "水泳",
    "in lotus position": "座禅",
    "fairy": "妖精",
    "mage": "魔法使い",
    "merperson": "人魚",
    "vampire": "吸血鬼",
    "zombie": "ゾンビ",
    "genie": "ランプの精",
    "elf": "エルフ",
    "superhero": "スーパーヒーロー",
    "supervillain": "悪役",
}

DROP_PARTS = [
    "dark skin tone",
    "light skin tone",
    "medium skin tone",
    "medium-dark skin tone",
    "medium-light skin tone",
    "facing right",
    "man",
    "woman",
    "person",
]


def normalize_english_name(name):
    if "beard" in name:
        return "beard"
    if "blond hair" in name:
        return "blond hair"
    base = name.split(":", 1)[0].strip()
    base = re.sub(r"\b(man|woman|person|men|women|people)\b", "", base)
    base = base.replace(" facing right", "")
    return re.sub(r"\s+", " ", base).strip()


def translate_name(name):
    if name.startswith("keycap: "):
        return f"{name.split(': ', 1)[1]}キー"
    if name in EXACT_NAMES:
        return EXACT_NAMES[name]

    base = normalize_english_name(name)
    if base in EXACT_NAMES:
        return EXACT_NAMES[base]

    lowered = base.lower()
    for phrase, translated in sorted(PHRASE_NAMES.items(), key=lambda item: len(item[0]), reverse=True):
        if phrase.lower() in lowered:
            return translated

    cleaned = lowered
    for part in DROP_PARTS:
        cleaned = cleaned.replace(part, "")
    cleaned = re.sub(r"[,:\s]+", " ", cleaned).strip()
    return EXACT_NAMES.get(cleaned, "")


def still_english(value):
    if re.search(r"[ぁ-んァ-ン一-龥]", value):
        return False
    return bool(re.search(r"[a-zA-Z]{2,}", value))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=CSV_PATH)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    with args.csv.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    changed = 0
    simplified = 0
    unresolved = 0
    for row in rows:
        if row.get("subcategory", "").startswith("animal-") and row.get("name_ja", "").endswith("の顔"):
            row["name_ja"] = row["name_ja"][:-2]
            simplified += 1
        if row.get("en_flag") != "1":
            continue
        translated = translate_name(row["name_en"])
        if translated:
            row["name_ja"] = translated
            row["en_flag"] = "1" if still_english(translated) else ""
            changed += 1
        if row.get("en_flag") == "1":
            unresolved += 1

    output = args.output or args.csv
    with output.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated {changed} English display names in {output}")
    print(f"Simplified {simplified} animal display names in {output}")
    print(f"Remaining en_flag=1 rows: {unresolved}")


if __name__ == "__main__":
    main()
