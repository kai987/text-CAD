import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { format, locales, messages } from '../src/localization.ts';
import { coordinationSummary, structuralSystems } from '../src/structural-design.ts';

const readJson = async path => JSON.parse(await readFile(new URL(path, import.meta.url), 'utf8'));

test('download copy follows each catalog model revision instead of a hard-coded house revision', async () => {
  const plan = await readJson('../../output/review/design_manifest.json');
  const model = await readJson('../../output/review/house_3d_assumptions_R01.json');
  const apartment = await readJson('../../output/review/apartment_2ldk_manifest.json');
  const revisionPairs = [
    { drawing: plan.drawing_revision, model: model.revision },
    { drawing: apartment.drawingRevision, model: apartment.modelRevision },
    { drawing: 'R99', model: 'R99-3D' },
  ];
  for (const locale of locales) for (const revisions of revisionPairs) {
    const header = format(messages[locale].downloads.revision, revisions);
    assert.ok(header.includes(revisions.drawing));
    assert.ok(header.includes(revisions.model));
    const detail = format(messages[locale].downloads.files.engineering.detail, revisions);
    assert.ok(detail.includes(revisions.drawing));
    assert.ok(!detail.includes('{drawing}'));
    assert.ok(!detail.includes('R20'));
  }
});

test('all structural systems retain distinct coordination limits without a stale current timber revision', async () => {
  const metadata = await readJson('../../output/review/structural_variants_R07.json');
  for (const locale of locales) {
    const timber = coordinationSummary(metadata.variants.W, locale);
    assert.ok(timber?.trim());
    assert.ok(!/R\d+/.test(timber), 'the old overlay revision must not describe the current house');
    for (const system of ['S', 'RC']) {
      assert.equal(coordinationSummary(metadata.variants[system], locale), metadata.variants[system].coordination.summary[locale]);
    }
    assert.equal(new Set(structuralSystems.map(system => coordinationSummary(metadata.variants[system], locale))).size, 3);
    assert.equal(coordinationSummary(undefined, locale), undefined);
  }
});
