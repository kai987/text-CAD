import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const run = promisify(execFile);
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
export const analysisReportPaths = ['output/analysis/current/house_review.json', 'output/analysis/current/house_review.md'];
const sourcePaths = ['output/review/design_manifest.json', 'output/review/engineering_inputs_R06.json',
  'output/review/house_3d_assumptions_R01.json'];

// Render with the exact current pure formatter, without importing the analysis
// module, its geometry dependencies or its CAD loading/generation entry point.
const renderMarkdown = `
import ast, json, sys
from pathlib import Path
source_path, report_path = map(Path, sys.argv[1:])
tree = ast.parse(source_path.read_text(encoding='utf-8'))
matches = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'markdown']
if len(matches) != 1:
    raise ValueError('Expected exactly one markdown formatter')
formatter = matches[0]
if formatter.decorator_list:
    raise ValueError('Decorated formatters are unsupported')
namespace = {'json': json}
exec(compile(ast.Module(body=[formatter], type_ignores=[]), str(source_path), 'exec'), namespace)
report = json.loads(report_path.read_text(encoding='utf-8'))
sys.stdout.buffer.write(namespace['markdown'](report).encode('utf-8'))
`;

export async function validateAnalysisReport(root) {
  const analysisPath = resolve(root, 'analysis/house_review.py');
  const reportPath = resolve(root, analysisReportPaths[0]);
  const [analysis, reportBytes, markdown, ...sources] = await Promise.all([
    readFile(analysisPath), readFile(reportPath), readFile(resolve(root, analysisReportPaths[1])),
    ...sourcePaths.map(path => readFile(resolve(root, path))),
  ]);
  const report = JSON.parse(reportBytes);
  if (report.schema_version !== 1 || report.status !== 'concept_review_only') throw new Error('Invalid concept analysis report.');
  if (report.structural_capacity_result !== null || report.statutory_compliance_result !== null) {
    throw new Error('Concept analysis must not claim structural or statutory approval.');
  }
  if (report.analysis_code_sha256 !== sha(analysis)) throw new Error('Stale analysis program binding; regenerate the space report.');
  const binding = report.source_binding;
  if (!binding || JSON.stringify(Object.keys(binding.source_sha256 ?? {}).sort()) !== JSON.stringify([...sourcePaths].sort())) {
    throw new Error('Invalid analysis source set.');
  }
  const data = sources.map(bytes => JSON.parse(bytes));
  const revisions = [data[0].revision, data[1].revision, data[2].attic?.revision];
  if (typeof binding.revision !== 'string' || revisions.some(revision => revision !== binding.revision)) {
    throw new Error('Mixed analysis source revisions; regenerate the space report.');
  }
  for (const [index, path] of sourcePaths.entries()) {
    if (binding.source_sha256[path] !== sha(sources[index])) throw new Error(`Stale analysis source binding: ${path}; regenerate the space report.`);
  }
  let rendered;
  try {
    const result = await run(process.env.CAD_ANALYSIS_PYTHON ?? 'python3', ['-c', renderMarkdown, analysisPath, reportPath],
      { encoding: 'buffer', maxBuffer: 4 * 1024 * 1024, timeout: 15_000 });
    rendered = result.stdout;
  } catch (error) {
    throw new Error('Cannot render the current analysis report with Python 3; regenerate or repair the formatter.', { cause: error });
  }
  if (!markdown.equals(rendered)) throw new Error('Analysis Markdown differs from its JSON report; regenerate both outputs together.');
  return { report, paths: analysisReportPaths };
}
