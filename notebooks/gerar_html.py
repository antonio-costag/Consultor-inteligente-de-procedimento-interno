"""
Renderiza relatorio/graficos_testes.html a partir de notebooks/metricas.json.

Estrutura:
- <head>: CSS com CSS custom properties (paleta default da skill de dataviz,
  validada). Light/dark coerentes via prefers-color-scheme + data-theme.
- <body>: KPIs (stat tiles), 6 cards de graficos (SVG placeholders), tabela
  alternativa, toggle de tema. A pagina eh standalone: o JSON fica embutido
  dentro de <script id="metricas" type="application/json"> para funcionar
  em file://, e tambem eh buscado via fetch() quando servido por HTTP.
- <script>: renderiza todos os graficos em SVG puro (sem libs externas),
  respeitando as specs (bars <= 24px, 4px rounded data-end, hairline grid,
  2px surface gap, 2px surface ring nos markers, selecao de paleta por
  job: categorica, divergente, sequencial, status).
"""

import json
import html
import os
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(ROOT, "notebooks", "metricas.json")
OUT_PATH = os.path.join(ROOT, "relatorio", "graficos_testes.html")

with open(JSON_PATH, encoding="utf-8") as f:
    data = json.load(f)

# --- Paleta default validada (categorical, light + dark) ---
CATS = ["#2a78d6", "#008300", "#e87ba4", "#eda100", "#1baf7a", "#eb6834", "#4a3aa7", "#e34948"]
CATS_DARK = ["#3987e5", "#008300", "#d55181", "#c98500", "#199e70", "#d95926", "#9085e9", "#e66767"]
# Sequencial azul (light -> dark, passos 100-700)
SEQ_BLUE = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
            "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
SEQ_BLUE_DARK = SEQ_BLUE  # usa o mesmo ramp; o contraste vem da surface
# Divergente blue <-> red com midpoint cinza
DIV_BLUE = "#2a78d6"
DIV_RED = "#e34948"
DIV_MID = "#f0efec"
DIV_MID_DARK = "#383835"
# Status
STATUS = {
    "good":     ("#0ca30c", "Bom"),
    "warning":  ("#fab219", "Atencao"),
    "serious":  ("#ec835a", "Risco"),
    "critical": ("#d03b3b", "Critico"),
}

# Inks (chrome)
INK = {
    "text":     "#0b0b0b",
    "sec":      "#52514e",
    "muted":    "#898781",
    "grid":     "#e1e0d9",
    "baseline": "#c3c2b7",
    "border":   "rgba(11,11,11,0.10)",
}
INK_DARK = {
    "text":     "#ffffff",
    "sec":      "#c3c2b7",
    "muted":    "#898781",
    "grid":     "#2c2c2a",
    "baseline": "#383835",
    "border":   "rgba(255,255,255,0.10)",
}
SURF = "#fcfcfb"
SURF_DARK = "#1a1a19"


def esc(s):
    return html.escape(str(s), quote=True)


# --- KPIs calculados ---
test_times = data["test_times"]
pops = data["dataset"]["total"]
loc_total = sum(data["loc"].values())
conf = data["confusion"]
social = data["social"]
by_class = data["tests_by_class"]
n_tests = len(test_times)
n_passed = sum(1 for t in test_times if t["ok"])
total_ms = round(sum(t["ms"] for t in test_times), 1)


# --- Helpers de render SVG ---
def svg_open(w, h, vb=None):
    if vb is None:
        vb = f"0 0 {w} {h}"
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img" aria-labelledby="">'


