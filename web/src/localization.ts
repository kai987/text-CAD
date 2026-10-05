import plan from '../../output/review/design_manifest.json' with { type: 'json' };
import model from '../../output/review/house_3d_assumptions_R01.json' with { type: 'json' };
import type { GroupId, ModelPartId, PartKind } from './model-state';

export type Locale = 'zh' | 'ja' | 'en';
export const locales = ['zh', 'ja', 'en'] as const;
export const languageNames = { zh: '中文', ja: '日本語', en: 'English' } as const;
export const htmlLanguages = { zh: 'zh-CN', ja: 'ja', en: 'en' } as const;
export function isLocale(value: unknown): value is Locale {
  return typeof value === 'string' && locales.some(locale => locale === value);
}
export function resolveLocale(saved: string | null): Locale { return isLocale(saved) ? saved : 'zh'; }
export function format(template: string, values: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (placeholder, name: string) =>
    Object.hasOwn(values, name) ? String(values[name]) : placeholder);
}

const zh = {
  models: { label: '户型方案', house: '日本两层一户建', apartment: '日本公寓 2LDK · 约 65㎡', note: '所有方案尺寸均为演示假设' },
  theme: { label: '颜色模式', system: '系统', light: '浅色', dark: '深色', help: '选择系统可跟随设备的明暗设置。' },
  app: { skip: '跳到查看区域', home: 'text-CAD 首页', nav: '房屋模型与图纸', language: '界面语言',
    title: '日本两层一户建', description: '查看日本两层一户建的参数化方案模型、平面图和可下载 CAD 文件。',
    tabs: { '3d': '三维模型', '1f': '一层平面', '2f': '二层平面', files: '文件下载' } },
  model: { region: '三维模型查看区域', title: '日本两层一户建', top: '俯视', reset: '重置视角',
    loadingViewer: '正在加载查看器…', loadingModel: '正在加载房屋模型…', selected: '已选部件', clear: '清除部件高亮',
    empty: '当前未显示部件，请勾选需要查看的部件。', gesture: '点选部件 · 拖动旋转 ·', wheel: '滚轮缩放', touch: '双指缩放',
    downloadGlb: '下载 GLB', canvas: '可旋转和缩放的房屋三维模型', fallback: '房屋模型静态预览',
    error: '当前浏览器无法显示交互模型。你仍可查看平面图或下载 GLB、STEP 文件。' },
  controls: { region: '模型控制', parts: '部件显示', cut: '剖切', enableCut: '启用剖切', height: '剖切高度', showFurniture: '显示家具', furnitureHelp: '床、沙发、桌椅与电视；不改变当前楼层和剖切高度。' },
  parameters: { title: '方案参数', units: '单位', millimetres: '毫米', outline: '外轮廓', storey: '层高', clearHeight: '净高', outlineArea: '外轮廓面积', interiorArea: '室内净面积合计', balconyArea: '阳台面积',
    note: '尺寸为演示假设。结构与管线尚未建模。' },
  groups: { F1: '一层', F2: '二层', stairs: '楼梯', roof: '屋顶', ceiling: '顶板', balcony: '阳台' },
  partKinds: { floor_slab: '楼板', external_walls: '外墙', partition_walls: '内隔墙', doors: '门', windows: '窗', storage_fixtures: '收纳柜', fixtures: '厨卫设备', furniture: '家具' },
  tree: { show: '显示{label}', collapse: '收起{label}部件', expand: '展开{label}部件', highlight: '高亮{label}',
    isolate: '单独查看{label}', alone: '单独', region: '{label}部件',
    help: '展开楼层可查看分类；点击名称高亮，使用“单独”查看部件。顶部视图按钮可恢复显示。' },
  presets: { region: '模型视图', exterior: '完整外观', first: '一层内部', second: '二层内部', interior: '室内剖视' },
  rooms: { ldk: 'LDK', bath: '浴室', wash: '洗面・脱衣室', pantry: '食品储藏室', foyer: '玄关', wc: '厕所',
    hall: '走廊', stairs: '楼梯', master: '主卧', bed2: '卧室 2', bed3: '卧室 3', storage: '储藏室', balcony: '阳台' },
  plan: { sidebar: '{floor}层图纸资料', viewer: '{floor}层平面图查看区域', title: '{floor}层平面图',
    details: 'A3 横向 · 1:50 · 单位 mm', downloadDxf: '下载 DXF', openPdf: '打开两层 PDF 图纸',
    originalNote: '原始 CAD、PDF 和矢量图纸保留日文标注；下方房间表随界面语言切换。',
    areaTitle: '房间净面积', room: '房间', areaNote: '墙内净面积，含家具占地。楼梯项为梯间预留面积。',
    range: '图纸显示范围', planOnly: '只看平面', fullSheet: '完整图框', zoomOut: '缩小平面图', zoom: '平面图缩放比例',
    zoomIn: '放大平面图', fit: '适合页面', error: '矢量图纸预览无法加载，请下载 DXF 或打开 PDF。', loading: '正在加载矢量图纸…',
    previewPlan: '{floor}层平面图，日文矢量预览；包含房间名、净尺寸、面积、门号和两向7280毫米外轮廓尺寸。可切换完整图框查看面积表和假设说明。',
    previewSheet: '{floor}层完整 A3 日文矢量图纸；包含房间名、净尺寸、面积、门号、两向7280毫米外轮廓尺寸、图框、表题栏、面积表和假设说明。' },
  downloads: { title: '文件下载', revision: '当前图纸 {drawing} · 三维模型 {model}', download: '下载', source: '参数化 Python 源码',
    notes: '方案说明', assumptionsTitle: '全部方案假设',
    originalNote: '原始 CAD、PDF 和矢量图纸保留日文标注；查看器界面和房间表支持中文、日文、英文。',
    summary: '7280 × 7280 mm 外轮廓及 2800 mm 层高是演示假设。当前模型用于方案查看，结构、墙体层次、设备管线及实际楼梯净空尚待深化。',
    drafting: '平面图采用東京都建設局 CAD 製图基准的共通项目用于住宅方案，保留可编辑标注；本次输出包含 DXF、STEP、GLB、PDF，未包含 SXF 电子纳品。',
    files: {
      glb: { title: 'GLB 三维模型', detail: '保留楼层与部件名称，可用于 Blender、Three.js。' },
      step: { title: 'STEP 精确实体', detail: '毫米制实体，可在 CAD 软件中继续编辑。' },
      first: { title: '一层平面', detail: '日文房间名与原生尺寸可编辑，包含 A3 纸空间。' },
      second: { title: '二层平面', detail: '日文房间名与原生尺寸可编辑，包含 A3 纸空间。' },
      pdf: { title: '两层 A3 图纸', detail: '日文图纸，1:50、A3 横向；打印选择实际尺寸。' },
      manifest: { title: '方案参数与假设', detail: '记录演示尺寸、房间净面积和待定项。' },
    } },
  assumptions: [...plan.assumptions, ...model.assumptions],
};

