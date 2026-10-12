import type { Locale } from './localization';

export const riverGroups = {
  water: ['River:water'],
  riverbed: ['Terrain:base', 'River:bed'],
  banks: ['Banks:left', 'Banks:right'],
  paths: ['Paths:left', 'Paths:right', 'Access:stairs'],
  bridge: ['Bridge:deck', 'Bridge:beams', 'Bridge:rails', 'Bridge:abutments', 'Bridge:approaches'],
  landscape: ['Landscape:trees', 'Landscape:benches'],
  lighting: ['Lighting:fixtures'],
} as const;
export type RiverGroupId = keyof typeof riverGroups;
export type RiverView = '3d' | 'plan' | 'section' | 'files';
export const riverViews: RiverView[] = ['3d', 'plan', 'section', 'files'];
export const riverDownloadFiles = [
  { id: 'glb', path: 'GLB/river_demo.glb', type: 'GLB' },
  { id: 'step', path: 'STEP/river_demo.step', type: 'STEP' },
  { id: 'plan', path: 'DXF/river_demo_plan.dxf', type: 'DXF' },
  { id: 'section', path: 'DXF/river_demo_section.dxf', type: 'DXF' },
  { id: 'manifest', path: 'output/review/river_demo_manifest.json', type: 'JSON' },
  { id: 'source3d', path: 'src/river_3d.py', type: 'PY' },
  { id: 'source2d', path: 'src/generate_river_plans.py', type: 'PY' },
  { id: 'parameters', path: 'src/lib/river_geometry.py', type: 'PY' },
] as const;

export function initialRiverView(search: string): RiverView {
  const value = new URLSearchParams(search).get('view');
  if (riverViews.includes(value as RiverView)) return value as RiverView;
  // Existing floor-plan bookmarks may be used when switching from a residential layout.
  return value === '1f' || value === '2f' ? 'plan' : '3d';
}
export function riverUrl(current: string, view: RiverView): string {
  const url = new URL(current);
  url.search = '';
  url.searchParams.set('model', 'river');
  url.searchParams.set('view', view);
  return url.href;
}
export function residentialUrl(current: string, model: 'house' | 'apartment'): string {
  const url = new URL(current);
  url.search = '';
  url.searchParams.set('model', model);
  url.searchParams.set('view', '3d');
  return url.href;
}