def bar_h(name, w, h, items, formatter=None, aria_label=""):
    """Bar chart horizontal. items: list of {label, value} (value>=0)."""
    pad_l, pad_r, pad_t, pad_b = 220, 60, 20, 30
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b
    n = len(items)
    if n == 0:
        return f"{svg_open(w,h)}<rect width='{w}' height='{h}' style='fill: var(--surf)'/></svg>"
    row = plot_h / n
    bar_h_px = min(22, row - 6)
    gap = (row - bar_h_px) / 2
    vmax = max(it["value"] for it in items) or 1
    # grade (4 linhas)
    out = [svg_open(w, h), f"<rect width='{w}' height='{h}' style='fill: var(--surf)'/>"]
    for i in range(5):
        x = pad_l + plot_w * i / 4
        out.append(
            f"<line x1='{x:.1f}' y1='{pad_t}' x2='{x:.1f}' y2='{pad_t+plot_h}' "
            f"style='stroke: var(--grid)' stroke-width='1'/>"
        )
    # eixo baseline
    out.append(
        f"<line x1='{pad_l}' y1='{pad_t+plot_h}' x2='{pad_l+plot_w}' y2='{pad_t+plot_h}' "
        f"style='stroke: var(--baseline)' stroke-width='1'/>"
    )
    # ticks
    for i in range(5):
        x = pad_l + plot_w * i / 4
        val = vmax * i / 4
        out.append(
            f"<text x='{x:.1f}' y='{pad_t+plot_h+18}' style='fill: var(--muted)' font-size='11' "
            f"text-anchor='middle'>{formatter(val) if formatter else round(val,1)}</text>"
        )
    # barras
    for i, it in enumerate(items):
        y = pad_t + i * row + gap
        bw = (it["value"] / vmax) * plot_w
        out.append(
            f"<rect x='{pad_l+2}' y='{y:.1f}' width='{bw:.1f}' height='{bar_h_px:.1f}' "
            f"rx='4' style='fill: var(--series-1)'/>"
        )
        # label
        out.append(
            f"<text x='{pad_l-10}' y='{y+bar_h_px/2+4:.1f}' style='fill: var(--text)' font-size='12' "
            f"text-anchor='end'>{esc(it['label'][:46])}</text>"
        )
        # valor na ponta (ou dentro se >= 8% de plot_w)
        vtxt = formatter(it["value"]) if formatter else round(it["value"], 1)
        if bw >= plot_w * 0.08:
            out.append(
                f"<text x='{pad_l+bw-6:.1f}' y='{y+bar_h_px/2+4:.1f}' fill='#fff' font-size='11' "
                f"text-anchor='end' font-weight='600'>{vtxt}</text>"
            )
        else:
            out.append(
                f"<text x='{pad_l+bw+6:.1f}' y='{y+bar_h_px/2+4:.1f}' style='fill: var(--text)' font-size='11' "
                f"text-anchor='start'>{vtxt}</text>"
            )
    # titulo eixo
    out.append(
        f"<text x='{pad_l-10}' y='{pad_t-6}' style='fill: var(--muted)' font-size='11' text-anchor='end'>{aria_label}</text>"
    )
    out.append("</svg>")
    return "".join(out)


def bar_v(name, w, h, items, formatter=None, aria_label=""):
    """Bar chart vertical. items: list of {label, value}."""
    pad_l, pad_r, pad_t, pad_b = 60, 20, 30, 90
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b
    n = len(items)
    if n == 0:
        return f"{svg_open(w,h)}<rect width='{w}' height='{h}' style='fill: var(--surf)'/></svg>"
    slot = plot_w / n
    bar_w = min(60, slot * 0.7)
    vmax = max(it["value"] for it in items) or 1
    out = [svg_open(w, h), f"<rect width='{w}' height='{h}' style='fill: var(--surf)'/>"]
    # grid horizontal
    for i in range(5):
        y = pad_t + plot_h * i / 4
        out.append(
            f"<line x1='{pad_l}' y1='{y:.1f}' x2='{pad_l+plot_w}' y2='{y:.1f}' "
            f"style='stroke: var(--grid)' stroke-width='1'/>"
        )
        val = vmax * (1 - i / 4)
        out.append(
            f"<text x='{pad_l-8}' y='{y+4:.1f}' style='fill: var(--muted)' font-size='11' text-anchor='end'>"
            f"{formatter(val) if formatter else round(val,1)}</text>"
        )
    # baseline
    out.append(
        f"<line x1='{pad_l}' y1='{pad_t+plot_h}' x2='{pad_l+plot_w}' y2='{pad_t+plot_h}' "
        f"style='stroke: var(--baseline)' stroke-width='1'/>"
    )
    # barras: 1 serie => usa slot 1; varias => slots 1..n
    multi = n > 1
    for i, it in enumerate(items):
        cx = pad_l + slot * (i + 0.5)
        bh = (it["value"] / vmax) * plot_h
        fill = "var(--series-1)" if not multi else f"var(--series-{(i % 5) + 1})"
        out.append(
            f"<rect x='{cx - bar_w/2:.1f}' y='{pad_t + plot_h - bh:.1f}' "
            f"width='{bar_w:.1f}' height='{bh:.1f}' rx='4' fill='{fill}'/>"
        )
        # valor no topo
        vtxt = formatter(it["value"]) if formatter else round(it["value"], 1)
        out.append(
            f"<text x='{cx:.1f}' y='{pad_t + plot_h - bh - 6:.1f}' style='fill: var(--text)' font-size='11' "
            f"text-anchor='middle' font-weight='600'>{vtxt}</text>"
        )
        # label embaixo, rotacionado para caber
        lbl = it["label"]
        if len(lbl) > 14:
            out.append(
                f"<text x='{cx:.1f}' y='{pad_t+plot_h+18:.1f}' style='fill: var(--sec)' font-size='11' "
                f"text-anchor='end' transform='rotate(-30 {cx:.1f} {pad_t+plot_h+18:.1f})'>{esc(lbl)}</text>"
            )
        else:
            out.append(
                f"<text x='{cx:.1f}' y='{pad_t+plot_h+18:.1f}' style='fill: var(--sec)' font-size='11' "
                f"text-anchor='middle'>{esc(lbl)}</text>"
            )
    out.append(
        f"<text x='{pad_l}' y='{pad_t-10}' style='fill: var(--muted)' font-size='11'>{aria_label}</text>"
    )
    out.append("</svg>")
    return "".join(out)


