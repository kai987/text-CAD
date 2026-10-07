"""Verified opening references, separate from permit approval and airflow design.

Tokyo remains an unspecified municipality: Edogawa is a named example only.
Osaka's approximate 0.2 m² guidance is not converted into a statutory maximum.
No numerical Kyoto/Nagoya limit is invented from silence in the reviewed pages.
"""
from math import isfinite

CHECKED_AT = '2026-10-07'
SOURCES = [
    {'id':'attic-edogawa-2026','url':'https://www.city.edogawa.tokyo.jp/documents/1028/toriatukai20260401.pdf','title':'江戸川区 2026-04-01 §9(7), printed p14'},
    {'id':'attic-osaka-2026','url':'https://www.city.osaka.lg.jp/toshikeikaku/cmsfiles/contents/0000021/21604/260401.1-1-1-23.pdf','title':'大阪市 2026-04 §1-18(3), p21'},
    {'id':'attic-kyoto-current','url':'https://www.city.kyoto.lg.jp/tokei/cmsfiles/contents/0000165/165090/HB0504Kijunsousoku2.pdf','title':'京都市 現行ハンドブック 総5-6, p48-51'},
    {'id':'attic-aichi-common-2026','url':'https://www.pref.aichi.jp/uploaded/attachment/605246.pdf','title':'愛知県内共通例規 2026-04-01版, p76-78'},
    {'id':'attic-aichi-scope','url':'https://www.pref.aichi.jp/soshiki/kenchikushido/kenchiku-toriatsukaietc.html','title':'愛知県内全域の共通取扱い・個別確認先'},
    {'id':'attic-nagoya-city','url':'https://www.city.nagoya.jp/jigyou/toshikeikaku/1018015/1018684/1018916/1034621.html','title':'名古屋市現行例規集・県例規との併読'},
]

def text(zh,ja,en):
    return {'zh':zh,'ja':ja,'en':en}

RULES = {
 'tokyo': {'source_ids':['attic-edogawa-2026'], 'scope':'Edogawa example only; actual Tokyo municipality unspecified',
    'numeric_kind':'edogawa_any', 'ratio_divisor':20, 'absolute_area_m2':.6,
    'required_form':None, 'jurisdiction_resolved':False,
    'description':text('东京区市町村未定。江户川区参考：换气开口合计小于阁楼床面积1/20，或不超过0.6㎡；仅为该区例，不代表全都。',
       '東京の区市町村は未定。江戸川区の参考は換気開口合計が床面積1/20未満、又は0.6㎡以下。他区市町村へ一律適用しない。',
       'Tokyo municipality is unspecified. Edogawa reference: total ventilation openings below 1/20 of attic floor area OR at most 0.6 m². This example is not a Tokyo-wide rule.')},
 'osaka': {'source_ids':['attic-osaka-2026'], 'scope':'Osaka City storage attic, excluding lofts',
    'numeric_kind':'approximate_guidance', 'approximate_area_m2':.2,
    'project_ceiling_m2':.2, 'required_form':'fixed_or_movable_louver', 'jurisdiction_resolved':True,
    'description':text('大阪市1-18(3)：非loft阁楼原则不设开口；换气用途约0.2㎡开口可，建具须固定或可动百叶。本方案自设0.2㎡上限，不将“约”改写为法定硬上限。',
       '大阪市1-18(3)：ロフト以外は原則開口不可。換気用約0.2㎡、固定又は可動ガラリ。計画上限0.2㎡は自主設定で、法定の厳密な上限ではない。',
       'Osaka City 1-18(3): non-loft attic openings are generally restricted; ventilation openings of approximately 0.2 m² use fixed or movable louvers. The 0.2 m² project ceiling is voluntary, not an exact statutory maximum.')},
 'kyoto': {'source_ids':['attic-kyoto-current'], 'scope':'Kyoto City current handbook, General 5-6, p48-51',
    'numeric_kind':'not_stated_in_reviewed_section', 'required_form':None, 'jurisdiction_resolved':True,
    'description':text('京都市現行総5-6所查页未给出窗面积数值上限，且阁楼窗不能计为居室有效采光。保留0.18㎡小型换气口，面积及规格须向主管机关核定。',
       '京都市の現行総5-6確認頁に窓面積の数値上限は明記されず、居室の有効採光に算入できない。0.18㎡の小型換気口を保持し、面積・仕様は審査先へ確認。',
       'The reviewed Kyoto General 5-6 pages state no numerical window-area ceiling and do not count attic windows as habitable-room daylight. Retain the small 0.18 m² vent; confirm area and specification with the authority.')},
 'nagoya': {'source_ids':['attic-aichi-common-2026','attic-aichi-scope','attic-nagoya-city'],
    'scope':'Nagoya City plus Aichi prefecture-wide common interpretation; individual confirmation pending',
    'numeric_kind':'not_stated_in_reviewed_section', 'required_form':None, 'jurisdiction_resolved':True,
    'description':text('名古屋市例规入口要求并读爱知县共通例规；2026版小屋裏物置条文76-78页未给出窗面积数值上限。0.18㎡是本方案控制值，仍须确认当地开口取扱。',
       '名古屋市例規と県内共通例規を併読。2026年版の小屋裏物置76-78頁に窓面積の数値上限は明記されない。0.18㎡は計画値で、個別の開口取扱いは審査先へ確認。',
       'Read Nagoya City rules with the prefecture-wide Aichi interpretation. Its 2026 attic pages 76-78 state no numerical window-area ceiling. The 0.18 m² area is a project value; local opening treatment still needs confirmation.')},
}

def review_opening(city, opening_area_m2, attic_reference_area_m2, opening_form):
    """Evaluate a known reference only; never return a building compliance result."""
    if city not in RULES: raise ValueError('Unknown jurisdiction')
    if not all(isinstance(v,(int,float)) and isfinite(v) and v>0 for v in (opening_area_m2,attic_reference_area_m2)):
        raise ValueError('Positive finite opening and reference areas required')
    rule=RULES[city]
    if rule['numeric_kind']=='edogawa_any':
        area_match=opening_area_m2<attic_reference_area_m2/20 or opening_area_m2<=.6
        status='reference_example_matches_actual_municipality_pending'
    elif rule['numeric_kind']=='approximate_guidance':
        area_match=opening_area_m2<=rule['project_ceiling_m2']
        status='within_voluntary_ceiling_for_approximate_guidance'
    else:
        area_match=None;status='numeric_opening_treatment_pending_authority'
    form_match=(opening_form in ('fixed_aluminium_louver','movable_louver')) if rule['required_form'] else None
    return {'checked_at':CHECKED_AT,'scope':rule['scope'],'source_ids':rule['source_ids'],
       'opening_area_m2':opening_area_m2,'opening_count':1,'opening_form':opening_form,
       'area_basis':'Gross wall aperture including frame, not glass area or aerodynamic free area',
       'attic_reference_area_m2':attic_reference_area_m2,
       'attic_reference_area_status':'Conservative model projection excluding hatch; not approved statutory floor area',
       'area_reference_match':area_match,'form_reference_match':form_match,'status':status,
       'actual_confirming_authority':None,'effective_ventilation_area_m2':None,
       'fire_equipment_specification':None,'statutory_compliance_result':None,
       'remaining_checks':['Actual confirming authority and storage-attic classification',
          'Manufacturer free area, ventilation path, weather/insect protection',
          'Fire district, spreading-fire exposure and approved opening equipment'],
       'description':rule['description']}