type Strings<T> = T extends string ? string : T extends readonly string[] ? readonly string[] : { [K in keyof T]: Strings<T[K]> };
export type Messages = Strings<typeof zh>;

const ja: Messages = {
  models: { label: '間取りプラン', house: '日本の2階建て戸建住宅', apartment: '日本のマンション 2LDK · 約65㎡', note: 'すべての寸法はデモ用の仮定です' },
  theme: { label: '表示モード', system: '自動', light: 'ライト', dark: 'ダーク', help: '自動を選ぶと端末の明暗設定に連動します。' },
  app: { skip: '閲覧エリアへ移動', home: 'text-CAD ホーム', nav: '住宅モデルと図面', language: '表示言語',
    title: '日本の2階建て戸建住宅', description: '日本の2階建て戸建住宅のパラメトリックな計画モデル、平面図、CADファイルを閲覧できます。',
    tabs: { '3d': '3Dモデル', '1f': '1階平面図', '2f': '2階平面図', files: 'ダウンロード' } },
  model: { region: '3Dモデル閲覧エリア', title: '日本の2階建て戸建住宅', top: '上面図', reset: '視点をリセット',
    loadingViewer: 'ビューアを読み込み中…', loadingModel: '住宅モデルを読み込み中…', selected: '選択中の部材', clear: '部材の強調表示を解除',
    empty: '表示中の部材がありません。閲覧したい部材を選択してください。', gesture: '部材を選択 · ドラッグで回転 ·', wheel: 'ホイールで拡大・縮小', touch: '2本指で拡大・縮小',
    downloadGlb: 'GLBをダウンロード', canvas: '回転・拡大・縮小できる住宅の3Dモデル', fallback: '住宅モデルの静止画プレビュー',
    error: 'このブラウザでは3Dモデルを表示できません。平面図の閲覧やGLB・STEPファイルのダウンロードは可能です。' },
  controls: { region: 'モデル操作', parts: '部材の表示', cut: '水平断面', enableCut: '水平断面を有効にする', height: '切断高さ', showFurniture: '家具を表示', furnitureHelp: 'ベッド・ソファ・テーブル・椅子・テレビ。表示階と断面高さは維持します。' },
  parameters: { title: '計画パラメータ', units: '単位', millimetres: 'ミリメートル', outline: '外形寸法', storey: '階高', clearHeight: '天井高', outlineArea: '外形面積', interiorArea: '室内有効面積の合計', balconyArea: 'バルコニー面積',
    note: '寸法はデモ用の仮定です。構造・設備配管は未モデル化です。' },
  groups: { F1: '1階', F2: '2階', stairs: '階段', roof: '屋根', ceiling: '天井スラブ', balcony: 'バルコニー' },
  partKinds: { floor_slab: '床スラブ', external_walls: '外壁', partition_walls: '間仕切り壁', doors: '建具・扉', windows: '窓', storage_fixtures: '収納家具', fixtures: '住宅設備', furniture: '家具' },
  tree: { show: '{label}を表示', collapse: '{label}の部材を折りたたむ', expand: '{label}の部材を展開', highlight: '{label}を強調表示',
    isolate: '{label}のみ表示', alone: '単独', region: '{label}の部材',
    help: '階を展開すると分類を表示します。名称を選択して強調表示、「単独」でその部材だけを表示できます。上部の表示切替で全体表示に戻せます。' },
  presets: { region: 'モデルの表示切替', exterior: '建物全体', first: '1階内部', second: '2階内部', interior: '室内断面' },
  rooms: { ldk: 'LDK', bath: '浴室', wash: '洗面・脱衣室', pantry: '食品庫', foyer: '玄関', wc: 'トイレ',
    hall: '廊下', stairs: '階段', master: '主寝室', bed2: '洋室 2', bed3: '洋室 3', storage: '納戸', balcony: 'バルコニー' },
  plan: { sidebar: '{floor}階の図面情報', viewer: '{floor}階平面図の閲覧エリア', title: '{floor}階平面図',
    details: 'A3 横 · 1:50 · 単位 mm', downloadDxf: 'DXFをダウンロード', openPdf: '2階分のPDF図面を開く',
    originalNote: '元のCAD・PDF・ベクトル図面は日本語表記のままです。下の室名一覧は表示言語に連動します。',
    areaTitle: '室内の有効面積', room: '室名', areaNote: '壁内側の有効面積で、家具の占有面積を含みます。階段の数値は階段室の確保面積です。',
    range: '図面の表示範囲', planOnly: '平面図のみ', fullSheet: '図面全体', zoomOut: '平面図を縮小', zoom: '平面図の表示倍率',
    zoomIn: '平面図を拡大', fit: '画面に合わせる', error: 'ベクトル図面を読み込めません。DXFをダウンロードするか、PDFを開いてください。', loading: 'ベクトル図面を読み込み中…',
    previewPlan: '{floor}階平面図の日本語ベクトルプレビュー。室名、有効寸法、面積、建具番号、縦横7280ミリメートルの外形寸法を含みます。図面全体に切り替えると面積表と仮定条件を確認できます。',
    previewSheet: '{floor}階のA3日本語ベクトル図面全体。室名、有効寸法、面積、建具番号、縦横7280ミリメートルの外形寸法、図枠、表題欄、面積表、仮定条件を含みます。' },
  downloads: { title: 'ファイルのダウンロード', revision: '図面 {drawing} · 3Dモデル {model}', download: 'ダウンロード', source: 'パラメトリックPythonソース',
    notes: '計画の説明', assumptionsTitle: 'すべての仮定条件',
    originalNote: '元のCAD・PDF・ベクトル図面は日本語表記のままです。ビューアの操作画面と室名一覧は中国語・日本語・英語に対応しています。',
    summary: '外形7280 × 7280 mm、階高2800 mmはデモ用の仮定です。モデルは計画の閲覧用であり、構造、壁の層構成、設備配管、階段の実際の頭上空間は今後の詳細検討が必要です。',
    drafting: '住宅計画に東京都建設局CAD製図基準の共通項目を適用し、編集可能な注記を保持しています。出力はDXF・STEP・GLB・PDFで、SXFによる電子納品は含みません。',
    files: {
      glb: { title: 'GLB 3Dモデル', detail: '階・部材名を保持。BlenderやThree.jsで利用できます。' },
      step: { title: 'STEP 精密ソリッド', detail: 'ミリメートル単位のソリッド。CADソフトで引き続き編集できます。' },
      first: { title: '1階平面図', detail: '日本語の室名・ネイティブ寸法を編集可能。A3ペーパー空間を含みます。' },
      second: { title: '2階平面図', detail: '日本語の室名・ネイティブ寸法を編集可能。A3ペーパー空間を含みます。' },
      pdf: { title: '2階分のA3図面', detail: '日本語図面、縮尺1:50・A3横。印刷時は実際のサイズを選択してください。' },
      manifest: { title: '計画パラメータと仮定条件', detail: 'デモ寸法、室内有効面積、未確定事項を記録しています。' },
    } },
  assumptions: [
    '外形7280 × 7280 mm、階高2800 mmはユーザー指定のデモ用仮定です。',
    '図面の北方向と南側玄関は表示用の仮定です。敷地・道路・現地資料は未提供です。',
    '外壁180 mm、内壁100 mm、建具・窓・家具寸法は計画上の仮寸法です。',
    '階段は16段の蹴上げ×175 mm、踏面260 mm、階段幅・中間踊り場900 mmです。',
    '室面積は壁内側の有効境界から算出し、家具占有面積を含みます。廊下面積に階段は含みません。',
    '階段面積は階段室の確保面積です。2階は床開口を含み、使用可能な床面積として扱えません。',
    '引き戸は壁内に収納する表現です。戸袋構造・枠厚は今後検討し、製品は未選定です。',
    '2階トイレ900 × 1700 mmはコンパクトです。700 mmの建具開口は平面上の寸法で、枠厚を差し引いていません。',
    '階高は各階基準面間の距離です。床スラブ・梁・仕上げ面は未設計です。',
    '切妻屋根の勾配・軒・窓台・建具高さは3D段階でデモ用パラメータを採用し、別途記録しています。',
    '構造・設備・防火・法規上の面積・階段の実際の頭上空間は未検証です。',
    'ユーザー確認済みのR01平面配置に従ってSTEP・GLBを生成しています。',
    '外形7280 × 7280 mm、階高2800 mm、北方向・南側玄関はデモ用の仮定です。',
    '確認済みR01の室内有効境界と建具・窓の平面位置を直接利用。1・2階トイレは上下で一致します。',
    '床仕上げ基準はZ=0・2800 mm。仮の床スラブ厚200 mmは仕上げ面下に配置し、壁の有効高さは2600 mmです。',
    '2階床は階段室全体1900 × 2720 mmを開口とし、階段を覆いません。屋根下に厚200 mmの概念上の天井スラブを設けています。',
    '建具開口高さ2100 mm、扉厚36 mm。閉位置で表示し、左右・上下に10 mmの仮の隙間を設けています。',
    '幅1000 mm超の大窓は窓台900 mm・窓高さ1300 mm。その他は窓台1500 mm・窓高さ600 mmです。',
    '窓枠見付45 mm・奥行70 mm、ガラス厚10 mm。建具・窓は未選定で、開口は下地開口寸法です。',
    '切妻屋根の棟は南北方向。勾配30度、全周軒450 mm、鉛直厚150 mmは変更可能なパラメータです。',
    '折り返し階段は16段の蹴上げ×175 mm、踏面260 mm、幅900 mm、中間踊り場奥行900 mm。各半階は7踏面と踊り場・2階床を8段目とします。',
    '階段は概念的な階段状ソリッドです。踊り場厚200 mm、上段の底面を踊り場底面と合わせて接触させています。2階床開口南端が最終蹴上げとなり、踏面を狭める追加板は設けていません。',
    '下駄箱高さ1800 mm、その他の収納家具2100 mm。配置は確認済み平面に従い、家具・住宅設備は公開寸法を参考にした独自のパラメトリック形状です。実製品は未選定です。',
    '引き戸の戸袋・階段手すり・構造接合・屋根と壁の層構成・設備システムは今後の詳細検討事項です。',
    '構造・防火・建築法規・階段の実際の頭上空間・建築確認申請要件は未検証です。',
  ],
};