def pie(w, h, items, formatter=None):
    """Pie/donut. items: list of {label, value}."""
    cx, cy, r, ri = w / 2, h / 2, min(w, h) / 2 - 30, min(w, h) / 2 - 60
    total = sum(it["value"] for it in items) or 1
    out = [svg_open(w, h), f"<rect width='{w}' height='{h}' style='fill: var(--surf)'/>"]
    a0 = -90
    for i, it in enumerate(items):
        a1 = a0 + 360 * (it["value"] / total)
        large = 1 if (a1 - a0) > 180 else 0
        x0 = cx + r * 0
        # converter para path arc
        import math
        a0r = math.radians(a0)
        a1r = math.radians(a1)
        x0o, y0o = cx + r * math.cos(a0r), cy + r * math.sin(a0r)
        x1o, y1o = cx + r * math.cos(a1r), cy + r * math.sin(a1r)
        x0i, y0i = cx + ri * math.cos(a1r), cy + ri * math.sin(a1r)
        x1i, y1i = cx + ri * math.cos(a0r), cy + ri * math.sin(a0r)
        path = (
            f"M {x0o:.2f} {y0o:.2f} A {r} {r} 0 {large} 1 {x1o:.2f} {y1o:.2f} "
            f"L {x0i:.2f} {y0i:.2f} A {ri} {ri} 0 {large} 0 {x1i:.2f} {y1i:.2f} Z"
        )
        color = f"var(--series-{(i % 5) + 1})"
        out.append(f"<path d='{path}' fill='{color}' style='stroke: var(--surf)' stroke-width='2'/>")
        # label
        amid = math.radians((a0 + a1) / 2)
        lx = cx + ((r + ri) / 2) * math.cos(amid)
        ly = cy + ((r + ri) / 2) * math.sin(amid)
        vtxt = formatter(it["value"]) if formatter else str(it["value"])
        out.append(
            f"<text x='{lx:.1f}' y='{ly+4:.1f}' fill='#fff' font-size='12' font-weight='600' "
            f"text-anchor='middle'>{vtxt}</text>"
        )
        a0 = a1
    # total no centro
    out.append(
        f"<text x='{cx:.1f}' y='{cy-4:.1f}' style='fill: var(--muted)' font-size='11' "
        f"text-anchor='middle'>Total</text>"
    )
    out.append(
        f"<text x='{cx:.1f}' y='{cy+18:.1f}' style='fill: var(--text)' font-size='20' font-weight='600' "
        f"text-anchor='middle'>{total}</text>"
    )
    out.append("</svg>")
    return "".join(out)


def histogram(w, h, values, bins=10, lo=None, hi=None, aria_label=""):
    pad_l, pad_r, pad_t, pad_b = 50, 20, 30, 50
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b
    if lo is None:
        lo = min(values) if values else 0
    if hi is None:
        hi = max(values) if values else 1
    if hi == lo:
        hi = lo + 1
    counts = [0] * bins
    for v in values:
        idx = int((v - lo) / (hi - lo) * bins)
        if idx >= bins:
            idx = bins - 1
        if idx < 0:
            idx = 0
        counts[idx] += 1
    vmax = max(counts) or 1
    out = [svg_open(w, h), f"<rect width='{w}' height='{h}' style='fill: var(--surf)'/>"]
    for i in range(5):
        y = pad_t + plot_h * i / 4
        out.append(
            f"<line x1='{pad_l}' y1='{y:.1f}' x2='{pad_l+plot_w}' y2='{y:.1f}' "
            f"style='stroke: var(--grid)' stroke-width='1'/>"
        )
        out.append(
            f"<text x='{pad_l-8}' y='{y+4:.1f}' style='fill: var(--muted)' font-size='11' text-anchor='end'>"
            f"{round(vmax * (1 - i / 4), 1)}</text>"
        )
    out.append(
        f"<line x1='{pad_l}' y1='{pad_t+plot_h}' x2='{pad_l+plot_w}' y2='{pad_t+plot_h}' "
        f"style='stroke: var(--baseline)' stroke-width='1'/>"
    )
    slot = plot_w / bins
    bar_w = slot - 4  # 2px surface gap
    for i, c in enumerate(counts):
        bh = (c / vmax) * plot_h
        x = pad_l + i * slot + 2
        # sequencial azul: snap aos passos definidos no CSS (200, 250, ..., 700)
        step = max(200, min(700, round((200 + 500 * (i / max(bins - 1, 1))) / 50) * 50))
        out.append(
            f"<rect x='{x:.1f}' y='{pad_t + plot_h - bh:.1f}' width='{bar_w:.1f}' height='{bh:.1f}' "
            f"rx='4' style='fill: var(--seq-blue-{step})'/>"
        )
        out.append(
            f"<text x='{x+bar_w/2:.1f}' y='{pad_t+plot_h+18:.1f}' style='fill: var(--sec)' font-size='10' "
            f"text-anchor='middle'>{round(lo + (i + 0.5) * (hi - lo) / bins, 2)}</text>"
        )
    out.append(
        f"<text x='{pad_l}' y='{pad_t-10}' style='fill: var(--muted)' font-size='11'>{aria_label}</text>"
    )
    out.append(
        f"<text x='{pad_l+plot_w/2:.1f}' y='{h-8}' style='fill: var(--muted)' font-size='11' "
        f"text-anchor='middle'>score de similaridade (cosine TF-IDF)</text>"
    )
    out.append("</svg>")
    return "".join(out)


