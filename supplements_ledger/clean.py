"""Cleaning rules for the supplement yearbooks: one tidy record per product, company and year."""
import re, json, collections
from . import parse_raw as parse

BIDI = re.compile(r'[​‎‏‪-‮⁦-⁩﻿]')
PDIG = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')


def txt(s):
    """Normalise a free-text cell: strip bidi marks, br tags, Arabic letter variants, extra spaces."""
    if s is None:
        return ''
    s = s.replace('<br>', ' ').replace('<br/>', ' ')
    s = BIDI.sub('', s)
    s = s.replace('ي', 'ی').replace('ك', 'ک').replace('ى', 'ی').replace('ة', 'ه').replace('ۀ', 'ه')
    s = s.replace('‌', ' ').replace('\xa0', ' ').translate(PDIG)
    s = s.replace('"', '').replace('“', '').replace('”', '')
    s = re.sub(r'\+?[A-Z]\d{2,5}:[A-Z]\d{2,5}', '', s)  # stray spreadsheet cell references left in some names
    s = re.sub(r'\s+', ' ', s).strip()
    if re.fullmatch(r'[-_—–.…\s]*', s) or s in ('ندارد', 'nan', 'NAN'):
        return ''
    return s


def num(s):
    s = BIDI.sub('', s or '').translate(PDIG).replace(',', '').replace(' ', '')
    if s in ('', '-'):
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return int(round(v))


