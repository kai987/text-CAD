import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
const load=path=>JSON.parse(readFileSync(new URL('../../'+path,import.meta.url),'utf8'));
test('R19 city opening reviews match gross geometry and preserve approval boundaries',()=>{
 const profiles=load('output/review/regulatory_profiles_R07.json');
 const opening=load('output/review/house_3d_assumptions_R01.json').attic.north_vent_opening;
 assert.equal(opening.gross_area_m2,opening.width_mm*opening.height_mm/1e6);
 assert.equal(opening.form,'fixed_aluminium_louver');
 const ids=new Set(profiles.sources.map(s=>s.id));
 for(const p of profiles.profiles){
  const r=p.attic_opening_review;
  assert.equal(r.opening_area_m2,opening.gross_area_m2);
  assert.equal(r.statutory_compliance_result,null);
  assert.equal(r.effective_ventilation_area_m2,null);
  for(const locale of ['zh','ja','en'])assert.ok(r.description[locale].length>20);
  for(const id of r.source_ids)assert.ok(ids.has(id));
  if(['kyoto','nagoya'].includes(p.id))assert.equal(r.area_reference_match,null);
  if(p.id==='osaka'){assert.equal(p.attic_opening_rule.numeric_kind,'approximate_guidance');assert.equal(r.form_reference_match,true);}
  if(p.id==='tokyo'){assert.equal(p.attic_opening_rule.jurisdiction_resolved,false);assert.equal(p.attic_opening_rule.numeric_kind,'edogawa_any');}
 }
});