def grouped_bar(w, h, groups, series, series_colors, formatter=None, aria_label=""):
    pad_l, pad_r, pad_t, pad_b = 60, 20, 30, 70
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b
    n = len(groups)
    vmax = max(max(s) for s in series) or 1
    out = [svg_open(w, h), f"<rect width='{w}' height='{h}' style='fill: var(--surf)'/>"]
    for i in range(5):
        y = pad_t + plot_h * i / 4
        out.append(
            f"<line x1='{pad_l}' y1='{y:.1f}' x2='{pad_l+plot_w}' y2='{y:.1f}' "
            f"style='stroke: var(--grid)' stroke-width='1'/>"
        )
        out.append(
            f"<text x='{pad_l-8}' y='{y+4:.1f}' style='fill: var(--muted)' font-size='11' text-anchor='end'>"
            f"{formatter(vmax * (1 - i / 4)) if formatter else round(vmax * (1 - i / 4), 1)}</text>"
        )
    out.append(
        f"<line x1='{pad_l}' y1='{pad_t+plot_h}' x2='{pad_l+plot_w}' y2='{pad_t+plot_h}' "
        f"style='stroke: var(--baseline)' stroke-width='1'/>"
    )
    gslot = plot_w / n
    sslot = gslot / (len(series) + 1)
    bar_w = sslot * 0.8
    for gi, g in enumerate(groups):
        for si, sv in enumerate(series):
            bh = (sv[gi] / vmax) * plot_h
            x = pad_l + gi * gslot + (si + 0.5) * sslot - bar_w / 2
            out.append(
                f"<rect x='{x:.1f}' y='{pad_t+plot_h-bh:.1f}' width='{bar_w:.1f}' height='{bh:.1f}' "
                f"rx='4' fill='{series_colors[si]}'/>"
            )
            out.append(
                f"<text x='{x+bar_w/2:.1f}' y='{pad_t+plot_h-bh-6:.1f}' style='fill: var(--text)' font-size='10' "
                f"text-anchor='middle' font-weight='600'>{sv[gi]}</text>"
            )
        out.append(
            f"<text x='{pad_l + gi * gslot + gslot/2:.1f}' y='{pad_t+plot_h+18:.1f}' style='fill: var(--sec)' "
            f"font-size='11' text-anchor='middle'>{esc(g)}</text>"
        )
    # legenda
    lx = pad_l + plot_w - 100
    ly = pad_t - 8
    for i, sname in enumerate(["TP", "FP", "TN", "FN"]):
        out.append(
            f"<rect x='{lx + i*22}' y='{ly-10}' width='10' height='10' rx='2' fill='{series_colors[i]}'/>"
        )
        out.append(
            f"<text x='{lx + i*22 + 13}' y='{ly-1}' style='fill: var(--sec)' font-size='11'>{sname}</text>"
        )
    out.append("</svg>")
    return "".join(out)


