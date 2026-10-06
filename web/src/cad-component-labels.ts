import type { Locale } from './localization.ts';
import type { ModelId } from './model-state.ts';

type Label = Readonly<Record<Locale, string>>;
type Catalog = Readonly<Record<string, Label>>;
const label = (zh: string, ja: string, en: string): Label => ({ zh, ja, en });

function lookup(catalog: Catalog, key: string, locale: Locale): string | null {
  return Object.hasOwn(catalog, key) ? catalog[key][locale] : null;
}

const componentLabels = {
  'roof:west_plane': label('西侧屋面', '西側の屋根面', 'West roof plane'),
  'roof:east_plane': label('东侧屋面', '東側の屋根面', 'East roof plane'),
  'roof:south_gable_wall': label('南侧山墙', '南側の妻壁', 'South gable wall'),
  'roof:north_gable_wall': label('北侧山墙', '北側の妻壁', 'North gable wall'),
  'roof:attic_ceiling_slab': label('屋顶下方顶板', '屋根下の天井スラブ', 'Ceiling slab beneath roof'),
  'roof:ridge_cap': label('屋脊盖板', '棟包み', 'Ridge cap'),
  'stairs:mid_landing': label('楼梯中间平台', '階段の中間踊り場', 'Intermediate stair landing'),
  'balcony:slab': label('阳台楼板', 'バルコニー床スラブ', 'Balcony floor slab'),
  'balcony:south_guard': label('阳台南侧栏板', 'バルコニー南側の腰壁', 'South balcony parapet'),
  'balcony:west_guard': label('阳台西侧栏板', 'バルコニー西側の腰壁', 'West balcony parapet'),
  'balcony:east_guard': label('阳台东侧栏板', 'バルコニー東側の腰壁', 'East balcony parapet'),
  'ceiling:slab': label('室内顶板', '室内の天井スラブ', 'Interior ceiling slab'),
} satisfies Catalog;

const directions = {
  south: label('南侧', '南側', 'South'), north: label('北侧', '北側', 'North'),
  west: label('西侧', '西側', 'West'), east: label('东侧', '東側', 'East'),
  south_west: label('南侧西坡', '南側・西面', 'South, west slope'),
  south_east: label('南侧东坡', '南側・東面', 'South, east slope'),
  north_west: label('北侧西坡', '北側・西面', 'North, west slope'),
  north_east: label('北侧东坡', '北側・東面', 'North, east slope'),
  south_gable: label('南侧山墙', '南側の妻壁', 'South gable'),
  north_gable: label('北侧山墙', '北側の妻壁', 'North gable'),
} satisfies Catalog;
const exteriorDetails = {
  cladding: label('外墙挂板饰面', '外壁サイディング', 'Exterior siding'),
  foundation: label('混凝土基座', 'コンクリート基礎立上り', 'Concrete plinth'),
  entry_panel: label('玄关木色饰面', '玄関の木目アクセント', 'Timber entry accent'),
  downpipe: label('落水管', 'たてとい', 'Downpipe'),
  standing_seam: label('屋面立缝', '屋根の立ちはぜ', 'Roof standing seam'),
  fascia: label('破风板', '破風板', 'Bargeboard'),
  soffit: label('檐底板', '軒天', 'Soffit'),
  gutter: label('檐沟', '軒とい', 'Eaves gutter'),
} satisfies Catalog;
const entryDetails = {
  canopy: label('玄关雨棚', '玄関庇', 'Entry canopy'),
  porch: label('玄关平台', '玄関ポーチ', 'Entry porch'),
  porch_step: label('玄关踏步', '玄関ポーチの段', 'Porch step'),
  frame: label('玄关门框', '玄関ドア枠', 'Entry door frame'),
  handle: label('玄关门拉手', '玄関ドアハンドル', 'Entry door handle'),
  threshold: label('玄关门槛', '玄関ドアの下枠', 'Entry threshold'),
} satisfies Catalog;

