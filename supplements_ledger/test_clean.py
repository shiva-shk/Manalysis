from supplements_ledger import clean


def test_txt_normalises_letters_and_placeholders():
    assert clean.txt('ويتامين  ك<br>') == 'ویتامین ک'
    assert clean.txt('-------') == ''
    assert clean.txt('نو+D3026:S3026تري') == 'نوتری'


def test_num_handles_commas_marks_and_decimals():
    assert clean.num('3,810,360‬') == 3810360
    assert clean.num('5,158,770.00') == 5158770
    assert clean.num('-') is None
    assert clean.num('') is None


def test_company_merges_variants_and_latin_names():
    assert clean.company('آباداروطب') == 'آبا دارو طب'
    assert clean.company('ABA DAROU TEB') == 'آبا دارو طب'
    assert clean.company('داروسازی خوارزمی') == 'خوارزمی'


def test_form_licensed_status():
    assert clean.form_std('TAB EFF') == 'Effervescent tablet'
    assert clean.form_std('كپسول نرم') == 'Softgel'
    assert clean.form_std('BOTTLE ( POWDER FILLED )') == 'Powder'
    assert clean.licensed_std('YES') == 'Yes'
    assert clean.licensed_std('خير') == 'No'
    assert clean.status_std('توليدي') == 'Own manufacture'


def test_category_does_not_match_inside_words():
    # "مواد" (materials) contains "مو" (hair) but must not be read as hair
    assert clean.category('تامین ویتامین ها و مواد معدنی', '', '') == 'General tonic & energy'
    assert clean.category('پوست، مو و ناخن', '', '') == 'Skin, hair & nails'
    assert clean.category('سایر', 'پروتئین وی', '') == 'Sports nutrition'
