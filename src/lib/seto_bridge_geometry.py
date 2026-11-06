"""Photo-informed North/South Bisan-Seto suspension bridges, mm and Z-up.

This dependency-free specification drives CAD, drawings and validation. Public
control dimensions are separated from appearance assumptions; it is neither a
survey nor an engineering design of the actual bridge.
"""
from copy import deepcopy
from functools import lru_cache
from math import cos, sin, pi, ceil, sqrt
from .seto_bridge_activity import activity_manifest, activity_specs, rail_height_mm, road_height_mm

MODEL_ID = 'seto-ohashi'
REVISION = 'BRIDGE-R05'
GROUPS = ('environment', 'foundations', 'towers', 'cables', 'hangers', 'truss', 'road', 'railway', 'traffic', 'vessels', 'trains')
GROUP_NAMES = {
    'environment': {'zh': '海面与岛屿示意', 'ja': '海面・島の概形', 'en': 'Sea and island context'},
    'foundations': {'zh': '基础与锚碇', 'ja': '基礎・アンカレイジ', 'en': 'Foundations and anchorages'},
    'towers': {'zh': '主塔与横撑', 'ja': '主塔・横構', 'en': 'Towers and cross-bracing'},
    'cables': {'zh': '主缆', 'ja': 'メインケーブル', 'en': 'Main cables'},
    'hangers': {'zh': '吊索', 'ja': 'ハンガー', 'en': 'Hangers'},
    'truss': {'zh': '补刚钢桁架', 'ja': '補剛トラス', 'en': 'Stiffening truss'},
    'road': {'zh': '上层公路', 'ja': '上層・道路', 'en': 'Upper road deck'},
    'railway': {'zh': '下层铁路与预留空间', 'ja': '下層・鉄道と留保空間', 'en': 'Lower railway and reserved space'},
    'traffic': {'zh': '行驶车辆', 'ja': '走行車両', 'en': 'Road traffic'},
    'vessels': {'zh': '游船', 'ja': '遊覧船', 'en': 'Sightseeing boats'},
    'trains': {'zh': '下层行驶电车', 'ja': '下層・走行電車', 'en': 'Lower-deck electric trains'},
}
NAMES = {'zh': '濑户大桥 · 南北备赞双桥', 'ja': '瀬戸大橋・南北備讃瀬戸大橋', 'en': 'Seto Ohashi · North and South Bisan-Seto'}
REFERENCES = [
    {'title': 'JB本四高速・北備讃瀬戸大橋（諸元・実景）', 'url': 'https://www.jb-honshi.co.jp/seto-ohashi/shoukai/6kyou5.html', 'notes': '北橋1538 m、274+990+274 m、主塔頂T.P.+184 m、主ケーブル直径998 mm（被覆を除く）。'},
    {'title': 'JB本四高速・南備讃瀬戸大橋（諸元・実景）', 'url': 'https://www.jb-honshi.co.jp/seto-ohashi/shoukai/6kyou6.html', 'notes': '南橋1648 m、274+1100+274 m、主塔頂T.P.+194 m、主ケーブル直径1062 mm（被覆を除く）。'},
    {'title': 'JB本四高速・北備讃瀬戸大橋公式側面図', 'url': 'https://www.jb-honshi.co.jp/corp_index/technology/introduction/introduction_kitabisan.html', 'notes': '北側BB1A・BB2P・BB3P・共用BB4Aの配置。'},
    {'title': 'JB本四高速・南備讃瀬戸大橋公式側面図', 'url': 'https://www.jb-honshi.co.jp/corp_index/technology/introduction/introduction_minamibisan.html', 'notes': '共用BB4A・BB5P・BB6P・BB7Aの配置と門形主塔、実景写真。'},
    {'title': '本四公団・南備讃瀬戸大橋の建設概要', 'url': 'https://www.jstage.jst.go.jp/article/coj1975/22/11/22_12/_pdf/-char/en', 'notes': '歴史的な側面図。主缆100m垂度と南側1%縦断勾配。現在の測量データではない。'},
    {'title': '本四公団・南北備讃瀬戸大橋共用アンカレイジの施工', 'url': 'https://www.jstage.jst.go.jp/article/coj1975/22/11/22_49/_pdf', 'notes': 'BB4A外包寸法、93m道路凸点、49mの接続区間、印刷50頁Fig.2のV溝底T.P.+52.500m。通行部の細部は概形。'},
    {'title': '川崎製鉄技報 18巻4号 1986・本州四国連絡橋の補剛桁組立工事', 'url': 'https://www.jfe-steel.co.jp/archives/ksc_giho/18-4/j18-372-378.pdf', 'notes': '印刷373頁 Fig.3：北橋主桁間30 m、桁高13 m、主缆間35 m。本文：格点13.2 m、鋼板組立箱形部材、在来線と新幹線留保空間。'},
    {'title':'瀬戸内Finder・瀬戸大橋クルーズの実景','url':'https://www.setouchi.travel/jp/trip-ideas/f20544/', 'notes':'白い船体、濃色の客室窓、露天甲板などの外観参考。船名・商標は複製せず、形状・寸法は独自の概念モデル。'},
    {'title':'JR西日本・マリンライナー公式車両紹介','url':'https://www.jr-odekake.net/railroad/train/marineliner/', 'notes':'銀色車体・青帯などの外観参考。モデルの2列×4両は独自の通勤電車概形で、マリンライナーの正確な編成・寸法・実際の運行ではない。'},
    {'title':'本四公団・北備讃瀬戸大橋塔架設工事（建設の機械化1986年5月）','url':'https://jcmanet.or.jp/bunken/wp-content/uploads/1986/jcma-1986_05.pdf','notes':'印刷34頁Fig.3：十字形3セル塔柱、塔頂7.1×4.8m・基部約10.7×4.8m、ケーブル間35m、上部2X・下部Xと山形の横構。個別塔の厳密標高・内部板厚は復元しない。'},
    {'title':'駒井鉄工・南備讃瀬戸大橋の概要と施工試験','url':'https://www.komaihaltec.co.jp/tec/komai/1986/vol5-12.pdf','notes':'印刷124頁Fig.1の塔正面図と実景を参照。上部2X、長い空腹区間、橋面下のXと山形。部材の取り合い・南橋断面の北橋準用は外観近似。'},
    {'title':'JB本四高速・長大橋の維持管理（2025年度講習資料）','url':'https://www.j-cma.jp/jcma-pics/10022220_HjZm38.pdf','notes':'PDF11頁の共用アンカレイジ実景。下部の絞り、橋軸端面の中央くぼみ、水平打継ぎ、下部の濃色保護面を参考。くぼみ深さ・仕上げ寸法は写真合わせの仮定。'},
]
P = {
    'north_length_mm': 1538000, 'south_length_mm': 1648000,
    'north_main_span_mm': 990000, 'south_main_span_mm': 1100000,
    'side_span_mm': 274000,
    'north_tower_top_mm': 184000, 'south_tower_top_mm': 194000,
    'north_cable_diameter_mm': 998, 'south_cable_diameter_mm': 1062,
    'shared_anchor_half_length_mm': 24500,
    'north_end_connection_mm': 48200, 'south_end_connection_mm': 50600,
    'truss_centres_mm': 30000, 'truss_height_mm': 13000,
    'cable_centres_mm': 35000, 'nominal_panel_mm': 13200,
    # Controls below are appearance assumptions, NOT surveyed elevations.
    'road_deck_z_mm': 93000, 'rail_deck_z_mm': 80000,
    'road_width_mm': 26000, 'road_effective_width_mm': 22500,
    'rail_deck_width_mm': 30000, 'width_mm': 37000,
    'north_cable_mid_z_mm': 91500, 'south_cable_mid_z_mm': 91500,
    'anchor_cable_z_mm': 83000,
    'sea_z_mm': 0, 'context_width_mm': 760000,
}