# ---------- company names ----------
LATIN2FA = {
 'ABA DAROU TEB': 'آبا دارو طب', 'ABIAN DAROU': 'ابیان دارو', 'ABIAN PHARMED': 'ابیان فارمد', 'ADONIS KISH': 'آدونیس کیش',
 'ALASHT PHARMED': 'آلاشت فارمد', 'ALBORZ DAROU': 'البرز دارو', 'AMIN': 'امین', 'ARIAN SALAMAT SINA': 'آرین سلامت سینا',
 'ARYAN SANA': 'آریان سناء', 'ASHBAL CHEMI': 'اشبال شیمی', 'ATLAS TEJARAT SOBHAN': 'اطلس تجارت سبحان',
 'AYLAR TEB AZAR': 'آیلار طب آذر', 'BARSAM PHARMED ALBORZ': 'برسام فارمد البرز', 'BEHESTAN BEHDASHT': 'بهستان بهداشت',
 'BEHSAZAN PAZHOUHAN OMID ARIA': 'به سازان پژوهان امید آریا', 'BONYAN SALAMAT KASRA': 'بنیان سلامت کسری', 'COSAR': 'کوثر',
 'DAANA': 'دانا', 'DANESH PAJHOHAN ARYA DARU': 'دانش پژوهان آریا دارو', 'DAY MAYBOD': 'دی میبد',
 'DONYA DAROU SEPEHR': 'دنیا دارو سپهر', 'DR ABIDI': 'دکتر عبیدی', 'EXIR': 'اکسیر', 'EXXON PHARMED': 'اکسون فارمد ایرانیان',
 'FANDA': 'فن آوریهای نوین دارویی آتیه (فندا)', 'FOROOGH SALAMAT MEHREGAN': 'فروغ سلامت مهرگان',
 'GITI SALAMAT ARIA': 'گیتی سلامت آریا', 'GOLDAROU': 'گل دارو', 'HAKIM': 'حکیم', 'HAKIMAN TEB KAR': 'حکیمان طب کار',
 'HEALIA PHARMED': 'هیلیا فارمد', 'HEALTH PARSIAN': 'هلث پارسیان', 'JAHAN PHARMED ARIA': 'جهان فارمد آریا',
 'JALINOUS': 'جالینوس', 'KAREN': 'کارن', 'KARNIC DAROU': 'کارنیک دارو', 'KHARAZMI': 'خوارزمی',
 'KHOSRO MEDISA TEB': 'خسرو مدیسا طب', 'KIA KAM PHARMED': 'کیاکام فارمد', 'KIAN TEB PASARGAD': 'کیان طب پاسارگاد',
 'KIMIA SALAMAT IRANIAN': 'کیمیا سلامت ایرانیان', 'KIMIA ZIST PARSIAN': 'کیمیا زیست پارسیان', 'LIVAR': 'لیوار', 'MAAD': 'ماد',
 'MAHAN DAROU DARMAN': 'مهان دارو درمان', 'MAHBAN DAROU': 'مهبان دارو', 'MEHR DAROU': 'مهر دارو',
 'NEDA DARMAN NIMA': 'ندا درمان نیما', 'NEXUS': 'نکسوس', 'NIK CINA EXIR': 'نیک سینا اکسیر',
 'OFOGH TADBIR SALAMAT': 'افق تدبیر سلامت', 'PAD JONDI SHAPOUR': 'پاد جندی شاپور', 'PARS GITA DAROU': 'پارس گیتا دارو',
 'PARS HAYAN': 'پارس حیان', 'PARS NAMAVARAN SALAMAT': 'پارس نام آوران سلامت',
 'PAZHOUHESH GOSTARAN TAGHZIEH ASAN': 'پژوهش گستران تغذیه آسان', 'PHARMED SALAMAT SINA': 'فارمد سلامت سینا',
 'POURATEB GOSTAR IRANIAN': 'پوراطب گستر ایرانیان', 'QIMIA MOKAMMEL ARAD': 'کیمیا مکمل آراد', 'RAZAK': 'رازک',
 'RAZAN PHARMED IRANIAN': 'رازان فارمد ایرانیان', 'ROUGINE': 'روژین فارمد', 'ROUGINE PHARMED': 'روژین فارمد',
 'SAG PAD DAROU': 'ساج پاد دارو', 'SAMANIK SALAMAT GOSTAR': 'سمانیک سلامت گستر', 'SAMAR TEB DARMAN': 'سمر طب درمان',
 'SHAHRE DAROU': 'شهردارو', 'SHARI': 'شاری', 'SIMORGH DAROU ATTAR': 'سیمرغ داروی عطار', 'TABIAT ZENDEH': 'طبیعت زنده',
 'TACHRA PHARMED': 'تچرا فارمد', 'TADBIR KALA JAM': 'تدبیر کالای جم', 'TAVAN EXIR PHARMED': 'توان اکسیر فارمد',
 'TEB MOFID NIKAN': 'طب مفید نیکان', 'TEHRAN CHEMIE': 'تهران شیمی', 'TEHRAN DAROU': 'تهران دارو',
 "TOSE'E SABZ TAMIM": 'توسعه سبز تمیم', 'TRITA DAROU ARTA': 'تریتا داروی آرتا', 'VANA DAROU GOSTAR': 'وانا داروگستر',
 'VITA ARIA': 'ویتا آریا',
}
# spelling variants / renamed entries -> one canonical name (only confident ones)
VARIANTS = {
 'آبا دارد طب': 'آبا دارو طب', 'آبا داروطب': 'آبا دارو طب', 'آباداروطب': 'آبا دارو طب',
 'امبد دارو سلامت': 'امید دارو سلامت', 'امیدطب کوشا': 'امید طب کوشا', 'انی درمان': 'آنی درمان',
 'ایده داروطب': 'ایده دارو طب', 'ایران هو.رمون': 'ایران هورمون', 'برسام فارمد': 'برسام فارمد البرز',
 'بنیان سلامت کسرا': 'بنیان سلامت کسری', 'بهارپایا': 'بهار پایا', 'به شاد دارو': 'بهشاد دارو',
 'تأمین گستر الوند': 'تامین گستر الوند', 'توان اکسیرفارمد': 'توان اکسیر فارمد', 'توسه تجارت قطره حیات': 'توسعه تجارت قطره حیات',
 'تولیدی تجاری خوش شیمی فارمد': 'خوش شیمی فارمد', 'تولیدی دارویی بهداشتی لیوار': 'لیوار', 'جابرابن حیان': 'جابر ابن حیان',
 'خرمشهردارو': 'خرمشهر دارو', 'داروافشان شایگان': 'دارو افشان شایگان', 'داروجویان حیات': 'دارو جویان حیات',
 'داروسلامت فارمد': 'دارو سلامت فارمد', 'داروپژوهان پاسارگاد': 'دارو پژوهان پاسارگاد', 'دنیا داروسپهر': 'دنیا دارو سپهر',
 'دینه': 'دینه ایران', 'مجتمع صنایع دینه ایران': 'دینه ایران', 'رازان فارمد': 'رازان فارمد ایرانیان', 'روژین': 'روژین فارمد',
 'رژین فارمد': 'روژین فارمد', 'رستا ژن دارو': 'رستاژن دارو', 'رستاژن': 'رستاژن دارو', 'روزدارو': 'روز دارو',
 'ساپونین ایرانیان': 'ساپونین ایران', 'ساچ پاد دارو': 'ساج پاد دارو', 'سانافارمد': 'سانا فارمد', 'سمرطب درمان': 'سمر طب درمان',
 'سوناطب پارسه': 'سونا طب پارسه', 'شهر دارو': 'شهردارو', 'شهردازو': 'شهردارو',
 'شیر خشک نوزاد پگاه شهرکرد': 'شیرخشک نوزاد پگاه شهرکرد', 'شیرخشگ نوزاد پگاه': 'شیرخشک نوزاد پگاه شهرکرد',
 'فارماشیمی': 'فارما شیمی', 'فرنوش دارو طب': 'فرنوش داروطب', 'لابراتوارهای داروهای گیاهی طبیعت زنده': 'طبیعت زنده',
 'مهردارو': 'مهر دارو', 'نو آوری زیستی گویا': 'نوآوری زیستی گویا', 'هیلیافارمد': 'هیلیا فارمد', 'وانا دارو گستر': 'وانا داروگستر',
 'ویتاآریا': 'ویتا آریا', 'ویتا بیوتیکس': 'ویتابیوتیکس فارمد', 'ویتابیوتیکس': 'ویتابیوتیکس فارمد',
 'ویتابیوتیکس تهران': 'ویتابیوتیکس فارمد', 'پوراطب': 'پوراطب گستر ایرانیان', 'پادجندی شاپور': 'پاد جندی شاپور',
 'حکیمان طب': 'حکیمان طب کار', 'الشن دارو مکمل سرزمین پارس': 'الشن دارو', 'اکسون فارمد': 'اکسون فارمد ایرانیان',
 'البرز دلرو': 'البرز دارو', 'فن آوریهای نوین دارویی آتیه فندا': 'فن آوریهای نوین دارویی آتیه (فندا)',
 'امید پارسینا دماوند': 'امید پارسینا دماوند', 'داروسازی آنوشا': 'آنوشا', 'داروسازی تهران شیمی': 'تهران شیمی',
 'داروسازی حکیم': 'حکیم', 'داروسازی خوارزمی': 'خوارزمی', 'داروسازی دکتر عبیدی': 'دکتر عبیدی', 'داروسازی زهراوی': 'زهراوی',
 'داروسازی پارس حیان': 'پارس حیان', 'داروسازی گل دارو': 'گل دارو',
}


