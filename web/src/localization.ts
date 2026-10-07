import { houseAssumptions } from './house-assumptions.ts';
import plan from '../../output/review/design_manifest.json' with { type: 'json' };
import model from '../../output/review/house_3d_assumptions_R01.json' with { type: 'json' };
import type { GroupId, ModelPartId, PartGroupId, PartKind } from './model-state';

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
  sceneLighting: { label: '模型昼夜', day: '白天', night: '夜晚', outdoor: '室外灯光', help: '模型昼夜独立于页面颜色模式。', fixtureHelp: '夜晚时为可见的室外灯具点灯；在部件树中可分别隐藏灯具。' },
  theme: { label: '颜色模式', system: '系统', light: '浅色', dark: '深色', help: '选择系统可跟随设备的明暗设置。' },
  app: { skip: '跳到查看区域', home: 'text-CAD 首页', nav: '房屋模型与图纸', language: '界面语言',
    title: '日本两层一户建', description: '查看日本两层一户建的参数化方案模型、平面图和可下载 CAD 文件。',
    tabs: { '3d': '三维模型', '1f': '一层平面', '2f': '二层平面', files: '文件下载' } },
  model: { region: '三维模型查看区域', title: '日本两层一户建', top: '俯视', reset: '重置视角',
    atticNote: '储物阁楼最高净高 1350 mm，为演示假设。检修梯仅表示展开状态，会占用二层走廊；可单独隐藏。法定面积与所在地用途认定待核定。',
    structureNote: '木造结构布置演示：柱、梁、土台、阁楼搁栅与开口边梁、屋架及候选承重墙。截面、荷载、连接件和基础承载尚未计算；候选墙不表示抗震等级。', demoNote: '演示方案 · 结构布置未计算；所在地、地盘、法定面积及确认申请待核定。',
    loadingViewer: '正在加载查看器…', loadingModel: '正在加载房屋模型…', loadingProgress: '正在下载模型：{amount}…', retry: '重新加载模型', selected: '已选部件', clear: '清除部件高亮',
    empty: '当前未显示部件，请勾选需要查看的部件。', gesture: '点选部件 · 拖动旋转 ·', wheel: '滚轮缩放', touch: '双指缩放',
    downloadGlb: '下载 GLB', canvas: '可旋转和缩放的房屋三维模型', fallback: '房屋模型静态预览',
    error: '模型未能加载或显示，请重试。你仍可查看平面图或下载 GLB、STEP 文件。' },
  controls: { region: '模型控制', parts: '部件显示', cut: '剖切', enableCut: '启用剖切', height: '剖切高度', showFurniture: '显示家具', furnitureHelp: '床、沙发、桌椅与电视；不改变当前楼层和剖切高度。' },
  parameters: { title: '方案参数', units: '单位', millimetres: '毫米', outline: '外轮廓', storey: '层高', clearHeight: '净高', outlineArea: '外轮廓面积', interiorArea: '室内净面积合计', balconyArea: '阳台面积',
    note: '尺寸与结构截面均为演示假设。荷载、连接件、地基承载与法规用途待核定。' },
  groups: { structure: '结构方案', F1: '一层', F2: '二层', attic: '储物阁楼', attic_access: '阁楼检修梯（展开）', stairs: '楼梯', roof: '屋顶', foundation: '建筑基础', yard: '院子', fence: '围栏', lighting: '室外灯具', ceiling: '顶板', balcony: '阳台' },
  partKinds: { columns: '柱', beams: '梁', sills: '土台', attic_joists: '阁楼搁栅', attic_headers: '阁楼开口边梁', roof_framing: '屋架', bearing_walls: '候选承重墙', existing_plinth: '周圈基座', internal_supports: '内部基础支承', floor_slab: '楼板', external_walls: '外墙', partition_walls: '内隔墙', doors: '门', windows: '窗', storage_fixtures: '收纳柜', fixtures: '厨卫设备', furniture: '家具', guardrails: '防护栏',
    raft: '基础底板', stem_walls: '基础立上墙', entrance_supports: '玄关支承', soil: '场地土层', ground_surfaces: '砾石地面', entrance_path: '入户步道', parking: '停车位', planting: '绿化', posts: '围栏立柱', panels: '围栏面板', footings: '围栏独立基础', wall: '外墙灯', path: '步道灯', garden: '庭院灯', gate: '门口灯' },
  tree: { show: '显示{label}', collapse: '收起{label}部件', expand: '展开{label}部件', highlight: '高亮{label}',
    search: '搜索部件', expandAll: '全部展开', collapseAll: '全部折叠', clearSearch: '清除搜索', noResults: '没有匹配的部件。', searchHelp: '搜索仅筛选部件列表，不改变模型显示；楼层勾选仍作用于整个楼层。',
    isolate: '单独查看{label}', alone: '单独', region: '{label}部件',
    help: '展开楼层或外构可查看分类；点击名称高亮，使用“单独”查看部件。顶部视图按钮可恢复显示。' },
  presets: { structure: '结构方案', region: '模型视图', exterior: '完整外观', first: '一层内部', second: '二层内部', attic: '阁楼内部', interior: '室内剖视' },
  rooms: { ldk: 'LDK', bath: '浴室', wash: '洗面・脱衣室', pantry: '食品储藏室', foyer: '玄关', wc: '厕所',
    hall: '走廊', stairs: '楼梯', master: '主卧', bed2: '卧室 2', bed3: '卧室 3', storage: '储藏室', closet: '衣柜收纳', wc_hall: '厕所前厅', balcony: '阳台' },
  plan: { sidebar: '{floor}层图纸资料', viewer: '{floor}层平面图查看区域', title: '{floor}层平面图',
    details: 'A3 横向 · 1:50 · 单位 mm', downloadDxf: '下载 DXF', openPdf: '打开两层 PDF 图纸',
    originalNote: '原始 CAD、PDF 和矢量图纸保留日文标注；下方房间表随界面语言切换。',
    areaTitle: '房间净面积', room: '房间', areaNote: '墙内净面积，含家具占地。楼梯项为梯间预留面积。',
    range: '图纸显示范围', planOnly: '只看平面', fullSheet: '完整图框', zoomOut: '缩小平面图', zoom: '平面图缩放比例',
    zoomIn: '放大平面图', fit: '适合页面', error: '矢量图纸预览无法加载，请下载 DXF 或打开 PDF。', loading: '正在加载矢量图纸…',
    previewPlan: '{floor}层平面图，日文矢量预览；包含房间名、净尺寸、面积、门号和8190 × 7280毫米外轮廓尺寸。可切换完整图框查看面积表和假设说明。',
    previewSheet: '{floor}层完整 A3 日文矢量图纸；包含房间名、净尺寸、面积、门号、8190 × 7280毫米外轮廓尺寸、图框、表题栏、面积表和假设说明。' },
  downloads: { title: '文件下载', revision: '当前图纸 {drawing} · 三维模型 {model}', download: '下载', sourceParameters: '阁楼与结构参数源码', source: '参数化 Python 源码',
    notes: '方案说明', assumptionsTitle: '全部方案假设',
    originalNote: '原始 CAD、PDF 和矢量图纸保留日文标注；查看器界面和房间表支持中文、日文、英文。',
    summary: '8190 × 7280 mm 外轮廓及 2800 mm 层高是演示假设。当前模型用于方案查看，结构、墙体层次、设备管线及实际楼梯净空尚待深化。',
    drafting: '平面图采用東京都建設局 CAD 製图基准的共通项目用于住宅方案，保留可编辑标注；本次输出包含 DXF、STEP、GLB、PDF，未包含 SXF 电子纳品。',
    files: {
      engineeringSource: { title: '结构与法规输入 Python 源码', detail: '可编辑的演示设计任务书；待核定输入保留为空值。' },
      engineering: { title: '结构与法规待定输入', detail: 'R13 演示参数、结构计算所需输入和所在地待核定项；不包含已完成计算。' },
      structure: { title: '可编辑结构布置方案', detail: '日文柱梁、搁栅、开口边梁和基础支承示意；截面与承载尚未计算。' },
      structurePdf: { title: '结构布置方案 PDF', detail: 'R10 补充图，标明结构方案、演示截面及待核定项目。' },
      glb: { title: 'GLB 三维模型', detail: '保留楼层与部件名称，可用于 Blender、Three.js。' },
      step: { title: 'STEP 精确实体', detail: '毫米制实体，可在 CAD 软件中继续编辑。' },
      first: { title: '一层平面', detail: '日文房间名与原生尺寸可编辑，包含 A3 纸空间。' },
      second: { title: '二层平面', detail: '日文房间名与原生尺寸可编辑，包含 A3 纸空间。' },
      attic: { title: '阁楼可编辑平面图', detail: '日文标注的储物阁楼、检修口、收纳和净高；尺寸均为演示假设。' },
      atticPdf: { title: '阁楼补充平面 PDF', detail: '独立 A3 日文补充图，包含阁楼净高与检修梯展开说明。' },
      site: { title: '院子与基础可编辑配置图', detail: '日文标注的用地、围栏、入户步道、停车位、基础与标高；尺寸均为演示假设。' },
      sitePdf: { title: '外构与基础补充 PDF', detail: '独立 A3 日文补充图，包含场地配置、基础及入口标高说明。' },
      pdf: { title: '两层 A3 图纸', detail: '日文图纸，1:50、A3 横向；打印选择实际尺寸。' },
      manifest: { title: '方案参数与假设', detail: '记录演示尺寸、房间净面积和待定项。' },
    } },
  assumptions: houseAssumptions.zh,
};

