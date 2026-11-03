// Single source of time for the film. Everything on screen is a pure function of the frame number.
import { VO, FILM_END, STORY_END, WARP } from './vo.js';

export const FPS = 24;
// Everything below is authored in story frames (0..STORY_END, the original 165 s cut). The film plays them
// stretched so each narration line gets its natural length: toStory() maps a film frame to a story frame
// along a smoothed curve (vo/plan_v2.py), so the picture slows into pauses instead of stopping dead.
export const TOTAL = FILM_END;
export function toStory(f) {
  if (f <= 0) return 0;
  if (f >= FILM_END) return STORY_END;
  const i = Math.floor(f), t = f - i;
  return WARP[i] + (WARP[i + 1] - WARP[i]) * t;
}

// ---------- easing / tracks ----------
export const clamp01 = (x) => Math.min(1, Math.max(0, x));
export const smoother = (t) => { t = clamp01(t); return t * t * t * (t * (t * 6 - 15) + 10); };
export const lerp = (a, b, t) => a + (b - a) * t;

// keys: [[frame, value], ...] sorted. Eased between keys, held outside.
export function track(keys, ease = smoother) {
  return (f) => {
    if (f <= keys[0][0]) return keys[0][1];
    for (let i = 1; i < keys.length; i++) {
      const [f1, v1] = keys[i];
      if (f <= f1) {
        const [f0, v0] = keys[i - 1];
        if (f1 - f0 <= 1) return f < f1 ? v0 : v1; // one-frame step: a switch, not a blend
        return lerp(v0, v1, ease((f - f0) / Math.max(1e-6, f1 - f0)));
      }
    }
    return keys[keys.length - 1][1];
  };
}
// visible window with fades
export const window01 = (f, f0, f1, fade = 10) => Math.min(smoother((f - f0) / fade), smoother((f1 - f) / fade));

// ---------- chapters ----------
// big: [[fromFrame, number, unit, subCn, subEn]] switch points inside a chapter
export const CHAPTERS = [
  { id: 'cold', f0: 0, f1: 240, idx: '', cn: '', en: '', years: [[0, 1229], [150, 2025]], big: [] },
  { id: 'c00', f0: 240, f1: 432, idx: '00', cn: '前史 · 水与稻', en: 'Before the City', years: [[240, -4000]],
    big: [[240, '约6000', '年前', '草鞋山遗址', 'Caoxieshan site']] },
  { id: 'c01', f0: 432, f1: 744, idx: '01', cn: '建城', en: 'Founded', years: [[432, -514]],
    big: [[432, '前514', '年', '阖闾大城', "Helü's City"], [560, '8+8', '门', '陆门八 · 水门八', '8 land gates · 8 water gates']] },
  { id: 'c02', f0: 744, f1: 1008, idx: '02', cn: '苏州 · 运河', en: 'Name & Canal', years: [[744, 589], [848, 610]],
    big: [[744, '589', '年', '始称苏州', 'first called Suzhou'], [848, '610', '年', '江南运河', 'Jiangnan Canal']] },
  { id: 'c03', f0: 1008, f1: 1320, idx: '03', cn: '唐 · 桥', en: 'Tang · Bridges', years: [[1008, 825], [1218, 961]],
    big: [[1008, '390', '桥', '红栏三百九十桥', '390 red-railed bridges']] },
  { id: 'c04', f0: 1320, f1: 2016, cardOut: 1650, idx: '04', cn: '平江图', en: 'The Pingjiang Map', years: [[1320, 1229]],
    big: [[1320, '1229', '年', '南宋 · 平江府', 'Southern Song · Pingjiang'], [1470, '2', '张棋盘', '水 · 路', 'water · streets']] },
  { id: 'c05', f0: 2016, f1: 2328, idx: '05', cn: '明清 · 繁华', en: 'Ming & Qing', years: [[2016, 1509], [2200, 1759]],
    big: [[2016, '1509', '年', '拙政园始建', "Humble Administrator's Garden begun"], [2204, '12,000+', '人', '《姑苏繁华图》', 'Prosperous Suzhou, 1759']] },
  { id: 'c06', f0: 2328, f1: 2472, idx: '06', cn: '战火', en: 'Fire', years: [[2328, 1860]], big: [[2328, '1860', '年', '', '']] },
  { id: 'c08', f0: 2472, f1: 2904, idx: '07', cn: '保护', en: 'Protected', years: [[2472, 1982], [2580, 1986]],
    big: [[2472, '1982', '年', '首批国家历史文化名城', 'among the first national historic cities'], [2580, '14.2', 'km²', '古城', 'the old city']] },
  // the year holds on what the narration says (1994 lands on "四年后", story 3099), then runs on to 2018 under the last line
  { id: 'c09', f0: 2904, f1: 3192, idx: '08', cn: '两翼', en: 'Two Wings', years: [[2904, 1990], [3098, 1990], [3114, 1994], [3146, 1994], [3192, 2018]], yearRamp: true,
    big: [[2904, '1990', '年', '西 · 新区', 'West · New District'], [3098, '1994', '年', '东 · 工业园区', 'East · Industrial Park']] },
  { id: 'c10', f0: 3192, f1: 3456, idx: '09', cn: '高度', en: 'Height', years: [[3192, 2019]],
    big: [[3192, '450', 'm', '苏州国际金融中心', 'Suzhou IFS'], [3330, '76', 'm', '北寺塔', 'North Temple Pagoda']] },
  { id: 'c11', f0: 3456, f1: 3768, idx: '10', cn: '枕河', en: 'On the River', years: [[3456, 2025]],
    big: [[3456, '2500+', '年', '人家尽枕河', 'homes on the river']] },
  { id: 'end', f0: 3768, f1: 3960, idx: '', cn: '', en: '', years: [[3768, 2025]], big: [] },
];