def parameters():
    p = deepcopy(P)
    p['north_start_mm'] = -p['shared_anchor_half_length_mm'] - p['north_length_mm']
    p['north_end_mm'] = -p['shared_anchor_half_length_mm']
    p['south_start_mm'] = p['shared_anchor_half_length_mm']
    p['south_end_mm'] = p['shared_anchor_half_length_mm'] + p['south_length_mm']
    p['overall_length_mm'] = p['south_end_mm'] + p['south_end_connection_mm'] - p['north_start_mm'] + p['north_end_connection_mm']
    p['north_outer_end_mm'] = p['north_start_mm']-p['north_end_connection_mm']
    p['south_outer_end_mm'] = p['south_end_mm']+p['south_end_connection_mm']
    p['tower_stations_mm'] = [p['north_start_mm']+p['side_span_mm'], p['north_end_mm']-p['side_span_mm'],
                               p['south_start_mm']+p['side_span_mm'], p['south_end_mm']-p['side_span_mm']]
    return p


def bridges(p=None):
    p = p or parameters()
    return [{'id': name, 'start': p[f'{name}_start_mm'], 'end': p[f'{name}_end_mm'],
             'tower_a': p[f'{name}_start_mm']+p['side_span_mm'],
             'tower_b': p[f'{name}_end_mm']-p['side_span_mm'],
             'tower_top': p[f'{name}_tower_top_mm'], 'cable_diameter': p[f'{name}_cable_diameter_mm'],
             'cable_mid_z': p[f'{name}_cable_mid_z_mm']} for name in ('north', 'south')]


def cable_z(x, bridge, p=None):
    """Parabolic appearance fit, explicitly not a loaded cable calculation."""
    p = p or parameters()
    a, b = bridge['tower_a'], bridge['tower_b']
    saddle = bridge['tower_top'] - 2500
    if a <= x <= b:
        q = (x-(a+b)/2)/((b-a)/2)
        return bridge['cable_mid_z']+(saddle-bridge['cable_mid_z'])*q*q
    end, tower = (bridge['start'], a) if x < a else (bridge['end'], b)
    t = (x-end)/(tower-end)
    anchor_z = p['anchor_cable_z_mm']-.01*abs(end)
    return anchor_z+(saddle-anchor_z)*t - 7000*t*(1-t)


def stations(bridge, p=None):
    """Nominal 13.2 m panels; residual end panels adapt to published spans."""
    p = p or parameters()
    count = ceil((bridge['end']-bridge['start'])/p['nominal_panel_mm'])
    return [bridge['start']+i*(bridge['end']-bridge['start'])/count for i in range(count+1)]


def tower_portal_profile(bridge, x, p=None):
    """Photo/general-drawing fit using the existing nominal model datum.

    North supplies the three-cell outer section. Applying it to South and
    fitting stage heights to the simplified deck are appearance assumptions.
    """
    p=p or parameters()
    base=10050
    steel_top=bridge['tower_top']-4500
    underdeck=rail_height_mm(x,p)-420-2500
    lower_bottom=base+4250
    lower_apex=underdeck-1400
    lower_middle=lower_bottom+(lower_apex-lower_bottom)*2/3
    upper_top=steel_top-3000
    upper_middle=upper_top-30890
    half_base=19626.5 if bridge['id']=='north' and x==bridge['tower_a'] else 19737
    return {'base_tp_mm':base,'column_bottom_mm':base+180,'column_top_mm':steel_top,
        'half_base_span_mm':half_base,'half_top_span_mm':17500,
        'column_width_mm':4800,'side_width_mm':3700,'core_depth_mm':3200,
        'base_depth_mm':10700,'top_depth_mm':7100,
        'head_beam_z_mm':steel_top-1500,'underdeck_beam_z_mm':underdeck,
        'upper_nodes_mm':[upper_middle-31610,upper_middle,upper_top],
        'lower_nodes_mm':[lower_bottom,lower_middle,lower_apex],
        'brace_width_mm':2000,'brace_depth_mm':2000,
        'scope':'Photo-fit stages with nominal tower/cable levels; not individual surveyed tower elevations.'}


def tower_column_centre(spec, z):
    a,b=spec['base_centre_mm'],spec['top_centre_mm']
    t=(z-a[2])/(b[2]-a[2])
    return [a[i]+t*(b[i]-a[i]) for i in range(3)]


def tower_column_outline(spec, top=False):
    """Twelve-corner cruciform envelope of a three-cell box tower column."""
    x,y,z=spec['top_centre_mm'] if top else spec['base_centre_mm']
    depth=spec['top_depth_mm'] if top else spec['base_depth_mm']
    a,b,c,d=depth/2,spec['core_depth_mm']/2,spec['side_width_mm']/2,spec['width_mm']/2
    ring=[(-a,-c),(-b,-c),(-b,-d),(b,-d),(b,-c),(a,-c),
          (a,c),(b,c),(b,d),(-b,d),(-b,c),(-a,c)]
    return [[x+u,y+v,z] for u,v in ring]


