"""Original demonstration cars, transverse cruises and electric trains.

All dimensions, traffic density, speeds and marine tracks are illustration
assumptions. This is not recorded traffic or a navigation route. Specification
vertices and extrusion vectors are absolute CAD millimetres, Z-up.
"""
from copy import deepcopy
from math import atan, cos, pi, sin


def road_height_mm(x, p):
    # The existing 49 m BB4A connector is flat between its two graded ends.
    return p['road_deck_z_mm'] - .01 * max(abs(x), p['shared_anchor_half_length_mm'])


def rail_height_mm(x, p):
    return p['rail_deck_z_mm'] + 420 - .01 * max(abs(x), p['shared_anchor_half_length_mm'])


def train_support_pose(x, direction, p, bogie_spacing=13800):
    half = bogie_spacing / 2
    rear, front = rail_height_mm(x-half, p), rail_height_mm(x+half, p)
    return (rear+front)/2, -atan(direction*(front-rear)/bogie_spacing)


def _route(axis, low, high, fixed):
    return {'axis':axis, 'min_mm':low, 'max_mm':high, 'fixed_mm':fixed}


def _actors(p):
    actors = []
    lo, hi = p['north_outer_end_mm'] + 8000, p['south_outer_end_mm'] - 8000
    for lane, y in enumerate((3500, 8500, -3500, -8500)):
        direction = 1 if y > 0 else -1
        for index in range(6):
            phase = (index + .28 + lane * .21) / 6
            x = lo + (hi - lo) * phase
            kind = 'bus' if index == 2 and lane in (1, 3) else 'van' if index == 4 else 'sedan'
            length, width, height = {'sedan': (4500, 1820, 1560), 'van': (5250, 1950, 2250),
                                     'bus': (10500, 2450, 3300)}[kind]
            derivative = 0 if abs(x) <= p['shared_anchor_half_length_mm'] else -.01 * (1 if x > 0 else -1)
            origin = [x, y, road_height_mm(x, p)]
            actors.append({'id': f'car_{lane+1}_{index+1:02d}', 'group': 'traffic', 'kind': kind,
                'origin_mm': origin, 'position_mm': origin[:], 'heading_rad': 0 if direction == 1 else pi,
                'pitch_rad': -atan(direction * derivative), 'direction': direction,
                # One speed per lane preserves spacing throughout the loop.
                'speed_mps': 22.5 + lane * .5,
                'phase': phase, 'route': _route('x', lo, hi, y),
                'length_mm': length, 'width_mm': width, 'height_mm': height,
                'dimensions_mm': [length, width, height],
                'colour': ('#C1D0D2', '#2C5B71', '#B04C3D', '#C9C1AD', '#F0EDE4', '#52685E')[(index+lane) % 6]})
    # Cross the navigable visual opening perpendicular to the bridge, away
    # from towers, island context and the central anchorage. These are demo tracks.
    for index, x in enumerate((-825000, -765000, 820000, 880000)):
        direction = 1 if index % 2 == 0 else -1
        phase = (.43, .64, .38, .76)[index]
        y = -300000 + 600000 * phase
        kind = 'ferry' if index == 1 else 'cruise'
        length, width, height = (34000, 9000, 8100) if kind == 'ferry' else (24000, 6400, 6400)
        origin = [x, y, 0]
        actors.append({'id': f'boat_{index+1:02d}', 'group': 'vessels', 'kind': kind,
            'origin_mm': origin, 'position_mm': origin[:], 'heading_rad': direction*pi/2,
            'pitch_rad': 0, 'direction': direction, 'speed_mps': 6.0 + index * .35,
            'phase': phase, 'route': _route('y', -300000, 300000, x),
            'length_mm': length, 'width_mm': width, 'height_mm': height,
            'draft_mm': 850, 'dimensions_mm': [length, width, height], 'colour': '#EFECE2'})
    # Two opposing four-car electric multiple units; each carriage has a rigid
    # shell but independently follows the rails at its two bogie centres.
    low, high = p['north_outer_end_mm']+100000, p['south_outer_end_mm']-100000
    for train, (y, direction, phase) in enumerate(((-5500,1,.40),(-10500,-1,.62))):
        lead = low + (high-low)*phase
        for carriage in range(4):
            offset = -20500*carriage
            x = lead + direction*offset
            z,pitch = train_support_pose(x,direction,p)
            origin = [x,y,z]
            actors.append({'id':f'emu_{train+1}_car_{carriage+1}', 'group':'trains','kind':'electric_carriage',
                'train_id':f'emu_{train+1}','carriage_index':carriage,'consist_offset_mm':offset,
                'lead_position_mm':lead,'bogie_spacing_mm':13800,
                'origin_mm':origin,'position_mm':origin[:],'heading_rad':0 if direction==1 else pi,
                'pitch_rad':pitch,'direction':direction,'speed_mps':25.0,'phase':phase,
                'route':_route('x',low,high,y), 'length_mm':20000,'width_mm':2850,'height_mm':5300,
                'dimensions_mm':[20000,2850,5300], 'colour':'#D6DEDE'})
    return actors


