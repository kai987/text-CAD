import house from './house-data.json';
export { house };
export const repository = 'https://github.com/kai987/text-CAD';
export const asset = (path: string) => `${import.meta.env.BASE_URL}artifacts/${path}`;
export const downloadFiles = [
  { title: 'GLB 三维模型', detail: '保留楼层与部件名称，可用于 Blender、Three.js。', path: 'GLB/house_3d.glb', type: 'GLB' },
  { title: 'STEP 精确实体', detail: '毫米制实体，可在 CAD 软件中继续编辑。', path: 'STEP/house_3d.step', type: 'STEP' },
  { title: '一层平面', detail: '房间名与原生尺寸可编辑，包含 A3 纸空间。', path: 'DXF/001D0PL2-1FPLAN.DXF', type: 'DXF' },
  { title: '二层平面', detail: '房间名与原生尺寸可编辑，包含 A3 纸空间。', path: 'DXF/002D0PL2-2FPLAN.DXF', type: 'DXF' },
  { title: '两层 A3 图纸', detail: '1:50、A3 横向；打印选择实际尺寸。', path: 'output/pdf/house_floor_plans_R02_JP.pdf', type: 'PDF' },
  { title: '方案参数与假设', detail: '记录演示尺寸、房间净面积和待定项。', path: 'output/review/design_manifest.json', type: 'JSON' },
];