def shared_anchor_profile():
    """BB4A Fig.2 envelope plus explicitly approximate photo-fit recesses.

    X dimensions/levels follow the 1984 general drawing. The top knots, face
    recess dimensions and finish courses are appearance fits, not shop data.
    The 62m overall transverse footprint includes the 2m footing lips.
    """
    outer=[[5000,26500],[33000,39500],[75190,36500],[86000,35750]]
    trough=[[52500,3000],[66000,14000],[81500,20500],[86000,29500]]
    outline=[[-26500,5000],[26500,5000],*[ [x,z] for z,x in outer[1:] ],
        *[[x,z] for z,x in reversed(trough)],
        *[[-x,z] for z,x in trough],[-35750,86000],[-36500,75190],[-39500,33000]]
    return {'outline_xz':outline,'outer_half_x_by_z':outer,'trough_half_x_by_z':trough,
        'body_width_mm':58000,'footing_width_mm':62000,'footing_length_mm':57000,
        'recess_half_width_mm':6000,'recess_depth_mm':4500,'recess_floor_mm':12000,
        'course_spacing_mm':3000,'course_band_mm':70}


def _interpolate_profile(knots,z):
    for (a,x),(b,y) in zip(knots,knots[1:]):
        if z<=b:return x+(y-x)*(z-a)/(b-a)
    return knots[-1][1]


def _clip_polygon(points,axis,limit,keep_lower=True):
    """Half-plane clipping for convex/monotone independent face pieces."""
    result=[]
    for a,b in zip(points,points[1:]+points[:1]):
        ina=(a[axis]<=limit) if keep_lower else (a[axis]>=limit)
        inb=(b[axis]<=limit) if keep_lower else (b[axis]>=limit)
        if ina:result.append(a)
        if ina!=inb:
            t=(limit-a[axis])/(b[axis]-a[axis])
            result.append([a[i]+t*(b[i]-a[i]) for i in range(2)])
    return result


def shared_anchor_recesses(profile=None):
    profile=profile or shared_anchor_profile()
    levels=[profile['recess_floor_mm'],33000,75190,86000]
    result=[]
    for sign in (-1,1):
        wall=[(z,_interpolate_profile(profile['outer_half_x_by_z'],z)) for z in levels]
        xz=[[sign*(x-profile['recess_depth_mm']),z] for z,x in wall]
        xz.extend([[sign*(x+1000),z] for z,x in reversed(wall)])
        result.append({'outline':[[x,-profile['recess_half_width_mm'],z] for x,z in xz],
            'extrusion':[0,profile['recess_half_width_mm']*2,0],
            'purpose':'photo_fit_blind_central_face_recess_not_through_opening'})
    return result


def shared_anchor_details():
    """Named CAD face bands, clipped to actual concrete and transport cuts."""
    profile=shared_anchor_profile();result=[];prefix='foundations:BB4A_shared:detail:'
    def prism(name,outline,extrusion,color):
        result.append({'name':prefix+name,'group':'foundations','kind':'prism',
            'outline':outline,'extrusion':extrusion,'color':color})
    # Thin finish bands overlap the face by 30mm to avoid coplanar surfaces.
    # Split at X=0 before clipping: the two wings above the trough floor
    # must never be bridged by a decorative strip across an empty V opening.
    for z in range(8000,86000,profile['course_spacing_mm']):
        low,high=z-35,z+35
        for half in (-1,1):
            band=_clip_polygon(profile['outline_xz'],0,0,half<0)
            band=_clip_polygon(_clip_polygon(band,1,high),1,low,False)
            if len(band)<3:continue
            for side in (-1,1):
                prism(f'course_Y_{side}_{half}_{z}',[[x,side*28970,zz] for x,zz in band],
                    [0,side*70,0],'#9CA59F')
        # Bridge-axis end faces have a 12m central blind recess. Joints stop
        # at its edges and also stay outside the existing transport opening.
        gap=16550 if high>77785 else (6050 if high>=profile['recess_floor_mm'] else 0)
        spans=[(-28950,-gap),(gap,28950)] if gap else [(-28950,28950)]
        for side in (-1,1):
            a=_interpolate_profile(profile['outer_half_x_by_z'],low)-30
            b=_interpolate_profile(profile['outer_half_x_by_z'],high)-30
            for index,(y0,y1) in enumerate(spans):
                prism(f'course_X_{side}_{index}_{z}',[[side*a,y0,low],[side*a,y1,low],
                    [side*b,y1,high],[side*b,y0,high]],[side*70,0,0],'#9CA59F')
    # Darker lower ramp protection visible in the owner's maintenance photo.
    # Panel depth and tone are illustrative; no historical coating specified.
    for side in (-1,1):
        a=_interpolate_profile(profile['outer_half_x_by_z'],8000)-20
        b=_interpolate_profile(profile['outer_half_x_by_z'],33000)-20
        for index,(y0,y1) in enumerate(((-28960,-6050),(6050,28960))):
            prism(f'lower_protection_{side}_{index}',[[side*a,y0,8000],[side*a,y1,8000],
                [side*b,y1,33000],[side*b,y0,33000]],[side*45,0,0],'#8B9290')
    return result


