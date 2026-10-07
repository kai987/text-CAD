import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { resolve, dirname } from 'node:path';
import { createHash } from 'node:crypto';
import { validateAnalysisReport } from '../scripts/analysis-report-validation.mjs';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const sources = {
  'output/review/design_manifest.json': { revision: 'R22', parameters: { width: 8190 } },
  'output/review/engineering_inputs_R06.json': { revision: 'R22', site: null },
  'output/review/house_3d_assumptions_R01.json': { attic: { revision: 'R22' }, parameters: { depth: 7280 } },
};
const program = `
raise RuntimeError('The analysis module must not be imported')
import nonexistent_geometry_dependency
def markdown(report):
    return '# ' + report['source_binding']['revision'] + ' 概念分析\\n' + str(report['space']['area']) + '\\n整体承重和法规未判定。\\n'
`;

async function fixture(t) {
  const root = await mkdtemp(resolve(tmpdir(), 'analysis-report-test-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const save = async (path, text) => {
    const full = resolve(root, path); await mkdir(dirname(full), { recursive: true }); await writeFile(full, text);
  };
  await save('analysis/house_review.py', program);
  const binding = {};
  for (const [path, json] of Object.entries(sources)) {
    const bytes = JSON.stringify(json); await save(path, bytes); binding[path] = sha(bytes);
  }
  const report = { schema_version: 1, status: 'concept_review_only', analysis_code_sha256: sha(program),
    source_binding: { revision: 'R22', source_sha256: binding }, space: { area: 59.6232 },
    structural_capacity_result: null, statutory_compliance_result: null };
  const saveReport = () => save('output/analysis/current/house_review.json', JSON.stringify(report));
  await saveReport();
  const markdown = '# R22 概念分析\n59.6232\n整体承重和法规未判定。\n';
  await save('output/analysis/current/house_review.md', markdown);
  return { root, save, report, saveReport, markdown };
}

test('analysis publication checks exact pure formatter without importing the CAD/geometry module', async t => {
  const { root, report } = await fixture(t);
  const checked = await validateAnalysisReport(root);
  assert.deepEqual(checked.report, report);
  assert.deepEqual(checked.paths, ['output/analysis/current/house_review.json', 'output/analysis/current/house_review.md']);
});

test('changed analysis source and every changed source JSON reject stale reports', async t => {
  const { root, save } = await fixture(t);
  await save('analysis/house_review.py', program + '# changed calculations\n');
  await assert.rejects(validateAnalysisReport(root), /Stale analysis program binding/);
  await save('analysis/house_review.py', program);
  for (const [path, json] of Object.entries(sources)) {
    const previous = await readFile(resolve(root, path));
    await save(path, JSON.stringify({ ...json, changed_geometry_or_input: true }));
    await assert.rejects(validateAnalysisReport(root), /Stale analysis source binding/);
    await save(path, previous);
  }
  await validateAnalysisReport(root);
});

test('mixed revisions or altered source catalogs cannot be blessed by updating hashes', async t => {
  const { root, save, report, saveReport } = await fixture(t);
  const path = 'output/review/design_manifest.json';
  const changed = JSON.stringify({ ...sources[path], revision: 'R23' });
  await save(path, changed); report.source_binding.source_sha256[path] = sha(changed); await saveReport();
  await assert.rejects(validateAnalysisReport(root), /Mixed analysis source revisions/);
  delete report.source_binding.source_sha256[path]; await saveReport();
  await assert.rejects(validateAnalysisReport(root), /Invalid analysis source set/);
});

test('Markdown drift and JSON content drift reject an unmatched report pair', async t => {
  const { root, save, report, saveReport, markdown } = await fixture(t);
  await save('output/analysis/current/house_review.md', markdown + 'Altered conclusion.\n');
  await assert.rejects(validateAnalysisReport(root), /Markdown differs from its JSON report/);
  await save('output/analysis/current/house_review.md', markdown);
  report.space.area = 100; await saveReport();
  await assert.rejects(validateAnalysisReport(root), /Markdown differs from its JSON report/);
});

test('concept publication rejects structural or statutory approval claims', async t => {
  const { root, report, saveReport } = await fixture(t);
  for (const field of ['structural_capacity_result', 'statutory_compliance_result']) {
    report[field] = true; await saveReport();
    await assert.rejects(validateAnalysisReport(root), /must not claim structural or statutory approval/);
    report[field] = null;
  }
});