// ---------- subtitles [f0, f1, cn, en] ----------
// Text only here; timing follows the narration (vo.js, film frames): on 3 frames before the voice, off 14
// after, never overlapping the next line.
const SUB_TEXT = [
  [10, 112, '这是一座城，近八百年前的样子。', 'This is a city as it looked nearly 800 years ago.'],
  [122, 232, '今天，这里还有许多人家枕河而居。', 'Today, many homes here still sit right on the water.'],
  [250, 340, '六千年前，这里的先民就在水边种稻。', 'Six thousand years ago, people here were already growing rice by the water.'],
  [0, 0, '上世纪90年代，考古队在城东的草鞋山，找到了那时的水田。', 'In the 1990s, archaeologists found their paddy fields at Caoxieshan, east of the city.'],
  [446, 548, '公元前514年，伍子胥“相土尝水，象天法地”。', 'In 514 BC, Wu Zixu tasted the water and read the land.'],
  [556, 646, '周回四十七里，陆门八，水门八。', 'Forty-seven li around: eight land gates, eight water gates.'],
  [654, 738, '此后两千五百多年，城址基本没有动过。', 'In the 2,500 years since, the city has stayed roughly where it was.'],
  [752, 840, '589年，因城西南的姑苏山，它第一次叫“苏州”。', 'In 589 it was first called Suzhou, after Mount Gusu to the southwest.'],
  [848, 930, '610年，江南运河开通，从镇江一直到杭州。', 'In 610 the Jiangnan Canal opened, running from Zhenjiang to Hangzhou.'],
  [938, 1002, '城里的船，从此能一路开到洛阳。', 'Boats from town could now reach Luoyang.'],
  [0, 0, '825年，白居易来苏州做刺史。', 'In 825, the poet Bai Juyi came to govern Suzhou.'],
  [1016, 1124, '他在诗里写：“绿浪东西南北水，红栏三百九十桥。”', 'In a poem he wrote of green water on every side and red rails on 390 bridges.'],
  [1132, 1210, '他还开了七里山塘河，一直通到虎丘。', 'He also dug the seven-li Shantang canal out to Tiger Hill.'],
  [1218, 1290, '虎丘塔建于961年，塔顶偏了2.34米。', 'Tiger Hill Pagoda dates from 961. Its top is 2.34 m off centre.'],
  // 04 平江图
  [1306, 1432, '1229年，平江府把整座城刻上了石碑。', 'In 1229, the whole city was cut into a stone stele.'],
  [1446, 1526, '城里的河道横平竖直，排成格子。', 'The canals ran straight, in a grid.'],
  [1532, 1600, '街巷大多贴着河走。', 'Most streets followed the water.'],
  [1614, 1736, '平江路一带，不少人家前门开在街上，后门出去就是河。', 'Along Pingjiang Road, many houses open onto the street in front and onto the canal behind.'],
  [1750, 1874, '近八百年后，许多街巷水道还对得上。', 'Nearly eight centuries on, many streets and canals still line up.'],
  [1886, 2008, '这块碑，今天立在苏州文庙。', 'The stele stands today in the Confucian Temple of Suzhou.'],
  // 05 →
  [2026, 2112, '明清两代，这里是全国最富庶的城市之一。', 'Under the Ming and Qing, it was one of the richest cities in China.'],
  [2118, 2196, '有钱人家修园子，把水引进了院里。', 'Wealthy families built gardens and brought the water inside.'],
  [0, 0, '1509年，王献臣在城东北开始修拙政园。', "In 1509, Wang Xianchen began the Humble Administrator's Garden in the northeast of the city."],
  [2204, 2322, '1759年，徐扬画的《姑苏繁华图》长12米，画了一万两千多人。', 'In 1759, Xu Yang painted the city on a 12-metre scroll, with more than 12,000 people in it.'],
  [2336, 2398, '1860年，战火烧到阊门外。', 'In 1860, war reached Chang Gate.'],
  [2404, 2466, '山塘的街市几乎烧光了。', "Shantang's market streets were almost all burned."],
  [2490, 2570, '1982年，苏州成为首批国家历史文化名城。', "In 1982, Suzhou became one of China's first historic cities."],
  [2580, 2660, '1986年的总体规划写明“全面保护古城风貌”。', 'The 1986 master plan called for "full protection of the old city\'s character".'],
  [2676, 2770, '平江路和山塘街后来都整修过，河街并行的格局留了下来。', 'Pingjiang Road and Shantang Street were later restored, their streets still running beside the canals.'],
  [2786, 2890, '盘门、胥门、阊门、相门一带的城墙和城门，也陆续修缮。', 'The walls and gates around Pan, Xu, Chang and Xiang Gates were repaired one after another.'],
  [2912, 3030, '新城区放在了护城河外，一东一西。', 'The new districts went outside the moat, one to the east and one to the west.'],
  [3038, 3186, '1990年先建西边的新区，四年后，东边的工业园区开工。', 'The western district came first, in 1990. Four years later, work began on the industrial park in the east.'],
  [0, 0, '工业园区由中国和新加坡两国政府合作开发。', 'The park was developed jointly by the governments of China and Singapore.'],
  [3200, 3318, '东边最高的楼是苏州国际金融中心，450米。', 'The tallest tower in the east, Suzhou IFS, is 450 m.'],
  [3326, 3450, '古城里的房子大多不到25米，北寺塔有76米。', 'Most buildings in the old city are under 25 m. North Temple Pagoda is 76 m.'],
  [3466, 3560, '从高处看，苏州城里城外仍然到处是河。', 'From above, Suzhou is still full of canals, inside the old city and out.'],
  [3568, 3660, '其中不少河道，在1229年的碑上就已经刻着。', 'Many of them were already carved on the stele in 1229.'],
  [3668, 3762, '“君到姑苏见，人家尽枕河。”—— 杜荀鹤', '"Come to Gusu, and you will see every home pillowed on the river." — Du Xunhe, Tang'],
];
export const SUBS = SUB_TEXT.map(([, , cn, en], i) => {
  const [v0, n] = VO[i];
  const next = VO[i + 1]?.[0] ?? TOTAL;
  return [v0 - 3, Math.min(v0 + n + 14, next - 5), cn, en];
});