@lru_cache(maxsize=1)
def _specs():
    p = parameters(); result = []
    steel, concrete, asphalt, rail = '#E0E8E5', '#AAAFA7', '#525F65', '#707D82'
    def box(group, name, bounds, color):
        result.append({'name': f'{group}:{name}', 'group': group, 'kind': 'box', 'bounds': list(bounds), 'color': color})
    def beam(group, name, a, b, width, depth=None, color=steel, kind='member'):
        result.append({'name': f'{group}:{name}', 'group': group, 'kind': 'beam', 'start': list(a), 'end': list(b),
                       'width_mm': width, 'depth_mm': depth or width, 'profile': kind, 'color': color})
    def ellipse(name, x, y, rx, ry, height, color):
        result.append({'name': f'environment:{name}', 'group': 'environment', 'kind': 'island',
                       'centre': [x,y], 'radii': [rx,ry], 'height_mm': height, 'color': color})
    box('environment', 'sea:illustrative_TP0', (p['north_start_mm']-110000,-p['context_width_mm']/2,-5000,
        p['south_end_mm']+110000,p['context_width_mm']/2,0), '#4D879F')
    ellipse('Yoshima_context_not_surveyed', p['north_start_mm']-25000,20000,115000,155000,23000,'#6B8C6F')
    ellipse('Mitsugojima_context_not_surveyed', -15000,15000,65000,50000,15000,'#718E6C')
    ellipse('Ban_no_su_context_not_surveyed', p['south_end_mm']+70000,0,155000,155000,12000,'#8B9981')
    # Single common 4A, not two separated island anchorages.
    for label,x,length,width in [('BB1A',p['north_start_mm']-24000,71000,50000),('BB4A_shared',0,79000,62000),('BB7A',p['south_end_mm']+30000,75000,52000)]:
        if label == 'BB4A_shared':
            profile=shared_anchor_profile()
            box('foundations',label+':base',(-28500,-31000,-14000,28500,31000,5000),concrete)
            result.append({'name':'foundations:BB4A_shared:V_notched_body','group':'foundations','kind':'anchorage',
                'outline_xz':profile['outline_xz'],'width_mm':profile['body_width_mm'],
                'surface_recesses':shared_anchor_recesses(profile),'color':'#BFC3BA'})
        else:
            box('foundations',label+':base',(x-length/2,-width/2,-14000,x+length/2,width/2,18000),concrete)
            box('foundations',label+':anchor_block',(x-length*.34,-width*.45,18000,x+length*.34,width*.45,67000),'#C1C5BC')
        # Keep the concrete silhouette and cable anchoring sides, while opening
        # the actual named CAD solid around both transport decks. The opening
        # dimensions are illustrative clearance envelopes, not an as-built bore.
        body=result[-1]
        xmin,xmax = (-39500,39500) if label=='BB4A_shared' else (x-length*.34,x+length*.34)
        lower=min(rail_height_mm(xx,p)-420 for xx in (xmin,xmax))-1800
        upper=max(road_height_mm(xx,p) for xx in (xmin,xmax,0) if xmin<=xx<=xmax)+2000
        body['clearance_cuts']=[{'bounds':[xmin-1000,-16500,lower,xmax+1000,16500,upper],
            'purpose':'road_rail_transport_envelope_demo'}]

    result.extend(shared_anchor_details())

    for b in bridges(p):
        ident = b['id']; xs = stations(b,p); zlo,zhi = p['rail_deck_z_mm'],p['road_deck_z_mm']
        for i,x in enumerate((b['tower_a'],b['tower_b'])):
            tower = f'{ident}:tower_{i+1}'
            profile=tower_portal_profile(b,x,p)
            box('foundations',tower+':marine_caisson_assumed',(x-12500,-30000,-22000,x+12500,30000,3500),concrete)
            box('foundations',tower+':pier',(x-8500,-26500,3500,x+8500,26500,profile['base_tp_mm']),'#CBCDC5')
            for sign in (-1,1):
                result.append({'name':f'towers:{tower}:leg_{sign}','group':'towers','kind':'tower_column',
                    'base_centre_mm':[x,sign*profile['half_base_span_mm'],profile['column_bottom_mm']],
                    'top_centre_mm':[x,sign*17500,profile['column_top_mm']],
                    'width_mm':4800,'side_width_mm':3700,'core_depth_mm':3200,
                    'base_depth_mm':10700,'top_depth_mm':7100,'color':steel})
                y=sign*profile['half_base_span_mm'];z=profile['base_tp_mm']
                box('towers',tower+f':base_plate_{sign}',(x-6150,y-3150,z,x+6150,y+3150,z+180),steel)
            # Under-deck support and head beam only: the photo's two upper X
            # stages are not crossed by additional horizontal portal bars.
            for j,z in ((1,profile['underdeck_beam_z_mm']),(5,profile['head_beam_z_mm'])):
                beam('towers',tower+f':crossbeam_{j}',(x,-17500,z),(x,17500,z),2300,2800)
            def inner(z):
                t=(z-profile['column_bottom_mm'])/(profile['column_top_mm']-profile['column_bottom_mm'])
                return profile['half_base_span_mm']+(17500-profile['half_base_span_mm'])*t-2200
            def brace(name,a,c):
                beam('towers',tower+':'+name,a,c,2000,2000)
            def joint(name,z):
                yz=[(-1500,-900),(-900,-1500),(900,-1500),(1500,-900),
                    (1500,900),(900,1500),(-900,1500),(-1500,900)]
                result.append({'name':f'towers:{tower}:joint:{name}','group':'towers','kind':'prism',
                    'outline':[[x-1100,y,z+v] for y,v in yz],'extrusion':[2200,0,0],'color':steel})
            for j,(a,c) in enumerate(zip(profile['upper_nodes_mm'],profile['upper_nodes_mm'][1:]),3):
                brace(f'X_{j}_L',(x,-inner(a),a),(x,inner(c),c))
                brace(f'X_{j}_R',(x,inner(a),a),(x,-inner(c),c))
                joint(f'upper_{j}',(a+c)/2)
            a,c,apex=profile['lower_nodes_mm']
            brace('X_0_L',(x,-inner(a),a),(x,inner(c),c))
            brace('X_0_R',(x,inner(a),a),(x,-inner(c),c))
            joint('lower',(a+c)/2)
            brace('lower_chevron_L',(x,-inner(c),c),(x,0,apex))
            brace('lower_chevron_R',(x,inner(c),c),(x,0,apex))
            for sign in (-1,1):
                box('towers',tower+f':saddle_{sign}',(x-3000,sign*17500-2200,profile['column_top_mm']-300,x+3000,sign*17500+2200,b['tower_top']),'#DCE5DF')
        box('road',ident+':deck',(b['start'],-p['road_width_mm']/2,zhi-700,b['end'],p['road_width_mm']/2,zhi),asphalt)
        # Lower open deck includes in-use conventional railway and an empty future corridor.
        box('railway',ident+':deck',(b['start'],-15000,zlo-700,b['end'],15000,zlo),'#8D9898')
        for sign in (-1,1):
            y = sign*p['truss_centres_mm']/2
            for level,z in [('upper',zhi),('lower',zlo)]:
                beam('truss',f'{ident}:chord:{level}:{sign}',(b['start'],y,z),(b['end'],y,z),1150,1450)
            for j,x in enumerate(xs):
                beam('truss',f'{ident}:vertical:{sign}:{j}',(x,y,zlo),(x,y,zhi),650,750)
            for j,(a,c) in enumerate(zip(xs,xs[1:])):
                # Alternating Warren diagonals, not a solid wall or circular tubes.
                za,zc = (zlo,zhi) if j%2==0 else (zhi,zlo)
                beam('truss',f'{ident}:diagonal:{sign}:{j}',(a,y,za),(c,y,zc),650,800)
            # Main cable as contiguous short octagonal prisms following the same profile as drawings.
            cx = sorted(set([*xs,b['tower_a'],b['tower_b']]))
            for j,(a,c) in enumerate(zip(cx,cx[1:])):
                beam('cables',f'{ident}:main:{sign}:{j}',(a,sign*17500,cable_z(a,b,p)),(c,sign*17500,cable_z(c,b,p)),b['cable_diameter'],kind='cable')
            for j,x in enumerate(xs[1:-1]):
                z = cable_z(x,b,p)
                if z-(zhi-.01*abs(x)) > 1200:
                    beam('hangers',f'{ident}:hanger:{sign}:{j}',(x,sign*17500,zhi),(x,sign*17500,z),160,kind='cable')
                    beam('truss',f'{ident}:hanger_bracket:{sign}:{j}',(x,y,zhi),(x,sign*17500,zhi),500,650)
            beam('road',f'{ident}:outer_barrier:{sign}',(b['start'],sign*12800,zhi+900),(b['end'],sign*12800,zhi+900),350,1500,color='#B7C4C4')
        for j,x in enumerate(xs):
            if j%2==0:
                beam('truss',f'{ident}:floorbeam:{j}',(x,-15000,zlo-1200),(x,15000,zlo-1200),800,1000)
        beam('road',f'{ident}:median',(b['start'],0,zhi+600),(b['end'],0,zhi+600),650,1000,color='#B6C2BE')
        for lane,y in enumerate((-5600,5600)):
            for j in range(int((b['end']-b['start'])/24000)):
                a = b['start']+j*24000+3000
                box('road',f'{ident}:lane_mark:{lane}:{j}',(a,y-80,zhi+10,a+6000,y+80,zhi+35),'#EFEEDB')
        # Conventional gauge 1067 mm. The two future Shinkansen paths stay unbuilt.
        for track,y in enumerate((-10500,-5500)):
            for sign in (-1,1):
                box('railway',f'{ident}:track_{track}:rail_{sign}',(b['start'],y+sign*533.5-65,zlo+200,b['end'],y+sign*533.5+65,zlo+420),rail)
        # The reserved half is an empty deck, delineated with a dashed edge.
        for j in range(int((b['end']-b['start'])/50000)):
            x = b['start']+j*50000
            box('railway',f'{ident}:reserved_zone_marker:{j}',(x,1800,zlo+10,x+8000,1950,zlo+30),'#D3CEAF')
    box('road','BB4A:road_continuation_assumed',(-24500,-13000,92300,24500,13000,93000),asphalt)
    box('railway','BB4A:rail_continuation_assumed',(-24500,-15000,79300,24500,15000,80000),'#8D9898')
    for track,y in enumerate((-10500,-5500)):
        for sign in (-1,1):
            box('railway',f'BB4A:track_{track}:rail_{sign}',(-24500,y+sign*533.5-65,80200,24500,y+sign*533.5+65,80420),rail)
    for ident,a,b in [('north_end',p['north_outer_end_mm'],p['north_start_mm']),('south_end',p['south_end_mm'],p['south_outer_end_mm'])]:
        box('road',ident+':road_continuation_assumed',(a,-13000,92300,b,13000,93000),asphalt)
        box('railway',ident+':rail_continuation_assumed',(a,-15000,79300,b,15000,80000),'#8D9898')
        for track,y in enumerate((-10500,-5500)):
            for sign in (-1,1):
                box('railway',f'{ident}:track_{track}:rail_{sign}',(a,y+sign*533.5-65,80200,b,y+sign*533.5+65,80420),rail)
    # The two bridge halves fall 1% away from the BB4A high point. South
    # follows the published longitudinal drawing; the North mirror is assumed.
    for part in result:
        if part['group'] in ('road','railway') and part['kind']=='box':
            part['longitudinal_gradient'] = .01
        if part['kind']=='beam' and part['group'] in ('road','railway','truss'):
            for key in ('start','end'): part[key][2] -= .01*abs(part[key][0])
        if part['kind']=='beam' and part['group']=='hangers':
            part['start'][2] -= .01*abs(part['start'][0])
    # Appearance accessories follow the graded bridge specification. The only
    # R01 edits are the four crossbeam_2 heights, raised for vehicle clearance.
    for b in bridges(p):
        for index,x in enumerate((b['tower_a'],b['tower_b'])):
            name=f"detail:{b['id']}:tower_{index+1}"
            for level,z in enumerate((p['road_deck_z_mm']-.01*abs(x)+4500,148000)):
                for sign in (-1,1):
                    y=sign*17500
                    box('towers',f'{name}:inspection_{level}_{sign}:deck',(x-3800,y-3000,z-180,x+3800,y+3000,z),'#AEBDBA')
                    for edge,ey in enumerate((y-2850,y+2850)):
                        beam('towers',f'{name}:inspection_{level}_{sign}:handrail_{edge}',(x-3600,ey,z+1100),(x+3600,ey,z+1100),90,100)
                    for edge,ex in enumerate((x-3600,x+3600)):
                        beam('towers',f'{name}:inspection_{level}_{sign}:end_rail_{edge}',(ex,y-2850,z+1100),(ex,y+2850,z+1100),90,100)
                        for side,ey in enumerate((y-2850,y+2850)):
                            beam('towers',f'{name}:inspection_{level}_{sign}:post_{edge}_{side}',(ex,ey,z),(ex,ey,z+1100),90,90)
            # Short fixed inspection ladder on the protected inner column face.
            z0=p['road_deck_z_mm']-.01*abs(x)+4500
            for side,offset in enumerate((-350,350)):
                beam('towers',f'{name}:ladder_rail_{side}',(x+2200,14500+offset,z0),(x+2200,14500+offset,z0+5000),75,75)
            for rung in range(12):
                z=z0+300+rung*400
                beam('towers',f'{name}:ladder_rung_{rung}',(x+2200,14150,z),(x+2200,14850,z),45,45)
            for seam in range(2):
                z=4500+seam*4200
                box('foundations',f'{name}:pier_joint_{seam}',(x-8580,-26580,z,x+8580,26580,z+90),'#8F9995')
        count=int((b['end']-b['start'])/220000)
        for index in range(count):
            x=b['start']+(index+.5)*(b['end']-b['start'])/count
            road_z=p['road_deck_z_mm']-.01*abs(x)
            for side in (-1,1):
                y=side*11900;name=f"detail:{b['id']}:road_lamp_{index}_{side}"
                beam('road',name+':pole',(x,y,road_z),(x,y,road_z+8500),160,190,color='#7F9599')
                beam('road',name+':arm',(x,y,road_z+8200),(x,y-side*2300,road_z+8700),150,150,color='#7F9599')
                box('road',name+':head',(x-650,y-side*2300-250,road_z+8500,x+650,y-side*2300+250,road_z+8800),'#CBD4CE')
    # Demonstration electric-railway contact and messenger wires. The occupied
    # conventional tracks remain at their original gauge and Y positions.
    wire_stations=sorted(set([p['north_outer_end_mm'],p['north_start_mm'],-24500,24500,
        p['south_end_mm'],p['south_outer_end_mm']]))
    for track,y in enumerate((-10500,-5500)):
        for segment,(a,c) in enumerate(zip(wire_stations,wire_stations[1:])):
            for label,height in (('contact',5400),('messenger',6400)):
                beam('railway',f'detail:catenary:{track}:{label}:{segment}',
                    (a,y,rail_height_mm(a,p)+height),(c,y,rail_height_mm(c,p)+height),50,50,color='#6B7E84')
        count=ceil((p['south_outer_end_mm']-p['north_outer_end_mm'])/120000)
        for number in range(count+1):
            x=p['north_outer_end_mm']+(p['south_outer_end_mm']-p['north_outer_end_mm'])*number/count
            z=rail_height_mm(x,p)
            beam('railway',f'detail:catenary:{track}:dropper:{number}',
                (x,y,z+5400),(x,y,z+6400),35,35,color='#70838A')
    result.extend(activity_specs(p))
    return result


