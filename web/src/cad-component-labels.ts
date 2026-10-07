import type { Locale } from './localization.ts';
import type { ModelId } from './model-state.ts';

type Label = Readonly<Record<Locale, string>>;
type Catalog = Readonly<Record<string, Label>>;
const label = (zh: string, ja: string, en: string): Label => ({ zh, ja, en });

function lookup(catalog: Catalog, key: string, locale: Locale): string | null {
  return Object.hasOwn(catalog, key) ? catalog[key][locale] : null;
}

const componentLabels = {
  'foundation:raft:slab': label('建筑筏板基础', '建物のベタ基礎底盤', 'Building raft foundation slab'),
  'foundation:raft:entrance_footing': label('玄关基础底板', '玄関ポーチの基礎底盤', 'Entrance foundation slab'),
  'foundation:stem_walls:south': label('南侧基础立上墙', '南側の基礎立上り', 'South foundation stem wall'),
  'foundation:stem_walls:north': label('北侧基础立上墙', '北側の基礎立上り', 'North foundation stem wall'),
  'foundation:stem_walls:west': label('西侧基础立上墙', '西側の基礎立上り', 'West foundation stem wall'),
  'foundation:stem_walls:east': label('东侧基础立上墙', '東側の基礎立上り', 'East foundation stem wall'),
  'foundation:stem_walls:perimeter': label('周圈基础立上墙', '外周の基礎立上り', 'Perimeter foundation stem wall'),
  'foundation:existing_plinth:south': label('南侧周圈基座', '南側の外周基台', 'South perimeter plinth'),
  'foundation:existing_plinth:north': label('北侧周圈基座', '北側の外周基台', 'North perimeter plinth'),
  'foundation:existing_plinth:west': label('西侧周圈基座', '西側の外周基台', 'West perimeter plinth'),
  'foundation:existing_plinth:east': label('东侧周圈基座', '東側の外周基台', 'East perimeter plinth'),
  'foundation:entrance_supports:porch': label('玄关平台支承', '玄関ポーチの支持部', 'Entrance porch support'),
  'foundation:entrance_supports:upper_step': label('玄关上踏步支承', '玄関上段の支持部', 'Upper entrance step support'),
  'yard:soil:base': label('院子土层', '庭の地盤層', 'Yard soil layer'),
  'yard:ground_surfaces:gravel': label('院子砾石地面', '庭の砂利敷き', 'Yard gravel surface'),
  'yard:entrance_path:paving': label('入户步道铺装', '玄関アプローチの舗装', 'Entrance path paving'),
  'yard:entrance_path:lower_step': label('入户步道下踏步', '玄関アプローチの下段', 'Lower entrance path step'),
  'yard:parking:paving': label('停车位铺装', '駐車スペースの舗装', 'Parking space paving'),
  'yard:parking:line_divider_1': label('两车位分隔线', '駐車2台の区画線', 'Shared parking divider'),
  'yard:parking:bay_1_wheel_stop_left': label('车位1·左车挡', '駐車1・左車止め', 'Bay 1 left wheel stop'),
  'yard:parking:bay_1_wheel_stop_right': label('车位1·右车挡', '駐車1・右車止め', 'Bay 1 right wheel stop'),
  'yard:parking:bay_2_wheel_stop_left': label('车位2·左车挡', '駐車2・左車止め', 'Bay 2 left wheel stop'),
  'yard:parking:bay_2_wheel_stop_right': label('车位2·右车挡', '駐車2・右車止め', 'Bay 2 right wheel stop'),
  'yard:parking:line_left': label('停车位左侧标线', '駐車スペースの左区画線', 'Left parking boundary line'),
  'yard:parking:line_right': label('停车位右侧标线', '駐車スペースの右区画線', 'Right parking boundary line'),
  'yard:parking:line_back': label('停车位后侧标线', '駐車スペースの奥側区画線', 'Rear parking boundary line'),
  'yard:parking:wheel_stop_left': label('停车位左侧车挡', '駐車スペースの左車止め', 'Left parking wheel stop'),
  'yard:parking:wheel_stop_right': label('停车位右侧车挡', '駐車スペースの右車止め', 'Right parking wheel stop'),
  'yard:planting:lawn_front': label('前院草坪', '前庭の芝生', 'Front yard lawn'),
  'yard:planting:lawn_north': label('北侧草坪', '北側の芝生', 'North yard lawn'),
  'yard:planting:lawn_east': label('东侧草坪', '東側の芝生', 'East yard lawn'),
  'yard:planting:lawn_west': label('西侧草坪', '西側の芝生', 'West yard lawn'),
  'roof:west_plane': label('西侧屋面', '西側の屋根面', 'West roof plane'),
  'roof:east_plane': label('东侧屋面', '東側の屋根面', 'East roof plane'),
  'structure:roof:slab_west': label('西侧 RC 屋面板示意', '西側RC屋根スラブ参考形状', 'Concept west RC roof slab'),
  'structure:roof:slab_east': label('东侧 RC 屋面板示意', '東側RC屋根スラブ参考形状', 'Concept east RC roof slab'),
  'structure:roof:gable_shear_south': label('南侧 RC 山墙候选', '南側RC妻壁候補', 'Candidate south RC gable wall'),
  'structure:roof:gable_shear_north': label('北侧 RC 山墙候选', '北側RC妻壁候補', 'Candidate north RC gable wall'),
  'structure:F1:slab_ground': label('一层地面结构板示意', '1階の構造床スラブ参考形状', 'Concept first-floor ground slab'),
  'structure:F2:slab_floor': label('二层结构楼板示意', '2階の構造床スラブ参考形状', 'Concept second-floor structural slab'),
  'structure:attic:slab_storage': label('储物阁楼结构板示意', '収納用小屋裏の構造床スラブ参考形状', 'Concept storage-attic structural slab'),
  'roof:south_gable_wall': label('南侧山墙', '南側の妻壁', 'South gable wall'),
  'roof:north_gable_wall': label('北侧山墙', '北側の妻壁', 'North gable wall'),
  'roof:attic_ceiling_slab': label('阁楼下地板（厚 24 mm）', '小屋裏の下地床（厚24 mm）', 'Attic subfloor (24 mm thick)'),
  'attic:deck_finish': label('阁楼地板饰面', '小屋裏の床仕上げ', 'Attic floor finish'),
  'attic:lining:flat_ceiling': label('阁楼限高平天花', '小屋裏の高さを制限する水平天井', 'Attic height-limiting flat ceiling'),
  'attic:lining:west_slope': label('阁楼西侧斜顶内衬', '小屋裏西側の勾配天井', 'West sloped attic lining'),
  'attic:lining:east_slope': label('阁楼东侧斜顶内衬', '小屋裏東側の勾配天井', 'East sloped attic lining'),
  'attic:knee_wall:west': label('阁楼西侧矮墙', '小屋裏西側の腰壁', 'West attic knee wall'),
  'attic:knee_wall:east': label('阁楼东侧矮墙', '小屋裏東側の腰壁', 'East attic knee wall'),
  'attic:gable_lining:south': label('阁楼南侧山墙内衬', '小屋裏南側の妻壁内装', 'South attic gable lining'),
  'attic:gable_lining:north': label('阁楼北侧山墙内衬', '小屋裏北側の妻壁内装', 'North attic gable lining'),
  'attic:guardrail:post_southwest': label('阁楼开口西南侧护栏立柱', '小屋裏開口・南西の手すり支柱', 'Attic hatch guardrail southwest post'),
  'attic:guardrail:post_southeast': label('阁楼开口东南侧护栏立柱', '小屋裏開口・南東の手すり支柱', 'Attic hatch guardrail southeast post'),
  'attic:guardrail:post_northwest': label('阁楼开口西北侧护栏立柱', '小屋裏開口・北西の手すり支柱', 'Attic hatch guardrail northwest post'),
  'attic:guardrail:post_northeast': label('阁楼开口东北侧护栏立柱', '小屋裏開口・北東の手すり支柱', 'Attic hatch guardrail northeast post'),
  'attic:guardrail:east_rail': label('阁楼开口东侧护栏横杆', '小屋裏開口・東側の手すり横桟', 'Attic hatch east guardrail rail'),
  'attic:guardrail:west_rail': label('阁楼开口西侧护栏横杆', '小屋裏開口・西側の手すり横桟', 'Attic hatch west guardrail rail'),
  'attic:guardrail:south_rail': label('阁楼开口南侧护栏横杆', '小屋裏開口・南側の手すり横桟', 'Attic hatch south guardrail rail'),
  'attic:guardrail:north_rail': label('阁楼开口北侧护栏横杆', '小屋裏開口・北側の手すり横桟', 'Attic hatch north guardrail rail'),
  'attic_access:left_stringer': label('阁楼检修梯左侧梯梁', '小屋裏点検はしご・左の側桁', 'Attic ladder left stringer'),
  'attic_access:right_stringer': label('阁楼检修梯右侧梯梁', '小屋裏点検はしご・右の側桁', 'Attic ladder right stringer'),
  'attic_access:hatch_trim': label('阁楼检修口边框', '小屋裏点検口の枠', 'Attic access hatch trim'),
  'attic_access:hatch_lid': label('阁楼检修口盖板（展开）', '小屋裏点検口のふた（展開）', 'Attic access hatch lid (deployed)'),
  'attic_access:hinge_left': label('阁楼检修口左侧铰链', '小屋裏点検口・左のヒンジ', 'Attic hatch left hinge'),
  'attic_access:hinge_right': label('阁楼检修口右侧铰链', '小屋裏点検口・右のヒンジ', 'Attic hatch right hinge'),
  'roof:ridge_cap': label('屋脊盖板', '棟包み', 'Ridge cap'),
  'stairs:mid_landing': label('楼梯中间平台', '階段の中間踊り場', 'Intermediate stair landing'),
  'balcony:slab': label('阳台楼板', 'バルコニー床スラブ', 'Balcony floor slab'),
  'balcony:finish': label('阳台地面饰面', 'バルコニー床仕上げ', 'Balcony floor finish'),
  'balcony:support_post_1': label('阳台西侧示意支柱', 'バルコニー西側の支持柱案', 'Concept west balcony support'),
  'balcony:support_post_2': label('阳台东侧示意支柱', 'バルコニー東側の支持柱案', 'Concept east balcony support'),
  'balcony:support_post_3': label('阳台中间示意支柱', 'バルコニー中央の支持柱案', 'Concept middle balcony support'),
  'balcony:footing_3': label('阳台中间示意基础', 'バルコニー中央の基礎案', 'Concept middle balcony footing'),
  'balcony:footing_1': label('阳台西侧示意基础', 'バルコニー西側の基礎案', 'Concept west balcony footing'),
  'balcony:footing_2': label('阳台东侧示意基础', 'バルコニー東側の基礎案', 'Concept east balcony footing'),
  'balcony:drying_post_1': label('晾衣架西侧立杆', '物干し西側の支柱', 'West drying rack post'),
  'balcony:drying_post_2': label('晾衣架东侧立杆', '物干し東側の支柱', 'East drying rack post'),
  'balcony:drying_rail': label('阳台晾衣杆', 'バルコニー物干し竿', 'Balcony drying rail'),
  'balcony:drain_outlet': label('阳台示意排水口', 'バルコニー排水口の参考形状', 'Concept balcony drain outlet'),
  'balcony:south_guard': label('阳台南侧栏板', 'バルコニー南側の腰壁', 'South balcony parapet'),
  'balcony:west_guard': label('阳台西侧栏板', 'バルコニー西側の腰壁', 'West balcony parapet'),
  'balcony:east_guard': label('阳台东侧栏板', 'バルコニー東側の腰壁', 'East balcony parapet'),
  'ceiling:slab': label('室内顶板', '室内の天井スラブ', 'Interior ceiling slab'),
} satisfies Catalog;

