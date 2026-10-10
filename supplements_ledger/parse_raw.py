"""Reader for the Iranian dietary supplement production yearbooks (pipe-style markdown tables).

Point SUPPLEMENTS_RAW_DIR at the folder holding the yearbook files. Each file name must end in
-<year>.md (for example 312b5eee-1396.md); the combined 1390-95 file ends in -1390-95.md.
"""
import re, os, glob, collections

U = os.environ.get("SUPPLEMENTS_RAW_DIR", "/root/.claude/uploads/d7584317-d5b0-5310-b1ed-08509a8b2733/").rstrip("/") + "/"


def _find_files():
    files = {}
    for p in glob.glob(U + "*.md"):
        name = os.path.basename(p)
        if name.endswith("-1390-95.md"):
            files[0] = name
        else:
            m = re.search(r"-(13\d\d|140\d)\.md$", name)
            if m:
                files[int(m.group(1))] = name
    return dict(sorted(files.items()))


FILES = _find_files()
# header keyword -> canonical field
KEYS=[("ردیف","row"),("نام شرکت","company"),("سال تولید","prod_year"),("نام فارسی","name_fa"),
("نام لاتین فرآورده","name_en"),("نام عمومی","name_en"),("نام تجاری","brand"),("نشان تجاری","umbrella"),
("شکل فرآورده","form"),("کد محصول در شرکت","code_co"),("کد محصول در سندیکا","code_synd"),("شماره پروانه","license_no"),
("کد تجاری","code_trade"),("کد شرکت","code_company"),("وضعیت","status"),("لیسانس","licensed"),
("عملکردی","func_group"),("بر اساس ترکیبات","ingr_group"),("تعداد ترکیبات","n_ingr"),("کشور سازنده","mfr_country"),
("شرکت سازنده","manufacturer"),("دارنده پروانه","mah"),("کشور","mah_country"),("میزان مواد","strength"),("طعم","flavor"),
("حجم","volume"),("گروه مصرف","user_group"),("عددی","units"),("ریالی","value_rial"),("توضیحات","notes")]
def canon(h):
    for k,v in KEYS:
        if k in h: return v
    return None
def cells(l): 
    c=[re.sub(r'\s+',' ',x).strip() for x in l.split('|')]
    return c[1:-1]
def load():
    out=[];odd=[]
    for y,f in FILES.items():
        L=open(U+f,encoding='utf-8').read().split('\n')
        hdr=cells(L[2]); cols=[canon(h) for h in hdr]
        buf=None;bi=0
        proc=[]
        for i,l in enumerate(L[3:],4):
            if re.match(r'^\|\s*"\d+<br>',l) and proc:
                pi,pl=proc[-1]
                proc[-1]=(pi,'| '+' | '.join(cells(pl)[:10]+cells(l)[:15])+' |')
            else:
                proc.append((i,l))
        for i,l in proc:
            if not l.strip() and buf is None: continue
            if buf is None: buf=l;bi=i
            else: buf=buf+" "+l
            c=cells(buf)
            if len(c)<len(cols) and not (buf.rstrip().endswith('|') and len(c)<=2 and False):
                if i-bi<8: continue
            if len(c)>len(cols):
                sur=len(c)-len(cols); c2=c[:4]
                for x in c[4:]:
                    if x=='' and sur>0: sur-=1; continue
                    c2.append(x)
                c=c2
            if len(c)!=len(cols): odd.append((y,bi,c)); buf=None; continue
            buf=None
            d=dict(zip(cols,c)); d['year']=y; d['src_line']=bi; d['file']=f
            d=dict(zip(cols,c)); d['year']=y; d['src_line']=i
            out.append(d)
    return out,odd
if __name__ == "__main__":
    r,odd=load(); print(len(r),len(odd))
    for o in odd[:30]: print(o[0],o[1],[x[:40] for x in o[2] if x][:8])
    print(collections.Counter(d['year'] for d in r))