const en: Messages = {
  models: { label: 'Layout', house: 'Japanese two-storey house', apartment: 'Japanese apartment 2LDK · approx. 65 m²', note: 'All plan dimensions are demonstration assumptions' },
  theme: { label: 'Color mode', system: 'Auto', light: 'Light', dark: 'Dark', help: 'Auto follows your device’s light or dark appearance.' },
  app: { skip: 'Skip to viewer', home: 'text-CAD home', nav: 'House model and drawings', language: 'Interface language',
    title: 'Japanese two-storey house', description: 'Explore a parametric concept model, floor plans and downloadable CAD files for a Japanese two-storey house.',
    tabs: { '3d': '3D model', '1f': 'First-floor plan', '2f': 'Second-floor plan', files: 'Downloads' } },
  model: { region: '3D model viewer', title: 'Japanese two-storey house', top: 'Top view', reset: 'Reset view',
    loadingViewer: 'Loading viewer…', loadingModel: 'Loading house model…', selected: 'Selected component', clear: 'Clear component highlight',
    empty: 'No components are visible. Select the components you want to view.', gesture: 'Select a component · Drag to rotate ·', wheel: 'Scroll to zoom', touch: 'Pinch to zoom',
    downloadGlb: 'Download GLB', canvas: 'House 3D model with rotation and zoom controls', fallback: 'Static house model preview',
    error: 'This browser cannot display the interactive model. You can still view the floor plans or download the GLB and STEP files.' },
  controls: { region: 'Model controls', parts: 'Component visibility', cut: 'Cutaway', enableCut: 'Enable cutaway', height: 'Cut height', showFurniture: 'Furniture', furnitureHelp: 'Beds, sofas, tables, chairs and TVs. Keeps the current floor and cut height.' },
  parameters: { title: 'Concept parameters', units: 'Units', millimetres: 'Millimetres', outline: 'Building outline', storey: 'Storey height', clearHeight: 'Clear height', outlineArea: 'Outline area', interiorArea: 'Total net interior area', balconyArea: 'Balcony area',
    note: 'Dimensions are demonstration assumptions. Structure and services have not been modelled.' },
  groups: { F1: 'First floor', F2: 'Second floor', stairs: 'Stairs', roof: 'Roof', ceiling: 'Ceiling slab', balcony: 'Balcony' },
  partKinds: { floor_slab: 'Floor slab', external_walls: 'External walls', partition_walls: 'Partitions', doors: 'Doors', windows: 'Windows', storage_fixtures: 'Storage cabinets', fixtures: 'Kitchen and bathroom fixtures', furniture: 'Furniture' },
  tree: { show: 'Show {label}', collapse: 'Collapse {label} components', expand: 'Expand {label} components', highlight: 'Highlight {label}',
    isolate: 'View only {label}', alone: 'Only', region: '{label} components',
    help: 'Expand a floor to see its categories. Select a name to highlight it, or use “Only” to isolate it. The view presets above restore the display.' },
  presets: { region: 'Model views', exterior: 'Whole house', first: 'First-floor interior', second: 'Second-floor interior', interior: 'Interior cutaway' },
  rooms: { ldk: 'Living / dining / kitchen', bath: 'Bathroom', wash: 'Washroom / changing room', pantry: 'Pantry', foyer: 'Entrance', wc: 'Toilet',
    hall: 'Hallway', stairs: 'Stairs', master: 'Main bedroom', bed2: 'Bedroom 2', bed3: 'Bedroom 3', storage: 'Storeroom', balcony: 'Balcony' },
  plan: { sidebar: 'Floor {floor} drawing information', viewer: 'Floor {floor} plan viewer', title: 'Floor {floor} plan',
    details: 'A3 landscape · 1:50 · Units mm', downloadDxf: 'Download DXF', openPdf: 'Open both floors as PDF',
    originalNote: 'The original CAD, PDF and vector drawings retain Japanese annotations. The room table below follows the interface language.',
    areaTitle: 'Net room areas', room: 'Room', areaNote: 'Net areas inside walls, including furniture footprints. The stairs entry is the reserved stairwell area.',
    range: 'Drawing view', planOnly: 'Plan only', fullSheet: 'Full sheet', zoomOut: 'Zoom out of plan', zoom: 'Plan zoom level',
    zoomIn: 'Zoom into plan', fit: 'Fit to page', error: 'The vector preview could not be loaded. Download the DXF or open the PDF.', loading: 'Loading vector drawing…',
    previewPlan: 'Floor {floor} plan, a Japanese vector preview with room names, clear dimensions, areas, door numbers and a 7280-millimetre outline in both directions. Switch to the full sheet for the area schedule and assumptions.',
    previewSheet: 'Floor {floor} full A3 Japanese vector drawing with room names, clear dimensions, areas, door numbers, a 7280-millimetre outline in both directions, drawing frame, title block, area schedule and assumptions.' },
  downloads: { title: 'File downloads', revision: 'Drawings {drawing} · 3D model {model}', download: 'Download', source: 'Parametric Python source',
    notes: 'Concept notes', assumptionsTitle: 'All design assumptions',
    originalNote: 'The original CAD, PDF and vector drawings retain Japanese annotations. Viewer controls and room tables support Chinese, Japanese and English.',
    summary: 'The 7280 × 7280 mm outline and 2800 mm storey height are demonstration assumptions. This model is for concept review; structure, wall layers, building services and actual stair headroom need further design.',
    drafting: 'The residential concept uses the common provisions of the Tokyo Metropolitan Government Bureau of Construction CAD drafting standard and retains editable annotations. Outputs include DXF, STEP, GLB and PDF; SXF electronic submission is not included.',
    files: {
      glb: { title: 'GLB 3D model', detail: 'Retains floor and component names for use in Blender and Three.js.' },
      step: { title: 'STEP exact solids', detail: 'Millimetre-based solids for further editing in CAD software.' },
      first: { title: 'First-floor plan', detail: 'Editable Japanese room names and native dimensions, with A3 paper space.' },
      second: { title: 'Second-floor plan', detail: 'Editable Japanese room names and native dimensions, with A3 paper space.' },
      pdf: { title: 'Both floors on A3 sheets', detail: 'Japanese drawings, 1:50, A3 landscape. Print at actual size.' },
      manifest: { title: 'Parameters and assumptions', detail: 'Records demonstration dimensions, net room areas and unresolved details.' },
    } },
  assumptions: [
    'The 7280 × 7280 mm outline and 2800 mm storey height are user-specified demonstration assumptions.',
    'Drawing north and the south entrance are display assumptions. Site, road and survey information has not been supplied.',
    'The 180 mm external walls, 100 mm partitions, door/window dimensions and furniture dimensions are concept placeholders.',
    'The stairs have 16 risers × 175 mm, 260 mm treads, a 900 mm flight width and a 900 mm intermediate landing.',
    'Room areas use clear boundaries inside walls and include furniture footprints. Hallway areas exclude the stairs.',
    'The stairs area is reserved stairwell space. The second floor includes a slab opening and must not be counted as usable floor area.',
    'Sliding doors are shown retracting into walls. Pocket construction and frame thickness need further design; products have not been selected.',
    'The second-floor toilet is compact at 900 × 1700 mm. Its 700 mm door opening is a plan dimension before frame allowances.',
    'Storey height is the distance between floor datums. Slabs, beams and finished surfaces have not been designed.',
    'Demonstration roof pitch, eaves, window sills and door/window heights were adopted at the 3D stage and recorded separately.',
    'Structure, services, fire safety, legally defined areas and actual stair headroom have not been verified.',
    'The user approved the R01 floor layout; STEP and GLB were generated from that layout.',
    'The 7280 × 7280 mm outline, 2800 mm storey height, north direction and south entrance are demonstration assumptions.',
    'Approved R01 clear room boundaries and door/window plan positions are reused directly. Toilets align between the two floors.',
    'Finished-floor datums are Z=0 and 2800 mm. The provisional 200 mm slabs sit below the finished floors; clear wall height is 2600 mm.',
    'The second-floor slab has an opening across the full 1900 × 2720 mm stairwell and does not cover the stairs. A 200 mm concept ceiling slab is provided below the roof.',
    'Door openings are 2100 mm high with 36 mm leaves, shown closed with illustrative 10 mm gaps on the sides and at the top and bottom.',
    'Large windows wider than 1000 mm have 900 mm sills and 1300 mm height. Other windows have 1500 mm sills and 600 mm height.',
    'Window frames are 45 mm wide and 70 mm deep, with 10 mm glass. Door/window products are unselected; dimensions describe rough openings.',
    'The gable roof ridge runs north–south. Its 30-degree pitch, 450 mm eaves on all sides and 150 mm vertical thickness are editable parameters.',
    'The U-shaped stair has 16 risers × 175 mm, 260 mm treads, 900 mm width and a 900 mm-deep landing. Each half flight has seven treads, with the landing or second-floor surface forming the eighth level.',
    'The stairs use concept stepped solids. The landing is 200 mm thick; the upper flight bottom meets the landing bottom. The south slab-opening edge forms the final riser, without an added panel reducing tread depth.',
    'The shoe cabinet is 1800 mm high and other storage cabinets are 2100 mm high. Positions follow the approved plan; furniture and fixtures are original parametric shapes informed by public dimensions, not selected manufacturer products.',
    'Sliding-door pockets, stair handrails, structural joints, roof/wall layers and service systems need further design.',
    'Structure, fire safety, building regulations, actual stair headroom and building-confirmation application requirements have not been verified.',
  ],
};

export const messages: Record<Locale, Messages> = { zh, ja, en };

export function selectionLabel(copy: Messages, id: ModelPartId): string {
  if (!id.includes(':')) return copy.groups[id as GroupId];
  const [floor, kind] = id.split(':') as ['F1' | 'F2', PartKind];
  return `${copy.groups[floor]} · ${copy.partKinds[kind]}`;
}
export function roomLabel(copy: Messages, id: string): string {
  return copy.rooms[id as keyof Messages['rooms']] ?? id;
}