def component_specs():
    return deepcopy(_specs())


def geometry_manifest():
    p = parameters(); specs = component_specs()
    cited = {
        'north_length_mm': {'value':1538000,'source_index':0}, 'south_length_mm':{'value':1648000,'source_index':1},
        'north_main_span_mm':{'value':990000,'source_index':0}, 'south_main_span_mm':{'value':1100000,'source_index':1},
        'side_span_mm':{'value':274000,'source_index':0},
        'north_tower_top_mm':{'value':184000,'datum':'T.P.','source_index':0},
        'south_tower_top_mm':{'value':194000,'datum':'T.P.','source_index':1},
        'north_cable_diameter_mm':{'value':998,'source_index':0}, 'south_cable_diameter_mm':{'value':1062,'source_index':1},
        'north_truss_centres_mm':{'value':30000,'source_index':6},'north_truss_height_mm':{'value':13000,'source_index':6},
        'north_cable_centres_mm':{'value':35000,'source_index':6},'north_nominal_panel_mm':{'value':13200,'source_index':6},
    }
    assumptions = [
        {'zh':'模型范围只包括南、北备赞濑户大桥，未包括濑户大桥的另外四座主要桥梁。它是照片引导的外观模型，不是实测原设计CAD、承载验算或施工图。',
         'ja':'対象は南・北備讃瀬戸大橋の二橋です。他の主要四橋は含みません。写真を参考にした外観モデルで、実測・原設計CAD・耐力検証・施工図ではありません。',
         'en':'Only the North and South Bisan-Seto bridges are included, not the other four principal Seto Ohashi bridges. This is a photo-informed appearance model, not a survey, original design CAD, capacity verification or construction drawing.'},
        {'zh':'主塔顶标高采用官方T.P.+184/+194m。海面暂置T.P.0；BB4A高点桥面93m、下层80m及两侧1%纵坡采用图示近似，北侧对称坡度与北桥90m垂度为假设；南桥依历史图100m垂度，主缆最低点约91.5m为图示近似。官方净空65m采用略最高高潮面基准，未与本模型T.P.海面直接换算。',
         'ja':'主塔頂は公式のT.P.+184/+194mです。海面T.P.0、BB4A頂点の上床93m・下床80mは図示近似で、南側1%に対する北側の対称勾配と北橋90m垂度は仮定で、南橋は歴史図の100m垂度から中央約91.5mを近似します。航路高65mは略最高高潮面基準であり、モデルのT.P.海面から直接換算していません。',
         'en':'Tower tops use the published T.P.+184/+194m. Sea at T.P.0 is assumed. Road/rail decks use approximate BB4A crest levels of 93/80m with a 1% fall; the North slope mirrors the published South slope as an assumption. The South parabolic cable uses the historical 100m sag to approximate a 91.5m low point; the North 90m sag is an appearance assumption. Published 65m clearance uses a high-water datum; no direct conversion to the model T.P. sea is asserted.'},
        {'zh':'北桥技术图的主桁间距30m、桁高13m及主缆间距35m沿用于南桥，南桥的此项沿用为假设。13.2m为参考格距，端部余量均分；截面尺寸、吊索简化、主塔横撑、路面、轨道及预留区均为演示近似。',
         'ja':'北橋資料の主桁間30m・桁高13m・主ケーブル間35mを南橋にも仮定して適用します。13.2mを基準に端部余長を均等調整します。部材断面、ハンガー省略、主塔横構、道路・軌道・留保空間の細部は概形です。',
         'en':'The North bridge 30m truss centres, 13m truss depth and 35m cable centres are also assumed for the South bridge. Nominal 13.2m panels are evenly adjusted at residual ends. Member sections, simplified hangers, tower bracing, roadway, tracks and reserved corridor details are illustrative.'},
        {'zh':'以共用BB4A为X=0，两悬索区1538/1648m与49m共用锚碇段及外端48.2/50.6m合成桥端间3333.8m（官方整桥1611+1723m的舍入口径）。49m锚碇上和两外端连接段的具体几何为演示假设。基础、入海深度和岛屿地形并非勘测。',
         'ja':'共用BB4AをX=0とし、補剛桁1538/1648mに共用アンカレイジ上49mと外端48.2/50.6mを加え、橋端間3333.8mとします（公式の全橋1611+1723mとは丸めの差）。49mと両外端の接続部の細部は仮定です。基礎、海中深さ、島の地形は未測量です。',
         'en':'With shared BB4A at X=0, 1538/1648m suspended sections plus a 49m shared-anchor section and 48.2/50.6m outer ends give 3333.8m between model endpoints (rounding differs from the published full lengths 1611+1723m). Details of these connecting sections are assumed. Foundations, submerged depths and island terrain are not surveyed.'},
    ]
    assumptions.append({
        'zh':'R02的主塔检修平台、短梯、墩身接缝和道路灯具为外观深化假设。24辆车及4艘游船均为独立原创的示意资产；尺寸、密度、速度和循环路线不是实时交通或航路资料。车辆按日本左侧通行展示，CAD/GLB保存t=0静态快照，网页动画不改变原桥结构。',
        'ja':'R02の主塔点検足場・短いはしご・橋脚目地・道路照明は外観詳細の仮定です。車24台と遊覧船4隻は独自の概念形状で、寸法・密度・速度・ループは実交通や航路情報ではありません。車両は左側通行を表し、CAD/GLBはt=0の静止形状、Webのみ表示用に動かします。',
        'en':'R02 tower inspection platforms, short ladders, pier joints and road lighting are appearance assumptions. The 24 vehicles and four sightseeing boats are original illustrative assets. Dimensions, density, speeds and loops are not live traffic or navigation information. Vehicles show left-hand traffic; CAD/GLB retain a static t=0 snapshot and only the web presentation animates.'})
    assumptions.append({
        'zh':'R02阶段为避免示意车辆穿过主塔横梁，四座主塔的道路上方横梁各提高3000 mm，模型中的梁底道路净高由2100 mm调整为5100 mm。此为演示通行需要的几何调整，不代表实桥测绘标高或结构设计结论，该阶段其余2962个R01构件保持原定义；R03的后续修正另列；R04按实景移除这些上方横梁，5.1m只作为旧版记录。',
        'ja':'R02で概念車両と主塔横梁の干渉を避けるため、4主塔の道路上方横梁を各3000 mm上げ、モデルの梁下面から路面までの高さを2100 mmから5100 mmへ変更しています。表示上の通行条件による幾何修正で、実橋の測量高さや構造設計の結果ではありません。その段階では他のR01部材2962件は変更していません。R03の変更は別記します。',
        'en':'In R02, to avoid illustrative vehicles intersecting the towers, the four crossbeams above the road are raised by 3000 mm, changing model road-to-soffit clearance from 2100 to 5100 mm. This geometric adjustment serves demonstration traffic and does not claim surveyed elevations or structural design of the actual bridge. At that stage the other 2962 R01 component definitions remained unchanged; subsequent R03 edits are listed separately. R04 removes these above-road bars to match the photo; 5.1m is only the historical R02 clearance.'})
    assumptions.append({
        'zh':'R03将4条游船演示航迹设为沿Y轴横穿两座主跨。新增2列相向行驶的原创4节编组电车，约20m/节；外形、速度、架线高度和线路均为演示假设，不对应指定车型。全编组共享运动时钟与回绕边界，每节以两转向架处轨顶高度的均值和连线坡度跟随轨道。海面波纹只用于网页视觉，CAD海面仍为T.P.0静态基准。',
        'ja':'R03の遊覧船4航跡はY軸方向に二つの主径間を横断します。対向する独自概形の4両編成電車2本（約20m/両）を追加します。形状・速度・架線高さ・軌跡は特定形式に対応しない仮定です。編成で共通の時刻・折返し境界を使い、各車両は両台車位置のレール上面の平均高と結線勾配に追従します。波はWebの視覚表現で、CADの海面はT.P.0の静止基準です。',
        'en':'R03 routes four demonstration boats transversely along Y through the two main spans. Two opposing original four-car electric trains are added at approximately 20m per carriage. Appearance, speeds, wire heights and routes are illustrative and do not reproduce a specified train class. Each consist shares its clock and loop boundary; carriages follow the mean rail-top elevation and secant grade at their two bogies. Web waves are visual only; the CAD sea stays a static T.P.0 datum.'})
    assumptions.append({
        'zh':'BB4A的V槽底依公团资料印刷50页Fig.2修正为T.P.+52.500m，79×62×86m外包络保留。3个锚碇实体均减去宽33m的公铁通行包络，保留侧部锚固体；此开口细部为演示净空假设，不代表实桥内部结构。122根铁路下横梁整体降低1200mm，使梁顶到下层桥面底，避免凸入轨顶。',
        'ja':'BB4AのV溝底は公団資料の印刷50頁Fig.2に基づきT.P.+52.500mへ修正し、79×62×86mの外包絡を保持します。3アンカレイジのCAD実体から幅33mの道路・鉄道通行包絡を差し引き、側部の定着体を残します。開口の細部は表示上の仮定で実橋内部の再現ではありません。下横桁122本は1200mm下げ、上端を下床版下面に合わせてレール上面への突出を解消します。',
        'en':'The BB4A V-trough is corrected to T.P.+52.500m from the authority paper, printed page 50 Fig.2, while retaining the 79×62×86m outer envelope. A 33m-wide road/rail clearance envelope is subtracted from each of the three anchorage solids, preserving lateral anchoring mass. Opening details are demonstration clearances, not an as-built internal structure. The 122 railway floorbeams are lowered by 1200mm so their upper faces meet the lower-deck underside rather than protrude above the rails.'})
    assumptions.append({
        'zh':'R04按用户实景及1986年施工图修正主塔：上部两层连续X、长空腹区、桥面下完整X与山形撑；移除无实景依据的横梁。十字形3单元塔柱采用北桥约4.8m横宽、7.1至10.7m纵深的外轮廓，南桥沿用为假设。既有184/194m名义塔顶及主缆控制仍是概念坐标，并非分别复原各塔的原施工标高；节点、底板及撑端尺寸为外观近似。',
        'ja':'R04は提供実景と1986年施工図から、上部2X・長い空腹区間・橋面下のXと山形横構へ修正し、実景にない横梁を除きます。十字形3セル塔柱は北橋資料の横4.8m・縦7.1〜10.7mの外包を参考にし、南橋への準用は仮定です。既存184/194mの名目塔頂と主ケーブル制御は概念座標で、各塔の原施工標高を個別に復元したものではありません。節点・底板・端部寸法は外観近似です。',
        'en':'R04 follows the supplied photograph and 1986 general drawings: two upper X stages, a long open portal, and a lower X plus chevron, removing unsupported horizontal bars. The cruciform three-cell envelope uses approximately 4.8m transverse width and 7.1–10.7m longitudinal depth from North drawings; applying it to South is assumed. Existing nominal 184/194m tower/cable controls remain concept coordinates, not individually restored historical tower elevations. Nodes, base plates and end details are appearance fits.'})
    assumptions.append({
        'zh':'R05按共用BB4A原施工总图与运营方维修近照重塑锚碇：TP+5m处53m纵长，经下部收腰至TP+33m处最大79m；上部缓收至TP+75.190m约73m，顶部86m、V底52.5m。62m横向外包包含基础边沿，墩身58m；57×62m基础仍保留假设水下深度。顶部折线、12m宽/4.5m深端面盲凹槽、3m分层接缝与下部保护面为照片近似，非实测或内部构造复原。通行开口沿用演示净空包络。',
        'ja':'R05はBB4A原施工一般図と管理者の維持管理写真から修正。TP+5mの縦53mからTP+33mの最大79mへ広がり、TP+75.190m付近73mへ緩く絞る。頂部86m、V底52.5m、横62m外包は基礎縁を含み躯体58m。57×62m基礎の海中深さは仮定を保持。頂部折線、幅12m・深さ4.5mの端面盲くぼみ、3m打継ぎ・下部保護面は写真合わせで、実測・内部設計の復元ではない。通行開口は既存の表示用包絡。',
        'en':'R05 follows the original shared-BB4A general drawing and owner maintenance photo: 53m longitudinal body at TP+5m widens to79m at TP+33m, then batters to about73m at TP+75.190m; top86m and V floor52.5m. The62m transverse footprint includes footing lips around a58m body. The57×62m footing retains an assumed submerged depth. Upper knots,12m-wide/4.5m-deep blind face recesses,3m course bands and lower protective faces are appearance fits, not surveyed or internal construction data. Existing demonstration transport clearances remain.'})
    return {'schema_version':1,'id':MODEL_ID,'model_id':MODEL_ID,'revision':REVISION,'units':'mm',
            'glb_units':'m','glb_up_axis':'Y','status':'reference_concept_only','names':deepcopy(NAMES),
            'coordinate_system':{'CAD':'X southward, Y transverse, Z up; datum T.P.; shared BB4A at X=0','GLB':'(X,Z,-Y)/1000'},
            'parameters':p,'official_dimensions':cited,'references':deepcopy(REFERENCES),'assumptions':assumptions,
            'shared_anchorage_alignment':shared_anchor_profile(),
            'tower_alignment':[{'id':f"{b['id']}:tower_{i+1}",'x_mm':x,**tower_portal_profile(b,x,p)}
                for b in bridges(p) for i,x in enumerate((b['tower_a'],b['tower_b']))],
            'groups':[{'id':g,'names':GROUP_NAMES[g],'count':sum(s['group']==g for s in specs)} for g in GROUPS],
            'activity':activity_manifest(p),'component_count':len(specs),'components':specs}


