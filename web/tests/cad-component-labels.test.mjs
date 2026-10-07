import test from 'node:test';
import assert from 'node:assert/strict';
import { loadGlbGeometry } from './helpers/load-glb-geometry.mjs';
import { cadComponentLabel } from '../src/cad-component-labels.ts';
import { locales, messages } from '../src/localization.ts';
import { modelCopy } from '../src/model-copy.ts';
import { modelLayouts } from '../src/model-state.ts';
import { bindCadNodes, selectionFor } from '../src/model-scene.ts';

const models = [['house', 'house_3d.glb'], ['apartment', 'apartment_2ldk.glb']];

async function loadModel(filename) {
  const gltf = await loadGlbGeometry(new URL(`../../GLB/${filename}`, import.meta.url));
  return { gltf, objects: bindCadNodes(gltf) };
}

// These are the categories the original CAD naming convention assigns to meshes.
// They are also the IDs used to highlight, isolate, and toggle the picked part.
function originalCategory(name) {
  if (/^F1:exterior:foundation:(?:south|north|west|east)$/.test(name)) return 'foundation:existing_plinth';
  const structural = /^structure:(F1|F2|attic|roof):([^:]+)/.exec(name);
  if (structural) {
    const kind = structural[2];
    if (kind.startsWith('column_')) return 'structure:columns';
    if (kind.startsWith('beam_')) return 'structure:beams';
    if (kind.startsWith('sill_')) return 'structure:sills';
    if (kind.startsWith('joist_')) return 'structure:attic_joists';
    if (/^(?:header|trimmer)_/.test(kind)) return 'structure:attic_headers';
    if (kind.startsWith('bearing_wall_')) return 'structure:bearing_walls';
    if (structural[1] === 'roof') return 'structure:roof_framing';
  }
  const siteCategory = /^(foundation|yard|fence|lighting):([^:]+):/.exec(name);
  if (siteCategory) return `${siteCategory[1]}:${siteCategory[2]}`;
  if (name === 'roof:attic_ceiling_slab' || name === 'attic:deck_finish') return 'attic:floor_slab';
  if (/^attic:(?:lining|knee_wall|gable_lining):/.test(name)) return 'attic:partition_walls';
  if (/^attic:north_vent:/.test(name)) return 'attic:windows';
  if (/^attic:storage:/.test(name)) return 'attic:storage_fixtures';
  if (/^attic:guardrail:/.test(name)) return 'attic:guardrails';
  const floor = /^(F[12]):/.exec(name)?.[1];
  if (!floor) return name.split(':')[0];
  if (/^F[12]:floor_slab$/.test(name)) return name;
  if (/^F[12]:wall_external_/.test(name)) return `${floor}:external_walls`;
  if (/^F[12]:exterior:(?:cladding|foundation|entry_panel|downpipe):/.test(name)) return `${floor}:external_walls`;
  if (/^F[12]:wall_partition_/.test(name)) return `${floor}:partition_walls`;
  if (/^F[12]:D\d+_door_/.test(name)) return `${floor}:doors`;
  if (/^F[12]:D\d+:(?:canopy|porch|porch_step|frame|handle|threshold)$/.test(name)) return `${floor}:doors`;
  if (/^F[12]:W\d+:/.test(name)) return `${floor}:windows`;
  if (/^F[12]:storage_/.test(name)) return `${floor}:storage_fixtures`;
  if (/^F1:under_stairs:/.test(name)) return `${floor}:storage_fixtures`;
  if (/^F[12]:fixture_/.test(name)) return `${floor}:fixtures`;
  if (/^F[12]:furniture:/.test(name)) return `${floor}:furniture`;
  assert.fail(`Unclassified original CAD mesh: ${name}`);
}

