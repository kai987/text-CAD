"""R02 drafting choices adapted from Tokyo Construction Bureau, April 2024.

The reference governs civil engineering, not residential architecture. These
are documented common-rule adaptations; DXF is not an SXF electronic delivery.
Paper measurements are millimetres and model geometry stays at actual size.
"""
REVISION = 'R13'
SCALE = 50
STANDARD = '東京都建設局 CAD製図基準 令和6年4月'
SOURCE_URL = 'https://www.kensetsu.metro.tokyo.lg.jp/documents/d/kensetsu/000067788'
LAYERS = {
    'WALL': 'D-STR-WALL', 'DOOR': 'D-STR-DOOR', 'WINDOW': 'D-STR-WIND',
    'STAIR': 'D-STR-STAI', 'FURNITURE': 'D-BYP-FIXT', 'TEXT': 'D-STR-TXT',
    'DIM': 'D-STR-DIM', 'NORTH': 'D-BMK-NORT',
}
# A1 0.5 group, reduced 50% for the retained A3; 0.125 is rounded to 0.13.
# Dimension pens follow the specific 0.13 mm rule independently.
PENS_MM = {'WALL': .5, 'DOOR': .25, 'WINDOW': .25, 'STAIR': .13,
           'FURNITURE': .13, 'TEXT': .13, 'DIM': .13, 'NORTH': .13}
TEXT_MM = {'room': 3.5, 'value': 2.5, 'small': 1.8, 'title': 5.0}


def canonical_filename(floor):
    return f'{floor:03d}D0PL2-{floor}FPLAN.DXF'
