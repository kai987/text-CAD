import type { Locale } from './localization';

export const landmarkIds = ['tokyo-tower', 'tokyo-skytree'] as const;
export type LandmarkId = typeof landmarkIds[number];
export const landmarkGroupIds = ['base', 'structure', 'core', 'decks', 'antenna'] as const;
export type LandmarkGroupId = typeof landmarkGroupIds[number];
export const landmarkViews = ['3d', 'plan', 'elevation', 'files'] as const;
export type LandmarkView = typeof landmarkViews[number];
export const landmarkCameras = ['iso', 'front', 'side', 'top'] as const;
export const landmarkDetailCameras = ['base', 'main-deck', 'top-deck', 'tembo-deck', 'tembo-galleria', 'spire'] as const;
export type LandmarkCamera = typeof landmarkCameras[number] | typeof landmarkDetailCameras[number] | 'steel-node';
export function landmarkCameraOptions(id: LandmarkId): readonly LandmarkCamera[] {
  return id === 'tokyo-tower'
    ? [...landmarkCameras, 'base', 'main-deck', 'top-deck', 'spire']
    : [...landmarkCameras, 'base', 'tembo-deck', 'tembo-galleria', 'spire'];
}
export const landmarkModels = {
  'tokyo-tower': { stem: 'tokyo_tower', revision: 'LANDMARK-R06', height: 333000, levels: [125000, 223550], nominalLevels: [150000, 250000],
    names: { zh: '东京塔', ja: '東京タワー', en: 'Tokyo Tower' },
    assumptionNotes: {
      zh: '东京塔展望台平面参考 JAEE 1962 年原图：H11 为 27 m 方形、H12 为 28 m 方形，H23 为直径 13 m 的圆形。历史 H13 的 29 × 24 m 独立平面单独记录，功能及其与当前外幕墙的对应关系尚未核定。R06参照实景照片，用48面近似较细的上部圆筒，独立表现H24圆形设备平台与白色格构。顶部改为两组红白圆形天线阵列，按供应商2012年Fig.5的环形布置控制，每组30×5片、合计300片。历史层号及当时用途仅作资料对应，当前用途尚未核定。H23的GL223.55 m沿用为结构带/屋顶参考，当前游客楼面完成面未实测。改修外观、外壳厚度、玻璃分格及设备细部仍为展示近似；钢材截面和连接尺寸未逐件实测，未进行结构计算。',
      ja: '東京タワーの展望台平面はJAEEの1962年原図を参照し、H11を27 m角、H12を28 m角、H23を直径13 mの円形として扱います。29 × 24 mの歴史H13平面を別記し、用途や現在の外装との対応は未確定です。R06は実景写真を参考に、細身の上部円筒を48面で近似し、H24の独立した円形設備床と白い格構を表現します。塔頂は供給元の2012年Fig.5を参考に赤白の円形アンテナ2組とし、各30×5枚、計300枚を配置します。歴史の層番号と当時の用途は資料上の対応で、現在の用途は未確認です。H23のGL223.55 mは構造帯・屋根の参照高さを継承し、現来場者床の仕上げ面は未実測です。改修後の外観、外装厚さ、ガラス割付、設備細部は表示用の近似です。部材断面・接合寸法の実測復元や構造計算は行っていません。',
      en: 'Tokyo Tower deck plans follow the JAEE 1962 original drawing: H11 is a 27 m square, H12 a 28 m square, and H23 a 13 m diameter circle. The historical 29 × 24 m H13 plan is recorded separately; its use and mapping to the current envelope remain unverified. R06 follows site photographs with a slimmer upper cylinder approximated by 48 facets, an independent circular H24 equipment platform and white lattice. Two red-and-white circular antenna banks follow the supplier’s 2012 Fig.5 arrangement, each with 30×5 panels, 300 panels in total. Historical level labels and uses describe their source documents; current uses remain unverified. H23 at GL223.55 m remains a structural-band/roof reference; the current visitor finished floor has not been surveyed. Current retrofit appearance, shell thickness, glazing divisions and equipment details remain display approximations. Member sections and connections have not been individually surveyed; no structural analysis is included.',
    },
    reference: 'https://www.tokyotower.co.jp/guidance/',
    constructionReference: 'https://www.miyaji-eng.co.jp/technology/newsletter/media/18/no18-p085-091.pdf' },
  'tokyo-skytree': { stem: 'tokyo_skytree', revision: 'LANDMARK-R05', height: 634000, levels: [350000, 450000],
    names: { zh: '东京晴空塔', ja: '東京スカイツリー', en: 'Tokyo Skytree' },
    assumptionNotes: {
      zh: '公开资料提供68 m三角形基部、315 m圆形转换、340/345/350 m楼层、375 m设备屋顶高度、445–450 m回廊与451.2 m最高点、向外倾斜71°的天望甲板立面及约6 m宽增益塔等控制。R05沿用角部/面中点圆弧和24点采样拟合塔身，以及展望台、回廊和分段天线设备外包络。圆弧半径、315 m以上约32→18 m的直锥、设备冠半径与分段截面、回廊宽度及未公开设备站点均为模型拟合近似，非竣工实测；375 m不是展望楼层。3组各4柱鼎桁架、模型 GL 0–50 m脚部连接区间及12.5/25 m环层保留。外周水平材改为中空圆管，内侧环桁架与放射连接保留方管（RHS）；基部补充三面宽翼格构，并保留中央尖拱开口。圆管指杆件截面，塔身平面仍由底部三角形过渡到315 m圆形。宽翼分格与节点为照片引导的拟合，构件数量、管径、节点和TMD帽细部未逐件复原，未进行结构计算。',
      ja: '公開資料の制御値は68 mの三角形基部、315 mの円形への移行、340/345/350 mのフロア、375 mの設備屋上高さ、445–450 mの回廊と最高点451.2 m、外側へ71°傾く天望デッキ外壁、約6 m幅のゲイン塔です。R05は隅部・面中央の円弧と24点の採形による塔体、展望台・回廊・分節したアンテナ設備の輪郭を継承します。円弧半径、315 m以高の約32→18 mの直線テーパー、設備冠の半径と分節断面、回廊幅、非公開の設備配置高さはモデルの形状合わせで、竣工実測ではありません。375 mは展望フロアではありません。各4柱の鼎3組、モデルGL 0–50 m脚部連結区間、12.5/25 mのリング層を保持します。外周水平材を中空円管とし、内側リングトラスと放射方向の連結には角管（RHS）を残します。基部に三面の幅広い格構翼を補い、中央の尖頭アーチ開口を保ちます。円管は部材断面を指し、塔体平面は基部の三角形から315 mの円形へ移行します。翼の割付と接合位置は写真に基づく近似で、部材数・管径・接合部・TMD頂部の細部は実測復元ではなく、構造計算も行っていません。',
      en: 'Published controls identify the 68 m triangular base, circular transition at 315 m, 340/345/350 m floors, 375 m equipment-roof height, 445–450 m gallery and 451.2 m high point, outward 71° deck facade and roughly 6 m wide gain tower. R05 retains corner and face-midpoint arcs with 24 contour samples, plus the deck, gallery and segmented antenna envelopes. Arc radii, the approximately 32-to-18 m upper taper, equipment-crown radii and sectional stations, gallery width and unpublished equipment stations are model-fit approximations, not surveyed as-built geometry; 375 m is not an observation floor. Three four-column clusters, a model GL 0–50 m base-connection zone and 12.5/25 m ring layers remain. Exterior horizontal members use hollow circular tubes; inner ring trusses and radial links retain rectangular hollow sections (RHS). Three broad lattice wings complete the base faces while preserving central pointed-arch openings. Circular tubes describe member sections; the body plan still changes from the base triangle to a circle at 315 m. Wing subdivisions and joints are photo-guided fits. Member counts, sections, joints and TMD-cap details are display approximations, not a member-for-member reconstruction. No structural analysis is included.',
    },
    reference: 'https://www.tokyo-skytree.jp/about/outline/' },
} as const;
export function isLandmarkId(value: unknown): value is LandmarkId { return landmarkIds.some(id => id === value); }
export function initialLandmarkView(search: string): LandmarkView {
  const value = new URLSearchParams(search).get('view');
  if (landmarkViews.some(id => id === value)) return value as LandmarkView;
  return value === '1f' || value === '2f' ? 'plan' : '3d';
}
export function landmarkUrl(current: string, id: LandmarkId, view: LandmarkView): string {
  const url = new URL(current);
  const environment = url.searchParams.get('environment');
  url.search = '';
  url.searchParams.set('model', id); url.searchParams.set('view', view);
  if (environment === 'day' || environment === 'night') url.searchParams.set('environment', environment);
  return url.href;
}
export function landmarkGroupForName(name: string): LandmarkGroupId | null {
  const tokens = name.toLowerCase().split(/[^a-z]+/);
  return landmarkGroupIds.find(group => tokens.includes(group)) ?? null;
}
export function landmarkDownloadFiles(id: LandmarkId) {
  const { stem } = landmarkModels[id];
  return [
    { id: 'glb', path: `GLB/${stem}.glb`, type: 'GLB' },
    { id: 'step', path: `STEP/${stem}.step`, type: 'STEP' },
    { id: 'plan', path: `DXF/${stem}_plan.dxf`, type: 'DXF' },
    { id: 'elevation', path: `DXF/${stem}_elevation.dxf`, type: 'DXF' },
    ...(id === 'tokyo-tower' ? [{ id: 'steelNodes', path: 'DXF/tokyo_tower_steel_nodes.dxf', type: 'DXF' } as const] : []),
    ...(id === 'tokyo-skytree' ? [{ id: 'structureZones', path: 'DXF/tokyo_skytree_structure_zones.dxf', type: 'DXF' } as const] : []),
    { id: 'pdf', path: `output/pdf/${stem}_sheets.pdf`, type: 'PDF' },
    { id: 'manifest', path: `output/review/${stem}_manifest.json`, type: 'JSON' },
  ] as const;
}
export const landmarkCopy = {
  zh: {
    modelLabel: '场景方案', subtitle: '东京地标 · 外形示意', description: '东京塔与东京晴空塔的参数化 CAD、可编辑图纸和分组 3D 模型。',
    nav: '地标模型与图纸', tabs: { '3d': '三维模型', plan: '平面图', elevation: '立面图', files: '文件下载' },
    parts: '部件显示', groups: { base: '基座与基础示意', structure: '塔身桁架', core: '中心筒', decks: '展望台', antenna: '天线与塔尖' },
    showAll: '显示全部', views: { iso: '等轴测', front: '正视', side: '侧视', top: '俯视', base: '塔脚', 'main-deck': '主展望台', 'top-deck': '特别展望台', 'tembo-deck': '天望甲板', 'tembo-galleria': '天望回廊', spire: '塔尖', 'steel-node': '钢节点近景' },
    steel: { title: '钢结构节点', node: '节点', focus: '查看节点近景', micro: '铆钉细节', modes: { auto: '自动', on: '显示', off: '隐藏' }, hidden: '塔身桁架已隐藏，显示该分类后可查看节点。', note: '根据公开立面和施工照片制作的外观近似。20处连接的位置及板件、加劲肋、铆钉的尺寸仍为演示假设，不代表原建筑的逐点节点设计。未进行承载力或连接强度验算。自动模式仅在近景显示铆钉。' },
    dimensions: '主要尺寸', height: '总高', levels: '展望台标高', source: '官方尺寸来源',
    modelGlLevels: '模型 GL 展望层', nominalLevels: '官方案内高度', constructionSource: '施工立面参考（印刷页 86）', glReferenceNote: '展望台平面参考 JAEE 1962 年原图，结构带标高参考宫地技报的 H11/H23：GL 120 m/223.55 m。H23为历史结构带/屋顶参考高度。模型沿用主展望台 120/125 m 双层及上部 223.55 m 的 GL 布置；当前游客楼面完成面高度尚未独立测绘核定。官方案内高度 150 m/250 m 另列，两组数值之间尚未核准换算关系。',
    environment: '场景', day: '白天', night: '夜晚',
    note: '总高和展望台参考尺寸依据公开资料；基座、截面、杆件、连接和外形细节均为示意假设。此模型并非原建筑测绘或施工图，未进行结构计算。',
    drawingNote: '图纸使用日文标注，模型空间单位为毫米。可下载原始 DXF 编辑文字和尺寸。',
    loading: '正在加载地标模型…', error: '模型加载失败，请检查连接后重试。', retry: '重试',
    planLoading: '正在加载图纸…', planError: '图纸加载失败，请重试。',
    empty: '部件已全部隐藏，请选择部件或显示全部。', gesture: '拖动旋转 · 滚轮或双指缩放 · 点击选择部件',
    selected: '已选部件', clear: '清除选择', reset: '重置缩放', zoom: '图纸缩放',
    downloads: 'CAD、三维模型与图纸', download: '下载', original: '保留名称和分组的原始模型，以及可编辑标注的图纸。',
    fileNames: { glb: '三维模型', step: 'CAD 精确实体', plan: '平面图', elevation: '立面图', steelNodes: '钢结构节点详图', structureZones: '钢结构分区图', pdf: 'A3 图纸', manifest: '参数与来源清单' },
    fileDetails: { glb: '通用 glTF 2.0 · 米 · Y 轴向上', step: '毫米单位 · 独立命名部件', plan: '可编辑日文名称与原生尺寸', elevation: '总高、塔身与展望台标高', steelNodes: '参考公开立面及施工照的外观近似 · 20处位置及尺寸为假设', structureZones: '三组四柱与管杆层次 · 模型区间尺寸 · 可编辑标注', pdf: '平面、立面和详图 · 按图示比例打印', manifest: '官方参考尺寸、示意假设与部件分类' },
  },
  ja: {
    modelLabel: 'モデル', subtitle: '東京のランドマーク · 外観モデル', description: '東京タワーと東京スカイツリーのパラメトリックCAD、編集可能な図面、部材別3Dモデル。',
    nav: 'ランドマークのモデルと図面', tabs: { '3d': '3Dモデル', plan: '平面図', elevation: '立面図', files: 'ダウンロード' },
    parts: '部材の表示', groups: { base: '基壇・基礎の概念形状', structure: '塔体トラス', core: '中心コア', decks: '展望台', antenna: 'アンテナ・塔頂' },
    showAll: 'すべて表示', views: { iso: '等角図', front: '正面', side: '側面', top: '上面', base: '塔脚', 'main-deck': 'メインデッキ', 'top-deck': 'トップデッキ', 'tembo-deck': '天望デッキ', 'tembo-galleria': '天望回廊', spire: '塔頂', 'steel-node': '鋼接合部の近景' },
    steel: { title: '鉄骨の接合部', node: '接合部', focus: '接合部を拡大', micro: 'リベットの詳細', modes: { auto: '自動', on: '表示', off: '非表示' }, hidden: '塔体トラスが非表示です。この分類を表示すると接合部を確認できます。', note: '公開立面図・施工写真を参考にした外観の近似モデルです。選択した20か所の位置と接合板・補剛リブ・リベットの寸法は仮定であり、実物の接合部を採寸して再現したものではありません。耐力や接合部強度の検証は行っていません。自動モードでは近景のみリベットを表示します。' },
    dimensions: '主要寸法', height: '全高', levels: '展望台の高さ', source: '公式の寸法資料',
    modelGlLevels: 'モデルのGL基準展望階', nominalLevels: '公式案内高さ', constructionSource: '施工立面の資料（冊子86ページ）', glReferenceNote: '展望台平面はJAEEの1962年原図、構造帯の高さは宮地技報のH11/H23（GL 120 m/223.55 m）を参照しています。H23は歴史の構造帯・屋根の参照高さです。モデルではメインデッキ120/125 mの2層と上部223.55 mのGL配置を継承しています。現在の来場者用床の仕上げ面高さは独立した実測で検証していません。公式案内の150 m/250 mを別記し、両者の換算関係が確認済みとは扱いません。',
    environment: 'シーン', day: '昼', night: '夜',
    note: '全高と展望台の参考寸法は公開資料に基づいています。基壇、断面、部材、接合部、外観の細部はモデル用の仮定です。実施設の実測図・施工図ではなく、構造計算は実施していません。',
    drawingNote: '原図は日本語表記、モデル空間の単位はmmです。元のDXFをダウンロードし、文字と寸法を編集できます。',
    loading: 'ランドマークを読み込み中…', error: 'モデルを読み込めません。接続を確認して再試行してください。', retry: '再試行',
    planLoading: '図面を読み込み中…', planError: '図面を読み込めません。再試行してください。',
    empty: 'すべての部材が非表示です。部材を選ぶか、すべて表示してください。', gesture: 'ドラッグで回転 · ホイール・2本指で拡大縮小 · クリックで部材選択',
    selected: '選択した部材', clear: '選択を解除', reset: '拡大率をリセット', zoom: '図面の拡大率',
    downloads: 'CAD・3Dモデル・図面', download: 'ダウンロード', original: '部材名と分類を保持した元のモデルと、編集可能な注記付きの図面です。',
    fileNames: { glb: '3Dモデル', step: 'CADソリッド', plan: '平面図', elevation: '立面図', steelNodes: '鉄骨接合部の詳細図', structureZones: '鋼構造の区分図', pdf: 'A3図面', manifest: 'パラメーター・出典一覧' },
    fileDetails: { glb: '標準glTF 2.0・m単位・Y-up', step: 'mm単位・部材ごとに命名', plan: '編集可能な日本語注記・寸法', elevation: '全高・塔体・展望台の高さ', steelNodes: '公開立面・施工写真に基づく外観近似・20か所の位置と寸法は仮定', structureZones: '3組の4柱・管材の階層・モデル区間寸法・編集可能な注記', pdf: '平面・立面・詳細図・記載した縮尺で印刷', manifest: '公式の参考寸法・仮定・部材分類' },
  },
  en: {
    modelLabel: 'Scene', subtitle: 'Tokyo landmarks · Exterior studies', description: 'Parametric CAD, editable drawings and grouped 3D models of Tokyo Tower and Tokyo Skytree.',
    nav: 'Landmark model and drawings', tabs: { '3d': '3D model', plan: 'Plan', elevation: 'Elevation', files: 'Downloads' },
    parts: 'Components', groups: { base: 'Base and foundation concept', structure: 'Tower lattice', core: 'Central core', decks: 'Observation decks', antenna: 'Antenna and spire' },
    showAll: 'Show all', views: { iso: 'Isometric', front: 'Front', side: 'Side', top: 'Top', base: 'Tower base', 'main-deck': 'Main deck', 'top-deck': 'Top deck', 'tembo-deck': 'Tembo Deck', 'tembo-galleria': 'Tembo Galleria', spire: 'Spire', 'steel-node': 'Steel connection close-up' },
    steel: { title: 'Steel connections', node: 'Connection', focus: 'View connection close-up', micro: 'Rivet details', modes: { auto: 'Auto', on: 'Show', off: 'Hide' }, hidden: 'The tower lattice is hidden. Show that category to inspect connections.', note: 'An appearance approximation informed by published elevations and construction photographs. The 20 selected locations and plate, stiffener and rivet dimensions remain modelling assumptions; they do not document the original connection designs. Member and connection capacities have not been verified. Auto mode shows rivets only in close-up views.' },
    dimensions: 'Key dimensions', height: 'Overall height', levels: 'Observation deck levels', source: 'Official dimension reference',
    modelGlLevels: 'Model deck levels above GL', nominalLevels: 'Official published guidance heights', constructionSource: 'Construction elevation (printed page 86)', glReferenceNote: 'Deck plans follow the JAEE 1962 original drawing; structural-band heights follow Miyaji Technical Reports H11/H23 at GL 120 m/223.55 m. H23 identifies a historical structural-band/roof reference. The model retains its two main-deck levels at 120/125 m and upper deck at 223.55 m above GL. Current visitor finished-floor heights have not been independently surveyed or verified. Official guidance heights of 150 m/250 m are listed separately; no verified conversion between these figures is claimed.',
    environment: 'Scene', day: 'Day', night: 'Night',
    note: 'Overall heights and reference deck dimensions follow public sources. Bases, sections, members, connections and exterior details are illustrative assumptions. These are not surveys or construction drawings of the actual towers; no structural analysis is included.',
    drawingNote: 'Original drawing labels are Japanese; model-space dimensions are in millimetres. Download DXF originals to edit text and dimensions.',
    loading: 'Loading landmark model…', error: 'The model could not be loaded. Check your connection and retry.', retry: 'Retry',
    planLoading: 'Loading drawing…', planError: 'The drawing could not be loaded. Please retry.',
    empty: 'All components are hidden. Select a component or show all.', gesture: 'Drag to rotate · Scroll or pinch to zoom · Click to select a component',
    selected: 'Selected component', clear: 'Clear selection', reset: 'Reset zoom', zoom: 'Drawing zoom',
    downloads: 'CAD, 3D models and drawings', download: 'Download', original: 'Original models retain names and component groups; drawing annotations remain editable.',
    fileNames: { glb: '3D model', step: 'CAD solids', plan: 'Plan drawing', elevation: 'Elevation drawing', steelNodes: 'Steel connection details', structureZones: 'Steelwork zones', pdf: 'A3 drawing sheets', manifest: 'Parameters and references' },
    fileDetails: { glb: 'Standard glTF 2.0 · metres · Y-up', step: 'Millimetres · individually named components', plan: 'Editable Japanese labels and native dimensions', elevation: 'Overall height, tower profile and deck levels', steelNodes: 'Appearance approximation from public elevations and construction photos · 20 assumed locations and dimensions', structureZones: 'Three four-column clusters · tube hierarchy · editable model interval dimensions', pdf: 'Plan, elevation and details · print at the stated scale', manifest: 'Official reference dimensions, assumptions and component groups' },
  },
} satisfies Record<Locale, object>;
