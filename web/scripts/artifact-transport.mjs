import { readFile, stat } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
import { gzipSync, gunzipSync } from 'node:zlib';

export const STATIC_FILE_LIMIT = 25 * 1024 * 1024;
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const metadata = bytes => ({ bytes: bytes.length, sha256: sha(bytes) });
const valid = entry => entry && Number.isSafeInteger(entry.bytes) && entry.bytes > 0
  && typeof entry.sha256 === 'string' && /^[0-9a-f]{64}$/.test(entry.sha256);

/** Logical original names remain in the catalog even when only gzip is hosted. */
export function artifactTransport(source, bytes, limit = STATIC_FILE_LIMIT) {
  if (!bytes.length) throw new Error(`Empty artifact: ${source}`);
  if (bytes.length > limit && !/\.(?:step|glb|dxf)$/i.test(source)) {
    throw new Error(`Oversized artifact has no gzip-capable reader: ${source}`);
  }
  const gzipOnly = bytes.length > limit || source === 'STEP/house_3d.step'
    || /^STEP\/tokyo_(tower|skytree)\.step$/.test(source);
  const original = metadata(bytes);
  if (!gzipOnly && !source.endsWith('.glb')) return { files: [[source, bytes]], records: { [source]: original } };
  const compressed = gzipSync(bytes, { level: 9 });
  if (!gunzipSync(compressed).equals(bytes)) throw new Error(`Artifact transport round-trip failed: ${source}`);
  const encodedName = `${source}.gz`;
  const encoded = { ...metadata(compressed), decodedBytes: original.bytes, decodedSha256: original.sha256 };
  const files = [];
  const records = { [source]: { ...original, ...(gzipOnly ? { transport: 'gzip' } : {}) } };
  if (!gzipOnly) files.push([source, bytes]);
  if (compressed.length > limit) {
    if (source.endsWith('.glb')) throw new Error(`Viewer gzip exceeds the static file limit: ${source}`);
    const half = Math.ceil(compressed.length / 2);
    if (half > limit) throw new Error(`Artifact exceeds the two-part static transport limit: ${source}`);
    const parts = [compressed.subarray(0, half), compressed.subarray(half)].map((payload, index) => {
      const path = `${encodedName}.part-${String(index + 1).padStart(3, '0')}`;
      const entry = metadata(payload); files.push([path, payload]); records[path] = entry;
      return { path, ...entry };
    });
    records[encodedName] = { ...encoded, transport: 'chunks', parts };
  } else {
    files.push([encodedName, compressed]); records[encodedName] = encoded;
  }
  return {
    files, records,
  };
}

/** Verify every physical payload and each logical original-to-gzip binding. */
export async function verifyArtifactTransports(directory, manifest, limit = STATIC_FILE_LIMIT) {
  const checked = new Set();
  async function payload(name) {
    const entry = manifest[name];
    if (!valid(entry) || (entry.transport !== undefined && entry.transport !== 'chunks')) throw new Error(`Invalid payload record: ${name}`);
    let bytes;
    if (entry.transport === 'chunks') {
      if (!name.endsWith('.gz') || !Array.isArray(entry.parts) || entry.parts.length !== 2
        || !valid({ bytes: entry.decodedBytes, sha256: entry.decodedSha256 })) throw new Error(`Invalid chunk transport: ${name}`);
      const buffers = [];
      for (const [index, part] of entry.parts.entries()) {
        const expectedName = `${name}.part-${String(index + 1).padStart(3, '0')}`;
        const actual = manifest[expectedName];
        if (!valid(part) || part.path !== expectedName || !valid(actual) || actual.transport !== undefined
          || actual.bytes !== part.bytes || actual.sha256 !== part.sha256 || actual.decodedBytes !== undefined
          || actual.decodedSha256 !== undefined) throw new Error(`Missing or inconsistent chunk binding: ${name}`);
        buffers.push(await payload(expectedName));
      }
      bytes = Buffer.concat(buffers);
      if (await stat(resolve(directory, name)).then(() => true, error => {
        if (error.code === 'ENOENT') return false; throw error;
      })) throw new Error(`Chunked artifact unexpectedly has a physical copy: ${name}`);
    } else {
      bytes = await readFile(resolve(directory, name));
      if (bytes.length > limit) throw new Error(`Published asset exceeds the static file limit: ${name}`);
    }
    if (bytes.length !== entry.bytes || sha(bytes) !== entry.sha256) throw new Error(`Published asset differs: ${name}`);
    if (entry.decodedBytes !== undefined || entry.decodedSha256 !== undefined) {
      if (!name.endsWith('.gz') || !Number.isSafeInteger(entry.decodedBytes) || entry.decodedBytes <= 0
        || typeof entry.decodedSha256 !== 'string' || !/^[0-9a-f]{64}$/.test(entry.decodedSha256)) {
        throw new Error(`Invalid decoded artifact record: ${name}`);
      }
      const decoded = gunzipSync(bytes);
      if (decoded.length !== entry.decodedBytes || sha(decoded) !== entry.decodedSha256) {
        throw new Error(`Restored artifact differs: ${name}`);
      }
      const original = manifest[name.slice(0, -3)];
      if (!valid(original) || original.bytes !== decoded.length || original.sha256 !== entry.decodedSha256) {
        throw new Error(`Logical artifact binding differs: ${name}`);
      }
    }
    checked.add(name);
    return bytes;
  }
  for (const [name, entry] of Object.entries(manifest)) {
    if (!valid(entry)) throw new Error(`Invalid artifact record: ${name}`);
    if (checked.has(name)) continue;
    if (entry.transport === undefined || entry.transport === 'chunks') { await payload(name); continue; }
    if (entry.transport !== 'gzip') throw new Error(`Unknown artifact transport: ${name}`);
    const encoded = manifest[`${name}.gz`];
    if (!valid(encoded) || (encoded.transport !== undefined && encoded.transport !== 'chunks') || encoded.decodedBytes !== entry.bytes
      || encoded.decodedSha256 !== entry.sha256) throw new Error(`Missing or inconsistent gzip binding: ${name}`);
    if (!checked.has(`${name}.gz`)) await payload(`${name}.gz`);
    try { await stat(resolve(directory, name)); }
    catch (error) { if (error.code === 'ENOENT') continue; throw error; }
    throw new Error(`Gzip-only artifact unexpectedly has a raw copy: ${name}`);
  }
  return [...checked].filter(name => manifest[name].transport === undefined).length;
}