def company(raw):
    s = txt(raw)
    key = re.sub(r'\s+', ' ', s.upper().replace('_', ' '))
    if key in LATIN2FA:
        return LATIN2FA[key]
    if s in VARIANTS:
        return VARIANTS[s]
    return s


# ---------- dosage form ----------
def form_std(raw):
    s = txt(raw).lower()
    if not s:
        return ''
    rules = [
        (r'جوشان|eff', 'Effervescent tablet'),
        (r'جویدنی|chew|مکیدنی', 'Chewable tablet'),
        (r'odt|باز شونده|melt in mouth', 'Orodispersible (melt in mouth)'),
        (r'زیر ?زبان|subling', 'Sublingual tablet'),
        (r'پاستیل|gummy|تافی|toffee|شوکوبار|بار$|^بار|^bar', 'Gummy / chew / bar'),
        (r'اسپری|spray', 'Spray'),
        (r'سافت ?ژل|soft ?gel|نرم|liquid filled|لیکوئید|ژلاتین', 'Softgel'),
        (r'پلت|pellet|رهش|انتریک', 'Capsule (modified release / pellets)'),
        (r'قرص و کپسول|tab , softgel', 'Mixed (tablet and capsule)'),
        (r'کپسول|cap', 'Capsule'),
        (r'قرص|tab', 'Tablet'),
        (r'ساشه|sachet', 'Sachet / stick'),
        (r'ورزشی|powd|پودر|bottle|شیشه', 'Powder'),
        (r'شربت|syrup|سوسپانسیون', 'Syrup / suspension'),
        (r'قطره|drop', 'Oral drops'),
        (r'ویال|vial|shot|blister', 'Vial / shot / ampoule'),
        (r'محلول|مایع|solution', 'Oral solution / liquid'),
    ]
    for pat, name in rules:
        if re.search(pat, s):
            return name
    return 'Other'