type Strings<T> = T extends string ? string : T extends readonly string[] ? readonly string[] : { [K in keyof T]: Strings<T[K]> };
export type Messages = Strings<typeof zh>;

const ja: Messages = {
  models: { label: '間取りプラン', house: '日本の2階建て戸建住宅', apartment: '日本のマンション 2LDK · 約65㎡', note: 'すべての寸法はデモ用の仮定です' },
  sceneLighting: { label: 'モデルの昼夜', day: '昼', night: '夜', outdoor: '屋外照明', help: 'モデルの昼夜はページの表示モードとは別に切り替えます。', fixtureHelp: '夜は表示中の屋外灯を点灯します。器具は部材ツリーで個別に非表示にできます。' },
  theme: { label: '表示モード', system: '自動', light: 'ライト', dark: 'ダーク', help: '自動を選ぶと端末の明暗設定に連動します。' },
  app: { skip: '閲覧エリアへ移動', home: 'text-CAD ホーム', nav: '住宅モデルと図面', language: '表示言語',
    title: '日本の2階建て戸建住宅', description: '日本の2階建て戸建住宅のパラメトリックな計画モデル、平面図、CADファイルを閲覧できます。',
    tabs: { '3d': '3Dモデル', '1f': '1階平面図', '2f': '2階平面図', files: 'ダウンロード' } },
  model: { region: '3Dモデル閲覧エリア', title: '日本の2階建て戸建住宅', top: '上面図', reset: '視点をリセット',
    atticNote: '収納用小屋裏の最高内法高さ1350 mmはデモ用の仮定です。点検はしごは展開状態のみを表し、2階廊下を占有します。個別に非表示にできます。法定面積と所在地での用途認定は未確定です。',
    structureNote: '木造の構造配置デモ：柱・梁・土台・小屋裏根太・開口補強梁・小屋組・耐力壁候補。断面・荷重・接合・基礎支持力は未計算で、候補壁は耐震等級を示しません。', demoNote: 'デモプラン · 構造配置は未計算。所在地・地盤・法定面積・建築確認は未確定です。',
    loadingViewer: 'ビューアを読み込み中…', loadingModel: '住宅モデルを読み込み中…', loadingProgress: 'モデルをダウンロード中：{amount}…', retry: 'モデルを再読み込み', selected: '選択中の部材', clear: '部材の強調表示を解除',
    empty: '表示中の部材がありません。閲覧したい部材を選択してください。', gesture: '部材を選択 · ドラッグで回転 ·', wheel: 'ホイールで拡大・縮小', touch: '2本指で拡大・縮小',
    downloadGlb: 'GLBをダウンロード', canvas: '回転・拡大・縮小できる住宅の3Dモデル', fallback: '住宅モデルの静止画プレビュー',
    error: 'モデルを読み込みまたは表示できませんでした。再読み込みしてください。平面図の閲覧やGLB・STEPファイルのダウンロードも可能です。' },
  controls: { region: 'モデル操作', parts: '部材の表示', cut: '水平断面', enableCut: '水平断面を有効にする', height: '切断高さ', showFurniture: '家具を表示', furnitureHelp: 'ベッド・ソファ・テーブル・椅子・テレビ。表示階と断面高さは維持します。' },
  parameters: { title: '計画パラメータ', units: '単位', millimetres: 'ミリメートル', outline: '外形寸法', storey: '階高', clearHeight: '天井高', outlineArea: '外形面積', interiorArea: '室内有効面積の合計', balconyArea: 'バルコニー面積',
    note: '寸法と部材断面はデモ用の仮定です。荷重・接合・基礎支持力・法規上の用途は未確定です。' },
  groups: { structure: '構造案', F1: '1階', F2: '2階', attic: '小屋裏収納', attic_access: '小屋裏点検はしご（展開）', stairs: '階段', roof: '屋根', foundation: '建物基礎', yard: '庭', fence: 'フェンス', lighting: '屋外照明器具', ceiling: '天井スラブ', balcony: 'バルコニー' },
  partKinds: { columns: '柱', beams: '梁', sills: '土台', attic_joists: '小屋裏根太', attic_headers: '小屋裏開口補強梁', roof_framing: '小屋組', bearing_walls: '耐力壁候補', existing_plinth: '外周の基壇', internal_supports: '内部基礎支持部', floor_slab: '床スラブ', external_walls: '外壁', partition_walls: '間仕切り壁', doors: '建具・扉', windows: '窓', storage_fixtures: '収納家具', fixtures: '住宅設備', furniture: '家具', guardrails: '手すり',
    raft: '基礎底盤', stem_walls: '基礎立上り', entrance_supports: '玄関支持部', soil: '地盤層', ground_surfaces: '砂利敷き', entrance_path: '玄関アプローチ', parking: '駐車スペース', planting: '植栽', posts: 'フェンス支柱', panels: 'フェンスパネル', footings: 'フェンス独立基礎', wall: '外壁灯', path: 'アプローチ灯', garden: '庭園灯', gate: '門灯' },
  tree: { show: '{label}を表示', collapse: '{label}の部材を折りたたむ', expand: '{label}の部材を展開', highlight: '{label}を強調表示',
    search: '部材を検索', expandAll: 'すべて展開', collapseAll: 'すべて折りたたむ', clearSearch: '検索をクリア', noResults: '一致する部材がありません。', searchHelp: '検索は部材一覧だけを絞り込みます。モデル表示は変わりません。階のチェックは階全体に適用されます。',
    isolate: '{label}のみ表示', alone: '単独', region: '{label}の部材',
    help: '階や外構を展開すると分類を表示します。名称を選択して強調表示、「単独」でその部材だけを表示できます。上部の表示切替で全体表示に戻せます。' },
  presets: { structure: '構造案', region: 'モデルの表示切替', exterior: '建物全体', first: '1階内部', second: '2階内部', attic: '小屋裏内部', interior: '室内断面' },
  rooms: { ldk: 'LDK', bath: '浴室', wash: '洗面・脱衣室', pantry: '食品庫', foyer: '玄関', wc: 'トイレ',
    hall: '廊下', stairs: '階段', master: '主寝室', bed2: '洋室 2', bed3: '洋室 3', storage: '納戸', closet: '収納', wc_hall: 'トイレ前ホール', balcony: 'バルコニー' },
  plan: { sidebar: '{floor}階の図面情報', viewer: '{floor}階平面図の閲覧エリア', title: '{floor}階平面図',
    details: 'A3 横 · 1:50 · 単位 mm', downloadDxf: 'DXFをダウンロード', openPdf: '2階分のPDF図面を開く',
    originalNote: '元のCAD・PDF・ベクトル図面は日本語表記のままです。下の室名一覧は表示言語に連動します。',
    areaTitle: '室内の有効面積', room: '室名', areaNote: '壁内側の有効面積で、家具の占有面積を含みます。階段の数値は階段室の確保面積です。',
    range: '図面の表示範囲', planOnly: '平面図のみ', fullSheet: '図面全体', zoomOut: '平面図を縮小', zoom: '平面図の表示倍率',
    zoomIn: '平面図を拡大', fit: '画面に合わせる', error: 'ベクトル図面を読み込めません。DXFをダウンロードするか、PDFを開いてください。', loading: 'ベクトル図面を読み込み中…',
    previewPlan: '{floor}階平面図の日本語ベクトルプレビュー。室名、有効寸法、面積、建具番号、8190 × 7280ミリメートルの外形寸法を含みます。図面全体に切り替えると面積表と仮定条件を確認できます。',
    previewSheet: '{floor}階のA3日本語ベクトル図面全体。室名、有効寸法、面積、建具番号、8190 × 7280ミリメートルの外形寸法、図枠、表題欄、面積表、仮定条件を含みます。' },
  downloads: { title: 'ファイルのダウンロード', revision: '図面 {drawing} · 3Dモデル {model}', download: 'ダウンロード', sourceParameters: '小屋裏・構造パラメータのソース', source: 'パラメトリックPythonソース',
    notes: '計画の説明', assumptionsTitle: 'すべての仮定条件',
    originalNote: '元のCAD・PDF・ベクトル図面は日本語表記のままです。ビューアの操作画面と室名一覧は中国語・日本語・英語に対応しています。',
    summary: '外形8190 × 7280 mm、階高2800 mmはデモ用の仮定です。モデルは計画の閲覧用であり、構造、壁の層構成、設備配管、階段の実際の頭上空間は今後の詳細検討が必要です。',
    drafting: '住宅計画に東京都建設局CAD製図基準の共通項目を適用し、編集可能な注記を保持しています。出力はDXF・STEP・GLB・PDFで、SXFによる電子納品は含みません。',
    files: {
      engineeringSource: { title: '構造・法規入力の Python ソース', detail: '編集可能なデモ設計要件。未確定入力は空値のまま保持します。' },
      engineering: { title: '構造・法規の未確定入力', detail: 'R13の仮定、構造計算に必要な入力、所在地での未確定事項。計算済みの成果ではありません。' },
      structure: { title: '編集可能な構造配置案', detail: '柱梁・根太・開口補強梁・基礎支持部の日本語概念図。断面・耐荷力は未計算です。' },
      structurePdf: { title: '構造配置案 PDF', detail: 'R10補足図。構造案・仮断面・未確定事項を記載します。' },
      glb: { title: 'GLB 3Dモデル', detail: '階・部材名を保持。BlenderやThree.jsで利用できます。' },
      step: { title: 'STEP 精密ソリッド', detail: 'ミリメートル単位のソリッド。CADソフトで引き続き編集できます。' },
      first: { title: '1階平面図', detail: '日本語の室名・ネイティブ寸法を編集可能。A3ペーパー空間を含みます。' },
      second: { title: '2階平面図', detail: '日本語の室名・ネイティブ寸法を編集可能。A3ペーパー空間を含みます。' },
      attic: { title: '編集可能な小屋裏平面図', detail: '小屋裏収納・点検開口・収納・内法高さを日本語で表示。寸法はデモ用の仮定です。' },
      atticPdf: { title: '小屋裏補足平面図 PDF', detail: '独立したA3日本語補足図。内法高さと点検はしごの展開説明を含みます。' },
      site: { title: '編集可能な外構・基礎配置図', detail: '敷地・フェンス・玄関アプローチ・駐車場・基礎・高さを日本語で表示。寸法はデモ用の仮定です。' },
      sitePdf: { title: '外構・基礎補足図 PDF', detail: '独立したA3日本語補足図。敷地配置、基礎と入口の高さを説明します。' },
      pdf: { title: '2階分のA3図面', detail: '日本語図面、縮尺1:50・A3横。印刷時は実際のサイズを選択してください。' },
      manifest: { title: '計画パラメータと仮定条件', detail: 'デモ寸法、室内有効面積、未確定事項を記録しています。' },
    } },
  assumptions: houseAssumptions.ja,
};