const externalWalls = {
  south: label('南侧外墙', '南側の外壁', 'South external wall'),
  north: label('北侧外墙', '北側の外壁', 'North external wall'),
  west: label('西侧外墙', '西側の外壁', 'West external wall'),
  east: label('东侧外墙', '東側の外壁', 'East external wall'),
} satisfies Catalog;

const numberedComponents = {
  partition: label('内隔墙', '間仕切り壁', 'Partition wall'),
  storage: label('收纳柜', '収納キャビネット', 'Storage cabinet'),
  lowerTread: label('下段梯段 · 踏步', '下側の階段 · 踏板', 'Lower flight · Tread'),
  upperTread: label('上段梯段 · 踏步', '上側の階段 · 踏板', 'Upper flight · Tread'),
} satisfies Catalog;

const doorKinds = {
  swing: label('平开门', '開き戸', 'Hinged door'),
  slide: label('推拉门', '引き戸', 'Sliding door'),
} satisfies Catalog;
const doorLeaf = label('门扇', '扉本体', 'Door leaf');
const windowName = label('窗', '窓', 'Window');
const windowDetails = {
  frame_1: label('下窗框', '下枠', 'Lower frame'),
  frame_2: label('上窗框', '上枠', 'Upper frame'),
  // The frame orientation follows the window axis, so side numbers stay valid
  // from either viewing direction and for both horizontal and vertical walls.
  frame_3: label('侧窗框 1', '縦枠 1', 'Side frame 1'),
  frame_4: label('侧窗框 2', '縦枠 2', 'Side frame 2'),
  frame_5: label('中间窗梃', '中央の方立', 'Centre mullion'),
  glass: label('玻璃', 'ガラス', 'Glass pane'),
  glass_1: label('玻璃 1', 'ガラス 1', 'Glass pane 1'),
  glass_2: label('玻璃 2', 'ガラス 2', 'Glass pane 2'),
  exterior_trim: label('外侧窗套', '外側の窓額縁', 'Exterior window trim'),
  sill: label('窗台水切', '窓台水切り', 'Sill flashing'),
} satisfies Catalog;

const roomLabels = {
  ldk: label('LDK', 'LDK', 'Living / dining / kitchen'),
  master: label('主卧', '主寝室', 'Main bedroom'),
  bed2: label('卧室 2', '洋室 2', 'Bedroom 2'),
  bed3: label('卧室 3', '洋室 3', 'Bedroom 3'),
} satisfies Catalog;
const apartmentBedroom1 = label('卧室 1', '洋室 1', 'Bedroom 1');

type FurnitureKind = 'bed' | 'sofa' | 'table' | 'chair' | 'television';
const furnitureObjects = {
  bed: { kind: 'bed', name: label('床', 'ベッド', 'Bed') },
  sofa: { kind: 'sofa', name: label('沙发', 'ソファ', 'Sofa') },
  coffee_table: { kind: 'table', name: label('茶几', 'ローテーブル', 'Coffee table') },
  dining_table: { kind: 'table', name: label('餐桌', 'ダイニングテーブル', 'Dining table') },
  dining_chair_west: { kind: 'chair', name: label('西侧餐椅', '西側のダイニングチェア', 'West dining chair') },
  dining_chair_east: { kind: 'chair', name: label('东侧餐椅', '東側のダイニングチェア', 'East dining chair') },
  television: { kind: 'television', name: label('电视与电视柜', 'テレビ・テレビ台', 'TV and console') },
} satisfies Record<string, { kind: FurnitureKind; name: Label }>;

