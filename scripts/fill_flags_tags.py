import argparse
from pathlib import Path

from emoji_assoc import DEFAULT_CSV, V2_FIELDS, join_list, read_rows, rebuild_search_terms, split_list, unique, write_rows


TARGET_CATEGORY = "Flags"

REGIONS = {
    "アジア": [
        "Japan", "China", "Taiwan", "Hong Kong", "Macao", "Korea", "Mongolia", "Vietnam", "Thailand",
        "Cambodia", "Laos", "Myanmar", "Malaysia", "Singapore", "Indonesia", "Philippines", "Brunei",
        "India", "Pakistan", "Bangladesh", "Sri Lanka", "Nepal", "Bhutan", "Maldives", "Afghanistan",
        "Kazakhstan", "Uzbekistan", "Kyrgyzstan", "Tajikistan", "Turkmenistan", "Armenia", "Azerbaijan",
        "Georgia", "Türkiye", "Turkey", "Cyprus", "Israel", "Palestinian", "Jordan", "Lebanon", "Syria",
        "Iraq", "Iran", "Saudi", "Kuwait", "Bahrain", "Qatar", "Emirates", "Oman", "Yemen",
    ],
    "ヨーロッパ": [
        "Andorra", "Albania", "Austria", "Belgium", "Bulgaria", "Bosnia", "Croatia", "Czech", "Denmark",
        "Estonia", "Finland", "France", "Germany", "Greece", "Hungary", "Iceland", "Ireland", "Italy",
        "Kosovo", "Latvia", "Liechtenstein", "Lithuania", "Luxembourg", "Malta", "Moldova", "Monaco",
        "Montenegro", "Netherlands", "North Macedonia", "Norway", "Poland", "Portugal", "Romania",
        "San Marino", "Serbia", "Slovakia", "Slovenia", "Spain", "Sweden", "Switzerland", "Ukraine",
        "United Kingdom", "England", "Scotland", "Wales", "Vatican", "Åland", "Faroe", "Gibraltar",
    ],
    "アフリカ": [
        "Angola", "Burkina", "Burundi", "Benin", "Botswana", "Congo", "Côte", "Cameroon", "Cape Verde",
        "Djibouti", "Algeria", "Egypt", "Western Sahara", "Eritrea", "Ethiopia", "Gabon", "Ghana",
        "Gambia", "Guinea", "Kenya", "Comoros", "Liberia", "Lesotho", "Libya", "Morocco", "Madagascar",
        "Mali", "Mauritania", "Mauritius", "Malawi", "Mozambique", "Namibia", "Niger", "Nigeria",
        "Rwanda", "Seychelles", "Sudan", "Sierra Leone", "Senegal", "Somalia", "South Africa",
        "South Sudan", "São Tomé", "Eswatini", "Chad", "Togo", "Tunisia", "Tanzania", "Uganda",
        "Zambia", "Zimbabwe", "Mayotte", "Réunion", "St. Helena", "Ascension", "Tristan",
    ],
    "北アメリカ": [
        "United States", "Canada", "Mexico", "Greenland", "Bermuda", "St. Pierre", "U.S. Outlying",
    ],
    "中央アメリカ": [
        "Belize", "Costa Rica", "El Salvador", "Guatemala", "Honduras", "Nicaragua", "Panama",
    ],
    "南アメリカ": [
        "Argentina", "Bolivia", "Brazil", "Chile", "Colombia", "Ecuador", "Falkland", "French Guiana",
        "Guyana", "Paraguay", "Peru", "Suriname", "Uruguay", "Venezuela",
    ],
    "カリブ": [
        "Antigua", "Anguilla", "Aruba", "Barbados", "Bahamas", "Curaçao", "Caribbean Netherlands",
        "Cayman", "Cuba", "Dominica", "Dominican", "Grenada", "Guadeloupe", "Haiti", "Jamaica",
        "Martinique", "Montserrat", "Puerto Rico", "St. Barth", "St. Kitts", "St. Lucia",
        "St. Martin", "St. Vincent", "Sint Maarten", "Trinidad", "Turks", "Virgin Islands",
    ],
    "オセアニア": [
        "Australia", "New Zealand", "Fiji", "Micronesia", "Guam", "Kiribati", "Marshall", "Northern Mariana",
        "New Caledonia", "Norfolk", "Nauru", "Niue", "French Polynesia", "Papua New Guinea", "Pitcairn",
        "Palau", "Solomon", "Tokelau", "Tonga", "Tuvalu", "Vanuatu", "Wallis", "Samoa", "Cook Islands",
        "American Samoa",
    ],
    "南極": ["Antarctica", "Bouvet", "French Southern", "Heard", "South Georgia"],
}

