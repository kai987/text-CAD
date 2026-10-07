"""Validate optional furniture geometry and the two approved plan layouts.

Run .venv/bin/python checks/validate_furniture.py. This does not export CAD,
alter model integrations, or write other files. Checks use native exact solids
and independent geometric bounds, not rendered images or triangle ordering.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from shapely.geometry import box

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))

from lib.apartment_plan import P as APARTMENT,apartment_plan
from lib.house_plan import P as HOUSE,floor_plan
from lib.furniture_geometry import clearance_report,furniture_group,furniture_placements


results=[]
counts=[]
def check(name,ok,evidence=None):
    results.append({'check':name,'pass':bool(ok),'evidence':evidence})

def leaves(node):
    if node.children:
        for child in node.children:yield from leaves(child)
    else:yield node

for model,floor,p in [('house',floor_plan(1),HOUSE),('house',floor_plan(2),HOUSE),
                     ('apartment',apartment_plan()[0],APARTMENT)]:
    prefix=f'{model}:F{floor.number}'
    for result in clearance_report(floor,model,p):
        results.append({**result,'check':prefix+':'+result['check']})
    group=furniture_group(floor,model,p)
    objects=list(group.children);parts=list(leaves(group));placements=furniture_placements(floor,model,p)
    counts.append({'model':model,'floor':floor.number,'objects':len(objects),'solid_parts':len(parts)})
    check(prefix+':semantic_layer',group.label==f'F{floor.number}:furniture')
    check(prefix+':one_group_per_furniture_object',len(objects)==len(placements))
    check(prefix+':leaf_labels_unique',len({s.label for s in parts})==len(parts))
    for part in parts:
        check(prefix+':'+part.label+':label_and_color',':furniture:' in part.label and part.color is not None)
        solids=part.solids()
        check(prefix+':'+part.label+':one_closed_positive_solid',len(solids)==1 and solids[0].is_valid and solids[0].volume>0)
    for item,obj in zip(placements,objects):
        b=obj.bounding_box();expected=item.footprint().bounds
        actual=(b.min.X,b.min.Y,b.max.X,b.max.Y)
        check(prefix+':'+item.id+':solid_footprint_matches_plan',all(abs(a-e)<.01 for a,e in zip(actual,expected)),list(actual))
        check(prefix+':'+item.id+':grounded_on_floor',abs(b.min.Z-(floor.number-1)*p.storey_height)<.01,b.min.Z)
        check(prefix+':'+item.id+':below_windows_and_ceiling',b.max.Z-(floor.number-1)*p.storey_height<1500,b.max.Z)
        names={part.label.rsplit(':',1)[-1] for part in leaves(obj)}
        if item.kind=='bed':
            check(prefix+':'+item.room+':bed_has_separate_soft_layers',{'frame','headboard','mattress','blanket','pillow_1'}<=names)
            # Bedroom headboards are deliberately below the smallest existing 900 mm sill.
            head=next(part for part in leaves(obj) if part.label.endswith(':headboard'))
            check(prefix+':'+item.room+':low_headboard',head.bounding_box().size.Z<=800)
        elif item.kind in ('sofa','corner_sofa'):
            check(prefix+':sofa:distinct_cushions_and_arms',{'seat_1','seat_2','back_cushion_1','back_cushion_2','arm_left','arm_right'}<=names)
            if item.kind=='corner_sofa':
                check(prefix+':sofa:four_separate_seats_and_chaise',{'seat_1','seat_2','seat_3','seat_4','chaise_base'}<=names)
        elif item.kind=='television':
            check(prefix+':TV:console_stand_screen',{'console','tv_foot','tv_stem','tv_bezel','tv_screen','drawer_1','drawer_2'}<=names)
    check(prefix+':model_has_beds_for_each_bedroom',
          {r.id for r in floor.rooms if r.id in ('master','bed2','bed3')}=={i.room for i in placements if i.kind=='bed'})
    if model=='house' and floor.number==1:
        sofa=next(i for i in placements if i.id=='sofa');tv=next(i for i in placements if i.id=='television')
        coffee=next(i for i in placements if i.id=='coffee_table')
        check(prefix+':R15:four_dining_chairs',len([i for i in placements if i.kind=='chair'])==4)
        check(prefix+':R15:TV_south_of_sofa_facing_north',tv.rotation==-180 and sofa.rotation==0 and tv.y+tv.depth<sofa.y)
        check(prefix+':R15:coffee_inside_L_cavity_without_overlap',box(*sofa.footprint().bounds).intersects(coffee.footprint()) and sofa.footprint().intersection(coffee.footprint()).area<.001)

summary={'checks':len(results),'passed':sum(r['pass'] for r in results),'failed':sum(not r['pass'] for r in results),
         'counts':counts,'units':'mm, exact BRep solids; clearance targets are demonstration assumptions'}
print(json.dumps(summary,ensure_ascii=False,indent=2))
for row in results:
    if not row['pass']:print(json.dumps(row,ensure_ascii=False))
raise SystemExit(0 if summary['failed']==0 else 1)