const furnitureDetails = {
  bed: {
    frame: label('床架', 'ベッドフレーム', 'Bed frame'),
    headboard: label('床头板', 'ヘッドボード', 'Headboard'),
    mattress: label('床垫', 'マットレス', 'Mattress'),
    blanket: label('被子', '掛け布団', 'Duvet'),
  },
  sofa: {
    base: label('底座', '土台', 'Base'),
    back: label('靠背', '背もたれ', 'Back'),
    arm_left: label('左扶手', '左ひじ掛け', 'Left armrest'),
    arm_right: label('右扶手', '右ひじ掛け', 'Right armrest'),
  },
  table: { top: label('桌面', '天板', 'Tabletop') },
  chair: {
    seat_frame: label('座面框架', '座面フレーム', 'Seat frame'),
    seat_cushion: label('坐垫', '座面クッション', 'Seat cushion'),
    back_post_left: label('左侧靠背支柱', '左の背もたれ支柱', 'Left back post'),
    back_post_right: label('右侧靠背支柱', '右の背もたれ支柱', 'Right back post'),
    backrest: label('椅背', '背もたれ', 'Backrest'),
  },
  television: {
    console: label('电视柜柜体', 'テレビ台本体', 'Console body'),
    tv_foot: label('电视底座', 'テレビスタンド台座', 'TV stand base'),
    tv_stem: label('电视支柱', 'テレビスタンド支柱', 'TV stand post'),
    tv_bezel: label('电视边框', 'テレビ画面枠', 'TV bezel'),
    tv_screen: label('电视屏幕', 'テレビ画面', 'TV screen'),
  },
} satisfies Record<FurnitureKind, Catalog>;

const furnitureLegs = {
  bed: label('床脚', 'ベッドの脚', 'Bed leg'),
  sofa: label('沙发脚', 'ソファの脚', 'Sofa leg'),
  table: label('桌腿', 'テーブルの脚', 'Table leg'),
  chair: label('椅腿', '椅子の脚', 'Chair leg'),
  television: label('电视柜脚', 'テレビ台の脚', 'Console leg'),
} satisfies Record<FurnitureKind, Label>;

type NumberedDetail = { name: Label; count: number };
const numberedFurnitureDetails: Record<FurnitureKind, Readonly<Record<string, NumberedDetail>>> = {
  bed: { pillow: { name: label('枕头', '枕', 'Pillow'), count: 2 } },
  sofa: {
    seat: { name: label('坐垫', '座面クッション', 'Seat cushion'), count: 2 },
    back_cushion: { name: label('靠背垫', '背もたれクッション', 'Back cushion'), count: 2 },
  },
  table: {},
  chair: {},
  television: {
    // These pieces are front panels, rather than complete drawer boxes.
    drawer: { name: label('抽屉面板', '引き出し前板', 'Drawer front'), count: 2 },
    pull: { name: label('抽屉拉手', '引き出し取っ手', 'Drawer pull'), count: 2 },
  },
};

function furnitureDetail(locale: Locale, kind: FurnitureKind, suffix: string): string | null {
  const exact = lookup(furnitureDetails[kind], suffix, locale);
  if (exact) return exact;
  const leg = /^leg_([1-4])$/.exec(suffix);
  if (leg) return `${furnitureLegs[kind][locale]} ${leg[1]}`;
  const numbered = /^(pillow|seat|back_cushion|drawer|pull)_([1-9]\d*)$/.exec(suffix);
  if (!numbered) return null;
  const catalog = numberedFurnitureDetails[kind];
  if (!Object.hasOwn(catalog, numbered[1])) return null;
  const detail = catalog[numbered[1]];
  return Number(numbered[2]) <= detail.count ? `${detail.name[locale]} ${numbered[2]}` : null;
}

type FixtureKind = 'kitchen' | 'bath' | 'vanity' | 'washer' | 'toilet';
const fixtureNames = {
  kitchen: label('整体厨房', 'システムキッチン', 'Kitchen unit'),
  bath: label('浴缸与淋浴', '浴槽・シャワー', 'Bath and shower'),
  vanity: label('洗面台', '洗面台', 'Vanity'),
  washer: label('洗衣机', '洗濯機', 'Washing machine'),
  toilet: label('坐便器', 'トイレ', 'Toilet'),
} satisfies Record<FixtureKind, Label>;

const faucetDetails = {
  drain_chrome: label('排水口', '排水口', 'Drain'),
  faucet_base_chrome: label('水龙头底座', '水栓台座', 'Faucet base'),
  faucet_chrome: label('水龙头', '水栓', 'Faucet'),
  mixer_lever_chrome: label('混水调节杆', '混合水栓レバー', 'Mixer lever'),
} satisfies Catalog;
const cabinetDetails = {
  cabinet_wood: label('柜体', 'キャビネット本体', 'Cabinet body'),
  toe_plinth_dark: label('柜底座', 'キャビネット台輪', 'Cabinet plinth'),
} satisfies Catalog;

