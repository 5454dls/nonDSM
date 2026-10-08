# -*- coding: utf-8 -*-
# REUSE-CHECKED: 이 파일은 새 모듈이 아니라 같은 도구의 정본 app.py 를 고친 판이다. 옛 판은
# `_이전판-시각고도화전-20261008/app.py` 에 보존했고, 확률 계산 `_probs` 는 옛 판과 글자까지 같다.
# 도구 폴더는 단독 배포(Hugging Face Spaces)되므로 lib/ 를 import 하지 않는다.
"""Chief problems and diagnostic-group probability (research tool).

Reads `model_all_groups.json` (coefficients, cut-offs, performance) and `item_domains.json`
(codebook domain of each item). Returns one probability per diagnostic group for the chief
problems you select. It fits nothing. It does not diagnose.

    pip install -r requirements.txt
    python app.py            # as before: also opens a temporary public link
    python app.py --local    # this computer only, http://127.0.0.1:7860

`_probs` (the probability computation) and the cut-off comparison are unchanged from
`_이전판-시각고도화전-20261008/app.py`; `test_tool_visual_upgrade.py` asserts the same
probabilities to 12 decimals. Everything else here is screen layout.
"""
import argparse
import html
import json
import math
from pathlib import Path

import gradio as gr

HERE = Path(__file__).resolve().parent
M = json.loads((HERE / "model_all_groups.json").read_text(encoding="utf-8"))

CLASSES = M["classes"]
LABELS = M["labels"]
PERF = M["performance"]
ITEMS = M["items"]
NAMES = [it["name"] for it in ITEMS]
INDEX = {n: i for i, n in enumerate(NAMES)}
MIN_ITEMS, MAX_ITEMS = 3, 10

# Item -> codebook domain (built by make_item_domains.py from analysis/code_dict.py).
_DOM = json.loads((HERE / "item_domains.json").read_text(encoding="utf-8"))
_NAME_OF_CODE = {it["code"]: it["name"] for it in ITEMS}
DOMAINS = [(d["label"], [_NAME_OF_CODE[c] for c in d["codes"]]) for d in _DOM["domains"]]
assert sorted(n for _, ns in DOMAINS for n in ns) == sorted(NAMES), "item_domains.json and model differ"

# Fill this in when the manuscript is accepted. Left as a placeholder on purpose.
CITATION = "[OO]"

# 🔴 "Other" 는 `dx_group.classify_dx_group()` 의 잔여(fallback) 범주다 — 이름이 가리키는
# 실체가 없어 다른 여섯과 확률로 나란히 비교하지 않는다. 항상 맨 아래, 구분선 뒤에 둔다.
# 실제 구성 , `projects/non-DSM/results/20260808-R4결함해소-3건.md` 3-1(축A 'Other' 군,
# 훈련셋 n=105, `dx_group8=="Other"`) — 인격장애 14.3%(15/105) · 신경인지 13.3%(14/105) ·
# 물질/알코올 8.6%(9/105) · 치매 5.7%(6/105). 규칙 자체는 `dx_group.py` classify_dx_group()
# 맨 끝 `return "Other"` (2026-08-08 R4-10 절, `20260808-R4결함해소-3건.py` 342행대).
OTHER_KEY = "Other"
OTHER_NOTE = ("Other diagnoses includes: personality disorders, neurocognitive disorders, "
              "dementia, and substance- or alcohol-related diagnoses, among diagnoses that do "
              "not match the other six groups' keywords (n = %d in the training set).")

# One accent colour; everything else is neutral. Contrast on white: ACCENT 6.9, INK 15.6,
# MUTED 5.9 (checked in test_tool_visual_upgrade.py).
ACCENT = "#2f5d8a"
INK = "#1c2430"
MUTED = "#5b6673"
RULE = "#d5dae0"

_ACCENT_SCALE = gr.themes.Color(
    c50="#eef3f8", c100="#dce6f0", c200="#b9cde1", c300="#8fb0cf", c400="#6190b9",
    c500="#3f74a2", c600=ACCENT, c700="#274d73", c800="#1f3d5c", c900="#172e45", c950="#0f2030")