def _parts(actor):
    out = []
    origin = actor['origin_mm']; pitch = actor['pitch_rad']; yaw = actor['heading_rad']
    cp, sp, cy, sy = cos(pitch), sin(pitch), cos(yaw), sin(yaw)

    def vector(v):
        x, y, z = cp*v[0]+sp*v[2], v[1], -sp*v[0]+cp*v[2]
        return [cy*x-sy*y, sy*x+cy*y, z]

    def point(v):
        return [round(a+b, 9) for a, b in zip(vector(v), origin)]

    def prism(name, outline, extrusion, colour):
        out.append({'name': f"{actor['group']}:{actor['id']}:{name}", 'group': actor['group'],
            'actor_id': actor['id'], 'kind': 'prism', 'outline': [point(p) for p in outline],
            'extrusion': vector(extrusion), 'color': colour})

    def box(name, bounds, colour):
        x, y, z, a, b, c = bounds
        prism(name, [(x,y,z),(a,y,z),(a,b,z),(x,b,z)], (0,0,c-z), colour)

    def profile(name, xz, half_width, colour, y_offset=0):
        prism(name, [(x,y_offset-half_width,z) for x,z in xz], (0,2*half_width,0), colour)

    def xy(name, points, base, height, colour):
        prism(name, [(x,y,base) for x,y in points], (0,0,height), colour)

    def round_piece(name, centre, radius, thickness, colour, axis='y'):
        cx,cy,cz = centre
        if axis == 'y':
            ring=[(cx+radius*cos(2*pi*i/16),cy-thickness/2,cz+radius*sin(2*pi*i/16)) for i in range(16)]
            prism(name,ring,(0,thickness,0),colour)
        else:
            ring=[(cx+radius*cos(2*pi*i/12),cy+radius*sin(2*pi*i/12),cz) for i in range(12)]
            prism(name,ring,(0,0,thickness),colour)

    l,w,h=actor['length_mm'],actor['width_mm'],actor['height_mm']
    glass, tyre, metal, white, red = '#284856','#202A2E','#B6C1BF','#F1E5BB','#C84D3C'
    if actor['group']=='traffic':
        radius=330 if actor['kind']=='sedan' else 360 if actor['kind']=='van' else 460
        body_low=radius*.9; belt=.62*h if actor['kind']=='sedan' else .48*h
        profile('painted_body',[(-l*.5,body_low),(-l*.5,belt*.86),(-l*.4,belt),
            (l*.37,belt),(l*.5,belt*.85),(l*.5,body_low)],w/2,actor['colour'])
        rear=-l*.33 if actor['kind']=='sedan' else -l*.46
        roof_rear=-l*.21 if actor['kind']=='sedan' else -l*.44
        roof_front=l*.08 if actor['kind']=='sedan' else l*.35
        front=l*.25 if actor['kind']=='sedan' else l*.46
        profile('cabin',[ (rear,belt*.95),(roof_rear,h),(roof_front,h),(front,belt*.97)],w*.445,actor['colour'])
        glazing=[(rear+l*.035,belt+65),(roof_rear+l*.025,h-95),
                 (roof_front-l*.025,h-95),(front-l*.035,belt+65)]
        for sign in (-1,1):
            profile(f'window_side_{sign}',glazing,14,glass,y_offset=sign*w*.45)
        # Front/rear sloping glass planes follow the cabin rather than a box.
        profile('windshield',[(roof_front-15,h-90),(roof_front+35,h-90),
            (front-65,belt+80),(front-115,belt+80)],w*.39,glass)
        profile('rear_glass',[(rear+65,belt+80),(rear+105,belt+80),
            (roof_rear+55,h-110),(roof_rear+15,h-110)],w*.36,glass)
        for axle,x in enumerate((-l*.29,l*.28)):
            for sign in (-1,1):
                y=sign*w*.47
                round_piece(f'tyre_{axle}_{sign}',(x,y,radius),radius,210 if actor['kind']!='bus' else 300,tyre)
                round_piece(f'hub_{axle}_{sign}',(x,y+sign*118,radius),radius*.48,35,metal)
        for sign in (-1,1):
            box(f'headlamp_{sign}',(l*.485,sign*w*.31-w*.10,belt*.53,l*.502,sign*w*.31+w*.10,belt*.78),white)
            box(f'taillamp_{sign}',(-l*.502,sign*w*.34-w*.07,belt*.56,-l*.485,sign*w*.34+w*.07,belt*.88),red)
        box('front_grille',(l*.493,-w*.19,body_low+80,l*.505,w*.19,belt*.48),tyre)
    elif actor['group']=='vessels':
        # Pointed bow, broad transom and separate dark lower hull are original
        # photo-informed shapes, not a copied vessel or branded boat asset.
        hull=[(-l*.5,-w*.42),(l*.22,-w*.5),(l*.5,0),(l*.22,w*.5),(-l*.5,w*.42)]
        keel=[(x*.94,y*.66) for x,y in hull]
        xy('lower_hull',keel,-850,900,'#264D67')
        xy('flared_hull',hull,0,1250,actor['colour'])
        xy('red_waterline_trim',[(x*1.001,y*1.008) for x,y in hull],930,180,red)
        xy('main_deck',[(x*.96,y*.91) for x,y in hull],1250,180,'#BFBBA7')
        cabin_h=h*.47
        profile('passenger_cabin',[(-l*.40,1430),(-l*.40,cabin_h),
            (l*.17,cabin_h),(l*.28,1430)],w*.40,white)
        for sign in (-1,1):
            for index in range(5):
                a=-l*.365+index*l*.105
                box(f'passenger_window_{sign}_{index}',(a,sign*w*.405-22,1740,
                    a+l*.085,sign*w*.405+22,cabin_h-190),glass)
        profile('sloped_forward_glass',[(l*.17-70,cabin_h-120),(l*.17+30,cabin_h-120),
            (l*.265,1630),(l*.255,1630)],w*.36,glass)
        roof=cabin_h+150
        box('upper_sundeck',(-l*.405,-w*.425,cabin_h,l*.20,w*.425,roof),white)
        for sign in (-1,1):
            box(f'upper_rail_{sign}',(-l*.395,sign*w*.415-55,roof+900,l*.17,sign*w*.415+55,roof+1000),metal)
            for index in range(4):
                x=-l*.38+index*l*.17
                box(f'rail_stanchion_{sign}_{index}',(x-45,sign*w*.415-45,roof,x+45,sign*w*.415+45,roof+950),metal)
        box('aft_upper_rail',(-l*.40-50,-w*.415,roof+900,-l*.40+50,w*.415,roof+1000),metal)
        profile('wheelhouse',[(-l*.04,roof),(-l*.04,roof+1500),(l*.13,roof+1500),(l*.16,roof)],w*.24,white)
        box('wheelhouse_front_glass',(l*.125,-w*.205,roof+450,l*.145,w*.205,roof+1340),glass)
        for sign in (-1,1):
            box(f'wheelhouse_side_glass_{sign}',(-l*.025,sign*w*.245-20,roof+420,l*.105,sign*w*.245+20,roof+1330),glass)
        box('mast',(l*.02-75,-75,roof+1500,l*.02+75,75,h-120),metal)
        round_piece('radar',(l*.02,0,h-140),330,100,white,axis='z')
        for sign in (-1,1):
            round_piece(f'lifebuoy_{sign}',(-l*.29,sign*w*.43,roof+300),230,100,'#DA7E43')
        box('funnel',(-l*.29,-w*.12,roof,-l*.21,w*.12,roof+1250),'#3F5F69')
    else:
        # Original generic 20 m EMU carriage, not a branded train asset.
        half=l/2; front_nose=actor['carriage_index']==0; rear_nose=actor['carriage_index']==3
        roof_front=half-1000 if front_nose else half
        roof_rear=-half+1000 if rear_nose else -half
        body=[(-half,1100)]
        if rear_nose: body.extend([(-half,1850),(roof_rear,3850)])
        else: body.append((-half,3850))
        body.append((roof_front,3850))
        if front_nose: body.append((half,1850))
        body.append((half,1100))
        profile('silver_carbody',body,w/2,actor['colour'])
        box('roof',(-l*.42,-w*.46,3850,l*.42,w*.46,3970),'#A4B2B7')
        box('underframe',(-l*.42,-w*.43,780,l*.42,w*.43,1120),'#58666C')
        for sign in (-1,1):
            box(f'blue_waist_stripe_{sign}',(-8500,sign*w*.505-16,1550,8500,sign*w*.505+16,1770),'#2D789F')
            for number,x in enumerate((-8050,-6550,-3850,-2350,2350,3850,6550,8050)):
                box(f'passenger_window_{sign}_{number}',(x-580,sign*w*.505-20,2240,x+580,sign*w*.505+20,3380),glass)
            for number,x in enumerate((-5400,0,5400)):
                box(f'sliding_door_{sign}_{number}',(x-680,sign*w*.508-25,1130,x+680,sign*w*.508+25,3650),'#AFBFC4')
                for leaf in (-1,1):
                    box(f'door_window_{sign}_{number}_{leaf}',(x+leaf*330-235,sign*w*.515-20,2380,
                        x+leaf*330+235,sign*w*.515+20,3270),glass)
        for bogie,x in enumerate((-6900,6900)):
            box(f'bogie_{bogie}',(x-1600,-1050,440,x+1600,1050,750),'#3C4C54')
            for axle,dx in enumerate((-1050,1050)):
                for sign in (-1,1):
                    # 1067 mm rail gauge: tread centre aligns with the two rails.
                    y=sign*533.5
                    round_piece(f'wheel_{bogie}_{axle}_{sign}',(x+dx,y,430),430,150,'#29383F')
                    round_piece(f'wheel_hub_{bogie}_{axle}_{sign}',(x+dx,y+sign*90,430),170,55,metal)
        for sign in (-1,1):
            box(f'coupler_{sign}',(sign*10000-250,-160,850,sign*10000+250,160,1100),'#46575D')
        for end,has_cab in ((1,front_nose),(-1,rear_nose)):
            if not has_cab: continue
            # Thin glazing lies outside the sloping end face at every height.
            x1=half-(2250-1850)/2000*1000
            x2=half-(3550-1850)/2000*1000
            profile(f'driver_glass_{end}',[(end*(x1+35),2250),(end*(x2+35),3550),
                (end*(x2+85),3550),(end*(x1+85),2250)],w*.39,glass)
            for sign in (-1,1):
                box(f'cab_headlamp_{end}_{sign}',(end*half-45,sign*820-160,1650,end*half+45,sign*820+160,1820),white)
        # Diamond pantograph remains below the illustrative 5.4 m contact wire.
        roof_z=3970
        box('pantograph_base',(-2350,-650,roof_z,-750,650,roof_z+170),'#526771')
        profile('pantograph_lower',[(-2250,roof_z+160),(-2150,roof_z+160),(-1300,4660),(-1400,4660)],650,metal)
        profile('pantograph_upper',[(-1400,4660),(-1300,4660),(-2150,5170),(-2250,5170)],650,metal)
        box('pantograph_contact_bar',(-2380,-900,5170,-2020,900,5300),'#374F5A')
    return out


def activity_specs(p):
    return [part for actor in _actors(p) for part in _parts(actor)]


def activity_manifest(p):
    actors = _actors(p)
    for actor in actors:
        actor['part_names'] = [part['name'] for part in _parts(actor)]
    return {'schema_version':2,'snapshot_time_s':0,'road_crest_z_mm':p['road_deck_z_mm'],
        'road_grade':.01,'rail_crest_z_mm':p['rail_deck_z_mm']+420,'shared_anchor_half_length_mm':p['shared_anchor_half_length_mm'],
        'route_scope':'Illustrative loops only; not real traffic records or navigable fairways.',
        'actors':deepcopy(actors)}