const fixtureDetails = {
  kitchen: {
    ...faucetDetails, ...cabinetDetails,
    counter_stone: label('台面', 'カウンター天板', 'Countertop'),
    sink_steel: label('厨房水槽', 'キッチンシンク', 'Kitchen sink'),
    sink_rim_steel: label('水槽边缘', 'シンク縁', 'Sink rim'),
    hob_dark: label('灶台', 'コンロ', 'Cooktop'),
  },
  bath: {
    ...faucetDetails,
    tub_shell_ceramic: label('浴缸本体', '浴槽本体', 'Tub body'),
    tub_rim_ceramic: label('浴缸边缘', '浴槽縁', 'Tub rim'),
    shower_rail_chrome: label('淋浴支杆', 'シャワー支柱', 'Shower support'),
    shower_head_chrome: label('淋浴喷头', 'シャワーヘッド', 'Shower head'),
    shower_face_dark: label('喷头出水面', 'シャワー散水面', 'Shower spray face'),
  },
  vanity: {
    ...faucetDetails, ...cabinetDetails,
    counter_ceramic: label('台面', 'カウンター天板', 'Countertop'),
    basin_ceramic: label('洗面盆', '洗面ボウル', 'Washbasin'),
    mirror_frame_chrome: label('镜框', '鏡枠', 'Mirror frame'),
    mirror: label('镜面', '鏡', 'Mirror'),
  },
  washer: {
    body_white: label('机身', '本体', 'Body'),
    porthole_chrome: label('门框', 'ドア枠', 'Door frame'),
    porthole_seal_rubber: label('门密封圈', 'ドアパッキン', 'Door seal'),
    washer_glass: label('门玻璃', 'ドアガラス', 'Door glass'),
    drum_steel: label('洗衣滚筒', '洗濯ドラム', 'Drum'),
    dial_chrome: label('控制旋钮', '操作ダイヤル', 'Control dial'),
    control_screen: label('控制显示屏', '操作ディスプレイ', 'Control display'),
    detergent_drawer_white: label('洗涤剂盒面板', '洗剤ケース前面', 'Detergent drawer front'),
    lower_service_panel_white: label('底部检修面板', '下部点検パネル', 'Lower service panel'),
  },
  toilet: {
    bowl_ceramic: label('便池', '便器本体', 'Toilet bowl'),
    seat_ceramic: label('座圈', '便座', 'Toilet seat'),
    // The dark disc represents the bowl outlet, not modeled trap plumbing.
    bowl_trap_dark: label('便池排水口', '便器排水口', 'Bowl outlet'),
    cistern_ceramic: label('水箱', 'トイレタンク', 'Cistern'),
    cistern_lid_ceramic: label('水箱盖', 'タンクふた', 'Cistern lid'),
    flush_chrome: label('冲水按钮', '洗浄ボタン', 'Flush button'),
    open_lid_ceramic: label('掀起的马桶盖', '開いた便ふた', 'Raised toilet lid'),
  },
} satisfies Record<FixtureKind, Catalog>;

const numberedFixtureDetails: Record<FixtureKind, Readonly<Record<string, NumberedDetail>>> = {
  kitchen: {
    front_wood: { name: label('橱柜前面板', 'キャビネット前面パネル', 'Cabinet front'), count: 5 },
    handle_chrome: { name: label('把手', '取っ手', 'Handle'), count: 5 },
    hob_ring_steel: { name: label('加热区圆环', '加熱ゾーンリング', 'Cooking zone ring'), count: 3 },
  },
  bath: {},
  vanity: {
    door_wood: { name: label('柜门', 'キャビネット扉', 'Cabinet door'), count: 2 },
    handle_chrome: { name: label('把手', '取っ手', 'Handle'), count: 2 },
  },
  washer: {},
  toilet: {},
};