THEME = gr.themes.Default(
    primary_hue=_ACCENT_SCALE, secondary_hue="slate", neutral_hue="slate",
    font=["Inter", "Segoe UI", "system-ui", "sans-serif"],
    radius_size=gr.themes.sizes.radius_sm,
).set(
    body_background_fill="#f5f6f8",
    block_shadow="none",
    block_border_width="1px",
    button_primary_background_fill=ACCENT,
    button_primary_background_fill_hover="#274d73",
    button_primary_border_color=ACCENT,
    button_primary_text_color="#ffffff",
    button_shadow="none",
)

CSS = """
:root, .gradio-container {color-scheme: light;}
.gradio-container {max-width: 1180px !important; font-size: 14px; color: #1c2430;}
:focus-visible {outline: 2px solid #2f5d8a !important; outline-offset: 2px;}
footer {display: none !important;}
#picker .meta-text, #picker .meta-text-center, #picker .timer, #count .meta-text,
#count .meta-text-center, #count .timer {display: none !important;}
.sr {position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0);
     white-space: nowrap;}

/* header */
#hdr {margin: 4px 0 14px 0; padding: 0 0 12px 0; border-bottom: 1px solid #d5dae0;}
#hdr .eyebrow {font-size: 11px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase;
               color: #2f5d8a; margin: 0 0 4px 0;}
#hdr h1 {font-size: 22px; font-weight: 600; margin: 0 0 4px 0; letter-spacing: -.01em; color: #1c2430;}
#hdr .lede {margin: 0 0 8px 0; font-size: 14px; color: #1c2430;}
#hdr .notice {margin: 0 0 10px 0; padding: 6px 10px; font-size: 12.5px; color: #1c2430;
              border: 1px solid #d5dae0; border-left: 3px solid #2f5d8a; background: #fff;}
#hdr .meta {display: flex; flex-wrap: wrap; gap: 4px 28px; margin: 0; font-size: 12px;}
#hdr .meta div {display: flex; gap: 6px;}
#hdr .meta dt {color: #5b6673; margin: 0;}
#hdr .meta dd {color: #1c2430; margin: 0; font-variant-numeric: tabular-nums;}

/* section titles */
.sect {font-size: 11px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase;
       color: #5b6673; margin: 2px 0 6px 0;}

/* input side */
#picker {gap: 6px !important;}
.dom {border: 1px solid #d5dae0 !important; background: #fff !important;}
.dom > button, .dom .label-wrap {font-size: 13px !important; font-weight: 500 !important;}
.cbg .wrap {flex-direction: column !important; gap: 3px !important;}
.cbg label {font-size: 13px !important;}
#count {margin: 8px 0 0 0;}
.cnt {font-size: 13px; color: #1c2430; margin: 0 0 6px 0; font-variant-numeric: tabular-nums;}
.cnt b {font-weight: 600;}
.cnt .st {color: #5b6673;}
.sel {margin: 0; padding: 0 0 0 18px; font-size: 12.5px; color: #1c2430; line-height: 1.55;}
.sel li {margin: 0 0 3px 0;}
.sel li span {color: #5b6673;}

/* result side */
#results {position: sticky; top: 12px; align-self: flex-start;}
#panel {border: 1px solid #d5dae0; border-radius: 4px; padding: 14px 16px 12px 16px;
        background: #fff;}
#panel table, #panel thead, #panel tbody, #panel tr, #panel th, #panel td, #panel caption {
  border: 0 !important; background: transparent !important; box-shadow: none !important;}
.res-title {font-size: 15px; font-weight: 600; margin: 0 0 2px 0; color: #1c2430;}
.echo {font-size: 12px; color: #5b6673; margin: 0 0 10px 0; line-height: 1.5;}
.summary {font-size: 13px; margin: 0 0 10px 0; color: #1c2430;}
.rt {width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums;
     margin: 0; display: table;}
.rt th {font-size: 11px; font-weight: 600; color: #5b6673; text-align: left;
        padding: 0 0 6px 0; vertical-align: bottom;
        border-bottom: 1px solid #d5dae0 !important; white-space: nowrap;}
.rt th.n, .rt td.n {text-align: right; padding-left: 10px;}
.rt td, .rt th[scope=row] {padding: 7px 0; border-bottom: 1px solid #eceff2 !important;
        vertical-align: middle; font-size: 13px; font-weight: 400; color: #1c2430;
        text-align: left; white-space: normal;}
.rt td.rk {width: 22px; color: #5b6673; font-size: 12px;}
.rt th[scope=row] {padding-right: 12px; min-width: 150px; line-height: 1.3;}
.rt td.bar {width: 40%; min-width: 130px; padding-right: 6px;}
.rt td.n {width: 56px; white-space: nowrap;}
.rt td.v {font-weight: 600;}
.rt td.st {width: 96px; padding-left: 12px; font-size: 12px; white-space: nowrap;}
.rt th.axisth {padding-right: 6px;}
.axis {position: relative; height: 13px; font-weight: 500; font-size: 10.5px;}
.axis span {position: absolute; top: 0; transform: translateX(-50%);}
.axis span:first-child {transform: none;}
.axis span:last-child {transform: translateX(-100%);}
.track {position: relative; height: 12px;}
.track .g {position: absolute; top: 0; bottom: 0; width: 1px; background: #eceff2;}
.fill {position: absolute; left: 0; top: 2px; bottom: 2px; box-sizing: border-box;}
.fill.above {background: #2f5d8a;}
.fill.below {background: #fff; border: 1.5px solid #5b6673;}
.tick {position: absolute; top: -3px; bottom: -3px; width: 2px; margin-left: -1px;
       background: #1c2430;}
.mk {display: inline-block; width: 9px; height: 9px; box-sizing: border-box;
     vertical-align: -1px; margin-right: 6px;}
.mk.above {background: #2f5d8a;}
.mk.below {background: #fff; border: 1.5px solid #5b6673;}
.mk.tk {width: 2px; height: 12px; background: #1c2430; border: 0; margin: 0 8px 0 4px;
        vertical-align: -2px;}
.rt tr.above td.st {font-weight: 600;}
.rt tr.sep th {padding: 14px 0 4px 0; font-size: 11px; font-weight: 600; color: #5b6673;
               border-bottom: 1px solid #d5dae0 !important; letter-spacing: .04em;
               text-transform: uppercase;}
.legend {margin: 12px 0 0 0; font-size: 11.5px; color: #5b6673;}
.legend span {margin-right: 16px; white-space: nowrap;}
.fine {font-size: 11.5px; color: #5b6673; margin: 6px 0 0 0; line-height: 1.5;}
.hint {font-size: 13px; color: #5b6673; padding: 18px 0 14px 0; margin: 0;}

/* model information */
.mi h3 {font-size: 12px; font-weight: 600; margin: 14px 0 4px 0; color: #1c2430;}
.mi h3:first-child {margin-top: 2px;}
.mi p, .mi li {font-size: 12.5px; line-height: 1.55; color: #1c2430; margin: 0 0 4px 0;}
.mi ul {margin: 0; padding-left: 18px;}
.mi table {border-collapse: collapse; margin: 4px 0 0 0; font-variant-numeric: tabular-nums;
           display: table; width: auto;}
.mi th {font-size: 11px; font-weight: 600; color: #5b6673; padding: 0 16px 5px 0; text-align: right;
        border-bottom: 1px solid #d5dae0 !important; background: transparent !important;}
.mi td {font-size: 12.5px; padding: 4px 16px 4px 0; text-align: right;
        border-bottom: 1px solid #eceff2 !important; background: transparent !important;}
.mi th:first-child, .mi td:first-child {text-align: left;}
.mi th, .mi td {border-left: 0 !important; border-right: 0 !important; border-top: 0 !important;}
.mi tr.resid td {color: #5b6673;}
"""


