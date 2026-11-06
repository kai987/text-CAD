// This module is shared by artifact preparation and the browser. Keep it free
// of Node APIs so schema checks stay identical before publication and at runtime.
export const bridgeSummaryPath = 'output/review/seto_ohashi_summary.json';
export const bridgeManifestPath = 'output/review/seto_ohashi_manifest.json';
export const bridgeSummaryDimensions = ['north_length_mm', 'south_length_mm', 'north_main_span_mm', 'south_main_span_mm'];
export const bridgeSummaryByteLimit = 64 * 1024;
const locales = ['zh', 'ja', 'en'];
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const exact = (value, keys) => object(value)
  && JSON.stringify(Object.keys(value).sort()) === JSON.stringify([...keys].sort());
const nonempty = value => typeof value === 'string' && value.trim().length > 0;

export function parseBridgeSummaryData(value, revision) {
  if (!/^BRIDGE-R\d{2,}$/.test(revision ?? '')
      || !exact(value, ['schema_version', 'model_id', 'revision', 'units', 'source_manifest_sha256', 'parameters', 'references', 'assumptions'])
      || value.schema_version !== 1 || value.model_id !== 'seto-ohashi' || value.revision !== revision || value.units !== 'mm'
      || !/^[a-f0-9]{64}$/.test(value.source_manifest_sha256 ?? '')) {
    throw new Error('Bridge summary identity, schema or source binding does not match.');
  }
  if (!exact(value.parameters, bridgeSummaryDimensions)
      || bridgeSummaryDimensions.some(key => !Number.isFinite(value.parameters[key]) || value.parameters[key] <= 0)) {
    throw new Error('Bridge summary dimensions must be positive millimetre controls.');
  }
  if (!Array.isArray(value.references) || !value.references.length || value.references.some(item => {
    if (!exact(item, ['title', 'url']) || !nonempty(item.title) || !nonempty(item.url)) return true;
    try { return new URL(item.url).protocol !== 'https:'; } catch { return true; }
  })) throw new Error('Bridge summary references must retain valid cited HTTPS sources.');
  if (!Array.isArray(value.assumptions) || value.assumptions.length < 3
      || value.assumptions.some(item => !exact(item, locales) || locales.some(locale => !nonempty(item[locale])))) {
    throw new Error('Bridge summary assumptions must retain every language.');
  }
  return {
    schema_version: 1, model_id: 'seto-ohashi', revision: value.revision, units: 'mm',
    source_manifest_sha256: value.source_manifest_sha256,
    parameters: Object.fromEntries(bridgeSummaryDimensions.map(key => [key, value.parameters[key]])),
    references: value.references.map(({ title, url }) => ({ title, url })),
    assumptions: value.assumptions.map(item => Object.fromEntries(locales.map(locale => [locale, item[locale]]))),
  };
}
