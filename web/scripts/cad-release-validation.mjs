import { readFile, readdir, stat } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve, relative, sep, parse } from 'node:path';

async function pythonFiles(directory, root) {
  const entries = await readdir(directory, { withFileTypes: true });
  return (await Promise.all(entries.filter(entry => entry.name !== '__pycache__').map(async entry => {
    const path = resolve(directory, entry.name);
    return entry.isDirectory() ? pythonFiles(path, root) : entry.name.endsWith('.py') ? [relative(root, path).split(sep).join('/')] : [];
  }))).flat();
}
// Keep this catalog aligned with src/cad_release.py::artifact_paths. A newly
// added export must be validated and registered before a web build can ship it.
async function artifactFiles(root) {
  const directories = ['DXF', 'STEP', 'GLB', 'output/pdf', 'output/vector',
    'output/review', 'output/review/cases'];
  const paths = (await Promise.all(directories.map(async directory => {
    let entries;
    try { entries = await readdir(resolve(root, directory), { withFileTypes: true }); }
    catch (error) { if (error.code === 'ENOENT') return []; throw error; }
    return entries.filter(entry => entry.isFile()
      && (!directory.startsWith('output/review') || entry.name.endsWith('.json'))
      && !parse(entry.name).name.includes('validation'))
      .map(entry => `${directory}/${entry.name}`);
  }))).flat().filter(path => path !== 'output/review/cad_release.json');
  const metadata = 'web/src/plan-preview-metadata.json';
  try { if ((await stat(resolve(root, metadata))).isFile()) paths.push(metadata); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  return paths.sort();
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
  if (JSON.stringify(await artifactFiles(root)) !== JSON.stringify(Object.keys(release.artifacts).sort())) {
    throw new Error('CAD artifact set changed; regenerate CAD before publishing.');
  }
  return release;
}