def _probs(picked):
    x = [0.0] * len(NAMES)
    for s in picked:
        x[INDEX[s]] = 1.0
    raw = {}
    for c in CLASSES:
        z = M["intercept"][c] + sum(w * xi for w, xi in zip(M["coef"][c], x))
        raw[c] = 1.0 / (1.0 + math.exp(-z))
    total = sum(raw.values())
    return {c: raw[c] / total for c in CLASSES}


def _pct(p):
    return "%.1f%%" % (100 * p)


def _esc(s):
    return html.escape(str(s), quote=True)


# ------------------------------------------------------------------ result panel
AXIS_TICKS = (0, 25, 50, 75, 100)     # fixed 0 to 100 % axis, the same for every input


def _axis_header():
    return '<div class="axis" aria-hidden="true">%s</div>' % "".join(
        '<span style="left:%d%%">%d%%</span>' % (t, t) for t in AXIS_TICKS)


def _row(rank, c, p, cut):
    over = p >= cut
    kind = "above" if over else "below"
    grid = "".join('<i class="g" style="left:%d%%"></i>' % t for t in AXIS_TICKS[1:-1])
    return (
        '<tr class="%s"><td class="rk">%s</td><th scope="row">%s</th>'
        '<td class="bar"><div class="track" aria-hidden="true">%s'
        '<div class="fill %s" style="width:%.2f%%"></div>'
        '<div class="tick" style="left:%.2f%%"></div></div></td>'
        '<td class="n v">%s</td><td class="n">%s</td>'
        '<td class="st"><span class="mk %s"></span>%s</td></tr>'
        % (kind, rank, _esc(LABELS[c]), grid, kind, 100 * min(p, 1.0), 100 * min(cut, 1.0),
           _pct(p), _pct(cut), kind, "At or above" if over else "Below"))