const structuralLevels = {
  F1: label('一层', '1階', 'First floor'), F2: label('二层', '2階', 'Second floor'),
  attic: label('阁楼', '小屋裏', 'Attic'), roof: label('屋顶', '屋根', 'Roof'),
} satisfies Catalog;
const structuralDetails = {
  column: label('柱', '柱', 'Column'), beam: label('梁', '梁', 'Beam'), sill: label('土台', '土台', 'Sill'),
  joist: label('搁栅', '根太', 'Joist'), header: label('开口边梁', '開口補強梁', 'Hatch header'),
  rafter: label('椽', '垂木', 'Rafter'), ridge: label('脊梁', '棟木', 'Ridge beam'),
  purlin: label('檩条', '母屋', 'Purlin'), post: label('屋架支柱', '小屋束', 'Roof post'),
  bearing_wall: label('候选承重墙', '耐力壁候補', 'Candidate bearing wall'),
  strap_brace: label('钢带支撑候选', '帯鋼ブレース候補', 'Candidate steel strap brace'),
  gusset: label('节点板示意', 'ガセットプレート参考形状', 'Concept gusset plate'),
  base_plate: label('柱脚板示意', '柱脚プレート参考形状', 'Concept base plate'),
  shear_wall: label('RC 抗震墙候选', 'RC耐震壁候補', 'Candidate RC shear wall'),
  slab: label('结构楼板示意', '構造床スラブ参考形状', 'Concept structural slab'),
} satisfies Catalog;
const atticTrimmer = label('检修口侧边梁', '点検口の側面補強梁', 'Hatch trimmer');
const ridgeLocation = label('屋脊处', '棟部', 'At the ridge');
const foundationSupport = label('内部基础支承', '内部基礎支持部', 'Internal foundation support');
const connectionCorners = {
  SW: label('左下节点', '左下の接合部', 'Lower-left joint'),
  SE: label('右下节点', '右下の接合部', 'Lower-right joint'),
  NW: label('左上节点', '左上の接合部', 'Upper-left joint'),
  NE: label('右上节点', '右上の接合部', 'Upper-right joint'),
} satisfies Catalog;

