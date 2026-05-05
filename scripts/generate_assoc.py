import argparse
import csv
import re
from pathlib import Path


DEFAULT_CSV = Path("data/emoji_enriched_re.csv")

LIMITS = {"1": 12, "2": 16, "3": 20}
TARGETS = {"1": 6, "2": 9, "3": 15}
MIN_TAGS = 7

NOISE = {
    "顔文字と感情", "人と体", "動物と自然", "食べ物と飲み物", "旅行と場所",
    "活動", "物", "記号", "旗", "会話向き", "自己紹介", "親しみ", "日常",
    "実用的", "中立", "活動的",
    "開けて口", "当て", "ぞき見る顔", "垂ら", "付け", "ひら", "揃え",
    "つむり",
}

KEEP_LONG = {
    "誕生日", "動物占い", "星座占い", "水族館", "夏休み", "推し活", "仕事終わり",
    "バレンタイン", "クリスマス", "ハロウィーン", "サファリ", "バーベキュー",
    "アクセシビリティ", "スピリチュアル",
    "かたつむり",
}

NORMALIZE = {
    "可愛い": "かわいい",
    "さわやか": "爽やか",
    "パーティ": "パーティー",
    "オッケー": "OK",
    "オーケー": "OK",
    "にこにこ": "にっこり",
    "ライオンの顔": "ライオン",
    "犬の顔": "犬",
    "猫の顔": "猫",
    "うさぎの顔": "うさぎ",
    "サルの顔": "サル",
    "クマの顔": "クマ",
    "トラの顔": "トラ",
    "カタツムリ": "かたつむり",
}

SUBCATEGORY_ASSOC = {
    "face-smiling": ["笑顔", "にっこり", "嬉しい", "楽しい", "明るい", "挨拶", "雑談"],
    "face-affection": ["好き", "愛", "ハート", "かわいい", "感謝", "推し活"],
    "face-tongue": ["冗談", "楽しい", "舌", "ふざける"],
    "face-hand": ["顔", "手", "内緒", "考える", "驚き"],
    "face-neutral-skeptical": ["考える", "無表情", "疑問", "困惑", "中立"],
    "face-sleepy": ["眠い", "疲れ", "休憩", "夜", "寝る"],
    "face-unwell": ["体調", "つらい", "病気", "疲れ", "不調"],
    "face-concerned": ["悲しい", "心配", "不安", "涙", "失敗"],
    "face-negative": ["怒り", "不満", "否定", "ぷんぷん", "強い"],
    "emotion": ["感情", "気持ち", "愛", "怒り", "涙"],
    "hand-fingers-open": ["手", "指", "挨拶", "ジェスチャー"],
    "hand-fingers-partial": ["手", "指", "OK", "ピース", "合図"],
    "hand-single-finger": ["手", "指", "指差し", "上", "注意"],
    "hand-fingers-closed": ["手", "了解", "応援", "OK", "グー"],
    "hands": ["手", "お願い", "感謝", "拍手", "祈り"],
    "person": ["人", "大人", "子供", "髪", "顔"],
    "person-gesture": ["人", "ジェスチャー", "挨拶", "お願い", "謝罪"],
    "person-role": ["人", "仕事", "職業", "作業", "専門家"],
    "person-fantasy": ["ファンタジー", "神話", "魔法", "仮装", "不思議"],
    "person-activity": ["人", "活動", "趣味", "移動", "日常"],
    "person-sport": ["スポーツ", "試合", "応援", "運動", "部活"],
    "person-resting": ["休む", "リラックス", "瞑想", "静か"],
    "family": ["家族", "親子", "子供", "カップル", "愛"],
    "animal-mammal": ["動物", "哺乳類", "動物園", "サファリ", "かわいい"],
    "animal-bird": ["動物", "鳥", "空", "自然", "朝"],
    "animal-marine": ["動物", "海", "水族館", "水", "涼しい"],
    "animal-bug": ["虫", "動物", "自然", "小さい"],
    "plant-flower": ["花", "植物", "季節", "きれい", "自然"],
    "plant-other": ["植物", "自然", "緑", "季節"],
    "food-fruit": ["果物", "食べ物", "甘い", "新鮮", "おやつ"],
    "food-vegetable": ["野菜", "食べ物", "健康", "料理"],
    "food-prepared": ["料理", "食べ物", "食事", "外食", "ご飯"],
    "food-asian": ["料理", "食べ物", "日本", "食事"],
    "food-sweet": ["甘い", "お菓子", "デザート", "かわいい"],
    "drink": ["飲み物", "休憩", "乾杯", "カフェ"],
    "place-geographic": ["場所", "自然", "旅行", "景色"],
    "place-building": ["建物", "場所", "街", "旅行"],
    "transport-ground": ["乗り物", "移動", "旅行", "通勤"],
    "transport-water": ["乗り物", "海", "船", "旅行"],
    "transport-air": ["乗り物", "空", "飛行機", "旅行"],
    "sky & weather": ["天気", "空", "季節", "外出", "自然"],
    "event": ["イベント", "お祝い", "パーティー", "季節", "楽しい"],
    "sport": ["スポーツ", "試合", "応援", "運動"],
    "game": ["ゲーム", "遊び", "趣味", "勝負"],
    "music": ["音楽", "ライブ", "趣味", "楽しい"],
    "musical-instrument": ["音楽", "楽器", "ライブ", "趣味"],
    "clothing": ["服", "ファッション", "身だしなみ"],
    "tool": ["道具", "作業", "修理", "仕事"],
    "office": ["仕事", "文房具", "作業", "整理"],
    "medical": ["医療", "病院", "体調", "健康"],
    "zodiac": ["星座", "占い", "運勢", "スピリチュアル"],
    "country-flag": ["旗", "国", "地域"],
    "flag": ["旗", "国", "地域"],
    "arrow": ["矢印", "方向", "案内"],
    "keycap": ["キー", "数字", "ボタン"],
    "geometric": ["図形", "形", "色"],
}

