import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import {
  bridgeManifestPath, bridgeSummaryPath, bridgeSummaryDimensions,
  bridgeSummaryByteLimit, parseBridgeSummaryData,
} from './bridge-summary-contract.mjs';

export { bridgeManifestPath, bridgeSummaryPath };
const sha = bytes => createHash('sha256').update(bytes).digest('hex');

/** Project an already verified downloadable manifest without copying its parts.
 * The digest binds exact native-manifest bytes, including any formatting.
 */
export function buildBridgeSummary(sourceBytes) {
  const source = JSON.parse(sourceBytes.toString('utf8'));
  if (source.schema_version !== 1 || source.model_id !== 'seto-ohashi' || source.id !== 'seto-ohashi'
      || source.units !== 'mm' || source.status !== 'reference_concept_only' || !source.parameters) {
    throw new Error('Invalid source manifest for bridge summary.');
  }
  const summary = parseBridgeSummaryData({
    schema_version: 1, model_id: source.model_id, revision: source.revision, units: source.units,
    source_manifest_sha256: sha(sourceBytes),
    parameters: Object.fromEntries(bridgeSummaryDimensions.map(key => [key, source.parameters[key]])),
    references: source.references.map(({ title, url }) => ({ title, url })),
    assumptions: source.assumptions,
  }, source.revision);
  const bytes = Buffer.from(JSON.stringify(summary) + '\n');
  if (bytes.length > bridgeSummaryByteLimit) throw new Error('Bridge summary exceeds its compact metadata budget.');
  return { summary, bytes };
}

/** Reject a stale or edited projection even when its transport hash is rebound. */
export function verifyBridgeSummary(sourceBytes, summaryBytes, records) {
  for (const [path, bytes] of [[bridgeManifestPath, sourceBytes], [bridgeSummaryPath, summaryBytes]]) {
    const entry = records?.[path];
    if (!entry || entry.transport !== undefined || entry.bytes !== bytes.length || entry.sha256 !== sha(bytes)) {
      throw new Error(`Bridge summary artifact binding differs: ${path}`);
    }
  }
  const expected = buildBridgeSummary(sourceBytes);
  const actual = parseBridgeSummaryData(JSON.parse(summaryBytes.toString('utf8')), expected.summary.revision);
  if (JSON.stringify(actual) !== JSON.stringify(expected.summary)) {
    throw new Error('Bridge summary is not the exact projection of its downloadable source.');
  }
  if (summaryBytes.length > bridgeSummaryByteLimit) throw new Error('Bridge summary exceeds its compact metadata budget.');
  return actual;
}

export async function verifyBridgeSummaryAssets(directory, records) {
  return verifyBridgeSummary(
    await readFile(resolve(directory, bridgeManifestPath)),
    await readFile(resolve(directory, bridgeSummaryPath)), records,
  );
}
