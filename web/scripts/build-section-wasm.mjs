import { execFileSync } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { crateDirectory, projectRoot, wasmDirectory, wasmBindgenVersion, sourceHashes, outputHashes, verifySectionWasmArtifacts } from './section-wasm-artifacts.mjs';

const cliVersion = execFileSync('wasm-bindgen', ['--version'], { encoding: 'utf8' }).trim();
if (cliVersion !== `wasm-bindgen ${wasmBindgenVersion}`) throw new Error(`Expected wasm-bindgen-cli ${wasmBindgenVersion}; received ${cliVersion}.`);
const env = {
  ...process.env,
  CARGO_TARGET_DIR: resolve(crateDirectory, 'target'),
  RUSTFLAGS: `${process.env.RUSTFLAGS ?? ''} --remap-path-prefix=${projectRoot}=.`.trim(),
};
execFileSync('cargo', ['test', '--locked'], { cwd: crateDirectory, env, stdio: 'inherit' });
execFileSync('cargo', ['build', '--locked', '--release', '--target', 'wasm32-unknown-unknown'], { cwd: crateDirectory, env, stdio: 'inherit' });
await mkdir(wasmDirectory, { recursive: true });
execFileSync('wasm-bindgen', [resolve(env.CARGO_TARGET_DIR, 'wasm32-unknown-unknown/release/text_cad_section_caps.wasm'),
  '--target', 'web', '--out-dir', wasmDirectory, '--out-name', 'section_caps'], { cwd: crateDirectory, env, stdio: 'inherit' });
const manifest = {
  version: 1,
  rustc: execFileSync('rustc', ['--version'], { cwd: crateDirectory, encoding: 'utf8' }).trim(),
  target: 'wasm32-unknown-unknown',
  wasmBindgenVersion,
  sources: await sourceHashes(),
  outputs: await outputHashes(),
};
await writeFile(resolve(wasmDirectory, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
const result = await verifySectionWasmArtifacts();
console.log(`Prepared and verified ${result.wasmBytes} bytes of section-cap WASM.`);