SUBCATEGORY_PREFIX_ASSOC = {
    "face-": ["表情", "顔", "リアクション"],
    "hand-": ["手", "指", "合図"],
    "person": ["人", "体", "服装"],
    "animal-": ["動物", "生き物", "観察"],
    "plant-": ["植物", "緑", "飾り"],
    "food-": ["食べ物", "料理", "味"],
    "place-": ["場所", "景色", "地図"],
    "transport-": ["乗り物", "交通", "通勤"],
    "sky": ["空", "天気", "景色"],
    "sport": ["スポーツ", "試合", "部活"],
    "game": ["ゲーム", "勝負", "休日"],
    "arts": ["芸術", "創作", "作品"],
    "clothing": ["服", "ファッション", "外出"],
    "sound": ["音", "通知", "メディア"],
    "phone": ["通信", "スマホ", "連絡"],
    "computer": ["パソコン", "作業", "通信"],
    "book": ["本", "学習", "知識"],
    "money": ["お金", "買い物", "支払い"],
    "mail": ["メール", "連絡", "手紙"],
    "writing": ["文房具", "書く", "記録"],
    "tool": ["道具", "修理", "便利"],
    "science": ["科学", "実験", "研究"],
    "medical": ["医療", "健康", "ケア"],
    "household": ["日用品", "掃除", "家"],
    "warning": ["注意", "危険", "警告"],
    "arrow": ["矢印", "方向", "操作"],
    "av-symbol": ["再生", "停止", "操作"],
    "zodiac": ["星座", "占い", "運勢", "スピリチュアル", "誕生日"],
    "flag": ["国", "地域", "海外"],
}

