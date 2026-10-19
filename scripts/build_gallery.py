#!/usr/bin/env python3
"""Build the results gallery (docs/index.html and docs/img/*) from the HTML reports written by FloodML-Geo.

Run it again after every new model run:

    python scripts/build_gallery.py \
        --dataset      docs/reports/02_dataset_report.html \
        --training     docs/reports/03_training_validation.html \
        --independent  docs/reports/05_independent_test_report.html \
        --map          docs/img/susceptibility_map.png \
        --about        docs/about_example.txt

It needs only Python 3.9+ and Pillow (pip install pillow). Nothing is sent anywhere; the figures are cut out of
the self-contained report files, shrunk for the web and written next to the page.
"""
from __future__ import annotations

import argparse
import base64
import html
import io
import json
import re
import sys
from pathlib import Path

from PIL import Image

MAX_W = 1500

# keyword in the figure caption -> short name used in file names
CAPTION_KEYS = [
    ('pooled roc and precision', 'compare'),
    ('spatial layout of the cross-validation', 'folds_map'),
    ('autocorrelation range', 'autocorr'),
    ('receiver operating', 'roc'),
    ('precision–recall curve', 'pr'),
    ('confusion matrix', 'confusion'),
    ('reliability diagram', 'calibration'),
    ('score distribution', 'scores'),
    ('metric variability', 'fold_metrics'),
    ('permutation importance', 'permutation'),
    ('shap summary', 'shap_summary'),
    ('shap dependence', 'shap_dependence'),
    ('residuals', 'residuals'),
    ('class balance', 'class_balance'),
    ('predictor distributions', 'distributions'),
    ('spearman correlation', 'correlation'),
    ('single-predictor', 'separability'),
    ('missing values', 'missing'),
    ('roc curve', 'roc'),
    ('precision–recall', 'pr'),
    ('calibration', 'calibration'),
]


def strip(t: str) -> str:
    return html.unescape(re.sub(r'<[^>]+>', '', t)).strip()


def key_for(caption: str) -> str:
    c = caption.lower()
    for needle, key in CAPTION_KEYS:
        if needle in c:
            return key
    return re.sub(r'\W+', '_', c)[:24]


def parse_tables(src: str) -> list[tuple[list[str], list[list[str]]]]:
    out = []
    for tb in re.findall(r'<table.*?</table>', src, flags=re.S):
        head = [strip(h) for h in re.findall(r'<th[^>]*>(.*?)</th>', tb, flags=re.S)]
        rows = []
        for tr in re.findall(r'<tr>(.*?)</tr>', tb, flags=re.S):
            cells = [strip(c) for c in re.findall(r'<td[^>]*>(.*?)</td>', tr, flags=re.S)]
            if cells:
                rows.append(cells)
        out.append((head, rows))
    return out


def parse_report(path: Path, plain_models: bool = False) -> dict:
    src = path.read_text(encoding='utf-8', errors='replace')
    title = strip((re.findall(r'<h1[^>]*>(.*?)</h1>', src, flags=re.S) or [''])[0])
    sub = strip((re.findall(r'<header.*?<p[^>]*>(.*?)</p>', src, flags=re.S) or [''])[0])
    figs, model, section = [], '', ''
    tok = re.compile(r'<h2[^>]*>(.*?)</h2>|<h3[^>]*>(.*?)</h3>|<img\b[^>]*?alt="([^"]*)"[^>]*?src="data:image/(\w+);base64,([^"]+)"', re.S)
    for m in tok.finditer(src):
        if m.group(1) is not None or m.group(2) is not None:
            h = strip(m.group(1) if m.group(1) is not None else m.group(2))
            mm = re.match(r'\d+\.\d+\s*·\s*(.+)$', h)         # "3.1 · RF" opens a model section
            if mm:
                model = mm.group(1).strip()
            elif plain_models and h not in ('Results', 'Independent test', 'Result is NOT valid') and not h.startswith('Result'):
                model = h                                          # independent test: one heading per model
            elif m.group(1) is not None:                           # any other main heading closes it
                model = ''
            if m.group(1) is not None:
                section = h
        else:
            cap = html.unescape(m.group(3))
            figs.append(dict(section=section, model=model, caption=cap, key=key_for(cap),
                             data=base64.b64decode(m.group(5))))
    notes = [strip(x) for x in re.findall(r'<li>(.*?)</li>', src, flags=re.S)]
    verdict = re.findall(r'class="callout[^"]*"[^>]*>(.*?)</div>', src, flags=re.S)
    return dict(title=title, sub=sub, figs=figs, tables=parse_tables(src), notes=notes,
                callouts=[strip(v) for v in verdict], text=strip(re.sub(r'<style.*?</style>', '', src, flags=re.S)))