SPECIAL = {
    "Japan": (["日の丸"], ["赤い丸", "白地"], ["日本", "アジア"]),
    "United States": (["星条旗"], ["星", "しま模様"], ["アメリカ", "北アメリカ"]),
    "United Kingdom": (["ユニオンジャック"], ["十字", "赤青白"], ["イギリス", "ヨーロッパ"]),
    "Canada": (["メープルリーフ"], ["カエデ", "赤白"], ["カナダ", "北アメリカ"]),
    "Brazil": (["ブラジル国旗"], ["緑", "黄色", "青い円"], ["ブラジル", "南アメリカ"]),
    "India": (["インド国旗"], ["法輪", "三色旗"], ["インド", "アジア"]),
    "Israel": (["イスラエル国旗"], ["ダビデの星", "青白"], ["イスラエル", "中東"]),
    "Türkiye": (["トルコ国旗"], ["星と三日月", "赤"], ["トルコ", "アジア", "ヨーロッパ"]),
    "Turkey": (["トルコ国旗"], ["星と三日月", "赤"], ["トルコ", "アジア", "ヨーロッパ"]),
    "Nepal": (["ネパール国旗"], ["三角", "赤"], ["ネパール", "アジア"]),
    "Switzerland": (["スイス国旗"], ["十字", "赤"], ["スイス", "ヨーロッパ"]),
    "United Nations": (["国連旗"], ["水色", "地球"], ["国際連合", "世界"]),
    "England": (["イングランド旗"], ["十字", "白地"], ["イングランド", "ヨーロッパ"]),
    "Scotland": (["スコットランド旗"], ["斜め十字", "青白"], ["スコットランド", "ヨーロッパ"]),
    "Wales": (["ウェールズ旗"], ["ドラゴン", "赤"], ["ウェールズ", "ヨーロッパ"]),
}


def region_terms(name_en):
    result = []
    for region, needles in REGIONS.items():
        if any(needle in name_en for needle in needles):
            result.append(region)
    if "Island" in name_en or "Islands" in name_en:
        result.append("島")
    return unique(result or ["海外"])


def country_name(row):
    if row["name_en"].startswith("flag: "):
        return row["name_en"][6:]
    return row["name_en"]


def fill_general_flag(row):
    name = row["name_en"].lower()
    direct = ["旗", row["name_ja"]]
    visual = ["旗", "布"]
    context = ["目印", "応援", "イベント"]
    symbolic = ["合図", "所属"]
    emotion = ["はっきり"]
    action = ["掲げる"]
    culture = []
    if "chequered" in name:
        direct += ["チェッカーフラッグ"]
        visual += ["白黒", "格子"]
        context += ["レース", "ゴール"]
        symbolic += ["終了", "勝負"]
    elif "triangular" in name:
        visual += ["三角", "赤"]
    elif "crossed" in name:
        visual += ["交差", "二本"]
        culture += ["日本"]
        symbolic += ["祝日"]
    elif "black" in name:
        visual += ["黒"]
        symbolic += ["抗議", "海賊"]
    elif "white" in name:
        visual += ["白"]
        symbolic += ["降参", "平和"]
    elif "rainbow" in name:
        visual += ["虹色", "多色"]
        symbolic += ["多様性", "プライド"]
    elif "transgender" in name:
        visual += ["水色", "ピンク", "白"]
        symbolic += ["多様性", "ジェンダー"]
    elif "pirate" in name:
        visual += ["黒", "どくろ"]
        symbolic += ["海賊", "冒険"]
    return direct, visual, context, symbolic, emotion, action, culture


def fill_country_flag(row):
    name = country_name(row)
    direct = ["国旗", "旗", row["name_ja"], name]
    visual = ["旗", "布"]
    context = ["旅行", "海外", "ニュース", "スポーツ応援"]
    symbolic = ["国", "地域", "代表", "所属"]
    emotion = ["公式"]
    action = ["掲げる", "応援する"]
    culture = region_terms(name)

    for needle, (direct_add, visual_add, culture_add) in SPECIAL.items():
        if needle in name:
            direct.extend(direct_add)
            visual.extend(visual_add)
            culture.extend(culture_add)
    return direct, visual, context, symbolic, emotion, action, culture


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
        values = fill_country_flag(row) if row["subcategory"] in {"country-flag", "subdivision-flag"} else fill_general_flag(row)
        for field, terms in zip([field for field in V2_FIELDS if field != "search_ja"], values):
            row[field] = join_list(unique(terms))
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