EN_WORD_ASSOC = {
    "grinning": ["笑顔", "にっこり"],
    "smiling": ["笑顔", "にっこり"],
    "laughing": ["笑う", "爆笑"],
    "joy": ["嬉しい", "涙"],
    "heart": ["ハート", "愛", "好き"],
    "exclamation": ["感嘆符", "!", "びっくり", "ビックリ", "強調", "注意"],
    "question": ["疑問符", "?", "はてな", "質問", "疑問"],
    "asterisk": ["アスタリスク", "*", "星印", "注記"],
    "plus": ["プラス", "+", "足す", "追加", "正"],
    "minus": ["マイナス", "-", "引く", "減る", "負"],
    "multiply": ["かけ算", "×", "掛ける", "計算"],
    "divide": ["割り算", "÷", "割る", "計算"],
    "check": ["チェック", "確認", "OK", "完了"],
    "cross": ["バツ", "禁止", "違う", "キャンセル"],
    "dharma": ["法輪", "仏教", "インド", "円", "車輪", "宗教"],
    "wheel": ["車輪", "円", "回る"],
    "crying": ["泣く", "悲しい", "涙"],
    "angry": ["怒り", "不満"],
    "cat": ["猫", "動物"],
    "dog": ["犬", "動物"],
    "lion": ["ライオン", "百獣の王", "獅子座", "動物占い"],
    "tiger": ["トラ", "動物", "寅年", "動物占い"],
    "rabbit": ["うさぎ", "動物", "卯年"],
    "monkey": ["サル", "動物", "申年", "動物占い"],
    "horse": ["馬", "動物", "午年"],
    "snake": ["蛇", "動物", "巳年"],
    "dragon": ["龍", "干支", "辰年"],
    "fish": ["魚", "海", "魚座"],
    "bird": ["鳥", "空", "自然"],
    "flower": ["花", "植物", "きれい"],
    "sun": ["太陽", "晴れ", "明るい"],
    "moon": ["月", "夜", "静か"],
    "star": ["星", "きらきら", "夜"],
    "rain": ["雨", "天気", "しっとり"],
    "snow": ["雪", "冬", "寒い"],
    "fire": ["火", "熱い", "情熱"],
    "water": ["水", "涼しい"],
    "party": ["パーティー", "お祝い", "楽しい"],
    "birthday": ["誕生日", "お祝い"],
    "cake": ["ケーキ", "甘い", "誕生日"],
    "beer": ["ビール", "乾杯", "飲み会"],
    "coffee": ["コーヒー", "休憩", "カフェ"],
    "car": ["車", "移動", "旅行"],
    "automobile": ["車", "移動", "道路", "ドライブ"],
    "airplane": ["飛行機", "旅行", "空"],
    "house": ["家", "安心"],
    "flag": ["旗", "国"],
    "rugby": ["ラグビー", "ボール", "楕円", "茶色", "スポーツ", "試合"],
    "football": ["フットボール", "ボール", "楕円", "スポーツ", "試合"],
    "train": ["電車", "鉄道", "駅", "移動", "速い"],
    "shinkansen": ["新幹線", "電車", "鉄道", "速い", "旅行", "出張"],
    "bullet": ["新幹線", "速い", "電車", "鉄道"],
    "rocket": ["ロケット", "宇宙", "速い", "発射", "勢い"],
    "comet": ["彗星", "宇宙", "尾", "流れ星", "速い"],
    "cloud": ["雲", "空", "白い", "ふわふわ"],
    "feather": ["羽", "軽い", "ふわふわ", "鳥"],
    "bubble": ["泡", "丸い", "ふわふわ", "水"],
    "sparkles": ["きらきら", "光", "輝き", "かわいい"],
    "star": ["星", "きらきら", "夜", "光"],
    "circle": ["丸", "円", "丸い", "図形"],
    "square": ["四角", "四角い", "図形"],
    "triangle": ["三角", "三角形", "図形"],
    "diamond": ["ひし形", "宝石", "きらきら", "図形"],
    "egg": ["卵", "楕円", "白い", "料理"],
    "pill": ["薬", "カプセル", "楕円", "医療"],
    "mouse": ["マウス", "小さい", "灰色", "動物", "パソコン"],
    "snail": ["カタツムリ", "ゆっくり", "ぐるぐる", "雨"],
    "turtle": ["亀", "ゆっくり", "長寿", "動物"],
    "wave": ["波", "海", "ざぶざぶ", "水"],
    "wind": ["風", "そよそよ", "涼しい", "天気"],
    "sweat": ["汗", "あせあせ", "焦る", "暑い"],
    "sleeping": ["眠い", "すやすや", "寝る", "夜"],
    "dizzy": ["くらくら", "目が回る", "混乱"],
    "ball": ["ボール", "丸い", "スポーツ", "遊び"],
    "basketball": ["バスケットボール", "ボール", "丸い", "オレンジ", "スポーツ"],
    "soccer": ["サッカー", "ボール", "丸い", "スポーツ", "試合"],
    "baseball": ["野球", "ボール", "白い", "スポーツ", "試合"],
    "tennis": ["テニス", "ボール", "黄色", "スポーツ", "試合"],
    "volleyball": ["バレーボール", "ボール", "丸い", "スポーツ", "試合"],
    "bowling": ["ボウリング", "ボール", "丸い", "重い", "遊び"],
    "yo": ["ヨーヨー", "丸い", "遊び", "おもちゃ"],
    "kite": ["凧", "空", "風", "ひらひら", "遊び"],
    "boomerang": ["ブーメラン", "曲がる", "投げる", "遊び"],
    "skateboard": ["スケートボード", "板", "滑る", "遊び"],
    "sled": ["そり", "雪", "滑る", "冬"],
    "bicycle": ["自転車", "移動", "乗り物", "ペダル"],
    "bus": ["バス", "乗り物", "移動", "道路"],
    "taxi": ["タクシー", "車", "移動", "黄色"],
    "motorcycle": ["バイク", "乗り物", "速い", "道路"],
    "boat": ["船", "海", "水", "移動"],
    "ship": ["船", "海", "水", "移動"],
    "anchor": ["いかり", "船", "海", "重い"],
    "mountain": ["山", "自然", "高い", "三角"],
    "volcano": ["火山", "山", "噴火", "熱い"],
    "desert": ["砂漠", "暑い", "乾燥", "砂"],
    "island": ["島", "海", "旅行", "南国"],
    "rainbow": ["虹", "カラフル", "空", "雨上がり"],
    "lightning": ["雷", "ぴかぴか", "光", "怖い"],
    "tornado": ["竜巻", "ぐるぐる", "風", "危険"],
    "umbrella": ["傘", "雨", "濡れる", "外出"],
    "leaf": ["葉", "緑", "ひらひら", "自然"],
    "maple": ["もみじ", "秋", "赤い", "葉"],
    "cherry": ["さくらんぼ", "赤い", "丸い", "甘い"],
    "rose": ["バラ", "花", "赤い", "恋愛"],
    "tulip": ["チューリップ", "花", "春", "かわいい"],
    "mushroom": ["きのこ", "森", "秋", "丸い"],
    "cactus": ["サボテン", "とげとげ", "砂漠", "緑"],
    "bread": ["パン", "朝食", "茶色", "ふわふわ"],
    "cheese": ["チーズ", "黄色", "食べ物", "とろける"],
    "meat": ["肉", "茶色", "料理", "焼く"],
    "rice": ["ご飯", "白い", "食事", "日本"],
    "noodle": ["麺", "細長い", "料理", "食事"],
    "spaghetti": ["パスタ", "麺", "細長い", "料理"],
    "popcorn": ["ポップコーン", "映画", "軽い", "ぽこぽこ"],
    "candy": ["キャンディ", "甘い", "かわいい", "カラフル"],
    "lollipop": ["キャンディ", "甘い", "丸い", "ぺろぺろ"],
    "ice": ["氷", "冷たい", "つるつる", "透明"],
    "magnet": ["磁石", "くっつく", "赤青", "理科"],
    "gear": ["歯車", "設定", "機械", "ぐるぐる"],
    "chain": ["鎖", "つながる", "金属", "リンク"],
    "bell": ["ベル", "通知", "音", "りんりん"],
    "hourglass": ["砂時計", "時間", "砂", "待つ"],
    "clock": ["時計", "時間", "予定", "待つ"],
}