// ---------- callouts: [f0, f1, worldXY(local m), heightM, cn, en, side] ----------
export const CALLOUTS = [
  [300, 425, [16208, 7100], 10, '草鞋山遗址 · 约六千年前的水田', 'Caoxieshan · rice paddies, c. 6,000 years ago', 'right'],
  [600, 738, [-1110, -2420], 12, '盘门 · 今存水陆城门', 'Pan Gate · land and water gates survive', 'right'],
  [760, 840, [-180, 100], 10, '苏州 · 589', 'Suzhou · named after Mount Gusu', 'right'],
  [862, 990, [-7175, 2679], 6, '江南运河 · 610', 'Jiangnan Canal · 610', 'right'],
  [1140, 1205, [-3536, 1892], 6, '七里山塘 · 825', 'Shantang canal · 825', 'right'],
  [1240, 1300, [-4439, 2993], 48, '虎丘塔 · 961 · 塔顶偏离 2.34 m', 'Tiger Hill Pagoda · 961 · top 2.34 m off centre', 'right'],
  [1700, 1780, [585, 765], 4, '平江路 · 河街并行', 'Pingjiang Road · canal beside street', 'right'],
  [1890, 2008, [-353, -1511], 6, '苏州文庙 · 平江图碑藏于此', 'Confucian Temple · home of the stele', 'right'],
  [2150, 2204, [139, 1668], 6, '拙政园 · 1509 始建 · 世界遗产', "Humble Administrator's Garden · begun 1509 · World Heritage", 'right'],
  [2214, 2322, [-1735, -1190], 8, '《姑苏繁华图》路线 · 示意', 'Route of the 1759 scroll · illustrative', 'right'],
  [2684, 2774, [585, 765], 4, '平江路 · 2002 起整修', 'Pingjiang Road · restored from 2002', 'right'],
  [2684, 2774, [-3536, 1892], 6, '山塘街 · 2002 起修复', 'Shantang Street · restored from 2002', 'left'],
  [2794, 2896, [-1110, -2418], 12, '盘门 · 1986 城楼原址重建', 'Pan Gate · tower rebuilt on its base, 1986', 'left'],
  [2800, 2896, [-1485, -1145], 12, '胥门 · 2003 起修缮', 'Xu Gate · repairs from 2003', 'left'],
  [2806, 2896, [-2122, 703], 12, '阊门 · 2006 城楼重建', 'Chang Gate · tower rebuilt, 2006', 'left'],
  [2812, 2896, [1266, 429], 16, '相门 · 2012 修缮完工', 'Xiang Gate · restoration completed, 2012', 'right'],
  [2930, 3096, [-5500, -1300], 10, '苏州新区 · 1990', 'Suzhou New District · 1990', 'left'],
  [3104, 3186, [4600, 800], 10, '苏州工业园区 · 1994', 'Suzhou Industrial Park · 1994', 'right'],
  [3212, 3318, [8528, 1465], 450, '苏州国际金融中心 · 450 m', 'Suzhou IFS · 450 m', 'right'],
  [3232, 3318, [4930, 890], 300, '东方之门 · 301.8 m', 'Gate of the Orient · 301.8 m', 'left'],
  [3392, 3450, [-718, 1344], 76, '北寺塔 · 76 m', 'North Temple Pagoda · 76 m', 'right'],
];

