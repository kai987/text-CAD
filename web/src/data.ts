import house from './house-data.json';
export { house };
export const repository = 'https://github.com/kai987/text-CAD';
export const asset = (path: string) => `${import.meta.env.BASE_URL}artifacts/${path}`;
export const downloadFiles = [
  { id: 'glb', path: 'GLB/house_3d.glb', type: 'GLB' },
  { id: 'step', path: 'STEP/house_3d.step', type: 'STEP' },
  { id: 'first', path: 'DXF/001D0PL2-1FPLAN.DXF', type: 'DXF' },
  { id: 'second', path: 'DXF/002D0PL2-2FPLAN.DXF', type: 'DXF' },
  { id: 'attic', path: 'DXF/house_attic_plan.dxf', type: 'DXF' },
  { id: 'atticPdf', path: 'output/pdf/house_attic_plan_R06_JP.pdf', type: 'PDF' },
  { id: 'structure', path: 'DXF/house_structural_scheme.dxf', type: 'DXF' },
  { id: 'structurePdf', path: 'output/pdf/house_structural_scheme_R06_JP.pdf', type: 'PDF' },
  { id: 'site', path: 'DXF/house_site_plan.dxf', type: 'DXF' },
  { id: 'sitePdf', path: 'output/pdf/house_site_plan_R05_JP.pdf', type: 'PDF' },
  { id: 'pdf', path: 'output/pdf/house_floor_plans_R09_JP.pdf', type: 'PDF' },
  { id: 'engineeringSource', path: 'src/lib/engineering_inputs.py', type: 'PY' },
  { id: 'engineering', path: 'output/review/engineering_inputs_R06.json', type: 'JSON' },
  { id: 'manifest', path: 'output/review/design_manifest.json', type: 'JSON' },
] as const;
