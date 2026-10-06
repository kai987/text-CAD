"""Independent door, furniture, route and saved-artifact checks of R10 draft."""
import hashlib
import json
import math
import sys
from itertools import combinations
from pathlib import Path

import ezdxf
import fitz
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from lib.house_redesign_plan import P, REVISION, dimensions, floor_plan
from lib.jp_drafting import LAYERS

checks=[]


def check(name,passed,evidence):
    checks.append({'name':name,'passed':bool(passed),'evidence':evidence})


def run():
    floors=[floor_plan(n) for n in (1,2)]
    outline=box(0,0,P.width,P.depth)
    for f in floors:
        prefix=f'{f.number}F/'
        rooms={r.id:r for r in f.rooms}
        obstacles=unary_union([box(*b) for _,b in f.fixtures])
        check(prefix+'unique_ids',len(rooms)==len(f.rooms) and
              len({d.id for d in f.doors})==len(f.doors),list(rooms))
        for r in f.rooms:
            check(prefix+r.id+'/valid',r.shape.is_valid and r.shape.area>0 and
                  r.shape.covers(Point(r.label)),{'area_m2':r.area,'label':r.label})
            check(prefix+r.id+'/no_wall_overlap',r.shape.intersection(f.walls).area<.01,
                  r.shape.intersection(f.walls).area)
        overlaps=[(a.id,b.id) for a,b in combinations(f.rooms,2)
                  if a.shape.intersection(b.shape).area>.01]
        check(prefix+'rooms_nonoverlapping',not overlaps,overlaps)
        fixtures=[(name,box(*b)) for name,b in f.fixtures]
        for name,geom in fixtures:
            owners=[r.id for r in f.rooms if r.shape.covers(geom)]
            check(prefix+'fixture/'+name,len(owners)==1,owners)
        collisions=[(a[0],b[0]) for a,b in combinations(fixtures,2)
                    if a[1].intersection(b[1]).area>.01]
        check(prefix+'fixtures_nonoverlapping',not collisions,collisions)
        graph={r.id:set() for r in f.rooms};graph['outside']=set()
        allcuts=[]
        for d in f.doors:
            thickness=P.external_wall if {'outside','balcony'} & {d.a,d.b} else P.internal_wall
            cut=d.opening(thickness);allcuts.append(cut)
            owners=[]
            for sign in (-1,1):
                offset=sign*(thickness/2+2)
                seg=LineString([(d.start+.1,d.at+offset),(d.start+d.width-.1,d.at+offset)]) if d.axis=='h' else \
                    LineString([(d.at+offset,d.start+.1),(d.at+offset,d.start+d.width-.1)])
                side=[r.id for r in f.rooms if r.shape.covers(seg)]
                if seg.disjoint(outline) and not side:side=['outside']
                owners.append(side)
            valid=all(len(side)==1 for side in owners) and sorted(side[0] for side in owners)==sorted([d.a,d.b])
            check(prefix+d.id+'/full_width_adjacency',valid,{'declared':[d.a,d.b],'owners':owners})
            check(prefix+d.id+'/opening_clear',cut.intersection(f.walls).area<.01,cut.intersection(f.walls).area)
            if valid:
                graph[d.a].add(d.b);graph[d.b].add(d.a)
            if d.kind=='slide':
                s=d.start+d.direction*d.width
                panel=box(s,d.at+15,s+d.width,d.at+45) if d.axis=='h' else box(d.at-45,s,d.at-15,s+d.width)
            elif d.kind=='swing':
                points=[(d.start,d.at)]+[(d.start+d.width*math.cos(i*math.pi/360),
                         d.at+d.direction*d.width*math.sin(i*math.pi/360)) for i in range(181)]
                panel=Polygon(points).difference(cut)
            elif d.kind=='bifold':
                lines=[]
                for edge,sign in ((d.start,1),(d.start+d.width,-1)):
                    lines.append(LineString([(edge,d.at),(edge+sign*d.width/8,d.at+d.direction*d.width/4),
                                             (edge+sign*d.width/4,d.at)]))
                panel=unary_union(lines).buffer(10).difference(cut)
            else:continue
            check(prefix+d.id+'/leaf_clear_of_fixtures',panel.intersection(obstacles).area<.01,
                  panel.intersection(obstacles).area)
            if d.kind=='slide':
                # The parked leaf represents a reserved wall pocket. It must
                # fit entirely inside an interior partition, not run into a room
                # or exterior/window frame. Pocket construction remains pending.
                pocket_error=panel.difference(f.walls).area
                inner=box(P.external_wall,P.external_wall,P.width-P.external_wall,P.depth-P.external_wall)
                check(prefix+d.id+'/interior_pocket_reservation',pocket_error<.01 and inner.covers(panel),
                      {'outside_partition_mm2':pocket_error,'construction':'unverified wall pocket'})
            else:
                # Nominal bifold centreline hinges coincide with jambs; permit
                # only the 10 mm drawing-envelope radius at those hinge points.
                freepanel=panel.difference(cut.buffer(10)) if d.kind=='bifold' else panel
                check(prefix+d.id+'/leaf_clear_of_walls',freepanel.intersection(f.walls).area<.01,
                      freepanel.intersection(f.walls).area)
        # Full-width window checks: verify each opening actually meets exterior.
        for i,(axis,at,start,width) in enumerate(f.windows):
            cut=box(start,at-P.external_wall/2-1,start+width,at+P.external_wall/2+1) if axis=='h' else \
                box(at-P.external_wall/2-1,start,at+P.external_wall/2+1,start+width)
            allcuts.append(cut)
            check(prefix+f'window/{i}/clear',cut.intersection(f.walls).area<.01,cut.intersection(f.walls).area)
        coverage=unary_union([r.shape for r in f.rooms]+[f.walls]+allcuts)
        missing=outline.difference(coverage)
        check(prefix+'whole_outline_assigned',missing.area<.01,missing.area)
        origin='outside' if f.number==1 else 'stairs'
        seen={origin};todo=[origin]
        while todo:
            for target in graph[todo.pop()]-seen:
                seen.add(target);todo.append(target)
        check(prefix+'all_rooms_reachable',set(rooms)<=seen,{'reachable':sorted(seen)})
        if f.number==2:
            public={'stairs','hall','wc_hall','balcony'};seen={'stairs'};todo=['stairs']
            while todo:
                for target in (graph[todo.pop()] & public)-seen:
                    seen.add(target);todo.append(target)
            check('2F/balcony_without_bedroom_transit','balcony' in seen,sorted(seen))
        # Independent occupied-room routes; 600 mm demonstration corridor swept
        # around the centreline. This is not an accessibility or legal test.
        routes=([('entry_stairs',[(6800,950),(6800,3100),(6560,3700),(6560,4500)]),
                 ('entry_wc',[(6800,3100),(5560,3500),(5560,4800),(5560,5800)]),
                 ('ldk_wash',[(5560,3900),(3500,3900),(3550,5700)])] if f.number==1 else
                [('stairs_balcony',[(7560,4500),(7560,3830),(3830,3830),(3830,-450)]),
                 ('stairs_wc',[(7560,3830),(5560,3830),(5560,5800)])])
        for name,points in routes:
            swept=LineString(points).buffer(300,cap_style='flat',join_style='mitre')
            conflict=swept.intersection(unary_union([f.walls,obstacles])).area
            check(prefix+'route/'+name,conflict<.01,{'width_mm':600,'collision_mm2':conflict})
        file=ROOT/f'DXF/house_redesign_R10_{f.number}f.dxf'
        doc=ezdxf.readfile(file);auditor=doc.audit();msp=doc.modelspace()
        check(prefix+'DXF/audit',not auditor.errors,[str(e) for e in auditor.errors])
        check(prefix+'DXF/units_revision',doc.units==ezdxf.units.MM and doc.ezdxf_metadata()['REVISION']==REVISION,
              {'units':doc.units,'revision':doc.ezdxf_metadata()['REVISION']})
        texts=[e.dxf.text for e in msp.query('TEXT')]
        check(prefix+'DXF/room_labels',all(any(r.name in text for text in texts) for r in f.rooms),texts)
        dims=list(msp.query('DIMENSION'))
        check(prefix+'DXF/native_editable_dimensions',len(dims)>=4,len(dims))
        badcolors=[e.dxf.handle for e in msp if e.dxf.get('color',256) not in (7,256)]
        check(prefix+'DXF/high_contrast',not badcolors,badcolors)
        check(prefix+'DXF/viewport_scale',all(abs(v.dxf.view_height/v.dxf.height-50)<1e-6
              for v in doc.layouts.get('JP_A3_1_50').query('VIEWPORT') if v.dxf.status>1),50)
    # R10 changes only the balcony outside the approved R09 indoor rooms.
    previous=json.loads((ROOT/'output/review/house_redesign_R09.json').read_text())
    for f in floors:
        old={r['id']:r for r in previous['floors'][f.number-1]['rooms']}
        for room in f.rooms:
            if room.id!='balcony':
                check(f'{f.number}F/R09_room_preserved/{room.id}',
                      room.shape.symmetric_difference(Polygon(old[room.id]['polygon_mm'])).area<.01,
                      room.shape.bounds)
    balcony=next(r for r in floors[1].rooms if r.id=='balcony')
    check('R10/balcony_left_fixed',dimensions()['bx']==2010,dimensions()['bx'])
    check('R10/balcony_east_aligns_with_wall',dimensions()['bx']+P.balcony_width==P.width,P.width)
    check('R10/balcony_clear_area',abs(balcony.area-8.372)<1e-8,balcony.area)
    check('R10/separate_canopy_disabled',P.entrance_canopy is False,P.entrance_canopy)
    from lib.exterior_geometry import E
    from lib.balcony_geometry import support_positions,B
    door=next(d for d in floors[0].doors if d.a=='outside')
    porch=box(door.start-E.entrance_canopy_margin,-E.porch_depth,
              door.start+door.width+E.entrance_canopy_margin,0)
    slab=box(dimensions()['bx'],-P.balcony_depth,dimensions()['bx']+P.balcony_width,0)
    check('R10/balcony_projects_over_full_entrance_porch',slab.covers(porch),porch.bounds)
    path=box(porch.bounds[0],-5500,porch.bounds[2],0)
    check('R10/three_supports_clear_entry_path',len(support_positions(P))==3 and all(
          box(x-B.footing_width/2,-1450-B.footing_width/2,
              x+B.footing_width/2,-1450+B.footing_width/2).intersection(path).area<.01
          for x in support_positions(P)),list(support_positions(P)))
    a,b=[{r.id:r for r in f.rooms} for f in floors]
    for room in ('stairs','wc'):
        check('vertical_alignment/'+room,a[room].shape.equals(b[room].shape),a[room].shape.bounds)
    pdf=fitz.open(ROOT/'output/pdf/house_floor_plans_R10_JP.pdf')
    check('PDF/2_A3_sheets',len(pdf)==2 and all(abs(p.rect.width-420*72/25.4)<1 for p in pdf),len(pdf))
    check('PDF/approval_and_assumptions',all('R10' in p.get_text() and '2800' in p.get_text().replace(',','') for p in pdf),True)
    report={'revision':REVISION,'status':'pass' if all(c['passed'] for c in checks) else 'fail',
            'scope':'Concept geometry and editable draft artifacts only; no engineering/code validation.',
            'checks':checks,'sha256':{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
                for path in [ROOT/'output/pdf/house_floor_plans_R10_JP.pdf',
                             ROOT/'DXF/house_redesign_R10_1f.dxf',ROOT/'DXF/house_redesign_R10_2f.dxf']}}
    (ROOT/'output/review/validation_redesign_R10.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    failures=[c for c in checks if not c['passed']]
    print(json.dumps({'status':report['status'],'checks':len(checks),'failures':failures},ensure_ascii=False,indent=2))
    return int(bool(failures))


if __name__=='__main__':raise SystemExit(run())
