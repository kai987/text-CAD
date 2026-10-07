import type { Locale } from './localization';
import type { ModelPartId, ModelSettings } from './model-state';

export const designCities = ['tokyo', 'osaka', 'kyoto', 'nagoya'] as const;
export const structuralSystems = ['W', 'S', 'RC'] as const;
export type DesignCity = typeof designCities[number];
export type StructuralSystem = typeof structuralSystems[number];
export interface StructuralDesign { city: DesignCity; system: StructuralSystem }
export type LocalizedText = Record<Locale, string>;
export interface RegulatorySource { id: string; title: LocalizedText | string; url: string }
export interface ReviewItem { id: string; text: LocalizedText; source_ids?: string[] }
export interface RegulatoryProfile {
  id: DesignCity;
  name: LocalizedText;
  authority: LocalizedText;
  jurisdiction_scope: LocalizedText;
  environmental_parameters: Record<string, {
    value: number | string | null; unit: string | null; status: string;
    scope: LocalizedText; source_ids?: string[];
  }>;
  review_items: ReviewItem[];
  pending_site_inputs: (string | ReviewItem)[];
  attic_opening_review?: {
    checked_at: string; source_ids: string[]; opening_area_m2: number; width_mm: number; height_mm: number; opening_count: number;
    description: LocalizedText; statutory_compliance_result: null;
  };
  statutory_compliance_result: null;
}
export interface RegulatoryProfiles { revision: string; checked_at: string; national_requirements: ReviewItem[]; profiles: RegulatoryProfile[]; sources: RegulatorySource[] }
export interface StructuralVariant {
  system: StructuralSystem;
  glb_path: string;
  step_path: string;
  coordination: { summary?: LocalizedText; [key: string]: unknown };
  capacity_results: null;
  statutory_compliance_result: null;
}
export interface StructuralVariants { variants: Record<StructuralSystem, StructuralVariant> }
export interface StructuralOverlayState {
  status: 'idle' | 'loading' | 'ready' | 'error';
  system: StructuralSystem | null;
  parts: ModelPartId[];
}
export function isDesignCity(value: unknown): value is DesignCity { return designCities.some(city => city === value); }
export function isStructuralSystem(value: unknown): value is StructuralSystem { return structuralSystems.some(system => system === value); }
export function initialStructuralDesign(query: string): StructuralDesign {
  const params = new URLSearchParams(query);
  const city = params.get('city'), system = params.get('system');
  return { city: isDesignCity(city) ? city : 'tokyo', system: isStructuralSystem(system) ? system : 'W' };
}
export function structuralDesignUrl(current: string, design: StructuralDesign): string {
  const url = new URL(current);
  url.searchParams.set('city', design.city); url.searchParams.set('system', design.system);
  return url.href;
}
export function structuralPaths(design: StructuralDesign) {
  return {
    glb: `GLB/structure_${design.system}.glb`, step: `STEP/structure_${design.system}.step`,
    case: `output/review/cases/${design.city}_${design.system}_R07.json`,
  };
}
/** The timber asset's historical revision is not the current architectural revision. */
export function coordinationSummary(variant: StructuralVariant | undefined, locale: Locale): string | undefined {
  if (!variant) return undefined;
  return variant.system === 'W' ? structuralCopy.timberCoordination[locale] : variant.coordination.summary?.[locale];
}
/** Visibility uses the selected variant after cut/part edits as well as the preset itself. */
export function structuralObjectVisible(id: ModelPartId, settings: ModelSettings): boolean {
  if (id === 'structure' || id === 'foundation') return !!settings.visibility[id];
  if (!id.startsWith('structure:') && !id.startsWith('foundation:')) return false;
  const group = id.startsWith('structure:') ? 'structure' : 'foundation';
  return !!settings.visibility[group] && !!settings.partVisibility[id as keyof ModelSettings['partVisibility']];
}