for (const [modelId, filename] of models) {
  test(`${modelId}: every original selectable GLB mesh has a localized label or its category fallback`, async t => {
    const { gltf, objects } = await loadModel(filename);
    const layout = modelLayouts[modelId];
    const originalNodes = gltf.parser.json.nodes;
    const originalJson = JSON.stringify(originalNodes);
    const meshNodes = originalNodes.filter(node => node.mesh !== undefined);
    const categoryMeshes = new Set(layout.parts.map(part => part.id));
    let componentCount = 0, categoryCount = 0;

    for (const node of meshNodes) {
      const object = objects.get(node.name);
      assert.ok(object?.isMesh, `${filename}: original mesh ${node.name} must be bound`);
      const selectionBefore = selectionFor(object, layout);
      assert.ok(selectionBefore, `${filename}: ${node.name} must be selectable`);
      assert.equal(selectionBefore.id, originalCategory(node.name), 'original highlight/category ID');
      assert.equal(selectionBefore.name, node.name, 'original CAD ID is retained');
      const loadedName = object.name;

      for (const locale of locales) {
        const label = cadComponentLabel(locale, node.name, modelId);
        if (categoryMeshes.has(node.name)) {
          // Floor slab meshes share the category ID. The UI already presents
          // the translated floor + category title, so no duplicate subtitle.
          assert.equal(label, null, `${locale}: ${node.name} is a category selection`);
          const part = layout.parts.find(part => part.id === node.name);
          const copy = modelCopy(messages[locale], locale, modelId);
          assert.ok(copy.groups[part.group]?.trim(), `${locale}: translated floor fallback`);
          assert.ok(copy.partKinds[node.name.split(':')[1]]?.trim(), `${locale}: translated category fallback`);
        } else {
          assert.equal(typeof label, 'string', `${modelId}/${locale}: ${node.name}`);
          assert.ok(label.trim(), `${modelId}/${locale}: ${node.name} must be nonempty`);
          assert.notEqual(label, node.name, `${locale}: friendly label must replace the raw CAD ID`);
          assert.doesNotMatch(label, /_/, `${locale}: raw CAD tokens are not shown`);
          assert.doesNotMatch(label, /(?:roof|stairs|balcony|ceiling|furniture|fixture_\d+|wall_external|wall_partition):/,
            `${locale}: no untranslated CAD path in the label`);
          if (locale === 'en') assert.doesNotMatch(label, /[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}]/u,
            `English label must not retain Chinese/Japanese copy: ${node.name}`);
          else assert.match(label, /[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}]/u,
            `${locale}: localized copy is present for ${node.name}`);
        }
      }
      if (categoryMeshes.has(node.name)) categoryCount++;
      else componentCount++;
      assert.equal(object.name, loadedName, 'localization does not change the loader name');
      assert.equal(object.userData.cadName, node.name, 'localization does not change the original CAD name');
      assert.deepEqual(selectionFor(object, layout), selectionBefore, 'selection and highlighting stay unchanged');
    }

    for (const node of originalNodes.filter(node => node.mesh === undefined)) {
      for (const locale of locales) {
        assert.equal(cadComponentLabel(locale, node.name, modelId), null,
          `${modelId}/${locale}: assembly ${node.name} does not get a leaf subtitle`);
      }
    }
    assert.equal(JSON.stringify(originalNodes), originalJson, 'GLB node names are not mutated');
    assert.ok(componentCount > 100, 'coverage includes the detailed fixture and furniture geometry');
    assert.equal(categoryCount, modelId === 'house' ? 2 : 1, 'only floor-slab category meshes use fallback');
    t.diagnostic(`${meshNodes.length} selectable meshes: ${componentCount} component labels in 3 locales, ${categoryCount} translated category fallbacks`);
  });
}