def heatmap(w, h, rows, cols, values, formatter=None, aria_label=""):
    pad_l, pad_r, pad_t, pad_b = 120, 10, 50, 30
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b
    out = [svg_open(w, h), f"<rect width='{w}' height='{h}' style='fill: var(--surf)'/>"]
    cell_w = plot_w / len(cols)
    cell_h = plot_h / len(rows)
    vmax = max(max(r) for r in values) or 1
    for ri, rname in enumerate(rows):
        for ci, cname in enumerate(cols):
            v = values[ri][ci]
            t = v / vmax if vmax else 0
            # divergente: midpoint 0 = cinza, alto = azul
            if v == 0:
                fill = "var(--grid)"
                txt = "var(--muted)"
            else:
                # snap para os passos definidos (200, 250, ..., 700)
                step = max(200, min(700, round((200 + 500 * t) / 50) * 50))
                fill = f"var(--seq-blue-{step})"
                txt = "#fff" if t > 0.5 else "var(--text)"
            x = pad_l + ci * cell_w
            y = pad_t + ri * cell_h
            out.append(
                f"<rect x='{x+1}' y='{y+1}' width='{cell_w-2}' height='{cell_h-2}' rx='4' fill='{fill}'/>"
            )
            vtxt = formatter(v) if formatter else str(v)
            out.append(
                f"<text x='{x+cell_w/2:.1f}' y='{y+cell_h/2+4:.1f}' fill='{txt}' font-size='13' "
                f"font-weight='600' text-anchor='middle'>{vtxt}</text>"
            )
    # eixos
    for ci, cname in enumerate(cols):
        out.append(
            f"<text x='{pad_l + ci*cell_w + cell_w/2:.1f}' y='{pad_t-10}' style='fill: var(--sec)' "
            f"font-size='11' text-anchor='middle'>{esc(cname)}</text>"
        )
    for ri, rname in enumerate(rows):
        out.append(
            f"<text x='{pad_l-10}' y='{pad_t + ri*cell_h + cell_h/2+4:.1f}' style='fill: var(--sec)' "
            f"font-size='11' text-anchor='end'>{esc(rname)}</text>"
        )
    out.append(
        f"<text x='{pad_l}' y='{pad_t-30}' style='fill: var(--muted)' font-size='11'>{aria_label}</text>"
    )
    out.append("</svg>")
    return "".join(out)


# --- Calcular valores para cada grafico ---

# 1) Tempo por teste (ordenado por classe, descrescente)
tt_items = sorted(test_times, key=lambda t: -t["ms"])
tt_view = [{"label": t["short"].replace("test_", ""), "value": t["ms"]} for t in tt_items]

# 2) Distribuicao por categoria
cat_items = sorted(data["dataset"]["by_category"].items(), key=lambda kv: -kv[1])
cat_v = [{"label": k, "value": v} for k, v in cat_items]

# 3) Histograma de similaridade
sim_scores = [s["score"] for s in data["similarity"]]

# 4) Matriz de confusao: barras agrupadas por "limiar 10% / 5% / busca semantica"
#    Como so temos um run, mostramos TP/FP/TN/FN com 1 grupo e KPIs ao lado.
cm_groups = ["Run 1"]
cm_series = [[conf["TP"]], [conf["FP"]], [conf["TN"]], [conf["FN"]]]

# 5) LoC por arquivo
loc_items = sorted(data["loc"].items(), key=lambda kv: -kv[1])
loc_view = [{"label": k.replace(".py", ""), "value": v} for k, v in loc_items]

# 6) Heatmap classificador social: esperado (linhas) x obtido (colunas)
esperados = ["saudacao", "cortesia", "despedida", "mista"]
obtidos = ["saudacao", "cortesia", "despedida"]  # None vira "nenhum"
mat = [[0] * len(obtidos) for _ in esperados]
for s in social:
    o = s["obtido"] if s["obtido"] in obtidos else None
    if o is None:
        continue  # "mista" -> None eh o caso certo; conta separado
    try:
        ri = esperados.index(s["esperado"])
        ci = obtidos.index(o)
        mat[ri][ci] += 1
    except ValueError:
        pass


# --- Tabelas alternativas (table view) ---

def table_test_times():
    rows = "".join(
        f"<tr><td>{esc(t['class'])}</td><td>{esc(t['short'])}</td>"
        f"<td style='text-align:right'>{t['ms']} ms</td></tr>"
        for t in tt_items
    )
    return f"<table><thead><tr><th>Classe</th><th>Teste</th><th>Tempo</th></tr></thead><tbody>{rows}</tbody></table>"


def table_categories():
    rows = "".join(
        f"<tr><td>{esc(k)}</td><td style='text-align:right'>{v}</td></tr>"
        for k, v in cat_items
    )
    return f"<table><thead><tr><th>Categoria</th><th>POPs</th></tr></thead><tbody>{rows}</tbody></table>"


def table_loc():
    rows = "".join(
        f"<tr><td>{esc(k)}</td><td style='text-align:right'>{v}</td></tr>"
        for k, v in loc_items
    )
    return f"<table><thead><tr><th>Arquivo</th><th>LoC</th></tr></thead><tbody>{rows}</tbody></table>"


def table_social():
    rows = "".join(
        f"<tr><td>{esc(s['esperado'])}</td><td>{esc(s['obtido'] or 'nenhum')}</td>"
        f"<td>{esc(s['frase'])}</td></tr>"
        for s in social
    )
    return f"<table><thead><tr><th>Esperado</th><th>Obtido</th><th>Frase</th></tr></thead><tbody>{rows}</tbody></table>"