JA_CONCEPT_ASSOC = {
    "ラグビー": ["楕円", "茶色", "ボール", "スポーツ", "試合"],
    "フットボール": ["楕円", "茶色", "ボール", "スポーツ", "試合"],
    "新幹線": ["速い", "電車", "鉄道", "旅行", "出張"],
    "電車": ["鉄道", "駅", "移動", "通勤", "速い"],
    "ロケット": ["宇宙", "速い", "発射", "勢い"],
    "彗星": ["宇宙", "尾", "流れ星", "速い"],
    "雲": ["白い", "ふわふわ", "空", "天気"],
    "羽": ["軽い", "ふわふわ", "鳥"],
    "泡": ["丸い", "ふわふわ", "水"],
    "星": ["きらきら", "光", "夜"],
    "雪": ["白い", "ふわふわ", "冬", "寒い"],
    "火": ["めらめら", "熱い", "赤い", "勢い"],
    "水": ["さらさら", "涼しい", "透明"],
    "波": ["ざぶざぶ", "海", "水"],
    "風": ["そよそよ", "涼しい", "天気"],
    "汗": ["あせあせ", "焦る", "暑い"],
    "涙": ["ぽろぽろ", "しくしく", "悲しい"],
    "眠": ["すやすや", "夜", "休む"],
    "怒": ["ぷんぷん", "いらいら", "強い"],
    "笑": ["にこにこ", "げらげら", "楽しい"],
    "猫": ["にゃんにゃん", "かわいい", "動物"],
    "犬": ["わんわん", "かわいい", "動物"],
    "カタツムリ": ["ゆっくり", "ぐるぐる", "雨"],
    "かたつむり": ["ゆっくり", "ぐるぐる", "雨"],
    "亀": ["ゆっくり", "長寿", "動物"],
    "卵": ["楕円", "白い", "料理"],
    "薬": ["カプセル", "楕円", "医療"],
    "丸": ["円", "丸い", "図形"],
    "四角": ["四角い", "図形"],
    "三角": ["三角形", "図形"],
    "ひし形": ["図形", "きらきら"],
    "ボール": ["丸い", "スポーツ", "遊び"],
    "バスケット": ["丸い", "オレンジ", "スポーツ"],
    "サッカー": ["丸い", "白黒", "スポーツ"],
    "野球": ["白い", "ボール", "スポーツ"],
    "テニス": ["黄色", "ボール", "スポーツ"],
    "ボウリング": ["丸い", "重い", "遊び"],
    "凧": ["空", "風", "ひらひら"],
    "ブーメラン": ["曲がる", "投げる", "遊び"],
    "スケートボード": ["板", "滑る", "遊び"],
    "そり": ["雪", "滑る", "冬"],
    "自転車": ["移動", "乗り物", "ペダル"],
    "バス": ["乗り物", "移動", "道路"],
    "タクシー": ["車", "移動", "黄色"],
    "バイク": ["乗り物", "速い", "道路"],
    "船": ["海", "水", "移動"],
    "いかり": ["船", "海", "重い"],
    "山": ["自然", "高い", "三角"],
    "自動車": ["車", "移動", "道路", "ドライブ"],
    "火山": ["噴火", "熱い", "山", "めらめら", "赤い"],
    "砂漠": ["暑い", "乾燥", "砂"],
    "島": ["海", "旅行", "南国"],
    "虹": ["カラフル", "空", "雨上がり"],
    "雷": ["ぴかぴか", "光", "怖い"],
    "竜巻": ["ぐるぐる", "風", "危険"],
    "傘": ["雨", "濡れる", "外出"],
    "葉": ["緑", "ひらひら", "自然"],
    "もみじ": ["秋", "赤い", "葉"],
    "さくらんぼ": ["赤い", "丸い", "甘い"],
    "バラ": ["花", "赤い", "恋愛"],
    "チューリップ": ["花", "春", "かわいい"],
    "きのこ": ["森", "秋", "丸い"],
    "サボテン": ["とげとげ", "砂漠", "緑"],
    "パン": ["朝食", "茶色", "ふわふわ"],
    "チーズ": ["黄色", "とろける", "食べ物"],
    "肉": ["茶色", "料理", "焼く"],
    "ご飯": ["白い", "食事", "日本"],
    "麺": ["細長い", "料理", "食事"],
    "パスタ": ["麺", "細長い", "料理"],
    "ポップコーン": ["映画", "軽い", "ぽこぽこ"],
    "キャンディ": ["甘い", "かわいい", "カラフル"],
    "氷": ["冷たい", "つるつる", "透明"],
    "磁石": ["くっつく", "赤青", "理科"],
    "歯車": ["設定", "機械", "ぐるぐる"],
    "鎖": ["つながる", "金属", "リンク"],
    "ベル": ["通知", "音", "りんりん"],
    "砂時計": ["時間", "砂", "待つ"],
    "時計": ["時間", "予定", "待つ"],
    "身分証": ["カード", "本人確認", "証明", "提示", "財布", "名前", "写真"],
    "法輪": ["仏教", "インド", "円", "車輪", "宗教", "回る"],
    "感嘆符": ["!", "びっくり", "ビックリ", "強調", "注意"],
    "疑問符": ["?", "はてな", "質問", "疑問"],
    "ビックリ": ["!", "感嘆符", "驚き", "強調"],
    "はてな": ["?", "疑問符", "質問", "疑問"],
}

NUMBER_ASSOC = {
    "0": ["0", "ゼロ", "数字", "番号"],
    "1": ["1", "一", "数字", "番号"],
    "2": ["2", "二", "数字", "番号"],
    "3": ["3", "三", "数字", "番号"],
    "4": ["4", "四", "数字", "番号"],
    "5": ["5", "五", "数字", "番号"],
    "6": ["6", "六", "数字", "番号"],
    "7": ["7", "七", "数字", "番号"],
    "8": ["8", "八", "数字", "番号"],
    "9": ["9", "九", "数字", "番号"],
    "10": ["10", "十", "数字", "番号"],
}

SYMBOL_LITERAL_ASSOC = {
    "!": ["!", "びっくり", "ビックリ", "感嘆符", "強調"],
    "?": ["?", "はてな", "疑問符", "質問", "疑問"],
    "*": ["*", "アスタリスク", "星印", "注記"],
    "#": ["#", "シャープ", "番号", "ハッシュタグ"],
    "+": ["+", "プラス", "足す", "追加"],
    "-": ["-", "マイナス", "引く", "減る"],
    "×": ["×", "バツ", "かけ算", "違う"],
    "÷": ["÷", "割り算", "割る", "計算"],
}