export const riverCopy = {
  zh: {
    title: '日本近郊河流 · 示范段', modelName: '近郊河流示范段', modelLabel: '场景方案', description: '带护岸、人行桥、步道和植被的参数化河流示范方案。',
    nav: '河流模型与图纸', tabs: { '3d': '三维模型', plan: '河流平面', section: '横断面', files: '文件下载' },
    parts: '部件显示', showAll: '显示全部', top: '俯视', reset: '重置视角', selected: '已选部件', clear: '清除选择',
    groups: { water: '水面', riverbed: '地形与河床', banks: '护岸', paths: '步道与亲水台阶', bridge: '人行桥', landscape: '植栽与休息设施', lighting: '灯具示意' },
    loading: '正在加载河流模型…', error: '河流模型无法加载，请检查连接后重试。', retry: '重试',
    empty: '全部部件已隐藏，请选择部件或显示全部。', gesture: '拖动旋转 · 滚轮或双指缩放 · 点击选择部件',
    dimensions: '演示参数', units: '单位', length: '南北投影长度', width: '场景宽度', waterWidth: '名义水面宽', bridgeSpan: '名义桥跨',
    parameterNote: '尺寸均为演示假设；水面宽及桥跨为名义参数。',
    note: '此为虚构的日本近郊河流示范段。水位、河床、堤岸及桥梁尺寸均为演示假设，未进行防洪、流量、桥梁承载或法规核定。',
    drawingNote: '原始 CAD 图内标注使用日语，尺寸单位为毫米；平面和横断面均可下载 DXF 修改。',
    planLoading: '正在加载图纸…', planError: '图纸无法加载，请重试。', planAlt: '日本近郊河流示范段平面图（日语标注）', sectionAlt: '河流示范段横断面图（日语标注）',
    downloads: '河流 CAD 与参数化源码', download: '下载', original: '原始可编辑文件；Python 源码包含几何参数与平面生成器。',
    fileNames: { glb: '河流三维模型', step: '河流 CAD 实体', plan: '河流平面图', section: '河流横断面图', manifest: '参数与假设清单', source3d: '三维生成器', source2d: '平面与断面生成器', parameters: '共享几何与参数' },
    fileDetails: { glb: '网页及通用三维查看器', step: 'CAD 编辑与分组查看', plan: '带日语设施标签与尺寸', section: '河床、水位、护岸及步道关系', manifest: '演示尺寸、坐标与限制', source3d: '生成 STEP 与 GLB', source2d: '生成可编辑 DXF 与 SVG 预览', parameters: '定义曲线河道及场景尺寸' },
  },
  ja: {
    title: '日本の郊外河川 · モデル区間', modelName: '郊外河川モデル区間', modelLabel: 'モデル', description: '護岸、歩道橋、遊歩道、植栽を備えたパラメトリックな河川の例。',
    nav: '河川モデルと図面', tabs: { '3d': '3Dモデル', plan: '河川平面図', section: '横断面図', files: 'ダウンロード' },
    parts: '部材の表示', showAll: 'すべて表示', top: '上面図', reset: '視点をリセット', selected: '選択した部材', clear: '選択を解除',
    groups: { water: '水面', riverbed: '地形・河床', banks: '護岸', paths: '遊歩道・親水階段', bridge: '歩道橋', landscape: '植栽・休憩施設', lighting: '照明器具のイメージ' },
    loading: '河川モデルを読み込み中…', error: '河川モデルを読み込めません。接続を確認して再試行してください。', retry: '再試行',
    empty: 'すべての部材が非表示です。部材を選ぶか、すべて表示してください。', gesture: 'ドラッグで回転 · ホイール・2本指で拡大縮小 · クリックで部材を選択',
    dimensions: '仮定した寸法', units: '単位', length: '南北投影長', width: 'シーン幅', waterWidth: '公称水面幅', bridgeSpan: '公称橋梁スパン',
    parameterNote: '寸法はすべてモデル用の仮定です。水面幅と橋梁スパンは公称値です。',
    note: '架空の日本の郊外河川モデルです。水位、河床、堤岸、橋梁寸法はすべて仮定であり、治水、流量、橋梁耐力、法規への適合は確認していません。',
    drawingNote: 'CAD原図は日本語表記、寸法単位はミリメートルです。平面図と横断面図はDXFでダウンロード・編集できます。',
    planLoading: '図面を読み込み中…', planError: '図面を読み込めません。再試行してください。', planAlt: '日本の郊外河川モデル区間の平面図', sectionAlt: '郊外河川モデル区間の横断面図',
    downloads: '河川CAD・パラメトリックソース', download: 'ダウンロード', original: '編集可能な原図とモデルです。Pythonソースに形状パラメーターと図面生成処理を含みます。',
    fileNames: { glb: '河川3Dモデル', step: '河川CADソリッド', plan: '河川平面図', section: '河川横断面図', manifest: 'パラメーター・仮定一覧', source3d: '3D生成プログラム', source2d: '平面・断面生成プログラム', parameters: '共通形状・パラメーター' },
    fileDetails: { glb: 'ウェブ・一般的な3Dビューアー用', step: 'CAD編集・部材別表示用', plan: '施設名称・寸法付き', section: '河床・水位・護岸・遊歩道の関係', manifest: '仮定した寸法・座標・制限', source3d: 'STEP・GLBを生成', source2d: '編集可能なDXF・SVGを生成', parameters: '蛇行河道・シーン寸法を定義' },
  },
  en: {
    title: 'Japanese suburban river · Demo reach', modelName: 'Suburban river demo', modelLabel: 'Scene', description: 'A parametric river scene with revetments, a footbridge, paths and planting.',
    nav: 'River model and drawings', tabs: { '3d': '3D model', plan: 'River plan', section: 'Cross-section', files: 'Downloads' },
    parts: 'Components', showAll: 'Show all', top: 'Top view', reset: 'Reset view', selected: 'Selected component', clear: 'Clear selection',
    groups: { water: 'Water', riverbed: 'Terrain and riverbed', banks: 'Revetments', paths: 'Paths and river access', bridge: 'Footbridge', landscape: 'Planting and seating', lighting: 'Lighting fixtures (concept)' },
    loading: 'Loading river model…', error: 'The river model could not be loaded. Check your connection and retry.', retry: 'Retry',
    empty: 'All components are hidden. Select a component or show all.', gesture: 'Drag to rotate · Scroll or pinch to zoom · Click to select a component',
    dimensions: 'Demo parameters', units: 'Units', length: 'North–south extent', width: 'Scene width', waterWidth: 'Nominal water width', bridgeSpan: 'Nominal bridge span',
    parameterNote: 'All dimensions are demo assumptions. Water width and bridge span are nominal parameters.',
    note: 'This is a fictional Japanese suburban river reach. Water level, riverbed, bank and bridge dimensions are demo assumptions; flood control, flow capacity, bridge strength and statutory compliance have not been assessed.',
    drawingNote: 'Original CAD labels are Japanese and dimensions are in millimetres. Download the plan and cross-section as editable DXF files.',
    planLoading: 'Loading drawing…', planError: 'The drawing could not be loaded. Please retry.', planAlt: 'Japanese suburban river demo plan with Japanese labels', sectionAlt: 'River demo cross-section with Japanese labels',
    downloads: 'River CAD and parametric source', download: 'Download', original: 'Editable original files. Python source includes geometry parameters and drawing generators.',
    fileNames: { glb: 'River 3D model', step: 'River CAD solids', plan: 'River plan', section: 'River cross-section', manifest: 'Parameters and assumptions', source3d: '3D generator', source2d: 'Plan and section generator', parameters: 'Shared geometry and parameters' },
    fileDetails: { glb: 'For web and general 3D viewers', step: 'For CAD editing and grouped viewing', plan: 'Facility labels and dimensions', section: 'Riverbed, water level, revetments and paths', manifest: 'Demo dimensions, coordinates and limits', source3d: 'Generates STEP and GLB', source2d: 'Generates editable DXF and SVG previews', parameters: 'Defines the curved channel and scene dimensions' },
  },
} satisfies Record<Locale, object>;