test('roof labels distinguish east/west planes, gable walls, and attic ceiling', () => {
  const expected = {
    zh: [/西.*屋面/, /东.*屋面/, /南.*山墙/, /北.*山墙/, /阁楼.*下地板/],
    ja: [/西.*屋根面/, /東.*屋根面/, /南.*妻壁/, /北.*妻壁/, /小屋裏.*下地床/],
    en: [/West.*roof plane/i, /East.*roof plane/i, /South.*gable wall/i, /North.*gable wall/i, /Attic.*subfloor/i],
  };
  const names = ['roof:west_plane', 'roof:east_plane', 'roof:south_gable_wall',
    'roof:north_gable_wall', 'roof:attic_ceiling_slab'];
  for (const locale of locales) {
    names.forEach((name, index) => assert.match(cadComponentLabel(locale, name), expected[locale][index], `${locale}: ${name}`));
  }
});
test('outdoor fixture labels identify their individual housings and diffusers in all three languages', () => {
  const fixtures = [
    ['wall', 'entrance_01', ['mount', 'lower_cap', 'upper_cap', 'left_trim', 'right_trim', 'diffuser']],
    ...['path_01', 'path_02'].map(id => ['path', id, ['base', 'body', 'diffuser', 'cap']]),
    ...['garden_01', 'garden_02'].map(id => ['garden', id, ['base', 'body', 'diffuser']]),
    ...['gate_01', 'gate_02'].map(id => ['gate', id, ['mount', 'lower_cap', 'upper_cap', 'left_trim', 'right_trim', 'diffuser']]),
  ];
  for (const locale of locales) {
    const labels = fixtures.flatMap(([category, fixture, details]) => details.map(detail => {
      const label = cadComponentLabel(locale, `lighting:${category}:${fixture}:${detail}`);
      assert.ok(label?.trim(), `${locale}: ${fixture}/${detail}`);
      assert.doesNotMatch(label, /lighting:|_/);
      return label;
    }));
    assert.equal(labels.length, 32);
    assert.equal(new Set(labels).size, labels.length, 'fixture numbers and individual details remain distinct');
    assert.equal(cadComponentLabel(locale, 'lighting'), null);
    assert.equal(cadComponentLabel(locale, 'lighting:wall'), null);
    assert.equal(cadComponentLabel(locale, 'lighting:wall:entrance_01'), null);
    assert.equal(cadComponentLabel(locale, 'lighting:wall:unknown:diffuser'), null);
  }
});
test('attic storage, hatch and ladder details have distinct labels in all three languages', () => {
  const groups = [
    ['attic:lining:west_slope', 'attic:lining:east_slope'],
    ['attic:knee_wall:west', 'attic:knee_wall:east'],
    ['attic:gable_lining:south', 'attic:gable_lining:north'],
    ['attic:guardrail:post_southwest', 'attic:guardrail:post_southeast', 'attic:guardrail:post_northwest', 'attic:guardrail:post_northeast'],
    ['attic:guardrail:west_rail', 'attic:guardrail:south_rail', 'attic:guardrail:north_rail'],
    ['attic_access:left_stringer', 'attic_access:right_stringer'],
    ['attic_access:hatch_trim', 'attic_access:hatch_lid'],
    ['attic_access:hinge_left', 'attic_access:hinge_right'],
    ['attic_access:tread_01', 'attic_access:tread_10'],
    ...['west_shelf', 'east_shelf'].map(shelf => ['back', 'side_south', 'side_north', 'bottom', 'middle', 'top']
      .map(panel => `attic:storage:${shelf}:${panel}`)),
    ...['southwest_box', 'southeast_box'].map(box => ['body', 'lid'].map(panel => `attic:storage:${box}:${panel}`)),
  ];
  for (const locale of locales) {
    assert.ok(cadComponentLabel(locale, 'attic:deck_finish')?.trim());
    for (const names of groups) {
      const labels = names.map(name => cadComponentLabel(locale, name));
      assert.ok(labels.every(label => label?.trim()), `${locale}: every detail is translated`);
      assert.equal(new Set(labels).size, names.length, `${locale}: left/right and part numbers remain distinguishable`);
    }
    assert.match(cadComponentLabel(locale, 'attic_access:tread_10'), /10$/);
    assert.notEqual(cadComponentLabel(locale, 'attic:storage:west_shelf:middle'),
      cadComponentLabel(locale, 'attic:storage:east_shelf:middle'));
  }
});