JA_BUTTON_ASSOC = {
    "CL": ["CL", "クリア", "消す", "ボタン"],
    "COOL": ["COOL", "クール", "かっこいい", "ボタン"],
    "FREE": ["FREE", "無料", "自由", "ボタン"],
    "ID": ["ID", "身分証", "識別", "ボタン"],
    "NEW": ["NEW", "新しい", "新着", "ボタン"],
    "NG": ["NG", "ダメ", "禁止", "ボタン"],
    "OK": ["OK", "了解", "確認", "ボタン"],
    "VS": ["VS", "対戦", "比較", "ボタン"],
    "有": ["有", "あり", "有料", "存在"],
    "割": ["割", "割引", "セール", "安い"],
    "無": ["無", "無料", "なし", "空"],
    "禁": ["禁", "禁止", "ダメ", "注意"],
    "可": ["可", "OK", "許可", "可能"],
    "申": ["申", "申請", "申し込み", "受付"],
    "合": ["合", "合格", "成功", "試験"],
    "空": ["空", "空室", "空き", "予約"],
    "営": ["営", "営業", "店", "開店"],
    "満": ["満", "満室", "いっぱい", "予約"],
}

ISO_REGIONS = {
    "アジア": {
        "AF", "AM", "AZ", "BD", "BN", "BT", "CN", "GE", "HK", "ID", "IN", "IO", "JP",
        "KG", "KH", "KP", "KR", "KZ", "LA", "LK", "MM", "MN", "MO", "MV", "MY", "NP",
        "PH", "PK", "SG", "TH", "TJ", "TL", "TM", "TW", "UZ", "VN",
    },
    "中東": {
        "AE", "BH", "CY", "EG", "IL", "IQ", "IR", "JO", "KW", "LB", "OM", "PS", "QA",
        "SA", "SY", "TR", "YE",
    },
    "ヨーロッパ": {
        "AD", "AL", "AT", "AX", "BA", "BE", "BG", "BY", "CH", "CZ", "DE", "DK", "EE",
        "ES", "EU", "FI", "FO", "FR", "GB", "GG", "GI", "GR", "HR", "HU", "IE", "IM",
        "IS", "IT", "JE", "LI", "LT", "LU", "LV", "MC", "MD", "ME", "MK", "MT", "NL",
        "NO", "PL", "PT", "RO", "RS", "RU", "SE", "SI", "SJ", "SK", "SM", "UA", "VA", "XK",
    },
    "アフリカ": {
        "AO", "BF", "BI", "BJ", "BW", "CD", "CF", "CG", "CI", "CM", "CV", "DJ", "DZ",
        "EH", "ER", "ET", "GA", "GH", "GM", "GN", "GQ", "GW", "KE", "KM", "LR", "LS",
        "LY", "MA", "MG", "ML", "MR", "MU", "MW", "MZ", "NA", "NE", "NG", "RE", "RW",
        "SC", "SD", "SH", "SL", "SN", "SO", "SS", "ST", "SZ", "TD", "TG", "TN", "TZ",
        "UG", "YT", "ZA", "ZM", "ZW",
    },
    "北アメリカ": {
        "AG", "AI", "AW", "BB", "BL", "BM", "BQ", "BS", "BZ", "CA", "CR", "CU", "CW",
        "DM", "DO", "GD", "GL", "GP", "GT", "HN", "HT", "JM", "KN", "KY", "LC", "MF",
        "MQ", "MS", "MX", "NI", "PA", "PM", "PR", "SV", "SX", "TC", "TT", "US", "VC",
        "VG", "VI",
    },
    "南アメリカ": {
        "AR", "BO", "BR", "CL", "CO", "EC", "FK", "GF", "GY", "PE", "PY", "SR", "UY", "VE",
    },
    "オセアニア": {
        "AS", "AU", "CK", "FJ", "FM", "GU", "KI", "MH", "MP", "NC", "NF", "NR", "NU",
        "NZ", "PF", "PG", "PN", "PW", "SB", "TK", "TO", "TV", "UM", "VU", "WF", "WS",
    },
    "南極": {"AQ", "BV", "GS", "HM", "TF"},
}

