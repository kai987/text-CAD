"""R19 saved CAD room-light coverage and source metadata, not lighting design."""
import json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from lib.house_plan import P,floor_plan
from lib.house_geometry import G
from lib.indoor_lighting import indoor_fixture_layout
root=Path(__file__).resolve().parents[1]
data=(root/'GLB/house_3d.glb').read_bytes();size=struct.unpack_from('<I',data,12)[0]
doc=json.loads(data[20:20+size]);nodes={n['name']:n for n in doc['nodes']}
fixtures=indoor_fixture_layout(P,G)
expected={(n,r.id) for n in (1,2) for r in floor_plan(n).rooms if r.kind!='outside'}|{(3,'attic')}
assert {(f['floor'],f['room']) for f in fixtures}==expected
assert len(expected)==14 and len(fixtures)==15
assert len({f["id"] for f in fixtures})==15
attic=[f for f in fixtures if f["floor"]==3]
assert len(attic)==2 and all(f["light_position_glb_m"][1]<6.9 for f in attic)
for f in fixtures:
 n=nodes[f['diffuser_label']];assert n['extras']['indoorLight']==f
 assert 'mesh' in n and f['target_glb_m'][1]<f['light_position_glb_m'][1]
 for suffix in (':shade',':diffuser'):assert f['group']+suffix in nodes
print(json.dumps({'status':'pass','room_lights':len(fixtures),'scope':'Named room coverage and GLB metadata only; no photometry/electrical certification.'}))