def save_img(data: bytes, dest: Path) -> tuple[int, int]:
    im = Image.open(io.BytesIO(data))
    im = im.convert('RGBA') if im.mode in ('P', 'LA') else im
    if im.width > MAX_W:
        im = im.resize((MAX_W, round(im.height * MAX_W / im.width)), Image.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, optimize=True)
    return im.size


def e(t) -> str:
    return html.escape(str(t), quote=True)


CSS = r"""
:root{
  --ink:#0e2230; --muted:#51636f; --fog:#edf1f3; --panel:#ffffff; --line:#cfd8de;
  --river:#2c7bb6; --flood:#d7191c; --link:#17598f;
  --c1:#2c7bb6; --c2:#abdda4; --c3:#ffffbf; --c4:#fdae61; --c5:#d7191c;
  --serif:'Newsreader','Iowan Old Style','Palatino Linotype',Georgia,serif;
  --sans:'Public Sans','Segoe UI',system-ui,-apple-system,Roboto,Helvetica,Arial,sans-serif;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){ --ink:#e4edf2; --muted:#93a6b2; --fog:#0b1822; --panel:#12212d; --line:#284050; --link:#7fbbe6; }
}
:root[data-theme="dark"]{ --ink:#e4edf2; --muted:#93a6b2; --fog:#0b1822; --panel:#12212d; --line:#284050; --link:#7fbbe6; }
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--fog);color:var(--ink);font:16px/1.6 var(--sans)}
a{color:var(--link)}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
nav.top{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--fog) 92%,transparent);backdrop-filter:blur(6px);border-bottom:1px solid var(--line)}
nav.top .wrap{display:flex;gap:22px;align-items:center;overflow-x:auto;white-space:nowrap;padding-top:10px;padding-bottom:10px}
nav.top b{font-family:var(--serif);font-size:18px;margin-right:auto}
nav.top a{text-decoration:none;color:var(--muted);font-size:14px}
nav.top a:hover,nav.top a:focus-visible{color:var(--ink);text-decoration:underline}
.hero{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,6fr);gap:40px;align-items:center;padding:48px 20px 36px}
.hero h1{font:600 clamp(40px,6vw,68px)/1.02 var(--serif);margin:0 0 16px;letter-spacing:-.01em}
.hero p.lead{font-size:19px;max-width:34ch;margin:0 0 26px}
.facts{display:grid;gap:10px;margin:0;padding:0;list-style:none;max-width:34ch}
.facts li{display:flex;justify-content:space-between;gap:16px;border-bottom:1px solid var(--line);padding-bottom:8px}
.facts b{font-variant-numeric:tabular-nums}
.hero figure{margin:0}
.hero img{width:100%;height:auto;display:block;background:#fff;border-radius:4px;cursor:zoom-in}
.ramp{display:flex;height:8px;margin:0}
.ramp i{flex:1}
section{padding:54px 0 12px}
h2{font:600 clamp(26px,3.4vw,36px)/1.15 var(--serif);margin:0 0 10px}
h3{font:600 20px/1.3 var(--serif);margin:30px 0 8px}
.intro{max-width:68ch;color:var(--muted);margin:0 0 22px}
.steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:0;border-top:2px solid var(--ink);margin-top:18px}
.steps div{padding:14px 16px 16px 0}
.steps b{display:block;font-family:var(--serif);font-size:19px}
.steps span{display:block;font-variant-numeric:tabular-nums;color:var(--river);font-weight:600;font-size:14px}
.steps p{margin:4px 0 0;color:var(--muted);font-size:14.5px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px;align-items:start}
.grid.wide{grid-template-columns:repeat(auto-fit,minmax(420px,1fr))}
figure.f{margin:0}
figure.f img{width:100%;height:auto;display:block;background:#fff;border:1px solid var(--line);border-radius:4px;cursor:zoom-in}
figure.f figcaption{font-size:13.5px;color:var(--muted);margin-top:6px;max-width:60ch}
table{border-collapse:collapse;width:100%;font-size:14.5px;font-variant-numeric:tabular-nums}
.tw{overflow-x:auto;margin:10px 0 6px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap;vertical-align:bottom}
th:first-child,td:first-child{text-align:left}
th{font-weight:600;border-bottom:2px solid var(--ink);white-space:normal;line-height:1.3}
.tw.narrow{max-width:460px}
.mapfig{max-width:820px}
.mswitch{display:inline-flex;border:1px solid var(--ink);border-radius:999px;overflow:hidden;margin:6px 0 14px}
.mswitch button{font:inherit;font-size:14px;background:none;color:var(--ink);border:0;padding:6px 18px;cursor:pointer}
.mswitch button[aria-pressed="true"]{background:var(--ink);color:var(--fog)}
.mswitch button:focus-visible{outline:3px solid var(--river);outline-offset:-3px}
.note{border-left:4px solid var(--c4);padding:4px 0 4px 16px;margin:18px 0;max-width:78ch}
.note.bad{border-color:var(--flood)}
.void{opacity:.5}
.note p{margin:6px 0}
.note b{font-weight:600}
ul.plain{padding-left:20px;max-width:78ch}
.dl a{display:inline-block;margin:0 18px 8px 0}
footer{margin-top:60px;border-top:1px solid var(--line);padding:26px 0 50px;color:var(--muted);font-size:14px}
dialog{border:0;padding:0;background:none;max-width:96vw;max-height:96vh}
dialog::backdrop{background:rgba(5,15,22,.82)}
dialog img{max-width:96vw;max-height:94vh;background:#fff;display:block;border-radius:4px}
@media (max-width:860px){.hero{grid-template-columns:1fr;gap:24px;padding-top:28px}.grid.wide{grid-template-columns:1fr}}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
"""