function fixtureDetail(locale: Locale, kind: FixtureKind, suffix: string): string | null {
  const exact = lookup(fixtureDetails[kind], suffix, locale);
  if (exact) return exact;
  const numbered = /^(front|door|handle|hob_ring)_([1-9]\d*)_(wood|chrome|steel)$/.exec(suffix);
  if (!numbered) return null;
  const catalog = numberedFixtureDetails[kind];
  const key = `${numbered[1]}_${numbered[3]}`;
  if (!Object.hasOwn(catalog, key)) return null;
  const detail = catalog[key];
  return Number(numbered[2]) <= detail.count ? `${detail.name[locale]} ${numbered[2]}` : null;
}

/** Labels the selected CAD mesh without changing its stable picking/export ID.
 * Category/group IDs (including floor_slab meshes) and unknown names return null,
 * allowing the caller to use its localized category title or component fallback.
 */
export function cadComponentLabel(locale: Locale, name: string, modelId: ModelId = 'house'): string | null {
  const fixed = lookup(componentLabels, name, locale);
  if (fixed) return fixed;

  const exterior = /^(?:F[12]:exterior|roof):(cladding|foundation|entry_panel|downpipe|standing_seam|fascia|soffit|gutter):([^:]+)$/.exec(name);
  if (exterior) {
    const seam = /^(west|east)_(\d{2})$/.exec(exterior[2]);
    const direction = lookup(directions, seam ? seam[1] : exterior[2], locale);
    const detail = lookup(exteriorDetails, exterior[1], locale);
    return direction && detail ? `${direction} · ${detail}${seam ? ` ${Number(seam[2])}` : ''}` : null;
  }
  const entry = /^F1:(D01):(canopy|porch|porch_step|frame|handle|threshold)$/.exec(name);
  if (entry) return `${entry[1]} · ${entryDetails[entry[2] as keyof typeof entryDetails][locale]}`;

  const wall = /^F[12]:wall_external_(south|north|west|east)$/.exec(name);
  if (wall) return externalWalls[wall[1] as keyof typeof externalWalls][locale];
  const numbered = /^F[12]:(wall_partition|storage)_(\d{2})$/.exec(name);
  if (numbered) return `${numberedComponents[numbered[1] === 'storage' ? 'storage' : 'partition'][locale]} ${numbered[2]}`;

  const door = /^F[12]:(D\d{2})_door_(swing|slide)$/.exec(name);
  if (door) return `${doorKinds[door[2] as keyof typeof doorKinds][locale]} ${door[1]} · ${doorLeaf[locale]}`;
  const window = /^F[12]:(W\d{2}):(frame_[1-5]|glass(?:_[12])?|exterior_trim|sill)$/.exec(name);
  if (window) return `${windowName[locale]} ${window[1]} · ${windowDetails[window[2] as keyof typeof windowDetails][locale]}`;
  const stair = /^stairs:(lower|upper)_tread_(0[1-7])$/.exec(name);
  if (stair) return `${numberedComponents[stair[1] === 'lower' ? 'lowerTread' : 'upperTread'][locale]} ${Number(stair[2])}`;

  const furniture = /^F[12]:furniture:([^:]+):([^:]+):([^:]+)$/.exec(name);
  if (furniture) {
    const room = modelId === 'apartment' && furniture[1] === 'master'
      ? apartmentBedroom1[locale] : lookup(roomLabels, furniture[1], locale);
    if (!room || !Object.hasOwn(furnitureObjects, furniture[2])) return null;
    const object = furnitureObjects[furniture[2] as keyof typeof furnitureObjects];
    const detail = furnitureDetail(locale, object.kind, furniture[3]);
    return detail ? `${room} · ${object.name[locale]} · ${detail}` : null;
  }

  const fixture = /^F[12]:fixture_(\d{2})_(kitchen|bath|vanity|washer|toilet):([^:]+)$/.exec(name);
  if (fixture) {
    const kind = fixture[2] as FixtureKind;
    const detail = fixtureDetail(locale, kind, fixture[3]);
    return detail ? `${fixtureNames[kind][locale]} ${fixture[1]} · ${detail}` : null;
  }
  return null;
}