def _render(prob, picked):
    """Six named groups by descending probability, a rule, then Other diagnoses (last).

    Other diagnoses is a residual category, so it is never ranked against the other six
    (see the OTHER_KEY note). One fixed 0 to 100 % axis; each group's cut-off is a tick on it.
    """
    has_other = OTHER_KEY in prob
    main = [c for c in CLASSES if c != OTHER_KEY] if has_other else list(CLASSES)
    order = sorted(main, key=lambda c: prob[c], reverse=True)
    over_n = sum(1 for c in CLASSES if prob[c] >= PERF[c]["cutoff"])
    over = [LABELS[c] for c in sorted(CLASSES, key=lambda c: -prob[c])
            if prob[c] >= PERF[c]["cutoff"]]
    line = ("%d of %d groups at or above their cut-off: %s." % (over_n, len(CLASSES), "; ".join(over))
            if over else "No group reaches its cut-off.")
    out = ['<p class="res-title">Result</p>',
           '<p class="echo"><b>Input (%d):</b> %s</p>'
           % (len(picked), "; ".join(_esc(s) for s in picked)),
           '<p class="summary">%s</p>' % _esc(line),
           '<table class="rt"><caption class="sr">Probability of each diagnostic group with its '
           'cut-off</caption><thead><tr><th>#</th><th>Diagnostic group</th>'
           '<th class="axisth"><span class="sr">Probability scale, 0 to 100 percent</span>%s</th><th class="n">Probability</th><th class="n">Cut-off</th>'
           '<th style="padding-left:12px">Status</th></tr></thead><tbody>' % _axis_header()]
    for i, c in enumerate(order, 1):
        out.append(_row(i, c, prob[c], PERF[c]["cutoff"]))
    if has_other:
        out.append('<tr class="sep"><th colspan="6" scope="colgroup">Residual category, '
                   'not ranked</th></tr>')
        out.append(_row("&ndash;", OTHER_KEY, prob[OTHER_KEY], PERF[OTHER_KEY]["cutoff"]))
    out.append("</tbody></table>")
    out.append('<p class="legend"><span><i class="mk above"></i>At or above the group cut-off</span>'
               '<span><i class="mk below"></i>Below</span>'
               '<span><i class="mk tk"></i>Group cut-off</span></p>')
    out.append('<p class="fine">Probabilities are normalised to sum to 100%% over the %d groups. '
               'Status compares unrounded values. Balanced class weights mean the probabilities do '
               'not reflect how common each group is.</p>' % len(CLASSES))
    if has_other:
        out.append('<p class="fine">%s</p>' % _esc(OTHER_NOTE % PERF[OTHER_KEY]["n"]))
    return "\n".join(out)