const atticStorage = {
  west_shelf: label('阁楼西侧置物架', '小屋裏西側の収納棚', 'West attic shelf'),
  east_shelf: label('阁楼东侧置物架', '小屋裏東側の収納棚', 'East attic shelf'),
  southwest_box: label('阁楼西南侧储物箱', '小屋裏南西の収納箱', 'Southwest attic storage box'),
  southeast_box: label('阁楼东南侧储物箱', '小屋裏南東の収納箱', 'Southeast attic storage box'),
} satisfies Catalog;
const atticShelfPanels = {
  back: label('背板', '背板', 'Back panel'),
  side_south: label('南侧板', '南側板', 'South side panel'),
  side_north: label('北侧板', '北側板', 'North side panel'),
  bottom: label('底板', '底板', 'Bottom panel'),
  middle: label('中层板', '中段棚板', 'Middle shelf'),
  top: label('顶板', '天板', 'Top panel'),
} satisfies Catalog;
const atticBoxPanels = {
  body: label('箱体', '箱本体', 'Box body'), lid: label('箱盖', 'ふた', 'Lid'),
} satisfies Catalog;
const atticLadderTread = label('阁楼检修梯踏步', '小屋裏点検はしごの踏み板', 'Attic access ladder tread');

const fenceSegments = {
  north: label('北侧', '北側', 'North'), west: label('西侧', '西側', 'West'), east: label('东侧', '東側', 'East'),
  south_west: label('南侧西段', '南側西区間', 'Southwest segment'),
  south_middle: label('南侧中段', '南側中央区間', 'South middle segment'),
  south_east: label('南侧东段', '南側東区間', 'Southeast segment'),
} satisfies Catalog;
const fenceDetails = {
  posts: label('围栏立柱', 'フェンス支柱', 'Fence post'),
  panels: label('围栏面板', 'フェンスパネル', 'Fence panel'),
  footings: label('围栏独立基础', 'フェンスの独立基礎', 'Fence footing'),
} satisfies Catalog;
const yardShrub = label('院子灌木', '庭の低木', 'Yard shrub');
const outdoorFixtures = {
  entrance_01: label('玄关外墙灯', '玄関の外壁灯', 'Entrance wall light'),
  path_01: label('步道灯 1', 'アプローチ灯 1', 'Path light 1'),
  path_02: label('步道灯 2', 'アプローチ灯 2', 'Path light 2'),
  garden_01: label('庭院灯 1', '庭園灯 1', 'Garden light 1'),
  garden_02: label('庭院灯 2', '庭園灯 2', 'Garden light 2'),
  gate_01: label('门口灯 1', '門灯 1', 'Gate light 1'),
  gate_02: label('门口灯 2', '門灯 2', 'Gate light 2'),
} satisfies Catalog;
const outdoorFixtureDetails = {
  mount: label('安装底座', '取付台', 'Mounting plate'),
  lower_cap: label('下端盖', '下部キャップ', 'Lower cap'),
  upper_cap: label('上端盖', '上部キャップ', 'Upper cap'),
  left_trim: label('左边框', '左側フレーム', 'Left trim'),
  right_trim: label('右边框', '右側フレーム', 'Right trim'),
  diffuser: label('柔光罩', '拡散カバー', 'Diffuser'),
  base: label('底座', 'ベース', 'Base'),
  body: label('灯体', '器具本体', 'Housing'),
  cap: label('顶盖', '上部カバー', 'Top cap'),
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

type FixtureKind = 'kitchen' | 'bath' | 'vanity' | 'washer' | 'toilet' | 'fridge' | 'cupboard';
const fixtureNames = {
  fridge: label('冰箱', '冷蔵庫', 'Refrigerator'),
  cupboard: label('电器收纳柜', 'カップボード', 'Appliance cupboard'),
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
  fridge: { body_white: label('冰箱机身', '冷蔵庫本体', 'Refrigerator body'), control_screen: label('温控面板', '温度操作パネル', 'Temperature control') },
  cupboard: { ...cabinetDetails, counter_stone: label('电器柜台面', 'カップボード天板', 'Appliance counter'), microwave_body_steel: label('微波炉', '電子レンジ', 'Microwave'), microwave_glass: label('微波炉门玻璃', 'レンジ扉ガラス', 'Microwave door glass'), microwave_screen: label('微波炉操作面板', 'レンジ操作パネル', 'Microwave control') },
  kitchen: {
    ...faucetDetails, ...cabinetDetails,
    counter_stone: label('台面', 'カウンター天板', 'Countertop'),
    sink_steel: label('厨房水槽', 'キッチンシンク', 'Kitchen sink'),
    sink_rim_steel: label('水槽边缘', 'シンク縁', 'Sink rim'),
    range_hood_steel: label('吸油烟机', 'レンジフード', 'Extractor hood'),
    hood_filter_dark: label('油烟机滤网', 'フードフィルター', 'Hood filter'),
    hood_duct_cover_steel: label('排烟管罩', '排気ダクトカバー', 'Exhaust duct cover'),
    hood_light_white: label('灶台灯', 'コンロ照明', 'Cooktop light'),
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
  fridge: { door_white: { name: label('冰箱门', '冷蔵庫扉', 'Refrigerator door'), count: 3 }, handle_chrome: { name: label('冰箱把手', '冷蔵庫取っ手', 'Refrigerator handle'), count: 3 } },
  cupboard: { front_wood: { name: label('柜门面板', '扉パネル', 'Cupboard front'), count: 3 }, handle_chrome: { name: label('柜把手', '取っ手', 'Cupboard handle'), count: 3 } },
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
  const numbered = /^(front|door|handle|hob_ring)_([1-9]\d*)_(wood|chrome|steel|white)$/.exec(suffix);
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
  const balcony = /^balcony:(south|west|east)_(rail_lower|rail_top|bar_\d+)$/.exec(name);
  if (balcony) {
    const side = directions[balcony[1] as keyof typeof directions][locale];
    const kind = balcony[2].startsWith('bar_') ? label('栏杆立条', '手すりの縦格子', 'Guard baluster') : label('栏杆横梁', '手すりの横桟', 'Guard rail');
    return `${side} · ${kind[locale]}${balcony[2].startsWith('bar_') ? ` ${Number(balcony[2].slice(4))}` : ''}`;
  }
  if (name === 'F2:D26_door_glass') return label('阳台门玻璃', 'バルコニー扉のガラス', 'Balcony door glazing')[locale];
  if (name === 'F2:D24_door_bifold') return label('衣柜折门 D24', '収納折戸 D24', 'Closet bifold door D24')[locale];
  const vent = /^attic:north_vent:(frame_[1-4]|open_glass|sill)$/.exec(name);
  if (vent) {
    const detail = vent[1] === 'open_glass' ? label('上悬玻璃', '外倒しガラス', 'Top-hung glass') : vent[1] === 'sill' ? windowDetails.sill : windowDetails[vent[1] as keyof typeof windowDetails];
    return `${label('阁楼北侧换气窗', '小屋裏北側換気窓', 'North attic ventilation window')[locale]} · ${detail[locale]}`;
  }
  const fixed = lookup(componentLabels, name, locale);
  if (fixed) return fixed;
  const outdoor = /^lighting:(?:wall|path|garden|gate):([^:]+):([^:]+)$/.exec(name);
  if (outdoor) {
    const fixture = lookup(outdoorFixtures, outdoor[1], locale);
    const detail = lookup(outdoorFixtureDetails, outdoor[2], locale);
    return fixture && detail ? `${fixture} · ${detail}` : null;
  }

  const variantMember = /^structure:(F1|F2|attic):(base_plate|shear_wall)_([A-Z]+\d{2})$/.exec(name);
  if (variantMember) return `${structuralLevels[variantMember[1] as keyof typeof structuralLevels][locale]} · ${structuralDetails[variantMember[2] as keyof typeof structuralDetails][locale]} ${variantMember[3]}`;
  const strap = /^structure:(F1|F2):strap_brace_(BW\d{2})_([AB])$/.exec(name);
  if (strap) return `${structuralLevels[strap[1] as keyof typeof structuralLevels][locale]} · ${structuralDetails.strap_brace[locale]} ${strap[2]} · ${strap[3]}`;
  const gusset = /^structure:(F1|F2):gusset_(BW\d{2})_(SW|SE|NW|NE)$/.exec(name);
  if (gusset) return `${structuralLevels[gusset[1] as keyof typeof structuralLevels][locale]} · ${structuralDetails.gusset[locale]} ${gusset[2]} · ${connectionCorners[gusset[3] as keyof typeof connectionCorners][locale]}`;

  const structural = /^structure:(F1|F2|attic):(column|beam|sill|joist|bearing_wall)_([A-Z]+\d{2})(?:_(south|north))?$/.exec(name);
  if (structural) {
    const direction = structural[4] ? `${directions[structural[4] as keyof typeof directions][locale]} · ` : '';
    return `${structuralLevels[structural[1] as keyof typeof structuralLevels][locale]} · ${direction}${structuralDetails[structural[2] as keyof typeof structuralDetails][locale]} ${structural[3]}`;
  }
  const hatchFrame = /^structure:attic:(trimmer|header)_(west|east|south|north)$/.exec(name);
  if (hatchFrame) return `${structuralLevels.attic[locale]} · ${directions[hatchFrame[2] as keyof typeof directions][locale]} · ${hatchFrame[1] === 'trimmer' ? atticTrimmer[locale] : structuralDetails.header[locale]}`;
  if (name === 'structure:roof:ridge_beam') return `${structuralLevels.roof[locale]} · ${structuralDetails.ridge[locale]}`;
  const purlin = /^structure:roof:purlin_(west|east)$/.exec(name);
  if (purlin) return `${directions[purlin[1] as keyof typeof directions][locale]} · ${structuralDetails.purlin[locale]}`;
  const roofFrame = /^structure:roof:(rafter|post)_(west|east|ridge)_([RP]\d{2})$/.exec(name);
  if (roofFrame) return `${roofFrame[2] === 'ridge' ? ridgeLocation[locale] : directions[roofFrame[2] as keyof typeof directions][locale]} · ${structuralDetails[roofFrame[1] as keyof typeof structuralDetails][locale]} ${roofFrame[3]}`;
  const support = /^foundation:internal_supports:(I\d{2})$/.exec(name);
  if (support) return `${foundationSupport[locale]} ${support[1]}`;

  const fence = /^fence:(posts|panels|footings):(north|west|east|south_west|south_middle|south_east)_(\d{2})$/.exec(name);
  if (fence) return `${fenceSegments[fence[2] as keyof typeof fenceSegments][locale]} · ${fenceDetails[fence[1] as keyof typeof fenceDetails][locale]} ${Number(fence[3])}`;
  const shrub = /^yard:planting:shrub_(\d{2})$/.exec(name);
  if (shrub) return `${yardShrub[locale]} ${Number(shrub[1])}`;

  const atticShelf = /^attic:storage:(west_shelf|east_shelf):(back|side_south|side_north|bottom|middle|top)$/.exec(name);
  if (atticShelf) return `${atticStorage[atticShelf[1] as keyof typeof atticStorage][locale]} · ${atticShelfPanels[atticShelf[2] as keyof typeof atticShelfPanels][locale]}`;
  const atticBox = /^attic:storage:(southwest_box|southeast_box):(body|lid)$/.exec(name);
  if (atticBox) return `${atticStorage[atticBox[1] as keyof typeof atticStorage][locale]} · ${atticBoxPanels[atticBox[2] as keyof typeof atticBoxPanels][locale]}`;
  const atticTread = /^attic_access:tread_(0[1-9]|10)$/.exec(name);
  if (atticTread) return `${atticLadderTread[locale]} ${Number(atticTread[1])}`;

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

  const fixture = /^F[12]:fixture_(\d{2})_(kitchen|bath|vanity|washer|toilet|fridge|cupboard):([^:]+)$/.exec(name);
  if (fixture) {
    const kind = fixture[2] as FixtureKind;
    const detail = fixtureDetail(locale, kind, fixture[3]);
    return detail ? `${fixtureNames[kind][locale]} ${fixture[1]} · ${detail}` : null;
  }
  return null;
}
