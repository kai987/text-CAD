import test from 'node:test';
import assert from 'node:assert/strict';
import { gzipSync } from 'node:zlib';
import { readFile } from 'node:fs/promises';
import { decodedStep } from '../src/step-download.ts';

test('compressed STEP restores every byte including geometry numbers and names', async () => {
  const source = await readFile(new URL('../../STEP/house_3d.step', import.meta.url));
  const result = await decodedStep('/house.step.gz', async () => new Response(gzipSync(source)));
  assert.deepEqual(Buffer.from(await result.arrayBuffer()), source);
});
test('HTTP and damaged gzip errors cannot become a successful CAD download', async () => {
  await assert.rejects(decodedStep('/missing', async () => new Response('', {status:404})), /404/);
  await assert.rejects(decodedStep('/corrupt', async () => new Response('not gzip')));
});

test('fetch may already decode gzip Content-Encoding without requiring a second decompression', async () => {
  const source = await readFile(new URL('../../STEP/house_3d.step', import.meta.url));
  const result = await decodedStep('/house.step.gz', async () => new Response(source, {
    headers: {'Content-Encoding': 'gzip'},
  }));
  assert.deepEqual(Buffer.from(await result.arrayBuffer()), source);
});
test('an HTTP 200 error page, including a gzip error page, cannot be saved as CAD', async () => {
  for (const body of ['<html>Unavailable</html>', gzipSync('<html>Unavailable</html>')]) {
    await assert.rejects(decodedStep('/wrong', async () => new Response(body)), /not a STEP document/);
  }
});