const en: Messages = {
  models: { label: 'Layout', house: 'Japanese two-storey house', apartment: 'Japanese apartment 2LDK · approx. 65 m²', note: 'All plan dimensions are demonstration assumptions' },
  sceneLighting: { label: 'Model time of day', day: 'Day', night: 'Night', outdoor: 'Outdoor lights', help: 'Model time of day is independent of the page color mode.', fixtureHelp: 'Lights visible outdoor fixtures at night. Hide fixtures separately in the component tree.' },
  theme: { label: 'Color mode', system: 'Auto', light: 'Light', dark: 'Dark', help: 'Auto follows your device’s light or dark appearance.' },
  app: { skip: 'Skip to viewer', home: 'text-CAD home', nav: 'House model and drawings', language: 'Interface language',
    title: 'Japanese two-storey house', description: 'Explore a parametric concept model, floor plans and downloadable CAD files for a Japanese two-storey house.',
    tabs: { '3d': '3D model', '1f': 'First-floor plan', '2f': 'Second-floor plan', files: 'Downloads' } },
  model: { region: '3D model viewer', title: 'Japanese two-storey house', top: 'Top view', reset: 'Reset view',
    atticNote: 'Storage attic with a demonstration maximum clear height of 1350 mm. The ladder shows its deployed state and occupies the second-floor hall; hide it separately. Statutory area and local use classification remain pending.',
    structureNote: 'Timber structural layout demonstration: columns, beams, sills, attic joists, hatch headers, roof framing and candidate bearing walls. Member sizes, loads, connections and foundation capacity are uncalculated; wall candidates do not indicate a seismic rating.', demoNote: 'Demonstration concept · Structural layout is uncalculated. Site, soil, statutory area and building approval remain pending.',
    loadingViewer: 'Loading viewer…', loadingModel: 'Loading house model…', loadingProgress: 'Downloading model: {amount}…', retry: 'Reload model', selected: 'Selected component', clear: 'Clear component highlight',
    empty: 'No components are visible. Select the components you want to view.', gesture: 'Select a component · Drag to rotate ·', wheel: 'Scroll to zoom', touch: 'Pinch to zoom',
    downloadGlb: 'Download GLB', canvas: 'House 3D model with rotation and zoom controls', fallback: 'Static house model preview',
    error: 'The model could not load or display. Please try again. You can also view the floor plans or download the GLB and STEP files.' },
  controls: { region: 'Model controls', parts: 'Component visibility', cut: 'Cutaway', enableCut: 'Enable cutaway', height: 'Cut height', showFurniture: 'Furniture', furnitureHelp: 'Beds, sofas, tables, chairs and TVs. Keeps the current floor and cut height.' },
  parameters: { title: 'Concept parameters', units: 'Units', millimetres: 'Millimetres', outline: 'Building outline', storey: 'Storey height', clearHeight: 'Clear height', outlineArea: 'Outline area', interiorArea: 'Total net interior area', balconyArea: 'Balcony area',
    note: 'Dimensions and member sizes are demonstration assumptions. Loads, connections, foundation capacity and regulatory use remain pending.' },
  groups: { structure: 'Structural scheme', F1: 'First floor', F2: 'Second floor', attic: 'Attic storage', attic_access: 'Attic access ladder (deployed)', stairs: 'Stairs', roof: 'Roof', foundation: 'Building foundation', yard: 'Yard', fence: 'Fence', lighting: 'Outdoor light fixtures', ceiling: 'Ceiling slab', balcony: 'Balcony' },
  partKinds: { columns: 'Columns', beams: 'Beams', sills: 'Sills', attic_joists: 'Attic joists', attic_headers: 'Attic hatch headers', roof_framing: 'Roof framing', bearing_walls: 'Candidate bearing walls', existing_plinth: 'Perimeter plinth', internal_supports: 'Internal foundation supports', floor_slab: 'Floor slab', external_walls: 'External walls', partition_walls: 'Partitions', doors: 'Doors', windows: 'Windows', storage_fixtures: 'Storage cabinets', fixtures: 'Kitchen and bathroom fixtures', furniture: 'Furniture', guardrails: 'Guardrails',
    raft: 'Foundation slabs', stem_walls: 'Stem walls', entrance_supports: 'Entrance supports', soil: 'Soil layer', ground_surfaces: 'Gravel surface', entrance_path: 'Entrance path', parking: 'Parking space', planting: 'Planting', posts: 'Fence posts', panels: 'Fence panels', footings: 'Fence footings', wall: 'Wall lights', path: 'Path lights', garden: 'Garden lights', gate: 'Gate lights' },
  tree: { show: 'Show {label}', collapse: 'Collapse {label} components', expand: 'Expand {label} components', highlight: 'Highlight {label}',
    search: 'Search components', expandAll: 'Expand all', collapseAll: 'Collapse all', clearSearch: 'Clear search', noResults: 'No matching components.', searchHelp: 'Search filters the list only. Model visibility stays unchanged; floor checkboxes still apply to the whole floor.',
    isolate: 'View only {label}', alone: 'Only', region: '{label} components',
    help: 'Expand a floor or site group to see its categories. Select a name to highlight it, or use “Only” to isolate it. The view presets above restore the display.' },
  presets: { structure: 'Structural scheme', region: 'Model views', exterior: 'Whole house', first: 'First-floor interior', second: 'Second-floor interior', attic: 'Attic interior', interior: 'Interior cutaway' },
  rooms: { ldk: 'Living / dining / kitchen', bath: 'Bathroom', wash: 'Washroom / changing room', pantry: 'Pantry', foyer: 'Entrance', wc: 'Toilet',
    hall: 'Hallway', stairs: 'Stairs', master: 'Main bedroom', bed2: 'Bedroom 2', bed3: 'Bedroom 3', storage: 'Storeroom', closet: 'Closet', wc_hall: 'WC lobby', balcony: 'Balcony' },
  plan: { sidebar: 'Floor {floor} drawing information', viewer: 'Floor {floor} plan viewer', title: 'Floor {floor} plan',
    details: 'A3 landscape · 1:50 · Units mm', downloadDxf: 'Download DXF', openPdf: 'Open both floors as PDF',
    originalNote: 'The original CAD, PDF and vector drawings retain Japanese annotations. The room table below follows the interface language.',
    areaTitle: 'Net room areas', room: 'Room', areaNote: 'Net areas inside walls, including furniture footprints. The stairs entry is the reserved stairwell area.',
    range: 'Drawing view', planOnly: 'Plan only', fullSheet: 'Full sheet', zoomOut: 'Zoom out of plan', zoom: 'Plan zoom level',
    zoomIn: 'Zoom into plan', fit: 'Fit to page', error: 'The vector preview could not be loaded. Download the DXF or open the PDF.', loading: 'Loading vector drawing…',
    previewPlan: 'Floor {floor} plan, a Japanese vector preview with room names, clear dimensions, areas, door numbers and an 8190 × 7280-millimetre outline. Switch to the full sheet for the area schedule and assumptions.',
    previewSheet: 'Floor {floor} full A3 Japanese vector drawing with room names, clear dimensions, areas, door numbers, an 8190 × 7280-millimetre outline, drawing frame, title block, area schedule and assumptions.' },
  downloads: { title: 'File downloads', revision: 'Drawings {drawing} · 3D model {model}', download: 'Download', sourceParameters: 'Attic and structural parameter source', source: 'Parametric Python source',
    notes: 'Concept notes', assumptionsTitle: 'All design assumptions',
    originalNote: 'The original CAD, PDF and vector drawings retain Japanese annotations. Viewer controls and room tables support Chinese, Japanese and English.',
    summary: 'The 8190 × 7280 mm outline and 2800 mm storey height are demonstration assumptions. This model is for concept review; structure, wall layers, building services and actual stair headroom need further design.',
    drafting: 'The residential concept uses the common provisions of the Tokyo Metropolitan Government Bureau of Construction CAD drafting standard and retains editable annotations. Outputs include DXF, STEP, GLB and PDF; SXF electronic submission is not included.',
    files: {
      engineeringSource: { title: 'Structural and regulatory input Python source', detail: 'Editable demonstration design brief. Pending inputs remain null.' },
      engineering: { title: 'Pending structural and regulatory inputs', detail: 'R13 assumptions, inputs required for structural calculations and pending local decisions. No completed calculation is included.' },
      structure: { title: 'Editable structural layout scheme', detail: 'Japanese concept drawings of columns, beams, joists, hatch headers and foundation supports. Sizes and capacity are uncalculated.' },
      structurePdf: { title: 'Structural layout scheme PDF', detail: 'R10 supplementary drawing with the structural proposal, assumed sizes and pending verification items.' },
      glb: { title: 'GLB 3D model', detail: 'Retains floor and component names for use in Blender and Three.js.' },
      step: { title: 'STEP exact solids', detail: 'Millimetre-based solids for further editing in CAD software.' },
      first: { title: 'First-floor plan', detail: 'Editable Japanese room names and native dimensions, with A3 paper space.' },
      second: { title: 'Second-floor plan', detail: 'Editable Japanese room names and native dimensions, with A3 paper space.' },
      attic: { title: 'Editable attic plan', detail: 'Japanese annotations for attic storage, hatch, cabinets and clear heights; dimensions are demonstration assumptions.' },
      atticPdf: { title: 'Supplementary attic plan PDF', detail: 'A separate A3 Japanese drawing with attic clear heights and the deployed access-ladder note.' },
      site: { title: 'Editable yard and foundation layout', detail: 'Japanese annotations for the plot, fence, entrance path, parking, foundation and levels; all dimensions are demonstration assumptions.' },
      sitePdf: { title: 'Supplementary site and foundation PDF', detail: 'A separate A3 Japanese drawing showing the site layout, foundation and entrance levels.' },
      pdf: { title: 'Both floors on A3 sheets', detail: 'Japanese drawings, 1:50, A3 landscape. Print at actual size.' },
      manifest: { title: 'Parameters and assumptions', detail: 'Records demonstration dimensions, net room areas and unresolved details.' },
    } },
  assumptions: houseAssumptions.en,
};

export const messages: Record<Locale, Messages> = { zh, ja, en };

export function selectionLabel(copy: Messages, id: ModelPartId): string {
  if (!id.includes(':')) return copy.groups[id as GroupId];
  const [group, kind] = id.split(':') as [PartGroupId, PartKind];
  return `${copy.groups[group]} · ${copy.partKinds[kind]}`;
}
export function roomLabel(copy: Messages, id: string): string {
  return copy.rooms[id as keyof Messages['rooms']] ?? id;
}