// ---------- small HUD notes (illustrative layers, hedges): [f0, f1, cn, en] ----------
export const NOTES = [
  [6, 236, '平江图碑旧照 · 线稿为示意重绘', 'Pingjiang stele, old photo · lines redrawn, illustrative'],
  [446, 738, '门位示意 · 城址据《吴越春秋》《越绝书》，学界尚有讨论', 'Gate positions illustrative · site per ancient texts, still debated'],
  [1016, 1124, '桥位取今日 OSM 桥梁 · 示意', "Bridge positions from today's OSM · illustrative"],
  [1372, 1622, '平江图碑旧照 ·《亚细亚大观》· 线稿为示意重绘', 'Pingjiang stele, old photo (Asia Taikan) · lines illustrative'],
  [1626, 1700, '卫星图：Sentinel-2 · EOX', 'Satellite: Sentinel-2 · EOX'],
  [1704, 1792, '平江图 · 示意重绘', 'Pingjiang Map · illustrative redraw'],
  [1796, 1884, '卫星图：Sentinel-2 · EOX', 'Satellite: Sentinel-2 · EOX'],
  [1888, 2008, '平江图 · 示意重绘', 'Pingjiang Map · illustrative redraw'],
  [2204, 2322, '路线示意', 'Route illustrative'],
  [2336, 2466, '范围示意', 'Extent illustrative'],
  [3540, 3740, '平江图碑旧照与示意重绘', 'Pingjiang stele, old photo and redraw'],
];