test('foundation, yard and fence labels distinguish directions and physical details in all languages', () => {
  const categories = [
    ['foundation:raft:slab', 'foundation:raft:entrance_footing'],
    ['south', 'north', 'west', 'east'].map(side => `foundation:stem_walls:${side}`),
    ['foundation:entrance_supports:porch', 'foundation:entrance_supports:upper_step'],
    ['yard:entrance_path:paving', 'yard:entrance_path:lower_step'],
    ['paving', 'line_left', 'line_right', 'line_back', 'line_divider_1', 'bay_1_wheel_stop_left', 'bay_1_wheel_stop_right', 'bay_2_wheel_stop_left', 'bay_2_wheel_stop_right'].map(part => `yard:parking:${part}`),
    ['lawn_front', 'lawn_north', 'lawn_east', 'lawn_west', 'shrub_01', 'shrub_02', 'shrub_03'].map(part => `yard:planting:${part}`),
    ...['posts', 'panels', 'footings'].map(kind => ['north_01', 'west_01', 'east_01', 'south_west_01', 'south_middle_01', 'south_east_01', 'north_02']
      .map(part => `fence:${kind}:${part}`)),
  ];
  for (const locale of locales) {
    for (const name of ['yard:soil:base', 'yard:ground_surfaces:gravel']) assert.ok(cadComponentLabel(locale, name)?.trim());
    for (const names of categories) {
      const labels = names.map(name => cadComponentLabel(locale, name));
      assert.ok(labels.every(label => label?.trim()), `${locale}: all physical site details are translated`);
      assert.equal(new Set(labels).size, names.length, `${locale}: left/right and directions remain distinguishable`);
    }
    for (const name of ['foundation', 'yard', 'fence', 'foundation:raft', 'yard:parking', 'fence:posts']) {
      assert.equal(cadComponentLabel(locale, name), null, `${locale}: group names use the localized selection title`);
    }
  }
});

test('doors and window details retain their IDs and distinguish physical parts', () => {
  const terms = {
    zh: { swing: /平开门/, slide: /(?:移门|推拉门)/, lower: /下.*框/, upper: /上.*框/, center: /(?:中.*梃|中.*框)/, glass: /玻璃/ },
    ja: { swing: /開き戸/, slide: /引き戸/, lower: /下.*枠/, upper: /上.*枠/, center: /(?:中.*方立|中央.*枠)/, glass: /ガラス/ },
    en: { swing: /(?:swing|hinged).*door/i, slide: /sliding.*door/i, lower: /lower.*frame/i, upper: /upper.*frame/i, center: /(?:cent(?:er|re)|central).*mullion/i, glass: /glass/i },
  };
  for (const locale of locales) {
    const checks = [
      ['F1:D01_door_swing', 'D01', terms[locale].swing, 'house'],
      ['F1:D03_door_slide', 'D03', terms[locale].slide, 'apartment'],
      ['F1:W01:frame_1', 'W01', terms[locale].lower, 'house'],
      ['F1:W01:frame_2', 'W01', terms[locale].upper, 'house'],
      ['F1:W01:frame_5', 'W01', terms[locale].center, 'apartment'],
      ['F1:W01:glass_2', 'W01', terms[locale].glass, 'apartment'],
    ];
    for (const [name, id, detail, modelId] of checks) {
      const label = cadComponentLabel(locale, name, modelId);
      assert.ok(label.includes(id), `${locale}: ${name} retains its door/window ID`);
      assert.match(label, detail, `${locale}: ${name} describes the correct detail`);
    }
    assert.match(cadComponentLabel(locale, 'F1:W01:glass_2', 'apartment'), /2/, 'pane number is retained');
    assert.notEqual(cadComponentLabel(locale, 'F1:W01:frame_3'), cadComponentLabel(locale, 'F1:W01:frame_4'), 'side frame pieces remain distinguishable');
  }
});