FLAG_VISUAL_ASSOC = {
    "JP": ["日の丸", "赤い丸", "白地", "丸", "円"],
    "BD": ["赤い丸", "緑", "丸", "円"],
    "PW": ["黄色い丸", "青い旗", "丸", "円"],
    "IN": ["三色旗", "オレンジ", "白", "緑", "法輪", "アショーカチャクラ", "円", "インド"],
    "IL": ["青い旗", "白", "ダビデの星", "星", "ユダヤ教"],
    "US": ["星条旗", "星", "縞模様", "赤白青", "アメリカ"],
    "GB": ["ユニオンジャック", "十字", "赤白青", "イギリス"],
    "CA": ["カエデ", "葉", "赤白", "カナダ"],
    "BR": ["緑", "黄色", "青い丸", "星", "ブラジル"],
    "CN": ["赤い旗", "黄色い星", "星", "中国"],
    "KR": ["太極", "赤青", "白地", "韓国"],
    "TR": ["赤い旗", "三日月", "星", "トルコ"],
    "PK": ["緑", "三日月", "星", "パキスタン"],
    "SG": ["赤白", "三日月", "星", "シンガポール"],
    "MY": ["縞模様", "三日月", "星", "赤白青", "マレーシア"],
    "AU": ["青い旗", "星", "ユニオンジャック", "オーストラリア"],
    "NZ": ["青い旗", "星", "ユニオンジャック", "ニュージーランド"],
    "FR": ["三色旗", "縦縞", "青白赤", "フランス"],
    "IT": ["三色旗", "縦縞", "緑白赤", "イタリア"],
    "IE": ["三色旗", "縦縞", "緑白オレンジ", "アイルランド"],
    "DE": ["三色旗", "横縞", "黒赤黄", "ドイツ"],
    "BE": ["三色旗", "縦縞", "黒黄赤", "ベルギー"],
    "NL": ["三色旗", "横縞", "赤白青", "オランダ"],
    "LU": ["三色旗", "横縞", "赤白水色", "ルクセンブルク"],
    "RU": ["三色旗", "横縞", "白青赤", "ロシア"],
    "ES": ["赤黄赤", "横縞", "紋章", "スペイン"],
    "PT": ["緑赤", "紋章", "ポルトガル"],
    "CH": ["赤い旗", "白十字", "十字", "スイス"],
    "SE": ["青い旗", "黄色い十字", "十字", "スウェーデン"],
    "NO": ["赤い旗", "青い十字", "十字", "ノルウェー"],
    "DK": ["赤い旗", "白十字", "十字", "デンマーク"],
    "FI": ["白地", "青い十字", "十字", "フィンランド"],
    "GR": ["青白", "縞模様", "十字", "ギリシャ"],
    "SA": ["緑", "アラビア文字", "剣", "サウジアラビア"],
    "ZA": ["カラフル", "緑", "Y字", "南アフリカ"],
    "MX": ["三色旗", "縦縞", "緑白赤", "ワシ", "メキシコ"],
    "AR": ["水色白", "太陽", "アルゼンチン"],
    "UY": ["水色白", "太陽", "縞模様", "ウルグアイ"],
    "CL": ["星", "赤白青", "チリ"],
    "VN": ["赤い旗", "黄色い星", "星", "ベトナム"],
    "PH": ["太陽", "星", "赤白青", "フィリピン"],
    "TH": ["横縞", "赤白青", "タイ"],
    "ID": ["赤白", "横縞", "インドネシア"],
    "PL": ["白赤", "横縞", "ポーランド"],
    "UA": ["青黄", "横縞", "ウクライナ"],
}

ZODIAC_BY_EN = {
    "aries": ["牡羊座", "星座", "占い", "運勢"],
    "taurus": ["牡牛座", "星座", "占い", "運勢"],
    "gemini": ["双子座", "星座", "占い", "運勢"],
    "cancer": ["蟹座", "星座", "占い", "運勢"],
    "leo": ["獅子座", "星座", "占い", "運勢"],
    "virgo": ["乙女座", "星座", "占い", "運勢"],
    "libra": ["天秤座", "星座", "占い", "運勢"],
    "scorpius": ["蠍座", "星座", "占い", "運勢"],
    "sagittarius": ["射手座", "星座", "占い", "運勢"],
    "capricorn": ["山羊座", "星座", "占い", "運勢"],
    "aquarius": ["水瓶座", "星座", "占い", "運勢"],
    "pisces": ["魚座", "星座", "占い", "運勢"],
}


def split_words(value):
    return [word for word in re.findall(r"[a-z]+", value.lower()) if word]


def split_assoc(value):
    return [item for item in str(value or "").split(";") if item]


def unique(values):
    seen = set()
    result = []
    for value in values:
        value = NORMALIZE.get(str(value).strip(), str(value).strip())
        if not value or value in NOISE:
            continue
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def name_tokens(name_ja):
    clean = re.sub(r"（.*?）", "", name_ja).strip()
    if clean.endswith("の旗"):
        return [clean[: -len("の旗")]]
    values = []
    if clean in KEEP_LONG or len(clean) <= 8:
        values.append(clean)
    for suffix in ("の旗", "の顔", "する人", "の人"):
        if clean.endswith(suffix):
            base = clean[: -len(suffix)]
            if suffix == "の旗" or len(base) <= 8:
                values.append(base)
    for suffix in ("マーク", "ボタン", "キー"):
        if clean.endswith(suffix):
            base = clean[: -len(suffix)]
            if base:
                values.append(base)
    for token in re.split(r"[・、/／\s]+", clean):
        if token and token != clean:
            values.append(token)
    for token in re.split(r"の|を|から|で|した|している|して|いる|た", clean):
        token = token.strip()
        if 1 < len(token) <= 8 and token != clean:
            values.append(token)
    for token in (
        "目", "口", "手", "指", "顔", "涙", "汗", "笑顔", "帽子", "メガネ",
        "電車", "船", "飛行機", "家", "学校", "病院", "店", "本", "紙",
        "電池", "買い物", "カート", "再生", "停止", "一時停止", "リピート",
        "ジェットコースター", "トイレットペーパー", "トランスジェンダー",
    ):
        if token in clean:
            values.append(token)
    if "笑顔" in clean:
        values.append("笑顔")
    if "ハート" in clean:
        values.append("ハート")
    if "シルエット" in clean:
        values.append("シルエット")
    if "左向き" in clean:
        values.append("左向き")
    if "右向き" in clean:
        values.append("右向き")
    if "上向き" in clean:
        values.append("上向き")
    if "下向き" in clean:
        values.append("下向き")
    if not values and clean:
        values.append(clean)
    return values


def concept_matches(concept, name_ja):
    if len(concept) <= 2:
        return concept == name_ja
    return concept in name_ja


def flag_iso(emoji):
    letters = []
    for char in emoji:
        code = ord(char)
        if 0x1F1E6 <= code <= 0x1F1FF:
            letters.append(chr(code - 0x1F1E6 + ord("A")))
    if len(letters) == 2:
        return "".join(letters)
    return ""