// ---------- camera keys: [frame, {tx, ty, dist, az, pitch, fov}] ----------
// az: heading the camera looks toward (deg, 0 = north, 90 = east). pitch: 90 = straight down.
// Two keys one frame apart make a cut at a chapter boundary.
const CITY = { tx: -180, ty: 0 };
const K = (tx, ty, dist, az, pitch, fov = 30) => ({ tx, ty, dist, az, pitch, fov });
export const CAM_KEYS = [
  // cold
  [0, { ...CITY, dist: 9400, az: 0, pitch: 89.5, fov: 30 }],
  [96, { ...CITY, dist: 9100, az: 0, pitch: 89.5, fov: 30 }],
  [200, K(-100, 300, 8200, -16, 46)],
  [240, K(-60, 400, 8600, -18, 44)],
  // 00 前史: pull out east over the water network, settle on Caoxieshan
  [304, K(5400, 2900, 23000, 4, 54)],
  [431, K(15900, 6800, 5600, 14, 42)],
  // 01 建城 (cut)
  [432, { ...CITY, tx: -200, ty: -60, dist: 11800, az: 0, pitch: 89.5, fov: 30 }],
  [743, { ...CITY, tx: -200, ty: -60, dist: 10200, az: -4, pitch: 89.5, fov: 30 }],
  // 02 苏州 · 运河 (cut): wide from the south-east, the canal comes in from the north-west
  [744, K(-2700, 1500, 12500, -40, 52)],
  [848, K(-4300, 2700, 15500, -40, 50)],
  [1008, K(-900, 500, 7000, -26, 50)],
  // 03 唐 · 桥
  [1100, K(-300, 300, 5200, -18, 47)],
  [1132, K(-1300, 700, 4600, -30, 42)],
  [1205, K(-3500, 2300, 3000, -42, 34)],
  [1234, K(-4420, 2960, 560, -35, 15, 34)],
  [1282, K(-4439, 2993, 450, -21, 13, 34)],
  // 04 平江图: one continuous pull-back off Tiger Hill to the city seen from straight above; the city turns to stone
  // and becomes the stele (follow: the target trails the zoom so the pagoda leaves frame late)
  [1408, { ...CITY, dist: 11600, az: 0, pitch: 89.5, fov: 30, follow: 1 }],
  [1588, { ...CITY, dist: 10200, az: 0, pitch: 89.5, fov: 30 }],
  [1662, K(-120, 80, 9300, 0, 89.5)],
  [1745, K(600, 640, 1150, -10, 24, 34)],
  [1782, K(575, 800, 1080, -11, 23, 34)],
  [1862, K(-60, -60, 7600, -12, 52)],
  [1894, K(-250, -900, 4200, -8, 48)],
  [2016, K(-330, -1350, 3300, -6, 46)],
  // 05 明清: wide, then north-east onto the gardens (拙政园 at 139,1668, 狮子林 beside it) while they are named,
  // then west along the 1759 scroll route
  [2110, K(-300, 300, 6000, -12, 52)],
  [2170, K(170, 1180, 2900, -8, 42)],
  [2202, K(150, 1560, 1750, -4, 34, 32)],
  [2264, K(-1500, -700, 4800, -20, 46)],
  [2328, K(-2500, 1000, 3200, -38, 34)],
  // 06 1860
  [2400, K(-3000, 1600, 2700, -45, 32)],
  [2471, K(-3700, 2250, 2500, -48, 31)],
  // 07 保护 (cut): the old city, then wide over Pingjiang Road and Shantang, then down on the restored walls
  [2472, K(-180, 0, 7600, -28, 42)],
  [2580, K(-180, 0, 7200, -6, 44)],
  [2690, K(-1500, 900, 9800, -18, 52)],
  // (保护, continued)
  [2780, { ...CITY, tx: -200, ty: -60, dist: 10600, az: 0, pitch: 89.5, fov: 30 }],
  [2904, { ...CITY, tx: -200, ty: -60, dist: 11200, az: 0, pitch: 89.5, fov: 30 }],
  // 09 两翼
  [2990, K(3500, 900, 29000, 0, 64)],
  [3191, K(3200, 700, 26500, 6, 56)],
  // 10 高度 (cut): low, looking east at the towers, then a swing west to the old city
  [3192, K(6300, 750, 4300, 76, 16, 32)],
  [3320, K(6700, 850, 3900, 82, 14, 32)],
  [3385, K(-560, 1250, 2300, -96, 13, 32)],
  [3455, K(-700, 1300, 1750, -92, 12, 32)],
  // 11 枕河 (cut): top-down over everything, settling on the old city
  [3456, K(2600, 1700, 30000, 0, 89.5)],
  [3768, K(200, 500, 12500, 0, 89.5)],
  // end: the board recedes
  [3960, K(2300, 1400, 30000, 6, 66)], // farther out, the edge of the map board shows
];

function camAt(f) {
  const k = CAM_KEYS;
  if (f <= k[0][0]) return { ...k[0][1] };
  for (let i = 1; i < k.length; i++) {
    if (f <= k[i][0]) {
      const [f0, a] = k[i - 1], [f1, b] = k[i];
      // keys one frame apart are a cut; the warped story time lands between them, so never blend across
      if (f1 - f0 <= 1) return { ...(f < f1 ? a : b) };
      const t = smoother((f - f0) / Math.max(1, f1 - f0));
      // log-space distance so push-ins feel even
      const out = {};
      for (const key of ['tx', 'ty', 'dist', 'az', 'pitch', 'fov']) {
        out[key] = key === 'dist' ? Math.exp(lerp(Math.log(a[key]), Math.log(b[key]), t)) : lerp(a[key], b[key], t);
      }
      if (b.follow) {
        // target moves with linear distance, not log distance: it stays on the subject until the view is wide
        const lin = (out.dist - a.dist) / (b.dist - a.dist);
        out.tx = lerp(a.tx, b.tx, lin); out.ty = lerp(a.ty, b.ty, lin);
      }
      return out;
    }
  }
  return { ...k[k.length - 1][1] };
}