def licensed_std(raw):
    s = txt(raw).lower()
    if s in ('بله', 'yes'):
        return 'Yes'
    if s in ('خیر', 'no', 'خیز'):
        return 'No'
    return ''


def status_std(raw):
    s = txt(raw)
    if not s:
        return ''
    if 'قرارداد' in s and s != 'تولید قراردادی-تولید مستقیم':
        return 'Contract manufactured'
    if 'بالک' in s:
        return 'Bulk'
    if 'وارد' in s:
        return 'Imported'
    if s in ('تولیدی', 'تولید', 'تولیدی/فعال', 'در حال تولید', 'فعال', 'تولید قراردادی-تولید مستقیم'):
        return 'Own manufacture'
    return ''


COUNTRY = {'ایران': 'Iran', 'ايران': 'Iran', 'آیران': 'Iran', 'هلند': 'Netherlands', 'انگلستان': 'United Kingdom',
           'آمریکا': 'USA', 'امریکا': 'USA', 'usa': 'USA', 'germany': 'Germany', 'آلمان': 'Germany', 'swiss': 'Switzerland',
           'کانادا': 'Canada', 'ایتالیا': 'Italy', 'پرتغال': 'Portugal', 'هندوستان': 'India', 'اندونزی': 'Indonesia',
           'دانمارک': 'Denmark', 'استرالیا': 'Australia'}


def country(raw):
    s = txt(raw)
    return COUNTRY.get(s, COUNTRY.get(s.lower(), '')) if s else ''


# ---------- functional category ----------
CAT_RULES = [
    ('Sports nutrition', r'ورزش|پروتئین|کربوهیدرات|عضله ?سازی|کراتین|bcaa|whey|protein|creatine|amino'),
    ('Weight management', r'لاغر|چاقی|کاهش وزن|افزایش وزن|وزن'),
    ('Medical / special nutrition', r'غذای کامل|بیماران بدحال|بیماری های خاص|بیماریهای خاص|سالمند|شیر ?خشک|نوزاد'),
    ('Diabetes & blood sugar', r'دیاب|قند'),
    ('Kidney & liver', r'کلیو|کبد'),
    ('Pregnancy, lactation & women', r'باردار|شیرده|بانوان|زنان|یائسگی|باروری بانوان|قاعدگی'),
    ("Men's health", r'آقایان|پروستات|جنسی|مردان'),
    ('Children', r'کودک'),
    ('Anemia & iron', r'کم ?خونی|آهن'),
    ('Immune support', r'ایمنی'),
    ('Antioxidant', r'اکسیدان'),
    ('Joint & cartilage', r'غضروف|مفاصل|مفصل|تسکین درد'),
    ('Calcium, bone & vitamin D', r'کلسیم|استخوان|ویتامین د'),
    ('Skin, hair & nails', r'پوست|(?<![\u0600-\u06ff])مو(?![\u0600-\u06ff])|ناخن|کلاژن|بافت پیوندی'),
    ('Heart, lipids & omega-3', r'قلب|چربی|امگا|omega'),
    ('Eye health', r'چشم|بینایی'),
    ('Brain, nerves & sleep', r'حافظه|خواب|عصب|ذهنی|اسپاسم|تمرکز|استرس'),
    ('Digestive', r'گوارش|هضم|پروبیوتیک|روده|probiotic'),
    ('Appetite', r'اشتها'),
    ('General tonic & energy', r'تقویت کننده|عمومی|انرژی|خستگی|ویتامین ها|مولتی|multivit'),
]
FALLBACK = [  # applied to ingredient group + latin names when the functional group is "other"/blank
    ('Sports nutrition', r'whey|protein|creatine|bcaa|amino|پروتئین|کراتین|carnitine|کارنیتین|گلوتامین|glutamine'),
    ('Heart, lipids & omega-3', r'omega|امگا|fish oil|coq10|کوآنزیم'),
    ('Anemia & iron', r'\biron\b|ferr|آهن|فولیک|folic'),
    ('Calcium, bone & vitamin D', r'calcium|کلسیم|vitamin d|ویتامین د|magnesium|منیزیم'),
    ('Immune support', r'zinc|زینک|vitamin c|ویتامین c|ویتامین ث|echinacea|elderberry'),
    ('Joint & cartilage', r'glucosamine|chondroitin|گلوکزامین|collagen type ii'),
    ('Skin, hair & nails', r'biotin|بیوتین|collagen|کلاژن|hair'),
    ('Antioxidant', r'lutein|لوتئین|antioxid|resveratrol|گلوتاتیون|glutathione|سلنیوم|selenium'),
    ('Digestive', r'probiotic|لاکتو|lactobac|enzyme|فیبر|fiber'),
    ('Brain, nerves & sleep', r'melatonin|ملاتونین|b12|b1 |ginkgo|جینکو'),
    ('General tonic & energy', r'multivit|مولتی|vitamin|ویتامین|mineral|مینرال|ginseng|جینسینگ'),
]