def predict(selected):
    picked = [s for s in (selected or []) if s in INDEX]
    n = len(picked)
    if n < MIN_ITEMS or n > MAX_ITEMS:
        return ('<p class="hint">Select between %d and %d chief problems. '
                'You selected %d.</p>' % (MIN_ITEMS, MAX_ITEMS, n))
    picked = sorted(set(picked), key=INDEX.get)
    return _render(_probs(picked), picked)


# ------------------------------------------------------------------ input side
HINT = '<p class="hint">Select chief problems, then press Compute.</p>'


def _gather(vals):
    picked = []
    for v in vals:
        picked.extend(v or [])
    return sorted(set(picked), key=lambda s: INDEX.get(s, 10 ** 6))


def _count_html(picked):
    n = len(picked)
    if n == 0:
        state = "Select %d to %d." % (MIN_ITEMS, MAX_ITEMS)
    elif n < MIN_ITEMS:
        state = "Select %d more (minimum %d)." % (MIN_ITEMS - n, MIN_ITEMS)
    elif n > MAX_ITEMS:
        state = "Remove %d (maximum %d)." % (n - MAX_ITEMS, MAX_ITEMS)
    else:
        state = "Ready to compute."
    body = '<p class="cnt"><b>%d selected</b> <span class="st">&middot; %s</span></p>' % (n, state)
    if picked:
        chosen = set(picked)
        lis = []
        for label, names in DOMAINS:
            sel = [x for x in names if x in chosen]
            if sel:
                lis.append("<li><b>%s</b> <span>%d of %d</span><br>%s</li>"
                           % (_esc(label), len(sel), len(names), _esc("; ".join(sel))))
        body += '<ul class="sel">%s</ul>' % "".join(lis)
    return body


def _domain_label(label, names):
    return "%s · %d item%s" % (label, len(names), "" if len(names) == 1 else "s")


def on_change(*vals):
    """Runs only when the user ticks a box. Updates the count panel; computes nothing."""
    return _count_html(_gather(vals))


def compute(*vals):
    return predict(_gather(vals))


def reset():
    return [[] for _ in DOMAINS] + [HINT, _count_html([])]


# ------------------------------------------------------------------ static text
def _header_html():
    return (
        "<div id='hdr'><p class='eyebrow'>Research tool</p>"
        "<h1>Chief problems and diagnostic groups</h1>"
        "<p class='lede'>Estimates the probability of each diagnostic group from the chief "
        "problems recorded at admission.</p>"
        "<p class='notice'><b>For research use only.</b> This tool does not make a diagnosis. "
        "It is not the model reported in the manuscript (see Model information).</p>"
        "<dl class='meta'>"
        "<div><dt>Model</dt><dd>refitted on %d patients, %d groups, %d items</dd></div>"
        "<div><dt>Generated</dt><dd>%s</dd></div>"
        "<div><dt>Diagnostic-group rule</dt><dd>%s</dd></div>"
        "<div><dt>Citation</dt><dd>%s</dd></div></dl></div>"
        % (M["n_patients"], len(CLASSES), len(ITEMS), _esc(M["generated"]), _esc(M["dx_rule"]),
           _esc(CITATION)))


