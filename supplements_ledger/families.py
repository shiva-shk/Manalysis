"""Keyword rules that place each product in an ingredient family (the supplement equivalent of a generic)."""
import re
FAMS = [
 ('Complete nutrition formulas', r'غذای کامل|enteral|ensure|entera|sustagen|nutrison|infant|formula milk|شیرخشک|فرمولا|پپتاموین|peptamen|تغذیه ای کامل|complete nutrition|اینتراکت'),
 ('Whey protein', r'whey|وی ?پروتئین|پروتئین وی|isolate|ایزوله|concentrate whey'),
 ('Creatine', r'creatine|کراتین|کرآتین'),
 ('Amino acids & BCAA', r'amino|bcaa|گلوتامین|glutamine|آرژنین|arginine|لوسین|leucine|hmb|اسید آمینه|اسیدآمینه|eaa|taurine|تائورین|citrulline|سیترولین|beta.?alanine|بتا آلانین|glycine|گلیسین|lysine|لیزین|tyrosine|carnosine|\\bnac\\b|n-acetyl'),
 ('Carnitine', r'carnitine|کارنیتین'),
 ('Protein, carbohydrate & gainers', r'protein|پروتئین|carbo(?!nate)|\\bcarbs?\\b|کربو|gainer|گینر|\\bmass\\b|ماس گینر|casein|کازئین|calorie|mealreplace|meal replacement|energy gel|ژل انرژی|sport drink|نوشیدنی ورزشی|maltodextrin|ملتودکسترین'),
 ('Pre-workout, caffeine & fat burners', r'caffeine|کافئین|pre.?workout|پری ورک|thermo|ترموژنیک|burner|چربی سوز|slim|لاغری|green tea|چای سبز|cla\b|garcinia|گارسینیا'),
 ('Multivitamin & minerals', r'multi|مولتی|vitamin.*mineral|ویتامین.*مینرال|mineral.*vitamin|prenatal|پری ناتال|پرینتال|centrum|sentrum|senior|essential vitamin'),
 ('Omega-3 & fish oil', r'omega|امگا|fish ?oil|روغن ماهی|cod liver|کادلیور|krill|کریل|flax|کتان|primrose|گل مغربی|borage'),
 ('Coenzyme Q10', r'q10|coq|کو ?کیو|کوآنزیم|کوانزیم|ubiquinol|يوبی'),
 ('Calcium & vitamin D', r'calcium|calsium|calcit|کلسیم|کلسی|کلسيم|osteo|bone|بون|استخوان'),
 ('Vitamin D', r'vitamin ?d|vit ?d|\bd3\b|\bd-?3\b|ویتامین ?د|ویتامين ?د|cholecalciferol|کله? کلسیفرول|ergocalciferol'),
 ('Vitamin C', r'vitamin ?c\b|vit ?c\b|ascorb|ویتامین ?c|ویتامین ?ث|ویتامين ?ث|ويتامين ?c|ويتامين ?ث|vitamin-c|c ?1000|ester-?c'),
 ('Vitamin E', r'vitamin ?e\b|vit ?e\b|tocopher|ویتامین ?e|ویتامین ?ای|ويتامين ?e|ويتامين ?ايي|ويتامين ?اي'),
 ('Vitamin A', r'vitamin ?a\b|vit ?a\b|retinol|ویتامین ?a|ویتامین ?آ|ويتامين ?آ|ويتامين ?a|beta.?carotene|بتاکاروتن'),
 ('B vitamins', r'vitamin ?b|vit ?b|b-?complex|b complex|ب ?- ?کمپلکس|ب کمپلکس|b12|b6|b1\b|thiamin|pyridox|cobalamin|cyanocobal|methylcobal|ویتامین ?ب|ويتامين ?ب|نیاسین|niacin|riboflavin|panthen|پانتوتنیک|inositol|اینوزیتول|choline|کولین'),
 ('Folic acid', r'folic|folate|فولیک|فوليک|اسید فولیک|methylfolate'),
 ('Biotin, hair & nails', r'biotin|بیوتین|بيوتين|hair|مو و ناخن|nail|keratin|کراتین مو|silicon|سیلیکون'),
 ('Collagen & skin', r'collagen|کلاژن|hyaluron|هیالورون|skin|پوست|glutathione|گلوتاتیون|beauty|بیوتی|elastin'),
 ('Joint health', r'glucosamine|گلوکز ?آمین|گلوکزامین|chondroitin|کندروئیتین|کندروتین|msm|joint|مفاصل|arthro|آرترو|cartilage|غضروف|boswellia|بوسولیا|curcumin|کورکومین|turmeric|زردچوبه|fish flex|فلکس|flex|egg ?shell'),
 ('Iron', r'\biron\b|ferrous|ferro|ferr|آهن|hemo|هموفیکس|هم ?آیرون|iron ?bisglycinate|هموگلوبین'),
 ('Zinc', r'zinc|زینک|(?<![\u0600-\u06ff])روی(?![\u0600-\u06ff])'),
 ('Magnesium', r'magnes|منیزیم|منيزيم|\bmg\b.*citrate'),
 ('Selenium & trace minerals', r'selen|سلنیوم|سلنيوم|chrom|کروم|iodine|(?<![\u0600-\u06ff])ید(?![\u0600-\u06ff])|copper|(?<![\u0600-\u06ff])مس(?![\u0600-\u06ff])|potassium|پتاسیم|molybd|boron|(?<![\u0600-\u06ff])بور(?![\u0600-\u06ff])|trace'),
 ('Melatonin & sleep', r'melatonin|ملاتونین|sleep|خواب|insomnia|valerian|والرین|l-theanine|تیانین|relax|ریلکس|calm|کالم'),
 ('Probiotics & digestion', r'probiotic|پروبیوتیک|lacto|لاکتو|bifido|digest|هضم|گوارش|enzyme|آنزیم|fiber|فیبر|psyllium|اسفرزه|prebiotic|synbiotic|سینبیوتیک|liver|کبد|silymarin|سیلیمارین|milk thistle|میلک تیستل|detox'),
 ('Eye health', r'lutein|لوتئین|لوتین|zeaxanthin|bilberry|eye|چشم|بینایی|astaxanthin|آستاگزانتین'),
 ('Women\'s & men\'s health', r'women|woman|زنان|بانوان|menopaus|یائسگی|maca|ماکا|prostate|پروستات|saw palmetto|testosterone|تستوسترون|fertility|باروری|sperm|اسپرم|libido|tribulus|تریبولوس|ginseng|جینسینگ|cranberry|کرنبری|pms\b|premenstrual|\\bmen\\b|\\bman\\b|آقایان|مردان'),
 ('Herbal & plant extracts', r'extract|عصاره|herb|گیاه|spirulina|اسپیرولینا|chlorella|کلرلا|garlic|(?<![\u0600-\u06ff])سیر(?![\u0600-\u06ff])|ginkgo|جینکو|ginger|زنجبیل|propolis|پروپولیس|royal jelly|ژل رویال|honey|عسل|aloe|آلوئه|apple cider|سرکه سیب|cider|vinegar|moringa|مورینگا|saffron|زعفران|nigella|سیاه ?دانه|echinacea|اکیناسه|elderberry|بادمجان|sambucus|ashwagandha|اشواگاندا|rhodiola|resveratrol|رسوراترول|grape|انگور|quercetin|کورستین|olive|زیتون|cinnamon|دارچین|berberine|بربرین|lipoic|\\bala\\b|لیپوئیک'),
 ('Children\'s supplements', r'kid|child|baby|کودک|بچه|junior|ژونیور|teen|نوجوان|pediatric|اطفال|gummy|پاستیل|toffee|تافی'),
 ('Electrolytes & hydration', r'electrolyte|الکترولیت|\bors\b|او ?آر ?اس|hydrat|oral rehydration|ors\b|sodium|سدیم'),
 ('Appetite & weight gain', r'appetite|اشتها|cyprohept|سیپروهپتادین|weight gain|افزایش وزن|apetamin|آپتامین'),
]
FAMILY_NAMES = [n for n, _ in FAMS] + ['Other and mixed formulas']
FAMS = [(n, re.compile(p)) for n, p in FAMS]
def family(ingr, name_en, name_fa, brand, category=''):
    blob=' '.join([ingr or '', name_en or '', name_fa or '', brand or '']).lower()
    for n,p in FAMS:
        if p.search(blob):
            return n
    return 'Other and mixed formulas'