// ---------- buildings: each one rises once, in story order ----------
// Old city: from the founding (01) to the Ming-Qing peak, centre first with some noise. Shantang corridor:
// from Bai Juyi's canal to 1759. Outside the moat: CMAB's '1985 or earlier' blocks rise through the protection chapter,
// nearest first; later blocks by their CMAB year through the two wings. Illustrative: today's buildings
// stand in for the city of each age.
const OLD_CITY_FILL = [[460, 0], [744, 0.18], [1008, 0.38], [1320, 0.62], [1440, 0.8], [2016, 0.9], [2200, 1]];
const SHANTANG_FILL = [[1141, 0], [1320, 0.3], [2016, 0.55], [2206, 1]];
const OUTER_OLD_FILL = [[2478, 0], [2898, 1]];
const YEAR_FRAMES = [[2560, 1982], [2904, 1990], [3040, 1994], [3192, 2018], [3456, 2025]];
export const RISE = 24; // story frames for one building to rise
const interp = (keys, x, ix = 0, iy = 1) => {
  if (x <= keys[0][ix]) return keys[0][iy];
  for (let i = 1; i < keys.length; i++) {
    if (x <= keys[i][ix]) { const a = keys[i - 1], b = keys[i]; return a[iy] + (b[iy] - a[iy]) * (x - a[ix]) / (b[ix] - a[ix]); }
  }
  return keys[keys.length - 1][iy];
};
const clamp01b = (x) => Math.min(1, Math.max(0, x));
// zone: 0 old city, else outside; corr: Shantang corridor parameter (>= 0 inside it); age: CMAB year
export function revealFrame(zone, rnd, age, x, y, corr) {
  if (zone === 0) {
    const u = clamp01b(0.6 * clamp01b(Math.hypot(x + 150, y + 100) / 2700) + 0.4 * rnd);
    return interp(OLD_CITY_FILL, u, 1, 0);
  }
  if (corr >= 0) return interp(SHANTANG_FILL, clamp01b(0.5 * corr + 0.5 * rnd), 1, 0);
  if (age < 1985) return interp(OUTER_OLD_FILL, clamp01b(0.55 * clamp01b((Math.hypot(x + 150, y + 100) - 2500) / 9000) + 0.45 * rnd), 1, 0);
  return interp(YEAR_FRAMES, age + rnd * 0.99, 1, 0);
}
// HUD-independent building year: drives the new-district tint/glow and the towers
const bldYearAt = (fo) => (fo < 293 ? 2030 : fo < 2560 ? 1980 : fo > 3456 ? 2030 : interp(YEAR_FRAMES, fo));