JS = r"""
(function(){
  var cur=null, groups=document.querySelectorAll('.mswitch');
  function setModel(m){
    cur=m;
    document.querySelectorAll('[data-model]').forEach(function(el){el.hidden = el.getAttribute('data-model')!==m;});
    groups.forEach(function(g){g.querySelectorAll('button').forEach(function(b){b.setAttribute('aria-pressed', b.dataset.m===m);});});
  }
  groups.forEach(function(g){g.querySelectorAll('button').forEach(function(b){b.addEventListener('click',function(){setModel(b.dataset.m);});});});
  if(groups.length){setModel(groups[0].querySelector('button').dataset.m);}
  var dlg=document.getElementById('lb'), big=dlg&&dlg.querySelector('img');
  document.addEventListener('click',function(ev){
    var im=ev.target.closest('img[data-zoom]');
    if(im&&dlg&&dlg.showModal){big.src=im.src;big.alt=im.alt;dlg.showModal();}
    else if(ev.target.closest('dialog')){dlg.close();}
  });
})();
"""


def fig_html(path: str, caption: str, zoom=True) -> str:
    return (f'<figure class="f"><img src="{e(path)}" alt="{e(caption)}" loading="lazy" data-zoom>'
            f'<figcaption>{e(caption)}</figcaption></figure>')


def table_html(head, rows) -> str:
    th = ''.join(f'<th>{e(h)}</th>' for h in head)
    tr = ''.join('<tr>' + ''.join(f'<td>{e(c)}</td>' for c in r) + '</tr>' for r in rows)
    cls = 'tw narrow' if len(head) <= 3 else 'tw'
    return f'<div class="{cls}"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


def first_float(s: str) -> float | None:
    m = re.search(r'-?\d+\.\d+', s)
    return float(m.group()) if m else None