def flag_assoc(row):
    if row.get("subcategory") not in {"country-flag", "subdivision-flag"}:
        return []
    values = ["国旗", "旗", "国", "地域"]
    iso = flag_iso(row.get("emoji", ""))
    for region, codes in ISO_REGIONS.items():
        if iso in codes:
            values.append(region)
    if iso:
        values.append(iso)
        values.extend(FLAG_VISUAL_ASSOC.get(iso, []))
    values.extend(["海外", "地図", "旅行"])
    return values


def number_assoc(row):
    text = " ".join([row.get("name_en", ""), row.get("name_ja", ""), row.get("emoji", "")])
    literal_text = " ".join([row.get("name_ja", ""), row.get("emoji", "")])
    values = []
    for number, assoc in NUMBER_ASSOC.items():
        if re.search(rf"(?<!\d){re.escape(number)}(?!\d)", text):
            values.extend(assoc)
    for char, assoc in SYMBOL_LITERAL_ASSOC.items():
        if char in literal_text:
            values.extend(assoc)
    if row.get("subcategory") in {"keycap", "alphanum"} and values:
        values.extend(["入力", "ボタン", "文字"])
    if row.get("subcategory") == "alphanum":
        clean = row.get("name_ja", "")
        label = re.sub(r"(マーク|ボタン|キー)$", "", clean)
        if label in JA_BUTTON_ASSOC:
            values.extend(JA_BUTTON_ASSOC[label])
    return values


def compact(values, limit):
    values = unique(values)
    kept = []
    for value in values:
        drop = False
        for other in values:
            if value == other or value in KEEP_LONG:
                continue
            if other in KEEP_LONG:
                continue
            if len(other) >= 2 and len(other) < len(value) and other in value:
                drop = True
                break
        if not drop:
            kept.append(value)
    return kept[:limit]


def fallback_assoc(row):
    values = []
    subcategory = row.get("subcategory", "")
    for prefix, assoc in SUBCATEGORY_PREFIX_ASSOC.items():
        if subcategory.startswith(prefix) or subcategory == prefix:
            values.extend(assoc)
    return values


def minimum_assoc(row):
    values = []
    subcategory = row.get("subcategory", "")
    values.extend(SUBCATEGORY_ASSOC.get(subcategory, []))
    values.extend(fallback_assoc(row))
    values.extend(flag_assoc(row))
    values.extend(number_assoc(row))
    if subcategory in {"heart"}:
        values.extend(["ハート", "愛", "好き", "恋愛", "気持ち", "かわいい", "赤い"])
    elif subcategory in {"punctuation", "other-symbol", "math"}:
        values.extend(["記号", "入力", "意味", "表示", "変換", "マーク", "強調"])
    elif subcategory in {"alphanum"}:
        values.extend(["入力", "文字", "英字", "日本語", "ボタン", "マーク", "表示", "変換"])
    elif subcategory in {"religion", "place-religious"}:
        values.extend(["宗教", "祈り", "信仰", "文化", "シンボル", "寺院", "歴史"])
    elif subcategory in {"time"}:
        values.extend(["時間", "時計", "予定", "待つ", "数字", "朝", "夜"])
    elif subcategory in {"body-parts"}:
        values.extend(["体", "人", "部位", "健康", "動き", "触る", "見る"])
    elif subcategory in {"light & video"}:
        values.extend(["光", "映像", "明るい", "照らす", "カメラ", "映画", "メディア"])
    elif subcategory in {"sound"}:
        values.extend(["音", "通知", "聞く", "鳴る", "音量", "メディア", "りんりん"])
    elif subcategory in {"other-object"}:
        values.extend(["物", "道具", "生活", "使う", "持ち物", "便利", "形"])
    elif subcategory in {"place-other"}:
        values.extend(["場所", "旅行", "遊び", "景色", "外出", "地図", "観光"])
    elif subcategory in {"transport-sign"}:
        values.extend(["標識", "道路", "交通", "案内", "注意", "移動", "街"])
    elif subcategory in {"country-flag", "subdivision-flag"}:
        values.extend(["代表", "国際", "地域名"])
    if subcategory.startswith("face-") or subcategory in {"cat-face", "monkey-face"}:
        values.extend(["表情", "顔", "感情", "リアクション", "キャラクター", "SNS", "チャット"])
    return values


def final_fill_assoc(row):
    category = row.get("category", "")
    subcategory = row.get("subcategory", "")
    if category == "Smileys & Emotion":
        return ["表情", "感情", "リアクション", "SNS", "チャット", "気持ち", "絵文字"]
    if category == "People & Body":
        return ["人", "体", "動き", "ポーズ", "生活", "場面", "絵文字"]
    if category == "Animals & Nature":
        return ["自然", "生き物", "見た目", "動き", "季節", "屋外", "絵文字"]
    if category == "Food & Drink":
        return ["食べ物", "味", "食事", "料理", "店", "見た目", "絵文字"]
    if category == "Travel & Places":
        return ["場所", "移動", "外出", "景色", "地図", "観光", "絵文字"]
    if category == "Activities":
        return ["遊び", "趣味", "場面", "道具", "イベント", "休日", "絵文字"]
    if category == "Objects":
        return ["物", "道具", "用途", "場所", "形", "素材", "絵文字"]
    if category == "Symbols":
        return ["記号", "マーク", "意味", "入力", "表示", "変換", "絵文字"]
    if category == "Flags" or subcategory.endswith("flag"):
        return ["旗", "国旗", "地域", "見た目", "色", "模様", "絵文字"]
    return ["検索", "連想", "見た目", "用途", "場面", "形", "絵文字"]


