"""雨温図（気温の折れ線＋降水量の棒グラフ）を SVG 文字列で生成する。"""

import math

from markupsafe import Markup

W, H = 400, 280
LEFT, RIGHT, TOP, BOTTOM = 48, 52, 20, 36


def _temp_range(temps):
    lo = min(-10, math.floor(min(temps) / 10) * 10)
    hi = max(30, math.ceil(max(temps) / 10) * 10)
    return lo, hi


def climograph_svg(temps, precs, title=""):
    lo, hi = _temp_range(temps)
    steps = (hi - lo) // 10                       # 気温目盛りの区間数（10℃刻み）
    p_step = 100 if max(precs) <= 500 else 200    # 降水量目盛り1区間あたりの mm
    p_max = steps * p_step
    while max(precs) > p_max:                     # 収まらない場合は目盛りを広げる
        p_step += 100
        p_max = steps * p_step

    pw, ph = W - LEFT - RIGHT, H - TOP - BOTTOM
    col = pw / 12

    def ty(t):
        return TOP + ph * (hi - t) / (hi - lo)

    def py(p):
        return TOP + ph * (1 - p / p_max)

    parts = [f'<svg viewBox="0 0 {W} {H}" class="climograph" role="img" '
             f'aria-label="雨温図{(" " + title) if title else ""}" xmlns="http://www.w3.org/2000/svg">']

    # 目盛り線とラベル
    for i in range(steps + 1):
        y = TOP + ph * i / steps
        t = hi - 10 * i
        p = p_max - p_step * i
        cls = "axis zero" if t == 0 else "grid"
        parts.append(f'<line x1="{LEFT}" y1="{y:.1f}" x2="{W - RIGHT}" y2="{y:.1f}" class="{cls}"/>')
        parts.append(f'<text x="{LEFT - 6}" y="{y + 4:.1f}" class="lbl t" text-anchor="end">{t}</text>')
        parts.append(f'<text x="{W - RIGHT + 6}" y="{y + 4:.1f}" class="lbl p">{p}</text>')

    # 降水量（棒）
    for m, p in enumerate(precs):
        x = LEFT + col * m + col * 0.15
        y = py(p)
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{col * 0.7:.1f}" '
                     f'height="{TOP + ph - y:.1f}" class="bar"><title>{m + 1}月 {p}mm</title></rect>')

    # 気温（折れ線）
    pts = " ".join(f"{LEFT + col * (m + 0.5):.1f},{ty(t):.1f}" for m, t in enumerate(temps))
    parts.append(f'<polyline points="{pts}" class="line"/>')
    for m, t in enumerate(temps):
        parts.append(f'<circle cx="{LEFT + col * (m + 0.5):.1f}" cy="{ty(t):.1f}" r="3" class="dot">'
                     f'<title>{m + 1}月 {t}℃</title></circle>')

    # 枠・月ラベル・単位
    parts.append(f'<rect x="{LEFT}" y="{TOP}" width="{pw}" height="{ph}" class="frame"/>')
    for m in range(12):
        parts.append(f'<text x="{LEFT + col * (m + 0.5):.1f}" y="{H - BOTTOM + 16}" '
                     f'class="lbl" text-anchor="middle">{m + 1}</text>')
    parts.append(f'<text x="{LEFT - 6}" y="{TOP - 6}" class="lbl t" text-anchor="end">℃</text>')
    parts.append(f'<text x="{W - RIGHT + 6}" y="{TOP - 6}" class="lbl p">mm</text>')
    parts.append(f'<text x="{LEFT + pw / 2}" y="{H - 4}" class="lbl" text-anchor="middle">月</text>')
    parts.append("</svg>")
    return Markup("".join(parts))
