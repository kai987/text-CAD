"""Independent door, furniture, route and saved-artifact checks of R10 draft."""
import hashlib
import json
import math
import sys
from itertools import combinations
from pathlib import Path

import ezdxf
import fitz
from shapely.affinity import scale
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
                panel=box(s,d.at+15,s+d.width,d.at+45) if d.axis=='h' else (box(d.at+15,s,d.at+45,s+d.width) if P.mirror_layout else box(d.at-45,s,d.at-15,s+d.width))
            elif d.kind=='swing':
                hinge=d.start+d.width if d.hinge_at_end else d.start
                sign=-1 if d.hinge_at_end else 1
                points=[(hinge,d.at)]+[(hinge+sign*d.width*math.cos(i*math.pi/360),
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
            check('R17/balcony_from_both_bedrooms',all('balcony' in graph[r] for r in ('master','bed2')),{k:sorted(v) for k,v in graph.items()})
        # Independent occupied-room routes; 600 mm demonstration corridor swept
        # around the centreline. This is not an accessibility or legal test.
        routes=([('entry_stairs',[(6800,950),(6800,3100),(6560,3700),(6560,4500)]),
                 ('entry_wc',[(6800,3100),(6800,3700),(5560,3700),(5560,5800)]),
                 ('ldk_wash',[(5560,3900),(4600,3900),(3900,4200),(3550,4900),(3550,5700)])] if f.number==1 else
                [('stairs_master',[(7560,4500),(7560,3830),(3450,3830),(3450,2800)]),
                 ('master_balcony',[(3150,2800),(2450,2800),(2450,1875),(2000,1875),(2000,500),(1450,500),(1450,-450)]),
                 ('stairs_wc',[(7560,3830),(5560,3830),(5560,5800)])])
        for name,points in routes:
            if P.mirror_layout:points=[(P.width-x,y) for x,y in points]
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
    # R15 world-space contract: reflect room topology without changing area.
    for f in floors:
        stairs=next(r.shape for r in f.rooms if r.id=='stairs')
        check(f'R15/F{f.number}/stairs_west',stairs.bounds[2]<P.width/2,stairs.bounds)
        west=[w for w in f.windows if w[0]=='v' and w[1]<P.width/2]
        east=[w for w in f.windows if w[0]=='v' and w[1]>P.width/2]
        check(f'R15/F{f.number}/west_only_stair_window',len(west)==1 and stairs.covers(Point(P.external_wall+1,west[0][2]+west[0][3]/2)),west)
        expected=['ldk'] if f.number==1 else ['master','bed3']
        owners=[r.id for w in east for r in f.rooms if r.shape.covers(Point(P.width-P.external_wall-1,w[2]+w[3]/2))]
        check(f'R15/F{f.number}/east_room_windows',sorted(owners)==sorted(expected),owners)
    entry=next(d for d in floors[0].doors if d.a=='outside')
    check('R15/entrance_southwest',entry.start+entry.width<P.width/2,[entry.start,entry.start+entry.width])
    kitchen=next(b for name,b in floors[0].fixtures if name=='対面キッチン')
    cupboard=next(b for name,b in floors[0].fixtures if name=='カップボード')
    check('R15/kitchen_main_rear_aisle_900',cupboard[1]-kitchen[3]==900,{'counter':kitchen,'cupboard':cupboard})
    # R10 changes only the balcony outside the approved R09 indoor rooms.
    previous=json.loads((ROOT/'output/review/house_redesign_R09.json').read_text())
    for f in floors:
        old={r['id']:r for r in previous['floors'][f.number-1]['rooms']}
        for room in f.rooms:
            if f.number==1 and room.id in ('ldk','stairs','under_stairs','wc'):continue
            if f.number==2 and room.id in ('master','bed2','bed3','closet','hall','wc'):continue
            if room.id!='balcony':
                check(f'{f.number}F/R09_room_preserved/{room.id}',
                      room.shape.symmetric_difference(scale(Polygon(old[room.id]['polygon_mm']),xfact=-1 if P.mirror_layout else 1,origin=(P.width/2,0))).area<.01,
                      room.shape.bounds)
    first=floors[0];first_rooms={r.id:r for r in first.rooms}
    check('R15/WC_forecourt_removed','wc_hall' not in first_rooms,list(first_rooms))
    check('R15/WC_direct_from_LDK',any(d.id=='D05' and {d.a,d.b}=={'ldk','wc'} for d in first.doors),[d.id for d in first.doors])
    check('R15/stair_storage_net_dimensions',first_rooms['under_stairs'].shape.bounds[2]-first_rooms['under_stairs'].shape.bounds[0]==800 and abs(first_rooms['under_stairs'].area-1.408)<1e-8,first_rooms['under_stairs'].shape.bounds)
    second_rooms={r.id:r for r in floors[1].rooms}
    for f in floors:
        wc=next(r for r in f.rooms if r.id=='wc')
        check(f'R17/F{f.number}/WC_south_wall_flush_with_washroom',wc.shape.bounds[1]==first_rooms['wash'].shape.bounds[1],wc.shape.bounds)
        check(f'R17/F{f.number}/WC_clear_900x1820',abs(wc.area-1.638)<1e-8,wc.area)
    check('R17/open_wardrobe_in_master','closet' not in second_rooms and abs(second_rooms['master'].area-14.76)<1e-8,second_rooms['master'].shape.bounds)
    new_doors={d.id:d for d in floors[1].doors}
    check('R17/master_door_at_hall_corner',new_doors['D21'].axis=='v' and new_doors['D21'].at==4360 and new_doors['D21'].start==3480 and new_doors['D21'].width==750,new_doors['D21'].__dict__)
    check('R17/north_bedroom_door_at_hall_corner',new_doors['D23'].axis=='h' and new_doors['D23'].at==4330 and new_doors['D23'].start==3510 and new_doors['D23'].width==750,new_doors['D23'].__dict__)
    check('R17/no_enclosed_closet_door','D24' not in new_doors,list(new_doors))
    check('R17/bedrooms_still_separate',not second_rooms['master'].shape.intersects(second_rooms['bed3'].shape),True)
    balcony=next(r for r in floors[1].rooms if r.id=='balcony')
    check('R10/balcony_left_fixed',dimensions()['bx']==0,dimensions()['bx'])
    check('R10/balcony_east_aligns_with_wall',dimensions()['bx']+P.balcony_width==P.width,P.width)
    check('R10/balcony_clear_area',abs(balcony.area-7.191)<1e-8,balcony.area)
    check('R10/separate_canopy_disabled',P.entrance_canopy is False,P.entrance_canopy)
    from lib.exterior_geometry import E
    from lib.balcony_geometry import support_positions,B
    door=next(d for d in floors[0].doors if d.a=='outside')
    porch=box(door.start-E.entrance_canopy_margin,-E.porch_depth,
              door.start+door.width+E.entrance_canopy_margin,0)
    slab=box(dimensions()['bx'],-P.balcony_depth,dimensions()['bx']+P.balcony_width,0)
    check('R12/balcony_depth',P.balcony_depth==1000,P.balcony_depth)
    check('R12/porch_outer_300mm_exposed',abs(slab.bounds[1]-porch.bounds[1]-300)<.01,porch.bounds)
    check('R12/no_ground_supports',not P.balcony_supports and not support_positions(P),list(support_positions(P)))
    a,b=[{r.id:r for r in f.rooms} for f in floors]
    for room in ('stairs','wc'):
        check('vertical_alignment/'+room,a[room].shape.bounds==b[room].shape.bounds if room=='stairs' else a[room].shape.equals(b[room].shape),a[room].shape.bounds)
    pdf=fitz.open(ROOT/'output/pdf/house_floor_plans_R10_JP.pdf')
    check('PDF/2_A3_sheets',len(pdf)==2 and all(abs(p.rect.width-420*72/25.4)<1 for p in pdf),len(pdf))
    check('PDF/approval_and_assumptions',all(REVISION in p.get_text() and '2800' in p.get_text().replace(',','') for p in pdf),True)
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
