import { bridgeRevision } from './bridge-copy.ts';
import { bridgeSummaryPath, parseBridgeSummaryData } from '../scripts/bridge-summary-contract.mjs';
import type { BridgeMetadata } from '../scripts/bridge-summary-contract.mjs';

export { bridgeSummaryPath };
export type { BridgeMetadata };

export function parseBridgeSummary(value: unknown): BridgeMetadata {
  return parseBridgeSummaryData(value, bridgeRevision);
}
