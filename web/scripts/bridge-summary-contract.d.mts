export interface BridgeMetadata {
  schema_version: 1;
  model_id: 'seto-ohashi';
  revision: string;
  units: 'mm';
  source_manifest_sha256: string;
  parameters: Record<string, number>;
  references: { title: string; url: string }[];
  assumptions: Record<'zh' | 'ja' | 'en', string>[];
}
export const bridgeSummaryPath: string;
export const bridgeManifestPath: string;
export const bridgeSummaryDimensions: string[];
export const bridgeSummaryByteLimit: number;
export function parseBridgeSummaryData(value: unknown, revision: string): BridgeMetadata;