def category(fg, ingr, nm):
    s = fg.lower()
    if s and s not in ('سایر', 'ساير'):
        for name, pat in CAT_RULES:
            if re.search(pat, s):
                return name
    blob = f'{ingr} {nm}'.lower()
    for name, pat in FALLBACK:
        if re.search(pat, blob):
            return name
    return 'Other / unclassified'


# ---------- main ----------
def build():
    rows, odd = parse.load()
    log = collections.Counter()
    out, excluded = [], []
    for d in rows:
        y = d['year']
        rid = d.get('row', '').strip()
        early = (y == 0)
        if y == 0:  # 1390-95 yearbook: the sales year sits in the "production year" column
            pyr = d.get('prod_year', '').strip()
            if pyr == '96-06':
                log['dropped: 1396 half-year lines in the 1390-95 file (1396 yearbook has the full year)'] += 1
                excluded.append(dict(year=1396, reason='Overlaps the 1396 yearbook (partial 1396 line in 1390-95 file)', company=company(d['company']), detail=txt(d.get('name_fa', ''))[:150]))
                continue
            y = 1300 + int(pyr.split('-')[0].split('.')[0])
            d['year'] = y
        # structural junk: totals / blank lines at the bottom of some sheets
        if not re.fullmatch(r'\d+', rid):
            log['dropped: blank / total / stray rows'] += 1
            excluded.append(dict(year=y, reason='Blank, total or stray row', company='', detail=' | '.join(str(v) for k, v in d.items() if v and k not in ('year', 'src_line', 'row'))[:150]))
            continue
        if d.get('units', '').strip() == '-' and d.get('value_rial', '').strip() == '-':
            log['dropped: company reported zero sales / no product info (placeholder)'] += 1
            excluded.append(dict(year=y, reason='Placeholder: no product, company reported nothing sold', company=company(d['company']), detail=txt(d.get('notes', ''))[:150]))
            continue
        if not (txt(d.get('name_fa', '')) or txt(d.get('name_en', '')) or txt(d.get('brand', ''))):
            log['dropped: company reported zero sales / no product info (placeholder)'] += 1
            excluded.append(dict(year=y, reason='Placeholder: no product, company reported nothing sold', company=company(d['company']), detail=txt(d.get('notes', ''))[:150]))
            continue
        r = {}
        r['year_j'] = y
        r['year_g'] = y + 621
        r['src_row'] = int(rid)
        r['company'] = company(d['company'])
        r['company_raw'] = txt(d['company'])
        py = txt(d.get('prod_year', '')).replace(',', '')
        if py.isdigit():
            py = int(py)
            py = py + 1300 if py < 200 else py
        else:
            py = ''
        r['prod_year'] = py
        r['name_fa'] = txt(d.get('name_fa', ''))
        r['name_en'] = txt(d.get('name_en', ''))
        r['brand'] = txt(d.get('brand', ''))
        r['umbrella'] = txt(d.get('umbrella', ''))
        r['strength'] = txt(d.get('strength', ''))
        r['flavor'] = txt(d.get('flavor', ''))
        r['volume'] = txt(d.get('volume', ''))
        r['form_raw'] = txt(d.get('form', ''))
        r['form'] = form_std(d.get('form', '')) or 'Not stated'
        r['licensed'] = licensed_std(d.get('licensed', ''))
        r['status'] = status_std(d.get('status', ''))
        r['func_raw'] = txt(d.get('func_group', ''))
        r['ingr'] = txt(d.get('ingr_group', ''))
        r['user_group'] = txt(d.get('user_group', ''))
        r['category'] = category(r['func_raw'], r['ingr'], f"{r['name_en']} {r['name_fa']}")
        r['mfr_country'] = country(d.get('mfr_country', ''))
        r['manufacturer'] = txt(d.get('manufacturer', ''))
        r['mah'] = txt(d.get('mah', ''))
        r['units'] = num(d.get('units', ''))
        r['value'] = num(d.get('value_rial', ''))
        flags = []
        if r['units'] is None:
            flags.append('Missing units')
        if r['value'] is None:
            flags.append('Missing rial value')
        if r['units'] is not None and r['units'] < 0:
            if r['value'] is not None and r['value'] > 0:
                r['units'] = -r['units']
                flags.append('Negative units sign fixed')
            else:
                flags.append('Negative sales (return)')
        if r['units'] == 0 or r['value'] == 0:
            flags.append('Zero sales')
        if r['units'] and r['value'] and r['units'] > 0 and r['value'] > 0 and r['value'] / r['units'] < 100:
            flags.append('Check: unit price under 100 rial')
        r['flag'] = '; '.join(flags)
        r['notes'] = txt(d.get('notes', ''))
        if r['notes'] and not flags:
            pass
        r['src_file'] = 'Yearbook 1390-95' if early else f'Yearbook {y}'
        r['src_line'] = d['src_line']
        out.append(r)
    # exact repeats of a line within the same year
    seen, final = {}, []
    for r in out:
        k = (r['year_j'], r['company'], r['name_fa'], r['name_en'], r['brand'], r['form_raw'], r['strength'], r['flavor'], r['volume'], r['units'], r['value'])
        if k in seen:
            if not (r['units'] or r['value']):
                log['dropped: exact repeat of a zero-sales line'] += 1
                excluded.append(dict(year=r['year_j'], reason='Exact repeat of a zero-sales line', company=r['company'], detail=(r['name_fa'] or r['name_en'])[:150]))
                continue
            r['flag'] = (r['flag'] + '; ' if r['flag'] else '') + 'Possible duplicate line'
            seen[k]['flag'] = (seen[k]['flag'] + '; ' if seen[k]['flag'] and 'Possible duplicate' not in seen[k]['flag'] else seen[k]['flag']) or 'Possible duplicate line'
            if 'Possible duplicate' not in seen[k]['flag']:
                seen[k]['flag'] += '; Possible duplicate line'
        else:
            seen[k] = r
        final.append(r)
    return final, excluded, log


if __name__ == '__main__':
    out, excl, log = build()
    print(len(out), len(excl), dict(log))
    json.dump(out, open('clean.json', 'w'), ensure_ascii=False)
    json.dump(excl, open('excluded.json', 'w'), ensure_ascii=False)
    print(collections.Counter(r['category'] for r in out).most_common())
    print(collections.Counter(r['form'] for r in out).most_common())
    print(collections.Counter(r['flag'] for r in out).most_common())
    print(len(set(r['company'] for r in out)))