// ---------- world state tracks ----------
const T = {
  // 1 = engraved stone (ink-black board, buildings sunk), 0 = white model
  stone: track([[0, 1], [100, 1], [170, 0], [1384, 0], [1432, 1], [1660, 1], [1725, 0.12], [1785, 0.12], [1840, 0], [STORY_END, 0]]),
  // buildings: global height multiplier (which buildings stand at all comes from revealFrame)
  grow: track([[0, 0.02], [110, 0.02], [200, 1], [240, 1], [292, 0], [440, 0], [456, 1], [1384, 1], [1432, 0.03], [1600, 0.03], [1622, 0], [1662, 0], [1745, 1], [1785, 1], [1835, 0.45], [1990, 0.45], [2070, 1], [STORY_END, 1]]),
  zoneOut: track([[0, 1], [STORY_END, 1]]),
  corrGrow: track([[0, 0], [STORY_END, 0]]),
  // cold open shows today's city in full; from 00 on each building rises once, at revealFrame()
  revealAll: track([[0, 1], [292, 1], [293, 0], [STORY_END, 0]]),
  pagoda: track([[0, 0.02], [110, 0.02], [200, 1], [1384, 1], [1432, 0.03], [1665, 0.03], [1745, 1], [STORY_END, 1]]),
  towerRise: track([[0, 1], [2904, 1], [2906, 0.3], [3192, 0.3], [3300, 1], [STORY_END, 1]]),
  // roads fade into the board for the pre-modern chapters, glow gold in the finale
  roadFade: track([[0, 0], [240, 0], [292, 1], [1420, 1], [1460, 0], [2016, 0], [2060, 0.8], [2472, 0.8], [2510, 0], [STORY_END, 0]]),
  roadGlow: track([[0, 0], [3456, 0], [3530, 1], [3768, 1], [3860, 0.5], [STORY_END, 0.5]]),
  // water
  waterGlow: track([[0, 0], [240, 0], [292, 0.2], [432, 0.2], [460, 0.1], [744, 0.1], [770, 0], [3456, 0], [3530, 0.42], [3768, 0.42], [3880, 0.25], [STORY_END, 0.25]]),
  waveOn: track([[0, 0], [744, 0], [770, 1], [1010, 1], [1080, 0], [STORY_END, 0]]),
  wave: track([[0, 0], [850, 0], [990, 21500], [1080, 30000], [STORY_END, 30000]], (t) => t),
  moatGlow: track([[0, 0], [540, 0], [580, 0.5], [744, 0.5], [780, 0], [2580, 0], [2620, 0.6], [2690, 0.35], [2770, 0.35], [2796, 0.12], [2904, 0.12], [2940, 0], [STORY_END, 0]]),
  // 00 Caoxieshan
  cao: track([[0, 0], [262, 0], [310, 1], [425, 1], [432, 0], [STORY_END, 0]]),
  // 01 moat line, gates, wall
  moatDraw: track([[0, 0], [446, 0], [560, 1], [STORY_END, 1]]),
  moatLine: track([[0, 0], [440, 0], [450, 1], [744, 1], [760, 0.7], [1000, 0.7], [1030, 0], [STORY_END, 0]]),
  gates: track([[0, 0], [566, 0], [660, 1], [STORY_END, 1]], (t) => t),
  gatesOn: track([[0, 0], [560, 0], [570, 1], [744, 1], [790, 0], [STORY_END, 0]]),
  wallFull: track([[0, 0], [580, 0], [660, 1], [1384, 1], [1432, 0], [2016, 0], [2060, 1], [2471, 1], [2472, 0], [STORY_END, 0]]),
  wallKeep: track([[0, 0], [110, 0], [200, 1], [240, 1], [292, 0], [580, 0], [660, 1], [1384, 1], [1432, 0.03], [1665, 0.03], [1745, 1], [STORY_END, 1]]),
  wallGone: track([[0, 0], [2471, 0], [2472, 1.03], [STORY_END, 1.03]], (t) => t),
  wallLine: track([[0, 0], [2770, 0], [2796, 1], [2890, 1], [2904, 0], [STORY_END, 0]]),
  keepGlow: track([[0, 0], [2770, 0], [2800, 1], [2890, 1], [2910, 0], [STORY_END, 0]]),
  // 03 bridges and Shantang (the Shantang line is reused as the fire front in 06)
  bridges: track([[0, 0], [1018, 0], [1112, 1], [STORY_END, 1]], (t) => t),
  bridgesOn: track([[0, 0], [1010, 0], [1018, 1], [1300, 1], [1345, 0], [STORY_END, 0]]),
  shantang: track([[0, 0], [1134, 0], [1206, 1], [2328, 1], [2330, 0], [2336, 0], [2466, 1], [STORY_END, 1]]),
  shantangOn: track([[0, 0], [1128, 0], [1136, 1], [1220, 1], [1236, 0], [2330, 0], [2338, 1], [2471, 1], [2472, 0], [STORY_END, 0]]),
  // 04 Pingjiang (+ lost canals in 07, the finale in 11)
  pjOpacity: track([[0, 1], [236, 1], [262, 0], [1440, 0], [1450, 1], [1990, 1], [2016, 0], [3540, 0], [3590, 1], [3740, 1], [3768, 0], [STORY_END, 0]]),
  pjDraw: track([[0, 0], [10, 0], [92, 1], [1320, 1], [1321, 0], [1450, 0], [1536, 1], [STORY_END, 1]]),
  pjMorph: track([[0, 0], [104, 0], [196, 1], [1406, 1], [1468, 0], [1586, 0], [1652, 1], [STORY_END, 1]]),
  canalV: track([[0, 0], [1478, 0], [1504, 1], [1590, 1], [1630, 0.45], [STORY_END, 0.45]]),
  canalH: track([[0, 0], [1498, 0], [1526, 1], [1590, 1], [1630, 0.45], [STORY_END, 0.45]]),
  street: track([[0, 0], [1536, 0], [1566, 1], [1700, 1], [1760, 0.35], [STORY_END, 0.35]]),
  match: track([[0, 0], [1790, 0], [1830, 1], [1990, 1], [2016, 0], [3540, 0], [3590, 1], [3768, 1], [3780, 0], [STORY_END, 0]]),
  lost: track([[0, 0], [STORY_END, 0]]),
  // the stele itself: old photo under the lines (cold open, the stele beat, the finale), then the satellite view
  photo: track([[0, 0.62], [70, 0.62], [150, 0], [1372, 0], [1422, 0.85], [1500, 0.85], [1590, 0.35], [1650, 0.14], [1700, 0], [3540, 0], [3600, 0.55], [3740, 0.55], [3768, 0], [STORY_END, 0]]),
  photoBlur: track([[0, 0], [40, 0], [130, 1], [1360, 1], [1361, 0], [1500, 0], [1592, 1], [3500, 1], [3501, 0.35], [STORY_END, 0.35]]),
  photoLines: track([[0, 0], [3500, 0], [3501, 1], [STORY_END, 1]]),
  sat: track([[0, 0], [1622, 0], [1678, 0.8], [1700, 0.8], [1735, 0], [1792, 0], [1832, 0.72], [1878, 0.72], [1908, 0], [STORY_END, 0]]),
  // 05 Ming-Qing
  fenqiang: track([[0, 0], [2016, 0], [2064, 1], [2472, 1], [2500, 0], [STORY_END, 0]]),
  gardens: track([[0, 0], [2112, 0], [2150, 1], [2328, 1], [2350, 0], [STORY_END, 0]]),
  route: track([[0, 0], [2204, 0], [2316, 1], [STORY_END, 1]]),
  routeOn: track([[0, 0], [2200, 0], [2210, 1], [2328, 1], [2340, 0], [STORY_END, 0]]),
  // 06 fire
  fire: track([[0, 0], [2336, 0], [2466, 1.2], [STORY_END, 1.2]], (t) => t),
  fireOn: track([[0, 0], [2330, 0], [2336, 1], [2471, 1], [2472, 0], [STORY_END, 0]]),
  // 07 gray city, 08 gold frame
  gray: track([[0, 0], [STORY_END, 0]]),
  frame: track([[0, 0], [2580, 0], [2660, 1], [STORY_END, 1]]),
  frameOn: track([[0, 0], [2574, 0], [2582, 1], [2770, 1], [2796, 0.15], [2904, 0.15], [2940, 0], [STORY_END, 0]]),
  // 09 wings, 10 heights, 11 weave
  newTint: track([[0, 0], [2940, 0], [2970, 1], [3192, 1], [3230, 0], [STORY_END, 0]]),
  fresh: track([[0, 0], [2958, 0], [2972, 1], [3172, 1], [3192, 0], [STORY_END, 0]]),
  ramp: track([[0, 0], [3192, 0], [3236, 1], [3456, 1], [3490, 0], [STORY_END, 0]]),
  dim: track([[0, 0], [3456, 0], [3520, 0.7], [3768, 0.7], [3860, 0.55], [STORY_END, 0.55]]),
  // grade
  exposure: track([[0, 1], [2200, 1], [2260, 0.84], [2328, 0.84], [2400, 0.74], [2472, 0.74], [2500, 1], [3768, 1], [3840, 0.5], [STORY_END, 0.5]]),
  bloom: track([[0, 0.5], [3456, 0.5], [3520, 0.62], [STORY_END, 0.62]]),
  fade: track([[0, 1], [3920, 1], [3960, 0]]),
  title: track([[0, 0], [3790, 0], [3836, 1], [3932, 1], [3956, 0]]),
  callig: track([[0, 0], [3800, 0], [3862, 1], [STORY_END, 1]], (t) => t),
  hudPlace: track([[0, 0], [196, 0], [232, 1], [3768, 1], [3800, 0], [STORY_END, 0]]),
};

