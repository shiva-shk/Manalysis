"""Build the Supplements Ledger 1 dashboard (one self-contained HTML page).

Usage (from the repo root):
    SUPPLEMENTS_RAW_DIR=/path/to/yearbooks python -m supplements_ledger.build_dashboard [out.html]
"""
import sys, os, re, json, collections
from . import clean
from .families import FAMILY_NAMES

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'supplements_ledger_1.html')


def norm(s):
    return re.sub(r'[^0-9a-z؀-ۿ]', '', s.lower())


def build_data():
    rows, excluded, log = clean.build()
    years = sorted({r['year_j'] for r in rows})
    yi = {y: i for i, y in enumerate(years)}
    n = len(years)
    companies = sorted({r['company'] for r in rows})
    ci = {c: i for i, c in enumerate(companies)}
    forms = sorted({r['form'] for r in rows})
    fi = {c: i for i, c in enumerate(forms)}
    cats = sorted({r['category'] for r in rows})
    ki = {c: i for i, c in enumerate(cats)}
    fams = FAMILY_NAMES
    gi = {c: i for i, c in enumerate(fams)}

    # A product line is one brand (or product name) of one company in one dosage form.
    prod = {}
    lines = []
    for r in rows:
        label = r['brand'] or r['name_en'] or r['name_fa']
        key = (r['company'], norm(label), r['form'])
        p = prod.get(key)
        if p is None:
            p = prod[key] = dict(label=label, fa=r['name_fa'], ci=ci[r['company']], fi=fi[r['form']],
                                 u=[0] * n, r=[0] * n, cat=collections.Counter(), fam=collections.Counter(), idx=len(prod))
        if not p['fa'] and r['name_fa']:
            p['fa'] = r['name_fa']
        y = yi[r['year_j']]
        p['u'][y] += r['units'] or 0
        p['r'][y] += r['value'] or 0
        w = abs(r['value'] or 0) + 1
        p['cat'][r['category']] += w
        p['fam'][r['family']] += w
        lines.append([y, p['idx'], r['strength'], r['flavor'], r['volume'], r['units'], r['value'], 1 if r['flag'] else 0])
    products = []
    for p in sorted(prod.values(), key=lambda p: p['idx']):
        products.append(dict(l=p['label'], fa=p['fa'] if p['fa'] != p['label'] else '', c=p['ci'], f=p['fi'],
                             k=ki[p['cat'].most_common(1)[0][0]], g=gi[p['fam'].most_common(1)[0][0]], u=p['u'], r=p['r']))
    totals = [[sum(p['u'][i] for p in products), sum(p['r'][i] for p in products)] for i in range(n)]
    return dict(years=years, companies=companies, forms=forms, cats=cats, fams=fams, products=products, totals=totals,
                lines=lines, nExcluded=len(excluded), nLines=len(rows)), log


if __name__ == '__main__':
    data, log = build_data()
    tpl = open(os.path.join(HERE, 'dashboard_template.html'), encoding='utf-8').read()
    blob = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    open(OUT, 'w', encoding='utf-8').write(tpl.replace('__DATA__', blob))
    print('saved', OUT, f'{len(blob) / 1e6:.2f} MB data,', len(data['products']), 'product lines')