def importance3_fill_assoc(row):
    category = row.get("category", "")
    subcategory = row.get("subcategory", "")
    if subcategory.startswith("face-") or subcategory in {"cat-face", "monkey-face"}:
        return ["SNS", "チャット", "返信", "スタンプ", "気持ち", "顔文字", "かわいい", "面白い", "雰囲気", "感覚"]
    if subcategory in {"heart", "emotion"}:
        return ["気持ち", "恋愛", "SNS", "チャット", "かわいい", "強調", "反応", "雰囲気", "感覚", "スタンプ", "色", "飾り"]
    if subcategory.startswith("animal-"):
        return ["生き物", "見た目", "鳴き声", "動き", "かわいい", "野生", "ペット", "図鑑", "自然", "観察", "毛", "足跡"]
    if subcategory.startswith("plant-"):
        return ["見た目", "色", "季節", "飾り", "自然", "庭", "公園", "春", "秋", "きれい", "香り", "花束"]
    if subcategory.startswith("food-") or subcategory in {"drink", "dishware"}:
        return ["味", "食感", "店", "メニュー", "食卓", "料理", "昼食", "夕食", "おやつ", "写真"]
    if subcategory.startswith("transport-"):
        return ["速い", "道路", "駅", "旅", "通勤", "出張", "乗る", "運ぶ", "遠出", "交通"]
    if subcategory.startswith("place-") or subcategory in {"sky & weather"}:
        return ["景色", "写真", "屋外", "観光", "季節", "空気", "天気", "遠く", "自然", "場所", "色", "明るさ"]
    if subcategory in {"event", "sport", "game", "music", "musical-instrument", "arts & crafts"}:
        return ["イベント", "趣味", "休日", "楽しい", "練習", "道具", "遊ぶ", "参加", "写真", "応援"]
    if category == "Objects":
        return ["用途", "場所", "素材", "形", "使う", "持つ", "置く", "生活", "道具", "便利", "カード", "確認", "保管"]
    if category == "Symbols":
        return ["入力", "表示", "意味", "変換", "案内", "強調", "状態", "操作", "マーク", "サイン"]
    return ["見た目", "用途", "場所", "形", "色", "動き", "場面", "感覚", "写真", "連想"]


def generate(row):
    importance = row.get("importance") or "2"
    limit = LIMITS.get(importance, 16)
    target = TARGETS.get(importance, 12)
    values = []
    values.extend(name_tokens(row.get("name_ja", "")))
    values.extend(SUBCATEGORY_ASSOC.get(row.get("subcategory", ""), []))
    values.extend(fallback_assoc(row))
    values.extend(flag_assoc(row))
    values.extend(number_assoc(row))

    words = split_words(row.get("name_en", ""))
    for word in words:
        values.extend(EN_WORD_ASSOC.get(word, []))
        values.extend(ZODIAC_BY_EN.get(word, []))
    name_ja = row.get("name_ja", "")
    for concept, assoc in JA_CONCEPT_ASSOC.items():
        if concept_matches(concept, name_ja):
            values.extend(assoc)

    if "skin tone" in row.get("name_en", ""):
        base = row.get("name_ja", "").split("（", 1)[0]
        values = [*name_tokens(base), "肌色違い", "バリエーション"]
        values.extend(SUBCATEGORY_ASSOC.get(row.get("subcategory", ""), []))
        values.extend(fallback_assoc(row))
        for concept, assoc in JA_CONCEPT_ASSOC.items():
            if concept_matches(concept, base):
                values.extend(assoc)
        if "medium-light skin tone" in row.get("name_en", ""):
            values.append("やや薄い肌色")
        elif "light skin tone" in row.get("name_en", ""):
            values.append("薄い肌色")
        elif "medium skin tone" in row.get("name_en", ""):
            values.append("中間の肌色")
        elif "medium-dark skin tone" in row.get("name_en", ""):
            values.append("やや濃い肌色")
        elif "dark skin tone" in row.get("name_en", ""):
            values.append("濃い肌色")
        compacted = compact(values, limit)
        if len(compacted) < MIN_TAGS:
            compacted = compact([*compacted, *minimum_assoc(row)], limit)
        if len(compacted) < MIN_TAGS:
            compacted = compact([*compacted, *final_fill_assoc(row)], limit)
        if importance == "3" and len(compacted) < TARGETS["3"]:
            compacted = compact([*compacted, *importance3_fill_assoc(row)], limit)
        return ";".join(compacted)

    if row.get("importance") == "1":
        values = [v for v in values if v not in {"かわいい", "楽しい", "明るい", "親しみ", "自然"}]

    compacted = compact(values, limit)
    if len(compacted) < target:
        compacted = compact([*compacted, *fallback_assoc(row)], limit)
    if len(compacted) < MIN_TAGS:
        compacted = compact([*compacted, *minimum_assoc(row)], limit)
    if len(compacted) < MIN_TAGS:
        compacted = compact([*compacted, *final_fill_assoc(row)], limit)
    if importance == "3" and len(compacted) < TARGETS["3"]:
        compacted = compact([*compacted, *importance3_fill_assoc(row)], limit)
    return ";".join(compacted)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    with args.csv.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    if "tag_num" not in fieldnames:
        fieldnames.append("tag_num")

    for row in rows:
        row["assoc_ja"] = generate(row)
        row["tag_num"] = str(len(split_assoc(row["assoc_ja"])))

    output = args.output or args.csv
    with output.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated compact assoc_ja for {len(rows)} rows into {output}")


if __name__ == "__main__":
    main()
