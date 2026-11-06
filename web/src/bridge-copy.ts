import type { Locale } from './localization';

export const bridgeId = 'seto-ohashi';
export const bridgeRevision = 'BRIDGE-R05';
export const bridgeGroups = ['environment', 'foundations', 'towers', 'cables', 'hangers', 'truss', 'road', 'railway', 'traffic', 'vessels', 'trains'] as const;
export type BridgeGroupId = typeof bridgeGroups[number];
/** Display-only switches; native CAD keeps its single environment group. */
export type BridgeEnvironmentVisibility = { sea: boolean; terrain: boolean };
export const bridgeViews = ['3d', 'plan', 'elevation', 'section', 'files'] as const;
export type BridgeView = typeof bridgeViews[number];
export const bridgeCameras = ['iso', 'elevation', 'top', 'tower', 'anchorage', 'deck', 'traffic', 'vessel', 'train'] as const;
export type BridgeCamera = typeof bridgeCameras[number];
export function initialBridgeView(search: string): BridgeView {
  const value = new URLSearchParams(search).get('view');
  return bridgeViews.includes(value as BridgeView) ? value as BridgeView : value === '1f' || value === '2f' ? 'plan' : '3d';
}
export function bridgeUrl(current: string, view: BridgeView): string {
  const url = new URL(current), environment = url.searchParams.get('environment');
  url.search = ''; url.searchParams.set('model', bridgeId); url.searchParams.set('view', view);
  if (environment === 'day' || environment === 'night') url.searchParams.set('environment', environment);
  return url.href;
}
export function bridgeGroupForName(name: string): BridgeGroupId | null {
  const token = name.split(/[:\-]/)[0];
  return bridgeGroups.find(group => group === token) ?? null;
}
export const bridgeDownloads = [
  { id: 'glb', path: 'GLB/seto_ohashi.glb', type: 'GLB' },
  { id: 'step', path: 'STEP/seto_ohashi.step', type: 'STEP' },
  { id: 'plan', path: 'DXF/seto_ohashi_plan.dxf', type: 'DXF' },
  { id: 'elevation', path: 'DXF/seto_ohashi_elevation.dxf', type: 'DXF' },
  { id: 'section', path: 'DXF/seto_ohashi_section.dxf', type: 'DXF' },
  { id: 'pdf', path: 'output/pdf/seto_ohashi_sheets.pdf', type: 'PDF' },
  { id: 'manifest', path: 'output/review/seto_ohashi_manifest.json', type: 'JSON' },
  { id: 'source3d', path: 'src/seto_bridge_3d.py', type: 'PY' },
  { id: 'source2d', path: 'src/generate_seto_bridge_plans.py', type: 'PY' },
  { id: 'parameters', path: 'src/lib/seto_bridge_geometry.py', type: 'PY' },
  { id: 'sourceDependency', path: 'src/lib/step_transport.py', type: 'PY' },
  { id: 'activitySource', path: 'src/lib/seto_bridge_activity.py', type: 'PY' },
] as const;
export const bridgeCopy = {
  zh: {
    title: '濑户大桥 · 南北备赞双桥', modelName: '濑户大桥 · 南北备赞双桥', modelLabel: '场景方案',
    description: '参考实景及官方侧面图的南、北备赞濑户大桥参数化 CAD 与公铁双层 3D 模型。', nav: '桥梁模型与图纸',
    tabs: { '3d': '三维模型', plan: '平面图', elevation: '侧立面', section: '横断面', files: '文件下载' },
    parts: '部件显示', showAll: '显示全部', groups: { environment: '海面与岛屿示意', foundations: '基础与锚碇', towers: '主塔', cables: '主缆', hangers: '吊索', truss: '加劲钢桁架', road: '上层道路桥面', railway: '下层铁路桥面', traffic: '行驶车辆', vessels: '水面游船', trains: '铁路电车' },
    cameras: { iso: '双桥全景', elevation: '侧视', top: '俯视', tower: '主塔近景', anchorage: '中间共用锚碇近景', deck: '公铁双层近景', traffic: '车辆跟随近景', vessel: '游船跟随近景', train: '电车跟随近景' },
    surroundings: { sea: '海面', terrain: '岛屿与地形示意' },
    dimensions: '官方参考尺寸', northLength: '北桥悬索区桁长', southLength: '南桥悬索区桁长', northSpan: '北桥主跨', southSpan: '南桥主跨',
    source: '资料与实景参考', assumptionTitle: '模型假设', note: '本次范围为南、北备赞濑户大桥双桥，未包含濑户大桥全线。桥长与主跨参考官方资料；截面、缆索曲线及环境细节为外观拟合，未进行结构计算。',
    motion: { title: '船车与水面', play: '播放行驶动画', waves: '水面波动', pause: '暂停行驶动画', note: '车辆按左侧通行；游船横穿主跨，电车沿下层轨道运行；航线、速度和数量为演示假设。STEP 和 GLB 保留静态时刻，动态仅在此查看器中呈现。拖动或缩放可结束跟随。', reduced: '系统已开启减少动态，动画默认暂停，可手动播放。' },
    nightNote: '昼夜为演示光照，未复原实际亮灯方案。', environment: '场景', day: '白天', night: '夜晚',
    loading: '正在加载双桥模型…', error: '桥梁模型加载失败，请检查连接后重试。', retry: '重试',
    empty: '全部部件已隐藏，请选择部件或显示全部。', selected: '已选部件', clear: '清除选择', gesture: '拖动旋转 · 滚轮或双指缩放 · 点击选择部件',
    drawingNote: '日文原图 · 模型空间单位 mm · DXF 文字和尺寸可编辑。', planLoading: '正在加载图纸…', planError: '图纸无法加载，请重试。', reset: '重置缩放',
    metadataError: '尺寸与来源清单加载失败。', downloads: '桥梁 CAD、三维模型与参数化源码', download: '下载', original: '保留独立部件、可编辑标注，以及官方尺寸和模型假设记录。',
    fileNames: { glb: '双桥三维模型', step: '命名部件 CAD 实体', plan: '双桥平面图', elevation: '双桥侧立面图', section: '公铁双层横断面', pdf: '图纸 PDF', manifest: '参数与资料清单', source3d: '三维模型生成器', source2d: '图纸生成器', parameters: '参数与共享几何', sourceDependency: 'STEP 导出辅助源码', activitySource: '游船、车辆及电车参数源码' },
    fileDetails: { glb: 'glTF 2.0 · 米 · Y-up', step: '毫米 · 可分组编辑', plan: '桥梁平面布置及跨度', elevation: '主塔、主缆与桥跨尺寸', section: '上层道路、下层铁路及钢桁架关系', pdf: '按图示比例打印', manifest: '尺寸来源、假设及部件命名', source3d: '生成 STEP 和 GLB', source2d: '生成可编辑 DXF、SVG 与 PDF', parameters: '按官方跨度和实景外形建立参数', sourceDependency: '三维生成器依赖的无损 STEP 导出辅助工具', activitySource: '静态船车与电车几何、航线、轨道、编组及速度' },
  },
  ja: {
    title: '瀬戸大橋 · 南北備讃の双子橋', modelName: '瀬戸大橋 · 南北備讃の双子橋', modelLabel: 'モデル',
    description: '実景と公式側面図を参考にした南・北備讃瀬戸大橋のパラメトリックCADと道路鉄道併用3Dモデル。', nav: '橋のモデルと図面',
    tabs: { '3d': '3Dモデル', plan: '平面図', elevation: '側面図', section: '横断面図', files: 'ダウンロード' },
    parts: '部材の表示', showAll: 'すべて表示', groups: { environment: '海面・島の概念形状', foundations: '基礎・アンカレイジ', towers: '主塔', cables: '主ケーブル', hangers: 'ハンガー', truss: '補剛トラス', road: '上層の道路', railway: '下層の鉄道', traffic: '走行車両', vessels: '遊覧船', trains: '鉄道の電車' },
    cameras: { iso: '双子橋の全景', elevation: '側面', top: '上面', tower: '主塔を拡大', anchorage: '中央アンカレイジを拡大', deck: '道路・鉄道を拡大', traffic: '車両を追う', vessel: '遊覧船を追う', train: '電車を追う' },
    surroundings: { sea: '海面', terrain: '島・地形（概形）' },
    dimensions: '公式資料の参考寸法', northLength: '北橋の補剛桁長', southLength: '南橋の補剛桁長', northSpan: '北橋の中央支間', southSpan: '南橋の中央支間',
    source: '資料・実景の出典', assumptionTitle: 'モデルの仮定', note: '対象は南・北備讃瀬戸大橋の双子橋で、瀬戸大橋全線ではありません。橋長・中央支間は公式資料を参照し、断面・ケーブル曲線・環境は外観の近似です。構造計算は実施していません。',
    motion: { title: '船・車・電車と波', play: '走行アニメーションを再生', waves: '水面の波', pause: '走行アニメーションを一時停止', note: '車は左側通行です。船は中央支間を横切り、電車は下層の線路を走ります。航路・速度・台数は表示用の仮定です。STEP・GLBは静止時点を保存し、動きはこのビューアーだけで表示します。ドラッグ・拡大縮小で追従を解除します。', reduced: '端末の動きを減らす設定に合わせ、初期状態は停止しています。手動で再生できます。' },
    nightNote: '昼夜の照明は表示用で、実際のライトアップを再現したものではありません。', environment: 'シーン', day: '昼', night: '夜',
    loading: '双子橋を読み込み中…', error: '橋のモデルを読み込めません。接続を確認して再試行してください。', retry: '再試行',
    empty: 'すべての部材が非表示です。部材を選ぶか、すべて表示してください。', selected: '選択した部材', clear: '選択を解除', gesture: 'ドラッグで回転 · ホイール・2本指で拡大縮小 · クリックで部材選択',
    drawingNote: '原図は日本語・モデル空間はmm単位です。DXFの注記・寸法は編集できます。', planLoading: '図面を読み込み中…', planError: '図面を読み込めません。再試行してください。', reset: '拡大率をリセット',
    metadataError: '寸法・出典一覧を読み込めません。', downloads: '橋のCAD・3Dモデル・パラメトリックソース', download: 'ダウンロード', original: '独立した部材、編集可能な注記、公式寸法とモデルの仮定を保持しています。',
    fileNames: { glb: '双子橋の3Dモデル', step: '命名済みCADソリッド', plan: '双子橋の平面図', elevation: '双子橋の側面図', section: '道路・鉄道の横断面', pdf: '図面PDF', manifest: 'パラメーター・出典一覧', source3d: '3D生成器', source2d: '図面生成器', parameters: 'パラメーター・共通形状', sourceDependency: 'STEP出力の補助ソース', activitySource: '遊覧船・車・電車のパラメーター' },
    fileDetails: { glb: 'glTF 2.0・m単位・Y-up', step: 'mm単位・部材別に編集', plan: '橋の平面配置・支間', elevation: '主塔・主ケーブル・支間寸法', section: '上層道路・下層鉄道・補剛トラスの関係', pdf: '図面記載の縮尺で印刷', manifest: '寸法の出典・仮定・部材名', source3d: 'STEP・GLBを生成', source2d: '編集可能なDXF・SVG・PDFを生成', parameters: '公式支間と実景の外形を参照', sourceDependency: '3D生成器が利用する可逆STEP出力処理', activitySource: '船・車・電車の静的形状、航路・車線・編成・速度' },
  },
  en: {
    title: 'Seto Ohashi · North & South Bisan-Seto', modelName: 'Seto Ohashi · Bisan-Seto twin bridges', modelLabel: 'Scene',
    description: 'Photo-informed parametric CAD and double-deck road–rail 3D models of the North and South Bisan-Seto bridges.', nav: 'Bridge model and drawings',
    tabs: { '3d': '3D model', plan: 'Plan', elevation: 'Elevation', section: 'Cross-section', files: 'Downloads' },
    parts: 'Components', showAll: 'Show all', groups: { environment: 'Sea and illustrative islands', foundations: 'Foundations and anchorages', towers: 'Main towers', cables: 'Main cables', hangers: 'Hangers', truss: 'Stiffening truss', road: 'Upper road deck', railway: 'Lower railway deck', traffic: 'Moving vehicles', vessels: 'Cruise boats', trains: 'Railway trains' },
    cameras: { iso: 'Twin-bridge overview', elevation: 'Side', top: 'Top', tower: 'Tower close-up', anchorage: 'Central anchorage close-up', deck: 'Road–rail close-up', traffic: 'Follow vehicles', vessel: 'Follow cruise boat', train: 'Follow train' },
    surroundings: { sea: 'Sea surface', terrain: 'Illustrative islands and terrain' },
    dimensions: 'Official reference dimensions', northLength: 'North stiffening girder', southLength: 'South stiffening girder', northSpan: 'North main span', southSpan: 'South main span',
    source: 'Sources and photo references', assumptionTitle: 'Modelling assumptions', note: 'This model covers the North and South Bisan-Seto twin bridges, rather than the entire Seto Ohashi route. Bridge lengths and main spans follow official sources; sections, cable curves and surroundings are visual approximations. No structural analysis is included.',
    motion: { title: 'Boats, traffic and waves', play: 'Play traffic animation', waves: 'Water animation', pause: 'Pause traffic animation', note: 'Vehicles keep left. Boats cross the main spans; trains use the lower tracks. Routes, speeds and counts are illustrative assumptions. STEP and GLB retain a static snapshot; movement is provided by this viewer. Drag or zoom to stop following.', reduced: 'Your reduced-motion preference pauses animation initially. You can start it manually.' },
    nightNote: 'Day/night lighting is illustrative and does not reproduce the actual illumination scheme.', environment: 'Scene', day: 'Day', night: 'Night',
    loading: 'Loading twin bridges…', error: 'The bridge model could not be loaded. Check your connection and retry.', retry: 'Retry',
    empty: 'All components are hidden. Select components or show all.', selected: 'Selected component', clear: 'Clear selection', gesture: 'Drag to rotate · Scroll or pinch to zoom · Click to select components',
    drawingNote: 'Japanese original labels · millimetre model space · editable DXF text and dimensions.', planLoading: 'Loading drawing…', planError: 'The drawing could not be loaded. Please retry.', reset: 'Reset zoom',
    metadataError: 'The dimension and source record could not be loaded.', downloads: 'Bridge CAD, 3D models and parametric sources', download: 'Download', original: 'Individually named components, editable annotations, official dimensions and explicit modelling assumptions.',
    fileNames: { glb: 'Twin-bridge 3D model', step: 'Named CAD solids', plan: 'Twin-bridge plan', elevation: 'Twin-bridge elevation', section: 'Road–rail cross-section', pdf: 'Drawing PDF', manifest: 'Parameters and references', source3d: '3D generator', source2d: 'Drawing generator', parameters: 'Parameters and shared geometry', sourceDependency: 'STEP export helper source', activitySource: 'Boat, vehicle and train parameters' },
    fileDetails: { glb: 'glTF 2.0 · metres · Y-up', step: 'Millimetres · independently editable parts', plan: 'Bridge layout and span dimensions', elevation: 'Towers, main cables and spans', section: 'Upper road, lower railway and stiffening truss', pdf: 'Print at the indicated scales', manifest: 'Dimension sources, assumptions and component names', source3d: 'Generate STEP and GLB', source2d: 'Generate editable DXF, SVG and PDF', parameters: 'Official spans and photo-informed profiles', sourceDependency: 'Lossless STEP export dependency used by the 3D generator', activitySource: 'Static craft, vehicles, trains, routes, consists and speeds' },
  },
} satisfies Record<Locale, object>;