test('new detached-house facade details have precise three-language component names', () => {
  const terms = {
    zh: { cladding: /(?:外墙|饰面|挂板)/, foundation: /(?:基础|基座)/, wood: /(?:木|玄关)/,
      drain: /(?:排水|落水|雨水)/, canopy: /(?:雨棚|门廊)/, porch: /(?:玄关|门廊|平台)/,
      handle: /(?:把手|拉手)/, sill: /(?:窗台|下沿)/, seam: /(?:屋面|屋顶).*(?:接缝|立边|立缝)|(?:接缝|立边|立缝).*(?:屋面|屋顶)/,
      ridge: /屋脊/, fascia: /(?:檐口|封檐|檐板|破风)/, soffit: /(?:檐底|檐下)/, gutter: /(?:天沟|雨槽|檐沟)/ },
    ja: { cladding: /(?:外壁|サイディング)/, foundation: /(?:基礎|巾木)/, wood: /(?:木|玄関)/,
      drain: /(?:竪樋|縦樋|排水|たてとい)/, canopy: /(?:庇|ひさし)/, porch: /(?:玄関|ポーチ)/,
      handle: /(?:取手|ハンドル|把手)/, sill: /(?:水切り|窓台)/, seam: /(?:立平|立ハゼ|立ちはぜ|継ぎ目|縦葺|屋根面).*/,
      ridge: /棟/, fascia: /(?:破風|鼻隠し|軒先)/, soffit: /軒天/, gutter: /(?:軒樋|雨樋|軒とい)/ },
    en: { cladding: /(?:cladding|siding)/i, foundation: /(?:foundation|plinth)/i, wood: /(?:wood|entrance|entry)/i,
      drain: /(?:downpipe|downspout)/i, canopy: /canopy/i, porch: /(?:porch|entrance|entry)/i,
      handle: /handle/i, sill: /sill/i, seam: /(?:standing.?seam|seam)/i,
      ridge: /ridge/i, fascia: /(?:fascia|bargeboard)/i, soffit: /soffit/i, gutter: /gutter/i },
  };
  const checks = [
    ['F1:exterior:cladding:east', 'cladding'], ['F1:exterior:foundation:east', 'foundation'],
    ['F1:exterior:entry_panel:south', 'wood'], ['F1:exterior:downpipe:east', 'drain'],
    ['F1:D01:canopy', 'canopy'], ['F1:D01:porch', 'porch'], ['F1:D01:handle', 'handle'],
    ['F1:W01:sill', 'sill'], ['roof:standing_seam:west_01', 'seam'],
    ['roof:ridge_cap', 'ridge'], ['roof:fascia:south_west', 'fascia'],
    ['roof:soffit:west', 'soffit'], ['roof:gutter:west', 'gutter'],
  ];
  for (const locale of locales) {
    for (const [name, key] of checks) {
      const label = cadComponentLabel(locale, name, 'house');
      assert.equal(typeof label, 'string', `${locale}: ${name} is localized`);
      assert.match(label, terms[locale][key], `${locale}: ${name} describes its physical component`);
    }
    assert.notEqual(cadComponentLabel(locale, 'roof:standing_seam:west_01'),
      cadComponentLabel(locale, 'roof:standing_seam:east_01'), 'east/west seams remain distinguishable');
    assert.notEqual(cadComponentLabel(locale, 'roof:standing_seam:west_01'),
      cadComponentLabel(locale, 'roof:standing_seam:west_02'), 'seam number is retained');
  }
});

test('furniture labels identify room, object, and model-specific bedroom name', () => {
  const terms = {
    zh: { bed: /床/, mattress: /床垫/, television: /电视/, screen: /屏幕/, ldk: /(?:LDK|客厅.*餐厅.*厨房)/ },
    ja: { bed: /ベッド/, mattress: /マットレス/, television: /テレビ/, screen: /画面/, ldk: /LDK/ },
    en: { bed: /bed/i, mattress: /mattress/i, television: /(?:television|TV)/i, screen: /screen/i, ldk: /Living.*dining.*kitchen/i },
  };
  for (const locale of locales) {
    const bedroom2 = cadComponentLabel(locale, 'F2:furniture:bed2:bed:mattress', 'house');
    assert.ok(bedroom2.includes(messages[locale].rooms.bed2), `${locale}: bedroom 2 room name`);
    assert.match(bedroom2, terms[locale].bed);
    assert.match(bedroom2, terms[locale].mattress);
    const tv = cadComponentLabel(locale, 'F1:furniture:ldk:television:tv_screen', 'apartment');
    assert.match(tv, terms[locale].ldk, `${locale}: LDK room name`);
    assert.match(tv, terms[locale].television);
    assert.match(tv, terms[locale].screen);
    const houseMaster = cadComponentLabel(locale, 'F2:furniture:master:bed:headboard', 'house');
    const apartmentMaster = cadComponentLabel(locale, 'F1:furniture:master:bed:headboard', 'apartment');
    assert.ok(houseMaster.includes(modelCopy(messages[locale], locale, 'house').rooms.master), `${locale}: house main bedroom`);
    assert.ok(apartmentMaster.includes(modelCopy(messages[locale], locale, 'apartment').rooms.master), `${locale}: apartment bedroom 1`);
    assert.notEqual(houseMaster, apartmentMaster);
  }
});