const chapterAt = (f) => CHAPTERS.find((c) => f >= c.f0 && f < c.f1) || CHAPTERS[CHAPTERS.length - 1];

function yearAt(ch, f) {
  const ys = ch.years;
  let y = ys[0][1];
  for (let i = 0; i < ys.length; i++) if (f >= ys[i][0]) y = ys[i][1];
  // roll between consecutive keys over 24 frames
  for (let i = 1; i < ys.length; i++) {
    const [fk, yk] = ys[i];
    if (f >= fk && f < fk + 24) y = Math.round(lerp(ys[i - 1][1], yk, smoother((f - fk) / 24)));
  }
  return y;
}

export function stateAt(film) {
  const f = toStory(film);
  const ch = chapterAt(f);
  const s = { f: film, fo: f, cam: camAt(f), chapter: ch };
  for (const [k, fn] of Object.entries(T)) s[k] = fn(f);
  s.bldYear = bldYearAt(f);
  // chapter card
  let big = null;
  for (const b of ch.big) if (f >= b[0]) big = b;
  s.card = big && ch.idx ? {
    alpha: window01(f, ch.f0 + 6, ch.cardOut ?? ch.f1 - 4, 12),
    bigAlpha: window01(f, big[0] + (big[0] === ch.f0 ? 6 : 0), ch.big[ch.big.indexOf(big) + 1]?.[0] ?? ch.cardOut ?? ch.f1 - 4, 10),
    idx: ch.idx, cn: ch.cn, en: ch.en, num: big[1], unit: big[2], subCn: big[3], subEn: big[4],
  } : null;
  const sub = SUBS.find(([a, b]) => film >= a - 2 && film <= b + 2);
  s.sub = sub ? { cn: sub[2], en: sub[3], alpha: window01(film, sub[0], sub[1], 8) } : null;
  s.callouts = CALLOUTS.filter(([a, b]) => f >= a && f <= b).map(([a, b, xy, h, cn, en, side]) => ({ xy, h, cn, en, side, alpha: window01(f, a, b, 10) }));
  const note = NOTES.find(([a, b]) => f >= a && f <= b);
  s.note = note ? { cn: note[2], en: note[3], alpha: window01(f, note[0], note[1], 10) } : null;
  s.year = ch.yearRamp ? Math.round(interp(ch.years, f)) : yearAt(ch, f);
  s.pagodaYear = s.year;
  return s;
}
