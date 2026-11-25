"""ケッペンの気候区分の判定ロジック（高校地理の教科書レベル）。

判定の順序（教科書のフローチャートに準拠）:
  1. 最暖月平均気温 < 10℃            → E（寒帯）  ET / EF
  2. 年降水量 < 乾燥限界             → B（乾燥帯）BS / BW
  3. 最寒月平均気温 >= 18℃           → A（熱帯）  Af / Am / Aw
  4. -3℃ <= 最寒月平均気温 < 18℃     → C（温帯）  Cs / Cw / Cfa / Cfb
  5. 最寒月平均気温 < -3℃            → D（亜寒帯）Df / Dw
"""

from dataclasses import dataclass, field

MONTHS = ["1月", "2月", "3月", "4月", "5月", "6月",
          "7月", "8月", "9月", "10月", "11月", "12月"]


@dataclass
class Result:
    code: str
    steps: list = field(default_factory=list)


def _halves(values, southern):
    """(夏半年, 冬半年) の値リストを返す。北半球の夏半年は4〜9月、南半球は10〜3月。"""
    nh_summer = values[3:9]
    nh_winter = values[9:] + values[:3]
    return (nh_winter, nh_summer) if southern else (nh_summer, nh_winter)


def dryness_limit(temps, precs, southern=False):
    """乾燥限界 r = 20(t + x) [mm] と、その根拠の説明を返す。"""
    t = sum(temps) / 12
    total = sum(precs)
    summer, winter = _halves(precs, southern)
    if total > 0 and sum(summer) / total >= 0.7:
        x, note = 14, "夏に雨が集中（夏半年に年降水量の70%以上）"
    elif total > 0 and sum(winter) / total >= 0.7:
        x, note = 0, "冬に雨が集中（冬半年に年降水量の70%以上）"
    else:
        x, note = 7, "年中ほぼ平均的に降る"
    return 20 * (t + x), f"{note}なので r = 20 × ({t:.1f} + {x})"


def classify(temps, precs, southern=False):
    """月平均気温[℃]・月降水量[mm]（各12か月）から気候区を判定する。"""
    if len(temps) != 12 or len(precs) != 12:
        raise ValueError("12か月分のデータが必要です")

    steps = []
    t_max, t_min = max(temps), min(temps)
    total = sum(precs)

    # 1. 寒帯
    if t_max < 10:
        steps.append(f"最暖月平均気温 {t_max:.1f}℃ < 10℃ → 樹木が育たない寒帯（E）")
        if t_max < 0:
            steps.append(f"最暖月平均気温 {t_max:.1f}℃ < 0℃ → 氷雪気候（EF）")
            return Result("EF", steps)
        steps.append(f"0℃ ≦ 最暖月平均気温 {t_max:.1f}℃ < 10℃ → ツンドラ気候（ET）")
        return Result("ET", steps)
    steps.append(f"最暖月平均気温 {t_max:.1f}℃ ≧ 10℃ → 寒帯（E）ではない")

    # 2. 乾燥帯
    limit, note = dryness_limit(temps, precs, southern)
    if total < limit:
        steps.append(f"年降水量 {total:.0f}mm < 乾燥限界 {limit:.0f}mm（{note}）→ 乾燥帯（B）")
        if total < limit / 2:
            steps.append(f"年降水量が乾燥限界の半分（{limit / 2:.0f}mm）未満 → 砂漠気候（BW）")
            return Result("BW", steps)
        steps.append(f"年降水量が乾燥限界の半分（{limit / 2:.0f}mm）以上 → ステップ気候（BS）")
        return Result("BS", steps)
    steps.append(f"年降水量 {total:.0f}mm ≧ 乾燥限界 {limit:.0f}mm（{note}）→ 乾燥帯（B）ではない")

    p_min = min(precs)
    summer, winter = _halves(precs, southern)

    # 3. 熱帯
    if t_min >= 18:
        steps.append(f"最寒月平均気温 {t_min:.1f}℃ ≧ 18℃ → 熱帯（A）")
        if p_min >= 60:
            steps.append(f"最少雨月降水量 {p_min:.0f}mm ≧ 60mm → 熱帯雨林気候（Af）")
            return Result("Af", steps)
        am_line = 100 - total / 25
        if p_min >= am_line:
            steps.append(f"最少雨月 {p_min:.0f}mm < 60mm だが、100 − 年降水量/25 = {am_line:.0f}mm 以上"
                         " → 弱い乾季のある熱帯モンスーン気候（Am）")
            return Result("Am", steps)
        steps.append(f"最少雨月 {p_min:.0f}mm が 60mm と {am_line:.0f}mm（100 − 年降水量/25）を下回る"
                     " → はっきりした乾季のあるサバナ気候（Aw）")
        return Result("Aw", steps)

    # 4/5. 温帯・亜寒帯の乾季の判定
    s_dry = min(summer) < 40 and min(summer) < max(winter) / 3
    w_dry = min(winter) < max(summer) / 10

    if t_min >= -3:
        steps.append(f"−3℃ ≦ 最寒月平均気温 {t_min:.1f}℃ < 18℃ → 温帯（C）")
        if s_dry:
            steps.append(f"夏の最少雨月 {min(summer):.0f}mm が冬の最多雨月 {max(winter):.0f}mm の1/3未満"
                         " → 夏に乾燥する地中海性気候（Cs）")
            return Result("Cs", steps)
        if w_dry:
            steps.append(f"冬の最少雨月 {min(winter):.0f}mm が夏の最多雨月 {max(summer):.0f}mm の1/10未満"
                         " → 冬に乾燥する温暖冬季少雨気候（Cw）")
            return Result("Cw", steps)
        steps.append("夏・冬ともにはっきりした乾季がない → 年中湿潤（f）")
        if t_max >= 22:
            steps.append(f"最暖月平均気温 {t_max:.1f}℃ ≧ 22℃ → 温暖湿潤気候（Cfa）")
            return Result("Cfa", steps)
        steps.append(f"最暖月平均気温 {t_max:.1f}℃ < 22℃ → 西岸海洋性気候（Cfb）")
        return Result("Cfb", steps)

    steps.append(f"最寒月平均気温 {t_min:.1f}℃ < −3℃ → 亜寒帯（D）")
    if w_dry:
        steps.append(f"冬の最少雨月 {min(winter):.0f}mm が夏の最多雨月 {max(summer):.0f}mm の1/10未満"
                     " → 冬に乾燥する亜寒帯冬季少雨気候（Dw）")
        return Result("Dw", steps)
    steps.append("冬にはっきりした乾季がない → 亜寒帯湿潤気候（Df）")
    return Result("Df", steps)