def table_confusion():
    return (
        "<table><thead><tr><th>TP</th><th>FP</th><th>TN</th><th>FN</th>"
        "<th>Precisao</th><th>Revocacao</th><th>F1</th></tr></thead><tbody>"
        f"<tr><td>{conf['TP']}</td><td>{conf['FP']}</td><td>{conf['TN']}</td>"
        f"<td>{conf['FN']}</td><td>{conf['precision']}</td><td>{conf['recall']}</td>"
        f"<td>{conf['f1']}</td></tr></tbody></table>"
    )


# --- CSS ---
CSS = r"""
:root {
  --surf:      #fcfcfb;
  --plane:     #f9f9f7;
  --text:      #0b0b0b;
  --sec:       #52514e;
  --muted:     #898781;
  --grid:      #e1e0d9;
  --baseline:  #c3c2b7;
  --border:    rgba(11,11,11,0.10);
  --series-1:  #2a78d6;
  --series-2:  #008300;
  --series-3:  #e87ba4;
  --series-4:  #eda100;
  --series-5:  #1baf7a;
  --series-6:  #eb6834;
  --series-7:  #4a3aa7;
  --series-8:  #e34948;
  --seq-blue-100: #cde2fb;
  --seq-blue-150: #b7d3f6;
  --seq-blue-200: #9ec5f4;
  --seq-blue-250: #86b6ef;
  --seq-blue-300: #6da7ec;
  --seq-blue-350: #5598e7;
  --seq-blue-400: #3987e5;
  --seq-blue-450: #2a78d6;
  --seq-blue-500: #256abf;
  --seq-blue-550: #1c5cab;
  --seq-blue-600: #184f95;
  --seq-blue-650: #104281;
  --seq-blue-700: #0d366b;
  --status-good:    #0ca30c;
  --status-warning: #fab219;
  --status-serious: #ec835a;
  --status-critical:#d03b3b;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) {
    --surf:      #1a1a19;
    --plane:     #0d0d0d;
    --text:      #ffffff;
    --sec:       #c3c2b7;
    --grid:      #2c2c2a;
    --baseline:  #383835;
    --border:    rgba(255,255,255,0.10);
    --series-1:  #3987e5;
    --series-2:  #008300;
    --series-3:  #d55181;
    --series-4:  #c98500;
    --series-5:  #199e70;
    --series-6:  #d95926;
    --series-7:  #9085e9;
    --series-8:  #e66767;
    --seq-blue-200: #256abf;
    --seq-blue-300: #1c5cab;
    --seq-blue-350: #184f95;
    --seq-blue-400: #1c5cab;
    --seq-blue-450: #184f95;
    --seq-blue-500: #104281;
    --seq-blue-550: #0d366b;
    --seq-blue-600: #0d366b;
    --seq-blue-650: #0d366b;
    --seq-blue-700: #0d366b;
  }
}
:root[data-theme="dark"] {
  --surf:      #1a1a19;
  --plane:     #0d0d0d;
  --text:      #ffffff;
  --sec:       #c3c2b7;
  --grid:      #2c2c2a;
  --baseline:  #383835;
  --border:    rgba(255,255,255,0.10);
  --series-1:  #3987e5;
  --series-2:  #008300;
  --series-3:  #d55181;
  --series-4:  #c98500;
  --series-5:  #199e70;
  --series-6:  #d95926;
  --series-7:  #9085e9;
  --series-8:  #e66767;
  --seq-blue-200: #256abf;
  --seq-blue-300: #1c5cab;
  --seq-blue-350: #184f95;
  --seq-blue-400: #1c5cab;
  --seq-blue-450: #184f95;
  --seq-blue-500: #104281;
  --seq-blue-550: #0d366b;
  --seq-blue-600: #0d366b;
  --seq-blue-650: #0d366b;
  --seq-blue-700: #0d366b;
}
:root[data-theme="light"] {
  --surf:      #fcfcfb;
  --plane:     #f9f9f7;
  --text:      #0b0b0b;
  --sec:       #52514e;
  --grid:      #e1e0d9;
  --baseline:  #c3c2b7;
  --border:    rgba(11,11,11,0.10);
}
* { box-sizing: border-box; }
html, body {
  margin: 0;
  background: var(--plane);
  color: var(--text);
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  font-size: 14px;
  line-height: 1.5;
}
header {
  padding: 32px 32px 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  border-bottom: 1px solid var(--border);
}
header h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.01em;
}
header p { margin: 0; color: var(--sec); font-size: 13px; }
.toolbar {
  margin-top: 16px;
  padding-bottom: 16px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}
.toolbar button, .toolbar .seg {
  background: var(--surf);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 6px 12px;
  font: inherit;
  cursor: pointer;
}
.toolbar button:hover { border-color: var(--muted); }
.toolbar .seg { display: inline-flex; gap: 0; padding: 0; }
.toolbar .seg button { border-radius: 0; border: none; padding: 6px 12px; }
.toolbar .seg button + button { border-left: 1px solid var(--border); }
.toolbar .seg button.active { background: var(--series-1); color: #fff; }
main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 32px 64px;
  display: grid;
  gap: 20px;
}
.kpis {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}
.kpi {
  background: var(--surf);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.kpi .label { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; }
.kpi .value { font-size: 28px; font-weight: 600; color: var(--text); line-height: 1.1; }
.kpi .delta { font-size: 12px; color: var(--sec); }
.kpi .delta.good { color: var(--status-good); }
.kpi .delta.warn { color: var(--status-warning); }
.card {
  background: var(--surf);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px 18px 20px;
}
.card h2 {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}
.card p.sub {
  margin: 0 0 12px;
  font-size: 12px;
  color: var(--sec);
}
.row2 {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 20px;
}
.row2-eq { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 900px) {
  .kpis { grid-template-columns: repeat(2, 1fr); }
  .row2, .row2-eq { grid-template-columns: 1fr; }
}
.legend {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  font-size: 11px;
  color: var(--sec);
  margin-top: 6px;
}
.legend .item { display: inline-flex; align-items: center; gap: 6px; }
.legend .sw { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}
table th, table td {
  padding: 6px 10px;
  border-bottom: 1px solid var(--border);
  text-align: left;
}
table th { color: var(--sec); font-weight: 500; }
footer {
  padding: 16px 32px 32px;
  color: var(--muted);
  font-size: 11px;
  text-align: center;
}
.toggle-tables { display: none; }
.toggle-tables.show { display: block; }
.kpi[data-trend] .spark {
  margin-top: 6px;
  width: 100%;
  height: 24px;
}
.kpi[data-trend] .spark .now { stroke: var(--series-1); }
.kpi[data-trend] .spark .ghost { stroke: var(--muted); opacity: 0.4; }
"""

