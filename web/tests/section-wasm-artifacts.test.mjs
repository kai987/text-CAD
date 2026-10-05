import test from 'node:test';
import assert from 'node:assert/strict';
import { verifySectionWasmArtifacts } from '../scripts/section-wasm-artifacts.mjs';

test('committed WASM and bindings match their Rust sources and are valid WebAssembly', async () => {
  const result = await verifySectionWasmArtifacts();
  assert.ok(result.wasmBytes > 8);
});