def clearance_cut_shapes(spec, bd):
    """Native solids removed from anchorage transport envelopes."""
    result=[]
    for cut in spec.get('clearance_cuts',[]):
        x,y,z,a,b,c=cut['bounds']
        result.append(bd.Solid.make_box(a-x,b-y,c-z,plane=bd.Plane(origin=(x,y,z))))
    return result


def _clear_transport(shape, spec, bd):
    cuts=clearance_cut_shapes(spec,bd)
    for recess in spec.get('surface_recesses',[]):
        face=bd.Face(bd.Wire.make_polygon(recess['outline'],close=True))
        cuts.append(bd.Solid.extrude(face,tuple(recess['extrusion'])))
    return shape.cut(*cuts) if cuts else shape


def cad_shape(spec, bd):
    if spec['kind']=='tower_column':
        rings=[bd.Wire.make_polygon(tower_column_outline(spec,top),close=True) for top in (False,True)]
        return bd.Solid.make_loft(rings,ruled=True)
    if spec['kind']=='prism':
        face=bd.Face(bd.Wire.make_polygon(spec['outline'],close=True))
        return bd.Solid.extrude(face,tuple(spec['extrusion']))
    if spec['kind']=='box':
        x,y,z,a,b,c=spec['bounds']
        if spec.get('longitudinal_gradient'):
            rings=[bd.Wire.make_polygon([(station,y,z-.01*abs(station)),(station,b,z-.01*abs(station)),
                (station,b,c-.01*abs(station)),(station,y,c-.01*abs(station))],close=True) for station in (x,a)]
            return _clear_transport(bd.Solid.make_loft(rings,ruled=True),spec,bd)
        return _clear_transport(bd.Solid.make_box(a-x,b-y,c-z,plane=bd.Plane(origin=(x,y,z))),spec,bd)
    if spec['kind']=='anchorage':
        width=spec['width_mm']
        face=bd.Face(bd.Wire.make_polygon([(x,-width/2,z) for x,z in spec['outline_xz']],close=True))
        return _clear_transport(bd.Solid.extrude(face,(0,width,0)),spec,bd)
    if spec['kind']=='island':
        x,y=spec['centre'];rx,ry=spec['radii'];h=spec['height_mm']
        rings=[]
        for z,scale in ((-1000,1),(h*.35,1),(h,.62)):
            points=[(x+scale*rx*cos(2*pi*i/16),y+scale*ry*sin(2*pi*i/16),z) for i in range(16)]
            rings.append(bd.Wire.make_polygon(points,close=True))
        return bd.Solid.make_loft(rings,ruled=True)
    a,b=spec['start'],spec['end'];d=[b[i]-a[i] for i in range(3)]
    length=sqrt(sum(v*v for v in d));direction=[v/length for v in d]
    reference=[0.,0.,1.] if abs(direction[2])<.95 else [1.,0.,0.]
    cross=lambda u,v:[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
    u=cross(direction,reference);norm=sqrt(sum(v*v for v in u));u=[v/norm for v in u];v=cross(direction,u)
    if spec['profile']=='cable':
        outline=[(spec['width_mm']/2*cos(2*pi*i/8),spec['width_mm']/2*sin(2*pi*i/8)) for i in range(8)]
    else:
        w,h=spec['width_mm']/2,spec['depth_mm']/2;outline=[(-w,-h),(w,-h),(w,h),(-w,h)]
    rings=[bd.Wire.make_polygon([[centre[k]+u[k]*x+v[k]*y for k in range(3)] for x,y in outline],close=True) for centre in (a,b)]
    # Extrude a single planar section: lofting two kilometre-offset octagons
    # can introduce tiny edge tolerances when the STEP reader sews faces.
    return bd.Solid.extrude(bd.Face(rings[0]),tuple(d))


def bridge_assembly():
    from cadgen import build123d as bd,srgb
    specs=component_specs();groups=[]
    for group in GROUPS:
        children=[]
        for spec in specs:
            if spec['group']!=group: continue
            shape=cad_shape(spec,bd);shape.label=spec['name'];shape.color=srgb(spec['color']);children.append(shape)
        groups.append(bd.Compound(children=children,label=group))
    return bd.Compound(children=groups,label='SetoOhashiBisanPair')