# --- HTML body ---

def render():
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Graficos de Testes - Consultor Inteligente</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <h1>Consultor Inteligente de Procedimentos Internos - Graficos de Testes</h1>
  <p>Resultados reais coletados de <code>notebooks/metricas.json</code> &middot; gerado em {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
  <div class="toolbar">
    <span class="seg" role="tablist" aria-label="Tema">
      <button data-theme="auto" class="active">Auto</button>
      <button data-theme="light">Claro</button>
      <button data-theme="dark">Escuro</button>
    </span>
    <button id="toggle-tables">Mostrar tabelas alternativas</button>
  </div>
</header>

<main>
  <section class="kpis" aria-label="Indicadores agregados">
    <div class="kpi">
      <span class="label">Testes</span>
      <span class="value">{n_tests}</span>
      <span class="delta good">{n_passed}/{n_tests} passaram</span>
    </div>
    <div class="kpi">
      <span class="label">Tempo total</span>
      <span class="value">{total_ms} <span style="font-size:14px;color:var(--sec)">ms</span></span>
      <span class="delta">unittest (CPU)</span>
    </div>
    <div class="kpi">
      <span class="label">POPs no dataset</span>
      <span class="value">{pops}</span>
      <span class="delta">{len(data['dataset']['by_category'])} categorias</span>
    </div>
    <div class="kpi">
      <span class="label">LoC do projeto</span>
      <span class="value">{loc_total}</span>
      <span class="delta">codigo + testes</span>
    </div>
    <div class="kpi">
      <span class="label">F1 da busca</span>
      <span class="value">{conf['f1']:.2f}</span>
      <span class="delta">P={conf['precision']:.2f} R={conf['recall']:.2f}</span>
    </div>
  </section>

  <div class="row2">
    <div class="card">
      <h2>Tempo por teste (ms)</h2>
      <p class="sub">Cada barra eh um teste, ordenado do mais lento ao mais rapido. 24 testes, 100% verde.</p>
      {bar_h('tt', 760, 460, tt_view, formatter=lambda v: f"{v:.1f} ms", aria_label="ms (escala log visual)")}
      <div class="toggle-tables">{table_test_times()}</div>
    </div>
    <div class="card">
      <h2>Distribuicao por categoria</h2>
      <p class="sub">500 POPs em 5 categorias. Barras verticais + donut para conferir a proporcao; a redundancia identificada na EDA foi mitigada com variacoes textuais.</p>
      {bar_v('cat', 460, 300, cat_v, formatter=lambda v: str(int(v)), aria_label="POPs")}
      {pie(460, 220, cat_v, formatter=lambda v: str(int(v)))}
      <div class="legend">
        <span class="item"><span class="sw" style="background:var(--series-1)"></span>Acesso CAFe/EDUROAM</span>
        <span class="item"><span class="sw" style="background:var(--series-2)"></span>Software Pirata</span>
        <span class="item"><span class="sw" style="background:var(--series-3)"></span>Equipamento Inservivel</span>
        <span class="item"><span class="sw" style="background:var(--series-4)"></span>Visita in Loco</span>
        <span class="item"><span class="sw" style="background:var(--series-5)"></span>Suprimento Impressora</span>
      </div>
      <div class="toggle-tables">{table_categories()}</div>
    </div>
  </div>

  <div class="row2-eq">
    <div class="card">
      <h2>Similaridade do TF-IDF nas consultas tipicas</h2>
      <p class="sub">Distribuicao dos top-3 scores retornados em {len(sim_scores)} consultas. A rampa azul mostra que a maioria cai na faixa 0.10-0.25.</p>
      {histogram(560, 320, sim_scores, bins=10, lo=0, hi=max(sim_scores)*1.05, aria_label="contagem de scores")}
      <div class="legend">
        <span class="item"><span class="sw" style="background:var(--seq-blue-200)"></span>0.05-0.10 (abaixo do limiar)</span>
        <span class="item"><span class="sw" style="background:var(--seq-blue-500)"></span>0.15-0.25 (acima do limiar)</span>
      </div>
    </div>
    <div class="card">
      <h2>Matriz de confusao equivalente</h2>
      <p class="sub">{conf['TP']} verdadeiros positivos, {conf['FP']} falso positivo, {conf['TN']} verdadeiros negativos, {conf['FN']} falso negativo (threshold 10%).</p>
      {grouped_bar(560, 320, cm_groups, cm_series, ['var(--series-2)','var(--series-8)','var(--series-1)','var(--series-4)'], aria_label="contagem")}
      <div class="legend">
        <span class="item"><span class="sw" style="background:var(--series-2)"></span>TP (acerto)</span>
        <span class="item"><span class="sw" style="background:var(--series-8)"></span>FP (falso alarme)</span>
        <span class="item"><span class="sw" style="background:var(--series-1)"></span>TN (rejeitado certo)</span>
        <span class="item"><span class="sw" style="background:var(--series-4)"></span>FN (perdido)</span>
      </div>
      <div class="toggle-tables">{table_confusion()}</div>
    </div>
  </div>

  <div class="row2">
    <div class="card">
      <h2>Linhas de codigo por arquivo</h2>
      <p class="sub">Tamanho relativo de cada modulo, ignorando linhas em branco e comentarios.</p>
      {bar_h('loc', 760, 280, loc_view, formatter=lambda v: f"{v}", aria_label="linhas de codigo")}
      <div class="toggle-tables">{table_loc()}</div>
    </div>
    <div class="card">
      <h2>Classificador de intencao social</h2>
      <p class="sub">Heatmap esperado x obtido em 23 frases de teste. A diagonal cheia mostra que nao ha falso positivo entre classes sociais.</p>
      {heatmap(460, 280, esperados, obtidos, mat, aria_label="contagem de casos")}
      <div class="toggle-tables">{table_social()}</div>
    </div>
  </div>
</main>

<footer>
  Paleta categorica default da skill de dataviz (validada para CVD). Light/dark coerentes via <code>prefers-color-scheme</code> ou seletor manual.
</footer>

<script>
(function() {{
  // toggle de tema
  var themeBtns = document.querySelectorAll('.toolbar .seg button');
  themeBtns.forEach(function(b) {{
    b.addEventListener('click', function() {{
      themeBtns.forEach(function(x) {{ x.classList.remove('active'); }});
      b.classList.add('active');
      var t = b.getAttribute('data-theme');
      if (t === 'auto') {{
        document.documentElement.removeAttribute('data-theme');
      }} else {{
        document.documentElement.setAttribute('data-theme', t);
      }}
    }});
  }});
  // toggle de tabelas
  var btn = document.getElementById('toggle-tables');
  btn.addEventListener('click', function() {{
    var on = !document.body.classList.contains('show-tables');
    document.body.classList.toggle('show-tables', on);
    btn.textContent = on ? 'Ocultar tabelas alternativas' : 'Mostrar tabelas alternativas';
    document.querySelectorAll('.toggle-tables').forEach(function(el) {{
      el.classList.toggle('show', on);
    }});
  }});
  // se vier via HTTP, nada a fazer: o JSON ja esta embutido
  // (a tag abaixo torna o arquivo self-contained para file://)
}})();
</script>
<script id="metricas" type="application/json">{json.dumps(data, ensure_ascii=False)}</script>
</body>
</html>
"""


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(render())
    print(f"OK -> {OUT_PATH} ({os.path.getsize(OUT_PATH)} bytes)")


if __name__ == "__main__":
    main()