def _model_html():
    cv = M["cv"]
    main = sorted([c for c in CLASSES if c != OTHER_KEY], key=lambda c: -PERF[c]["n"])
    rows = []
    for c in main + ([OTHER_KEY] if OTHER_KEY in CLASSES else []):
        p = PERF[c]
        rows.append('<tr%s><td>%s</td><td>%d</td><td>%s</td><td>%.3f</td><td>%s</td><td>%.3f</td></tr>'
                    % (' class="resid"' if c == OTHER_KEY else "", _esc(LABELS[c]), p["n"],
                       _pct(p["prevalence"]), p["auc"], _pct(p["cutoff"]), p["youden_j"]))
    dropped = "; ".join("%s (n = %d)" % (_esc(k.replace("_", " ")), v)
                        for k, v in M["dropped_groups"].items())
    return (
        '<div class="mi">'
        "<h3>Training set</h3>"
        "<p>%d patients, %d diagnostic groups, %d chief-problem items in %d codebook domains. "
        "Model: L2-penalised logistic regression, one-vs-rest, balanced class weights. The "
        "group probabilities are normalised to sum to 100%%.</p>"
        "<h3>Performance and cut-off by group</h3>"
        "<table><thead><tr><th>Diagnostic group</th><th>n</th><th>Prevalence</th>"
        "<th>Out-of-fold AUC</th><th>Cut-off</th><th>Youden J</th></tr></thead><tbody>%s</tbody>"
        "</table>"
        "<h3>Cut-off definition</h3>"
        "<p>The cut-off of each group is the Youden point (maximum of sensitivity + specificity "
        "- 1) of its out-of-fold ROC curve, from %d-fold stratified cross-validation repeated "
        "%d times (seed %d).</p>"
        "<h3>Groups left out</h3>"
        "<p>%s: fewer than %d patients, so stratified cross-validation does not hold.</p>"
        "<h3>How this differs from the manuscript</h3>"
        "<p>The manuscript reports four diagnostic groups. This tool is refitted on all %d "
        "patients across %d groups, so its coefficients and performance are not the "
        "manuscript's.</p>"
        "<h3>Limits</h3>"
        "<ul><li>Internal validation only.</li>"
        "<li>Balanced class weights mean these probabilities do not reflect how common each "
        "group is in practice.</li>"
        "<li>This tool does not make a diagnosis.</li></ul></div>"
        % (M["n_patients"], len(CLASSES), len(ITEMS), len(DOMAINS), "".join(rows),
           cv["splits"], cv["repeats"], cv["seed"], dropped, M["min_group_n"],
           M["n_patients"], len(CLASSES)))


# ------------------------------------------------------------------ app
with gr.Blocks(title="Chief problems and diagnostic groups", css=CSS, theme=THEME,
               js="() => { document.body.classList.remove('dark'); }") as demo:
    gr.HTML(_header_html())
    with gr.Row(equal_height=False):
        with gr.Column(scale=5, elem_id="picker"):
            gr.HTML("<p class='sect'>1. Chief problems by codebook domain</p>")
            cbs = []
            for label, names in DOMAINS:
                with gr.Accordion(_domain_label(label, names), open=False, elem_classes=["dom"]):
                    cbs.append(gr.CheckboxGroup(choices=names, value=[], label=label,
                                                show_label=False, elem_classes=["cbg"]))
            count = gr.HTML(_count_html([]), elem_id="count")
            with gr.Row():
                run = gr.Button("Compute", variant="primary")
                clear = gr.Button("Reset", variant="secondary")
        with gr.Column(scale=7, elem_id="results"):
            gr.HTML("<p class='sect'>2. Result</p>")
            with gr.Column(elem_id="panel"):
                out = gr.HTML(HINT)
            with gr.Accordion("Model information", open=False):
                gr.HTML(_model_html())

    # 🔴 Compute 를 눌러야만 계산한다. 고를 때마다 도는 것은 소장님이 원치 않으셨다
    # (고를 때마다 도는 것은 개수 표시뿐이다). 이벤트는 사용자가 상자를 누를 때(`input`)만
    # 오고 페이지를 열 때는 오지 않는다(`change` 는 열 때 20번 돌아서 쓰지 않는다). 하나의 이벤트
    # 정의에 상자 20개의 `input` 과 `select` 를 묶었다(둘 중 하나만 와도 같은 결과).
    gr.on(triggers=[cb.input for cb in cbs] + [cb.select for cb in cbs], fn=on_change, inputs=cbs, outputs=[count],
          show_progress="hidden", trigger_mode="always_last")
    run.click(compute, inputs=cbs, outputs=[out])
    clear.click(reset, inputs=None, outputs=cbs + [out, count], show_progress="hidden")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", action="store_true", help="no temporary public link")
    ap.add_argument("--port", type=int, default=7860)
    a = ap.parse_args()
    demo.launch(share=not a.local, server_port=a.port, show_api=False)