const text = (zh: string, ja: string, en: string): LocalizedText => ({ zh, ja, en });
export const cityNames = {
  tokyo: text('东京', '東京', 'Tokyo'), osaka: text('大阪市', '大阪市', 'Osaka City'),
  kyoto: text('京都市', '京都市', 'Kyoto City'), nagoya: text('名古屋市', '名古屋市', 'Nagoya City'),
};
export const systemNames = {
  W: text('W造 · 木结构', 'W造 · 木造', 'W · Timber'),
  S: text('S造 · 轻钢结构', 'S造 · 軽量鉄骨造', 'S · Light steel'),
  RC: text('RC造 · 钢筋混凝土', 'RC造 · 鉄筋コンクリート造', 'RC · Reinforced concrete'),
};
export const structuralCopy = {
  atticWindow: text('阁楼换气口核查', '小屋裏換気口の確認', 'Attic ventilation opening review'),
  atticQuantity: text('多开口数量取扱待主管机关确认。', '複数開口の取扱いは審査先へ確認。', 'Multiple-opening interpretation requires authority confirmation.'),
  atticOpening: text('固定铝百叶 · 墙体洞口合计', '固定アルミガラリ・壁開口合計', 'Fixed aluminium louver · Total gross wall apertures'),
  atticPending: text('有效通风面积、防火规格与审批待核定。', '有効換気面積・防火仕様・確認は未確定。', 'Effective ventilation area, fire specification and approval remain pending.'),
  title: text('结构与法规方案', '構造・法規プラン', 'Structure and regulatory concept'),
  city: text('所在地参考', '地域の参照先', 'Jurisdiction reference'),
  system: text('结构体系', '構造種別', 'Structural system'),
  status: text('条件方案 · 未计算／未认定', '条件付き計画 · 未計算・未認定', 'Conditional concept · Uncalculated / unapproved'),
  introduction: text('4 个城市 × 3 种体系，共 12 个条件方案。尺寸为演示假设；所在地仅切换法规资料，设计荷载及合规结论待地块信息确定。', '4地域 × 3構造、計12の条件付き計画。寸法はデモ用の仮定です。地域選択で参照法規を切り替えます。設計荷重と適合判定は敷地情報確定後の検討事項です。', 'Four jurisdictions × three systems: 12 conditional concepts. Dimensions are demonstration assumptions. City selection changes the regulatory reference; design loads and compliance remain pending site information.'),
  loading: text('正在加载所选结构…', '選択した構造を読み込み中…', 'Loading selected structural concept…'),
  loadError: text('所选结构加载失败，可重试或下载文件。', '選択した構造を読み込めません。再試行またはファイルのダウンロードが可能です。', 'The selected structure could not load. Retry or download its files.'),
  retry: text('重试', '再試行', 'Retry'),
  details: text('法规依据与待核定事项', '参照法規・未確定事項', 'Regulatory references and pending inputs'),
  national: text('全国共通要求', '全国共通の要件', 'National requirements'),
  references: text('官方资料', '公式資料', 'Official references'),
  profileLoading: text('正在加载法规资料…', '法規資料を読み込み中…', 'Loading regulatory references…'),
  profileError: text('法规资料加载失败，请重试。', '法規資料を読み込めません。再試行してください。', 'Regulatory references could not load. Please retry.'),
  pending: text('待核定', '未確定', 'Pending'),
  required: text('必要的地块与计算输入', '必要な敷地・計算入力', 'Required site and calculation inputs'),
  commonInputs: text('准确地址、测量与道路资料、用途与防火区、地盘调查、材料等级、恒载与活载、连接及基础计算。', '所在地・測量・接道、用途地域・防火指定、地盤調査、材料等級、固定荷重・積載荷重、接合部・基礎計算。', 'Exact address, survey and road access, zoning and fire district, ground investigation, material grades, dead/live loads, connections and foundation calculations.'),
  coordination: text('建筑协调待定项', '建築との調整事項', 'Architectural coordination pending'),
  timberCoordination: text('木结构演示架构沿镜像平面布置；截面、节点与基础均未验算。', '木造概念架構を左右反転の間取りに沿って配置。断面・接合部・基礎は未計算。', 'The timber concept follows the mirrored layout; sections, connections and foundations are uncalculated.'),
  exterior: text('完整外观沿用现有建筑方案；所选体系在「结构方案」视图中显示，尚未完成门窗、室内净空与外轮廓协调。', '建物全体は既存の建築計画です。選択構造は「構造プラン」で表示し、開口・内法・外形の調整は未完了です。', 'Whole-house view retains the architectural concept. The selected system appears in Structural scheme; openings, clearances and the envelope are not fully coordinated.'),
  downloadGlb: text('结构 GLB', '構造GLB', 'Structural GLB'),
  downloadStep: text('结构 STEP', '構造STEP', 'Structural STEP'),
  downloadCase: text('当前方案 JSON', '選択プランJSON', 'Selected case JSON'),
  referenceValues: text('地域参考值（未用于计算）', '地域の参考値（計算には未適用）', 'Regional references (not applied to calculations)'),
  basic_wind_speed: text('基准风速', '基準風速', 'Basic wind speed'),
  snow_depth: text('垂直积雪量', '垂直積雪量', 'Vertical snow depth'),
  roughness: text('地表粗度', '地表面粗度', 'Terrain roughness'),
  seismic_z: text('地震地域系数 Z', '地震地域係数 Z', 'Seismic regional coefficient Z'),
  referencesChecked: text('资料核对日期', '資料確認日', 'References checked'),
};
