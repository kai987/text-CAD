import { readFile, readdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve, relative, sep } from 'node:path';

async function pythonFiles(directory, root) {
  const entries = await readdir(directory, { withFileTypes: true });
  return (await Promise.all(entries.filter(entry => entry.name !== '__pycache__').map(async entry => {
    const path = resolve(directory, entry.name);
    return entry.isDirectory() ? pythonFiles(path, root) : entry.name.endsWith('.py') ? [relative(root, path).split(sep).join('/')] : [];
  }))).flat();
}
export async function validateCadRelease(root) {
  const release = JSON.parse(await readFile(resolve(root, 'output/review/cad_release.json'), 'utf8'));
  if (release.schema_version !== 1 || !release.validation_commands?.length) throw new Error('Missing CAD validation provenance.');
  const sources = [...await pythonFiles(resolve(root, 'src'), root), ...await pythonFiles(resolve(root, 'checks'), root),
    'requirements.txt', 'web/scripts/generate-plan-svg.py'].sort();
  if (JSON.stringify(sources) !== JSON.stringify(Object.keys(release.sources).sort())) throw new Error('CAD source set changed; regenerate CAD before publishing.');
  for (const section of ['sources', 'artifacts']) {
    for (const [path, expected] of Object.entries(release[section])) {
      const full = resolve(root, path);
      if (!full.startsWith(resolve(root) + sep)) throw new Error('Invalid CAD release path.');
      const hash = createHash('sha256').update(await readFile(full)).digest('hex');
      if (hash !== expected) throw new Error(`Stale CAD ${section}: ${path}; run .venv/bin/python src/cad_pipeline.py --regenerate.`);
    }
  }
  return release;
}