def build(args) -> None:
    out = Path(args.out)
    img = out / 'img'
    img.mkdir(parents=True, exist_ok=True)

    ds = parse_report(Path(args.dataset)) if args.dataset else None
    tr = parse_report(Path(args.training)) if args.training else None
    ind = parse_report(Path(args.independent), plain_models=True) if args.independent else None

    # ---- save figures -------------------------------------------------------------------------------
    def dump(rep, prefix):
        saved = {}
        for f in rep['figs']:
            name = '_'.join(x for x in [prefix, re.sub(r'\W+', '', f['model']).lower(), f['key']] if x) + '.png'
            if name in saved:
                continue
            save_img(f['data'], img / name)
            saved[name] = f
        return saved

    ds_saved = dump(ds, 'data') if ds else {}
    tr_saved = dump(tr, 'cv') if tr else {}
    ind_saved = dump(ind, 'test') if ind else {}

    def pick(saved, key, model=''):
        mk = re.sub(r'\W+', '', model).lower()
        for name, f in saved.items():
            if f['key'] == key and re.sub(r'\W+', '', f['model']).lower() == mk:
                return f'img/{name}', f['caption']
        return None

    # ---- facts --------------------------------------------------------------------------------------
    head_tr = tr['tables'][0] if tr and tr['tables'] else ([], [])
    models = [r[0] for r in head_tr[1]]
    hdr = head_tr[0]
    auc_i = next((i for i, h in enumerate(hdr) if h.startswith('ROC-AUC')), 1)
    auc = {r[0]: first_float(r[auc_i]) for r in head_tr[1]}
    sub = tr['sub'] if tr else ''
    m_n = re.search(r'([\d,]+) observations \(([\d,]+) flood / ([\d,]+) non-flood\)', sub)
    n_all, n_fl, n_nf = (m_n.group(1), m_n.group(2), m_n.group(3)) if m_n else ('', '', '')
    share = ''
    if m_n:
        share = f"{int(n_fl.replace(',', '')) / int(n_all.replace(',', '')) * 100:.1f} %"
    block = re.search(r'Block size\s*([\d,]+ m)', tr['text']) if tr else None
    folds = re.search(r'spatial \((\d+) folds\)', tr['text']) if tr else None

    map_rel = ''
    if args.map and Path(args.map).exists():
        dst = img / 'susceptibility_map.png'
        if Path(args.map).resolve() != dst.resolve():
            Image.open(args.map).save(dst, optimize=True)
        map_rel = 'img/susceptibility_map.png'

    about = ''
    if args.about and Path(args.about).exists():
        about = Path(args.about).read_text(encoding='utf-8').strip()

    P = []   # page parts
    P.append(f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FloodML-Geo results</title>
<meta name="description" content="Example results of the FloodML-Geo QGIS plugin: spatially validated flood susceptibility modelling.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,600&family=Public+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<nav class="top"><div class="wrap"><b>FloodML-Geo</b>
<a href="#workflow">Workflow</a><a href="#map">Map</a><a href="#data">Data check</a><a href="#validation">Validation</a><a href="#drivers">Drivers</a><a href="#independent">Independent test</a><a href="#reading">Reading the results</a><a href="#reports">Full reports</a></div></nav>''')

    # hero
    facts = []
    if n_all:
        facts.append(f'<li><span>Locations</span><b>{e(n_all)}</b></li>')
        facts.append(f'<li><span>Flooded</span><b>{e(share)}</b></li>')
    if auc:
        facts.append('<li><span>ROC-AUC, spatial CV</span><b>' + ' / '.join(f'{v:.3f}' for v in auc.values() if v is not None) + '</b></li>')
        facts.append('<li><span>Models</span><b>' + e(' + '.join(models)) + '</b></li>')
    if block:
        facts.append(f'<li><span>Validation block</span><b>{e(block.group(1))}</b></li>')
    hero_img = (f'<figure><img src="{map_rel}" alt="Flood susceptibility classes map" data-zoom></figure>' if map_rel else '')
    P.append(f'''<header class="wrap hero"><div>
<h1>FloodML-Geo</h1>
<p class="lead">Flood susceptibility mapping inside QGIS, checked with spatial cross-validation. These are example results.</p>
<ul class="facts">{''.join(facts)}</ul></div>{hero_img}</header>
<p class="ramp" aria-hidden="true"><i style="background:var(--c1)"></i><i style="background:var(--c2)"></i><i style="background:var(--c3)"></i><i style="background:var(--c4)"></i><i style="background:var(--c5)"></i></p>
<main class="wrap">''')

    # workflow
    P.append('''<section id="workflow"><h2>Workflow</h2>
<p class="intro">Each tool reads the output of the one before it. The flood raster is an input of the first tool, so no label field is needed on your points or grid.</p>
<div class="steps">
<div><span>01</span><b>Build the table</b><p>Flood raster and predictor rasters, read at your points or grid cells, written to a CSV.</p></div>
<div><span>02</span><b>Check the table</b><p>Class balance, leakage hints, correlation and a suggested block size.</p></div>
<div><span>03</span><b>Train and validate</b><p>Nested spatial cross-validation, confidence intervals, SHAP, residual maps.</p></div>
<div><span>04</span><b>Map</b><p>Susceptibility raster, classes, styles and an extrapolation warning raster.</p></div>
<div><span>05</span><b>Independent test</b><p>Scores on data the models never saw, with an overlap check.</p></div>
<div><span>06</span><b>Self-test</b><p>Runs the whole chain on synthetic data and says whether it works.</p></div>
</div></section>''')

    if map_rel:
        P.append(f'''<section id="map"><h2>Susceptibility map</h2>
<p class="intro">Five classes from the ensemble prediction. With quantile classes each class holds about the same number of cells by design, so the map ranks places against each other. It is not a probability of flooding.</p>
<div class="mapfig">{fig_html(map_rel, args.map_caption or 'Susceptibility classes from the ensemble of models')}</div></section>''')

    # data check
    if ds:
        verdict = [c for c in ds['callouts']]
        advice = [n for n in ds['notes']]
        P.append('<section id="data"><h2>Data check</h2>')
        P.append('<p class="intro">Tool 02 inspects the CSV before any model is trained.</p>')
        figs = ''.join(fig_html(*p) for p in [pick(ds_saved, k) for k in ('class_balance', 'separability', 'correlation', 'distributions', 'missing')] if p)
        P.append(f'<div class="grid">{figs}</div>')
        if len(ds['tables']) > 1:
            P.append('<h3>Variance inflation</h3>' + table_html(*ds['tables'][1]))
        P.append('</section>')

    # validation
    if tr:
        P.append('<section id="validation"><h2>Spatial validation</h2>')
        P.append('<p class="intro">Every record is predicted by a model that did not see it or its neighbourhood. Intervals come from a cluster bootstrap over the spatial blocks.</p>')
        P.append(table_html(*head_tr))
        cm = pick(tr_saved, 'compare')
        fm = pick(tr_saved, 'folds_map')
        ac = pick(tr_saved, 'autocorr')
        P.append('<div class="grid wide">' + ''.join(fig_html(*p) for p in (cm, fm, ac) if p) + '</div>')
        P.append('<h3>One model at a time</h3>')
        sw = '<div class="mswitch" role="group" aria-label="Model">' + ''.join(
            f'<button type="button" data-m="{e(m)}" aria-pressed="false">{e(m)}</button>' for m in models) + '</div>'
        P.append(sw)
        for m in models:
            figs = ''.join(fig_html(*p) for p in [pick(tr_saved, k, m) for k in ('roc', 'pr', 'confusion', 'calibration', 'scores', 'fold_metrics')] if p)
            P.append(f'<div data-model="{e(m)}"><div class="grid">{figs}</div></div>')
        P.append('</section>')

        P.append('<section id="drivers"><h2>What drives the prediction</h2>')
        P.append('<p class="intro">Permutation importance drops each predictor on held-out folds. SHAP shows how each value moves the prediction. Both describe the model, not cause and effect.</p>')
        P.append(sw)
        for m in models:
            figs = ''.join(fig_html(*p) for p in [pick(tr_saved, k, m) for k in ('permutation', 'shap_summary', 'shap_dependence', 'residuals')] if p)
            P.append(f'<div data-model="{e(m)}"><div class="grid wide">{figs}</div></div>')
        notes = [n for n in tr['notes'] if 'Moran' in n or 'missing' in n]
        if notes:
            P.append('<div class="note"><b>Notes from the run</b><ul class="plain">' + ''.join(f'<li>{e(n)}</li>' for n in notes) + '</ul></div>')
        P.append('</section>')

    # independent
    if ind:
        invalid = [n for n in ind['notes'] if n.startswith('NOT INDEPENDENT')]
        P.append('<section id="independent"><h2>Independent test</h2>')
        if invalid:
            P.append('<div class="note bad"><b>Flagged by the safeguard.</b><p>In this example the test table is the training table, so the scores below measure memory, not generalisation. The plugin detects this and refuses to call the result valid. For a real test, use another area, event or year.</p></div>')
        else:
            P.append('<p class="intro">Scores on records the models never saw.</p>')
        if ind['tables']:
            t = table_html(*ind['tables'][0])
            P.append(f'<div class="void" title="Not valid: same records as training">{t}</div>' if invalid else t)
        if invalid:
            P.append('<ul class="plain">' + ''.join(f'<li>{e(n)}</li>' for n in invalid[:1]) + '</ul>')
        mods = [r[0] for r in ind['tables'][0][1]] if ind['tables'] else []
        figs = ''.join(fig_html(*p) for p in [pick(ind_saved, k, m) for m in mods[:1] for k in ('roc', 'confusion', 'calibration')] if p)
        if figs:
            P.append(f'<div class="grid">{figs}</div>')
        P.append('</section>')

    # reading the results
    P.append('<section id="reading"><h2>Reading these results</h2>')
    if about:
        for para in re.split(r'\n\s*\n', about):
            P.append(f'<p style="max-width:72ch">{e(para.strip())}</p>')
    cav = []
    if tr:
        cav = [n for n in tr['text'].split('6 · Interpretation caveats')[-1].split('Generated by')[0].split('. ') if n.strip()]
    P.append('<div class="note"><b>Always true of susceptibility maps</b><ul class="plain">'
             '<li>A predictor must be known before the flood. A layer made from the flood image leaks the answer.</li>'
             '<li>Scores are susceptibility ranks, not flood depth, return period or risk.</li>'
             '<li>Tree models do not enforce the direction you give a predictor; the direction only changes scaling.</li>'
             '<li>Check the extrapolation raster before trusting cells outside the training range.</li></ul></div></section>')

    # reports
    P.append('<section id="reports"><h2>Full reports</h2><p class="intro">The complete files written by the plugin, with every figure and table.</p><p class="dl">')
    for label, p in [('Data check', args.dataset), ('Training and validation', args.training), ('Independent test', args.independent)]:
        if p:
            P.append(f'<a href="reports/{e(Path(p).name)}">{label}</a>')
    P.append('<a href="USER_GUIDE.html">User guide</a></p></section></main>')
    P.append(f'''<footer><div class="wrap">Developed by Md Mominul Islam. Page built from the report files by scripts/build_gallery.py.</div></footer>
<dialog id="lb"><img alt=""></dialog><script>{JS}</script></body></html>''')

    (out / 'index.html').write_text('\n'.join(P), encoding='utf-8')
    summary = dict(models=models, auc=auc, records=n_all, flood=n_fl, nonflood=n_nf,
                   headline=dict(header=head_tr[0], rows=head_tr[1]))
    (out / 'results_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print('wrote', out / 'index.html', 'and', len(ds_saved) + len(tr_saved) + len(ind_saved), 'figures')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dataset'); ap.add_argument('--training'); ap.add_argument('--independent')
    ap.add_argument('--map', help='PNG of the class map exported by tool 04')
    ap.add_argument('--map-caption', dest='map_caption', help='caption under the map in the gallery')
    ap.add_argument('--about', help='text file with a short note about the example (paragraphs separated by a blank line)')
    ap.add_argument('--out', default='docs')
    build(ap.parse_args(argv))


if __name__ == '__main__':
    sys.exit(main())
