import { createHash } from 'node:crypto';
import { readFile, readdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve, relative } from 'node:path';

export const projectRoot = fileURLToPath(new URL('../../', import.meta.url));
export const crateDirectory = resolve(projectRoot, 'rust/section-caps');
export const wasmDirectory = resolve(projectRoot, 'web/src/wasm');
export const wasmBindgenVersion = '0.2.114';
export const wasmOutputs = ['section_caps.js', 'section_caps.d.ts', 'section_caps_bg.wasm', 'section_caps_bg.wasm.d.ts'];
const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');

async function rustFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  return (await Promise.all(entries.map(entry => entry.isDirectory() ? rustFiles(resolve(directory, entry.name)) :
    entry.name.endsWith('.rs') ? [resolve(directory, entry.name)] : []))).flat();
}

export async function sourceHashes() {
  const paths = [resolve(crateDirectory, 'Cargo.toml'), resolve(crateDirectory, 'Cargo.lock'),
    resolve(crateDirectory, 'rust-toolchain.toml'), ...await rustFiles(resolve(crateDirectory, 'src'))].sort();
  return Object.fromEntries(await Promise.all(paths.map(async path => [relative(projectRoot, path).replaceAll('\\', '/'), sha256(await readFile(path))])));
}

export async function outputHashes() {
  return Object.fromEntries(await Promise.all(wasmOutputs.map(async name => [name, sha256(await readFile(resolve(wasmDirectory, name)))])));
}

/** Ordinary npm builds use committed WASM, but reject stale Rust or modified output. */
export async function verifySectionWasmArtifacts(distDirectory) {
  const manifest = JSON.parse(await readFile(resolve(wasmDirectory, 'manifest.json'), 'utf8'));
  if (manifest.version !== 1 || manifest.wasmBindgenVersion !== wasmBindgenVersion ||
      JSON.stringify(manifest.sources) !== JSON.stringify(await sourceHashes()) ||
      JSON.stringify(manifest.outputs) !== JSON.stringify(await outputHashes())) {
    throw new Error('Rust/WASM artifacts are stale. Run npm run build:wasm and commit the updated source and generated files.');
  }
  const bytes = await readFile(resolve(wasmDirectory, 'section_caps_bg.wasm'));
  if (!WebAssembly.validate(bytes)) throw new Error('Invalid section-cap WebAssembly binary.');
  if (distDirectory) {
    const assets = resolve(distDirectory, 'assets');
    const names = (await readdir(assets)).filter(name => /^section_caps_bg-.*\.wasm$/.test(name));
    if (names.length !== 1 || sha256(await readFile(resolve(assets, names[0]))) !== manifest.outputs['section_caps_bg.wasm']) {
      throw new Error('Published Rust/WASM asset differs from the tested binary.');
    }
  }
  return { wasmBytes: bytes.length };
}