test('fixture labels describe the picked component precisely rather than just its assembly', () => {
  const terms = {
    zh: { sink: /水槽/, rim: /(?:边缘|槽沿)/, body: /机身/, glass: /玻璃/, seal: /密封/, drain: /排水/, mirror: /镜/, frame: /框/ },
    ja: { sink: /シンク/, rim: /(?:縁|リム)/, body: /本体/, glass: /ガラス/, seal: /(?:パッキン|シール)/, drain: /排水/, mirror: /鏡|ミラー/, frame: /枠|フレーム/ },
    en: { sink: /sink/i, rim: /rim/i, body: /body/i, glass: /glass/i, seal: /seal/i, drain: /drain/i, mirror: /mirror/i, frame: /frame/i },
  };
  for (const locale of locales) {
    const checks = [
      ['F1:fixture_02_kitchen:sink_rim_steel', ['sink', 'rim']],
      ['F1:fixture_05_washer:body_white', ['body']],
      ['F1:fixture_05_washer:washer_glass', ['glass']],
      ['F1:fixture_05_washer:porthole_seal_rubber', ['seal']],
      ['F1:fixture_03_bath:drain_chrome', ['drain']],
      ['F1:fixture_04_vanity:mirror_frame_chrome', ['mirror', 'frame']],
    ];
    for (const [name, keys] of checks) {
      const label = cadComponentLabel(locale, name);
      for (const key of keys) assert.match(label, terms[locale][key], `${locale}: ${name}`);
      assert.notEqual(label, cadComponentLabel(locale, name.replace(/:[^:]+$/, '')), 'component is not an assembly label');
    }
  }
});

test('unknown CAD names and category/group selections leave the translated category fallback in charge', () => {
  for (const locale of locales) {
    for (const name of ['', 'unknown:part', 'roof:diagonal_plane', 'F1:W01:unknown',
      'F1:fixture_02_kitchen:unknown', 'F1:furniture:ldk:sofa:unknown',
      'F1', 'F2', 'roof', 'stairs', 'balcony', 'ceiling', 'F1:doors', 'F2:windows',
      'F1:floor_slab', 'F2:floor_slab', 'F1:fixtures', 'F1:furniture',
      'attic', 'attic_access', 'attic:floor_slab', 'attic:guardrails', 'attic:storage:west_shelf',
      'attic:storage:west_shelf:lid', 'attic:storage:southwest_box:middle',
      'attic_access:tread_00', 'attic_access:tread_11', 'attic_access:tread_1']) {
      assert.equal(cadComponentLabel(locale, name), null, `${locale}: ${name}`);
    }
  }
});


test('R06 structural proposal details retain member references in all three languages', () => {
  const samples = [
    'structure:F1:column_C01', 'structure:F2:beam_B01', 'structure:F1:sill_S01',
    'structure:attic:joist_J01_south', 'structure:attic:joist_J01_north',
    'structure:attic:trimmer_west', 'structure:attic:trimmer_east',
    'structure:attic:header_south', 'structure:attic:header_north',
    'structure:roof:ridge_beam', 'structure:roof:purlin_west', 'structure:roof:purlin_east',
    'structure:roof:rafter_west_R01', 'structure:roof:rafter_east_R01',
    'structure:roof:post_ridge_P01', 'structure:F1:bearing_wall_BW01',
    'attic:lining:flat_ceiling',
  ];
  for (const locale of locales) {
    const labels = samples.map(name => cadComponentLabel(locale, name));
    assert.ok(labels.every(label => label?.trim()), `${locale}: every R06 detail is translated`);
    assert.equal(new Set(labels).size, labels.length, `${locale}: direction and member type remain distinguishable`);
    assert.ok(labels.every(label => !label.includes('_') && !label.includes('structure:')));
  }
});
