// Inside the café: the cup at eye level, the corner seat seen from behind her, the chair opposite, the whole shop.
import { W, H, PAL, rgba, L, S, inSet, camT, camK, toScreen, glow, lamp, shadePool, rain, ring, bokeh, steam, pen, chalk, circlePts, MAN, IM, clamp, lerp, sstep, hash, noise1, makeCanvas, TAU, E } from './stage.js';
import { TM, B, T0, CT, beatNear, beatIdx, kickN, since, ramp } from './core.js';

const [maskCv, maskCx] = makeCanvas(960, 540);
const half = (cx) => { cx.setTransform(0.5, 0, 0, 0.5, 0, 0); cx.globalAlpha = 1; cx.globalCompositeOperation = 'source-over'; cx.clearRect(0, 0, W, H); return cx; };
const ASP = W / H;
// something hanging from a point above it: swings about the top of its cord
function hang(c, set, cam, name, x, y, s, ang, p = 1) {
  const m = MAN[name], Lc = m.ay * s;
  c.save(); camT(c, set, cam, p); c.translate(x, y - Lc); c.rotate(ang); c.translate(0, Lc); c.scale(s, s); c.drawImage(IM[name], m.ox - m.ax, m.oy - m.ay); c.restore();
  return [x - Math.sin(ang) * Lc, y - Lc + Math.cos(ang) * Lc];
}

// ================================================================ the cup at eye level
const CS = 'cup', SAUCER = [1330, 1160], BASE = [1330, 1128];
// lift 0..1 takes the cup up and to the right, to a mouth we never see. o.empty: the coffee is gone
function cupScene(c, cam, t, o = {}) {
  const lift = o.lift ?? 0, grip = o.grip ?? 0, night = o.night ?? 0;
  L(c, CS, cam, 'cs_bg');
  // the street's lights through the window, and the rain between
  c.save(); camT(c, CS, cam, 1); c.beginPath(); c.rect(0, 0, 1490, 850); c.clip(); c.setTransform(1, 0, 0, 1, 0, 0);
  if (night) { c.globalCompositeOperation = 'multiply'; c.fillStyle = rgba([70, 86, 140], night); c.fillRect(0, 0, W, H); c.globalCompositeOperation = 'source-over'; }
  bokeh(c, t, { n: 30, a: 0.42 + 0.3 * night, y0: H * 0.16, y1: H * 0.62, r: 44, seed: o.seed ?? 41, v: 50 });
  rain(c, t, { n: 90, a: 0.16, len: 80, seed: 8 });
  c.restore();
  inSet(c, CS, cam, 1, () => { lamp(c, 2150, 280, 760, t, 0.55 + 0.12 * kickN(t, 2), { seed: 3 }); glow(c, 1500, 1160, 900, PAL.amber, 0.14 + 0.05 * kickN(t, 2), { sy: 0.35 }); });
  S(c, CS, cam, 'cs_saucer', SAUCER[0], SAUCER[1]);
  const cx = BASE[0] + 200 * lift * lift, cy = BASE[1] - 600 * E.inOutQuad(lift), rot = 0.46 * lift;
  {
    S(c, CS, cam, 'cs_cup', cx, cy, 1, { r: rot });
    if (o.empty) inSet(c, CS, cam, 1, () => { c.save(); c.translate(cx, cy); c.rotate(rot); c.fillStyle = 'rgb(236,224,198)'; c.beginPath(); c.ellipse(0, -330, 266, 39, 0, 0, TAU); c.fill(); c.strokeStyle = 'rgba(120,80,52,0.55)'; c.lineWidth = 5; c.beginPath(); c.ellipse(0, -326, 236, 30, 0, 0.2, 3.3); c.stroke(); c.fillStyle = 'rgba(92,58,40,0.6)'; c.beginPath(); c.ellipse(30, -318, 110, 14, 0, 0, TAU); c.fill(); c.restore(); });
    if (grip > 0.003) { const hx = cx + 370 * Math.cos(rot) + 190 * Math.sin(rot), hy = cy + 370 * Math.sin(rot) - 190 * Math.cos(rot); S(c, CS, cam, 'cs_hand', hx + 900 * (1 - grip), hy + 120 * (1 - grip), 1, { r: rot * 0.8 }); }
  }
  if (!o.empty && o.steam !== 0) inSet(c, CS, cam, 1, () => steam(c, t, cx, cy - 350, { h: 640, w: 74, a: 0.40 * (o.steam ?? 1) * (1 - lift), sway: 120, n: 30, per: 0.26, seed: 4, bend: o.bend, blend: 'source-over' }));
  return [cx, cy, rot];
}
function cupGlass(cam, t, cupPos, grip, lift) {      // rain on the pane behind the cup, not on the cup
  const m = half(maskCx);
  inSet(m, CS, cam, 1, () => { m.fillStyle = '#fff'; m.fillRect(0, 0, 1480, 846); });
  { S(m, CS, cam, 'cs_cup', cupPos[0], cupPos[1], 1, { r: cupPos[2], blend: 'destination-out' }); if (grip > 0.5) { const [cx, cy, rot] = cupPos; S(m, CS, cam, 'cs_hand', cx + 370 * Math.cos(rot) + 190 * Math.sin(rot), cy + 370 * Math.sin(rot) - 190 * Math.cos(rot), 1, { r: rot * 0.8, blend: 'destination-out' }); } }
  return maskCv;
}
// CH1 「下雨天 喝咖啡」
export function hero(c, t, lt, sh) {
  const cam = camK(t, [[sh.t0, 1330, 800, 2360], [sh.t1, 1360, 790, 1960]], { ease: 'out', drift: 4 });
  const pos = cupScene(c, cam, t, { steam: 1.2 });
  return { glass: { rain: 0.6, beads: 0.5, fog: 0.5, mask: cupGlass(cam, t, pos, 0, 0), seed: 50 }, grade: { warm: 0.3, bloom: 0.9, sat: 1.08 } };
}
// CH1 「独身主义的余味 / 在舌尖慢慢…」: the hand, the lift, the sip, the cup set down; then the picture itself lets go.
export function sip(c, t, lt, sh) {
  const g0 = sh.t0 + 0.1, up = T0(12) + 0.7, down = T0(13) + 0.5;
  const grip = ramp(t, g0, 0.55, 'out'), lift = ramp(t, up, 0.9, 'io') * (1 - ramp(t, down, 1.0, 'io'));
  const cam = camK(t, [[sh.t0, 1400, 800, 2050], [up + 0.9, 1480, 600, 2050], [down + 1.0, 1400, 800, 2000], [sh.t1 + 2, 1360, 790, 1900]], { drift: 4 });
  const pos = cupScene(c, cam, t, { lift, grip, steam: 1.1 + 1.2 * ramp(t, down + 0.9, 0.4) * (1 - ramp(t, down + 2, 1.5)), seed: 43 });
  return { glass: { rain: 0.6, beads: 0.5, fog: 0.5, mask: cupGlass(cam, t, pos, grip, lift), seed: 50 }, grade: { warm: 0.3, bloom: 0.9, sat: 1.08 } };
}
// CH2 「独身主义的余味」, at night, seen from the street through the wet window
export function sipNight(c, t, lt, sh) {
  const grip = 1, lift = ramp(t, sh.t0 + 0.5, 1.0, 'io') * (1 - ramp(t, sh.t1 - 0.2, 1.0, 'io'));
  const cam = camK(t, [[sh.t0, 1500, 820, 2300], [sh.t1, 1440, 760, 1960]], { drift: 5 });
  cupScene(c, cam, t, { lift: lift * 0.7, grip, steam: 1.3, night: 0.75, seed: 47 });
  return { glass: { rain: 0.75, beads: 0.5, fog: 0.32, scale: 0.75, seed: 60, fogCol: [0.55, 0.62, 0.72] }, grade: { warm: 0.2, bloom: 1.1, sat: 1.15, vig: 0.6 } };
}
// BRIDGE 「我抿一口 微苦的温柔」: the room has gone grey with other people's questions. Colour comes back from the cup.
export function sipWarm(c, t, lt, sh) {
  const lift = ramp(t, sh.t0 + 0.5, 1.0, 'io') * (1 - ramp(t, CT(34, 4) + 0.1, 1.1, 'io'));
  const cam = camK(t, [[sh.t0, 1380, 800, 1900], [sh.t1, 1380, 780, 2200]], { drift: 4 });
  const [cx, cy] = cupScene(c, cam, t, { lift: lift * 0.8, grip: 1, steam: 1.4, seed: 44 });
  const [sx, sy] = toScreen(CS, cam, BASE[0], BASE[1] - 200), r = lerp(0.0, 0.62, ramp(t, CT(34, 2), sh.t1 - CT(34, 2) + 0.2, 'io'));
  return { grade: { sat: 0.10, cold: 0.75, satIn: 1.1, wave: [sx / H, sy / H, r], warm: 0.25, bloom: 0.9 } };
}
// CH3 「独身主义的余味」: the last of it
export function lastSip(c, t, lt, sh) {
  const u = ramp(t, sh.t0 + 0.15, 0.7, 'io') * (1 - ramp(t, sh.t1 - 1.25, 0.9, 'io')), empty = t > sh.t0 + 1.0;
  const cam = camK(t, [[sh.t0, 1440, 640, 2100], [sh.t1, 1360, 800, 1850]], { drift: 4 });
  cupScene(c, cam, t, { lift: u, grip: 1, steam: empty ? 0 : 1, empty, seed: 45 });
  return { grade: { warm: 0.42, bloom: 1.0, sat: 1.12 } };
}

// ================================================================ the corner, from behind her
const CN = 'corner', PL = MAN.cn_bg.place, FAR = [2090, 1060, 0.80], FIG = [1320, 1420], TBL = [1770, 1470, 1.1], LMP = [1770, 430, 0.72];
const COAT_ON = [FAR[0] + MAN.ch_coat.on_chair[0] * FAR[2], FAR[1] + MAN.ch_coat.on_chair[1] * FAR[2]];
// o: coat ('on' | [x, y, r, s, a] | null), fig ('sit' | 'none' | custom fn), lampLv, cupEmpty
function cornerRoom(c, cam, t, o = {}) {
  L(c, CN, cam, 'cn_bg');
  // rain light: slow soft bars crossing the floor and the wall from the window
  inSet(c, CN, cam, 1, () => {
    c.save(); c.globalCompositeOperation = 'multiply';
    for (let i = 0; i < 7; i++) { const x = ((i * 300 + t * 26) % 2100) - 100, g = c.createLinearGradient(x, 0, x + 120, 0); g.addColorStop(0, 'rgba(70,84,130,0)'); g.addColorStop(0.5, `rgba(70,84,130,${0.07 + 0.04 * hash(i)})`); g.addColorStop(1, 'rgba(70,84,130,0)'); c.fillStyle = g; c.save(); c.transform(1, 0, 0.5, 1, 0, 0); c.fillRect(x - 400, 880, 120, 800); c.restore(); }
    c.restore();
  });
  const lv = o.lampLv ?? 1, fs = FAR[2];
  inSet(c, CN, cam, 1, () => glow(c, 1900, 640, 900, PAL.amber, 0.16 * lv));
  S(c, CN, cam, 'ch_chair_sh', FAR[0], FAR[1], 1, { s: fs, a: 0.8 });
  S(c, CN, cam, 'ch_chair', FAR[0], FAR[1], 1, { s: fs });
  if (o.coat === 'on') { S(c, CN, cam, 'ch_coat_sh', COAT_ON[0], COAT_ON[1], 1, { s: fs, a: 0.8 }); S(c, CN, cam, 'ch_coat', COAT_ON[0], COAT_ON[1], 1, { s: fs }); }
  S(c, CN, cam, 'cn_table', TBL[0], TBL[1], 1, { s: TBL[2] });
  const cupX = 1690, cupY = TBL[1] - 378 * TBL[2] - 6;
  S(c, CN, cam, 'cs_saucer', cupX, cupY + 6, 1, { s: 0.17 });
  S(c, CN, cam, 'cs_cup', cupX, cupY, 1, { s: 0.17 });
  if (!o.cupEmpty) inSet(c, CN, cam, 1, () => steam(c, t, cupX, cupY - 62, { h: 260, w: 16, a: 0.3, sway: 40, n: 22, per: 0.3, seed: 6 }));
  if (o.fig !== 'none') {
    S(c, CN, cam, 'ch_chair', FIG[0], FIG[1], 1, { s: 1 });
    if (typeof o.fig === 'function') o.fig(); else S(c, CN, cam, 'fig_sit', FIG[0], FIG[1] - 12 + 3 * Math.sin(t * 1.1), 1, { s: 1.0, sy: 1 + 0.006 * Math.sin(t * 1.1) });
    c.save(); camT(c, CN, cam, 1); c.beginPath(); c.rect(FIG[0] - 400, FIG[1] - 760, 800, 735); c.clip(); c.setTransform(1, 0, 0, 1, 0, 0);     // her chair's back is on our side of her
    S(c, CN, cam, 'ch_chair', FIG[0], FIG[1], 1, { s: 1 }); c.restore();
  } else S(c, CN, cam, 'ch_chair', FIG[0], FIG[1], 1, { s: 1 });
  if (Array.isArray(o.coat)) S(c, CN, cam, 'ch_coat', o.coat[0], o.coat[1], 1, { r: o.coat[2], s: o.coat[3], a: o.coat[4] ?? 1, sx: o.coat[5] ?? 1 });
  const sw = 0.014 * Math.sin(t * 0.8) + (o.swing || 0);
  const [bx, by] = hang(c, CN, cam, 'lamp_pendant', LMP[0], LMP[1], LMP[2], sw);
  inSet(c, CN, cam, 1, () => { lamp(c, bx, by + 8, 640, t, 0.8 * lv); glow(c, TBL[0], TBL[1] - 400, 520, PAL.warm, 0.20 * lv, { sy: 0.3 }); });
}
function cornerMask(cam, extra) {
  const m = half(maskCx);
  inSet(m, CN, cam, 1, () => { m.fillStyle = '#fff'; for (const p of MAN.cn_bg.panes) m.fillRect(p[0], p[1], p[2] - p[0], p[3] - p[1]); });
  if (extra) extra(m);
  return maskCv;
}
// the coat's flight between her and the chair opposite: u 0 (with her) → 1 (draped)
function coatFlight(u) {
  const a = [FIG[0] + 150, FIG[1] - 520], b = COAT_ON, e = E.inOutCubic(clamp(u));
  const x = lerp(a[0], b[0], e), y = lerp(a[1], b[1], e) - 190 * Math.sin(e * Math.PI), settle = u > 1 ? Math.exp(-(u - 1) * 9) * Math.sin((u - 1) * 26) : 0;
  return [x, y + 14 * settle, lerp(-1.0, 0, e) + 0.05 * settle, lerp(0.42, FAR[2], e), clamp(u * 8), 1 + 0.05 * settle];
}
// V1 「角落的座位 / 只坐得下一个人」, and then the coat goes across
export function corner(c, t, lt, sh) {
  // one set-up, visited twice (the table from above is cut into the middle of it), so its clock is the song's, not the shot's
  const s0 = beatNear(30.6), e0 = T0(6) - 0.12, fly0 = e0 - 1.72, uf = (t - fly0) / 1.45;
  const cam = camK(t, [[s0, 1440, 830, 2700], [T0(5) + 2.5, 1560, 860, 2200], [e0, 1660, 820, 1950]], { drift: 3 });
  cornerRoom(c, cam, t, { coat: uf > 1.6 ? 'on' : uf > 0 ? coatFlight(uf) : null });
  return { glass: { rain: 0.6, beads: 0.5, fog: 0.3, mask: cornerMask(cam), scale: 2.0, seed: 70 }, grade: { warm: 0.18, bloom: 0.7 } };
}
// BRIDGE 「说至少此刻 / 我拥有」: the colour that began in the cup goes on through the room
export function iHave(c, t, lt, sh) {
  const cam = camK(t, [[sh.t0, 1700, 940, 1750], [sh.t1, 1470, 830, 2640]], { ease: 'io', drift: 3 });
  const on = [CT(36, 0), CT(36, 1), CT(36, 2)].filter((x) => x <= t).length;
  cornerRoom(c, cam, t, { coat: 'on', lampLv: 0.55 + 0.25 * on + 0.3 * Math.exp(-since(t, [CT(36, 0), CT(36, 1), CT(36, 2)]) * 5) });
  const [sx, sy] = toScreen(CN, cam, 1690, 1050), r = lerp(0.42, 2.6, ramp(t, sh.t0 + 0.3, CT(36, 2) - sh.t0, 'in'));
  return { glass: { rain: 0.5, beads: 0.5, fog: 0.3, mask: cornerMask(cam), scale: 2.0, seed: 70 }, grade: { sat: 0.10, cold: 0.75, satIn: 1.1, wave: [sx / H, sy / H, r], warm: 0.3, bloom: 0.9 } };
}
// CH3 「不等谁来陪」: the coat comes back to her; she gets up, and goes
export function leave(c, t, lt, sh) {
  // the coat comes back the way it went; she is already getting up to meet it
  const f0 = sh.t0 + 0.35, uf = 1 - (t - f0) / 1.25, up = ramp(t, f0 + 0.5, 1.2, 'io');
  const cam = camK(t, [[sh.t0, 1600, 850, 2250], [sh.t1 + 0.4, 1480, 800, 2050]], { drift: 3 });
  const fig = () => S(c, CN, cam, 'fig_sit', FIG[0] + 10 * up, FIG[1] - 12 - 70 * up, 1, { r: 0.03 * up });
  cornerRoom(c, cam, t, { coat: uf >= 1 ? 'on' : uf > 0.02 ? coatFlight(uf) : null, fig, cupEmpty: true });
  return { glass: { rain: 0.12, beads: 0.3, fog: 0.12, mask: cornerMask(cam), scale: 2.0, seed: 70 }, grade: { warm: 0.4, bloom: 0.9, sat: 1.08 } };
}
// CH3 「不等谁来陪」, second half: the chair opposite, bare again. The same chair as in the bridge; nothing about it hurts now.
export function bareChair(c, t, lt, sh) {
  const cam = camK(t, [[sh.t0, 1280, 660, 1750], [sh.t1 + 0.5, 1280, 720, 2300]], { ease: 'out', drift: 3 });
  chairRoom(c, cam, t, { lampLv: 1.25, rainA: 0.25 });
  // she puts the empty cup down where it was, and takes her hand away
  const dn = ramp(t, sh.t0 + 0.15, 0.7, 'out'), off = ramp(t, sh.t0 + 1.2, 0.9, 'in'), sc = 0.62, cx = 1840, cy = lerp(1880, 1330, dn);
  S(c, CH, cam, 'cs_saucer', cx, 1345, 1.15, { s: sc, a: dn });
  S(c, CH, cam, 'cs_cup', cx, cy, 1.15, { s: sc });
  inSet(c, CH, cam, 1.15, () => { c.save(); c.translate(cx, cy); c.scale(sc, sc); c.fillStyle = 'rgb(236,224,198)'; c.beginPath(); c.ellipse(0, -330, 266, 39, 0, 0, TAU); c.fill(); c.strokeStyle = 'rgba(120,80,52,0.5)'; c.lineWidth = 5; c.beginPath(); c.ellipse(0, -326, 236, 30, 0, 0.2, 3.3); c.stroke(); c.fillStyle = 'rgba(92,58,40,0.6)'; c.beginPath(); c.ellipse(30, -318, 110, 14, 0, 0, TAU); c.fill(); c.restore(); });
  if (off < 1) S(c, CH, cam, 'cs_hand', cx + 370 * sc + 900 * off, cy - 190 * sc + 60 * off, 1.15, { s: sc });
  inSet(c, CH, cam, 1, () => glow(c, CHAIR[0], CHAIR[1] - 260, 700, PAL.amber, 0.14 + 0.05 * kickN(t, 2)));
  return { grade: { warm: 0.42, bloom: 0.9, sat: 1.1 } };
}

// ================================================================ the chair opposite, from her seat
const CH = 'chair', CHAIR = MAN.ch_bg.chair, COAT = [CHAIR[0] + MAN.ch_coat.on_chair[0], CHAIR[1] + MAN.ch_coat.on_chair[1]];
function chairRoom(c, cam, t, o = {}) {
  L(c, CH, cam, 'ch_bg');
  const pool = MAN.ch_bg.wall_pool, lv = o.lampLv ?? 1;
  inSet(c, CH, cam, 1, () => {
    glow(c, pool[0], pool[1], pool[2] * 1.3, PAL.amber, 0.22 * lv);
    // the window, out of frame to the left, lays its rain on the wall
    c.save(); c.globalCompositeOperation = 'multiply';
    for (let i = 0; i < 8; i++) { const x = ((i * 190 + t * 22 * (o.rainSp ?? 1)) % 1300) - 150, g = c.createLinearGradient(x, 0, x + 90, 0); g.addColorStop(0, 'rgba(80,96,140,0)'); g.addColorStop(0.5, `rgba(80,96,140,${(0.07 + 0.05 * hash(i)) * (o.rainA ?? 1)})`); g.addColorStop(1, 'rgba(80,96,140,0)'); c.fillStyle = g; c.save(); c.transform(1, 0, -0.25, 1, 0, 0); c.fillRect(x, -50, 90, 800); c.restore(); }
    c.restore();
  });
  if (o.behind) o.behind();
  S(c, CH, cam, 'ch_chair_sh', CHAIR[0], CHAIR[1], 1, { a: o.shA ?? 1 });
  S(c, CH, cam, 'ch_chair', CHAIR[0], CHAIR[1]);
  if (o.coat) { S(c, CH, cam, 'ch_coat_sh', COAT[0], COAT[1]); S(c, CH, cam, 'ch_coat', COAT[0], COAT[1] + 2 * Math.sin(t * 0.9), 1, { r: 0.006 * Math.sin(t * 0.9 + 1), sy: 1 + 0.004 * Math.sin(t * 1.8) }); }
  L(c, CH, cam, 'ch_table', 1.12);
}
// V1 「把外套搭在对面 / 假装有人 跟我对饮」
export function coatPOV(c, t, lt, sh) {
  const tk = CT(7, 5), cl = CT(7, 7);          // 跟 … 对
  const cam = camK(t, [[sh.t0, 1280, 720, 2350], [tk, 1280, 690, 2000], [sh.t1, 1280, 640, 1700]], { drift: 4 });
  chairRoom(c, cam, t, { coat: true, lampLv: 1 + 0.25 * Math.exp(-Math.max(0, t - cl) * 2.5) * (t > cl ? 1 : 0) });
  // her cup comes up into the picture: to you, whoever you are
  const up = ramp(t, tk - 0.5, cl - tk + 0.4, 'out'), nod = Math.exp(-Math.max(0, t - cl) * 5) * Math.sin(Math.max(0, t - cl) * 16) * (t > cl ? 1 : 0), dn = ramp(t, cl + 2.0, 1.2, 'io');
  const u = up * (1 - dn), cx = lerp(1900, 1830, u), cy = lerp(1850, 1215, u) - 34 * nod, sc = 0.62;
  S(c, CH, cam, 'cs_cup', cx, cy, 1.15, { s: sc, r: -0.10 * u - 0.05 * nod });
  S(c, CH, cam, 'cs_hand', cx + 370 * sc, cy - 190 * sc, 1.15, { s: sc, r: -0.08 * u });
  inSet(c, CH, cam, 1.15, () => steam(c, t, cx, cy - 340 * sc, { h: 300, w: 30, a: 0.3 * u, sway: 50, n: 20, per: 0.3, seed: 9 }));
  return { grade: { warm: 0.22, bloom: 0.7 } };
}
// BRIDGE 「他们问 你不怕老了以后 / 椅子对面 空得刺眼难受」: other people's voices as shadows on the wall; then the glare.
export function bridgeChair(c, t, lt, sh) {
  const q0 = T0(32), g0 = T0(33) - 0.1, glare = ramp(t, g0, 0.35, 'out');
  const cam = camK(t, [[sh.t0, 1280, 720, 2400], [g0, 1280, 700, 2050], [sh.t1, 1280, 660, 1500]], { drift: 3 });
  const heads = [[560, 900, 2.7, 0.14, 0], [930, 1000, 2.2, 0.06, 2], [1700, 960, 2.4, -0.08, 1], [2090, 880, 2.9, -0.15, 3], [170, 1040, 3.3, 0.2, 4]];
  chairRoom(c, cam, t, { lampLv: 0.5 * (1 - glare), rainSp: 9, rainA: 1.6 * (1 - glare), shA: 0.6 + 0.4 * glare, behind: () => inSet(c, CH, cam, 1, () => {
    // days go by across the wall: the window's light sweeping, faster and faster
    const yrs = (t - q0) * 0.55, sweep = (yrs * (1 + 0.25 * yrs)) % 1;
    if (t > q0 - 1 && glare < 1) { c.save(); c.globalCompositeOperation = 'screen'; const x = -500 + 3400 * sweep, g = c.createLinearGradient(x, 0, x + 520, 0); g.addColorStop(0, 'rgba(230,236,250,0)'); g.addColorStop(0.5, `rgba(230,236,250,${0.20 * (1 - glare) * ramp(t, q0 - 1, 1)})`); g.addColorStop(1, 'rgba(230,236,250,0)'); c.fillStyle = g; c.transform(1, 0, -0.3, 1, 0, 0); c.fillRect(x, -100, 520, 1300); c.restore(); }
    // they lean in
    c.save(); c.globalCompositeOperation = 'multiply'; c.filter = 'blur(22px)';
    for (const [hx, hy, s, lean, k] of heads) {
      const a = ramp(t, CT(32, Math.min(k, 2)) - 0.15 + 0.12 * k, 0.7, 'out') * (1 - glare); if (a <= 0.003) continue;
      const rise = (1 - a) * 300, sway = 14 * Math.sin(t * 0.9 + k * 2);
      c.save(); c.translate(hx + sway, hy + rise); c.rotate(lean + 0.03 * Math.sin(t * 0.7 + k)); c.scale(s, s);
      c.fillStyle = `rgba(52,58,84,${0.5 * a})`;
      c.beginPath(); c.ellipse(0, -150, 62, 76, 0, 0, TAU); c.fill();
      c.beginPath(); c.moveTo(-170, 420); c.quadraticCurveTo(-170, -60, 0, -72); c.quadraticCurveTo(170, -60, 170, 420); c.fill();
      c.restore();
    }
    c.restore();
  }) });
  // 空得刺眼: one hard light, straight down on the empty chair, and nothing else
  if (glare > 0.003) inSet(c, CH, cam, 1, () => {
    shadePool(c, CHAIR[0], CHAIR[1] - 160, 300, 1150, 'rgb(46,48,62)', 0.88 * glare);
    c.save(); c.globalCompositeOperation = 'screen'; c.globalAlpha = glare * (0.9 + 0.1 * noise1(t * 11, 2));
    const g = c.createLinearGradient(0, -200, 0, CHAIR[1] + 400); g.addColorStop(0, 'rgba(255,255,250,0.55)'); g.addColorStop(1, 'rgba(255,255,250,0.10)');
    c.fillStyle = g; c.beginPath(); c.moveTo(CHAIR[0] - 110, -200); c.lineTo(CHAIR[0] + 110, -200); c.lineTo(CHAIR[0] + 430, CHAIR[1] + 420); c.lineTo(CHAIR[0] - 430, CHAIR[1] + 420); c.fill();
    c.restore();
    glow(c, CHAIR[0], CHAIR[1] - 20, 420, [255, 255, 250], 0.55 * glare, { sy: 0.4 });
    for (let k = 0; k < 26; k++) { const u = ((t * 0.05 * (0.5 + hash(k)) + hash(k * 3)) % 1), x = CHAIR[0] + (hash(k * 7) - 0.5) * 520 * (0.4 + u), y = -100 + 1250 * u; c.fillStyle = `rgba(255,255,250,${0.5 * glare * Math.sin(u * Math.PI)})`; c.beginPath(); c.arc(x + 12 * Math.sin(t + k), y, 2.5 + 2 * hash(k), 0, TAU); c.fill(); }
  });
  return { grade: { sat: 0.10, cold: 0.75, gain: 0.96, bloom: 0.4 + 1.6 * glare, contrast: 0.04 + 0.18 * glare, vig: 0.6 }, lyric: {} };
}

// ================================================================ the whole shop
const SP = 'shop', SM = MAN.sp_room, SEAT = SM.seat;
function shopRoom(c, cam, t, o = {}) {
  L(c, SP, cam, 'sp_room');
  const lv = o.lv || (() => 1), groove = o.groove ?? 0;
  // rain on the three windows
  inSet(c, SP, cam, 1, () => {
    for (const q of SM.wins) {
      c.save(); c.beginPath(); c.moveTo(q[0][0], q[0][1]); for (let k = 1; k < 4; k++) c.lineTo(q[k][0], q[k][1]); c.closePath(); c.clip();
      c.strokeStyle = rgba(PAL.rain, 0.35 * (o.rain ?? 1)); c.lineWidth = 2;
      for (let i = 0; i < 26; i++) { const h1 = hash(i * 3.1 + q[0][0]), sp = 0.7 + 0.6 * hash(i * 7.7), y = ((h1 * 700 + 900 * sp * t) % 700) + q[0][1] - 60, x = lerp(q[0][0], q[1][0], hash(i * 1.3 + q[0][0] * 0.1)); c.beginPath(); c.moveTo(x, y); c.lineTo(x - 4, y + 36 * sp); c.stroke(); }
      c.restore();
    }
    // the record goes round
    const [rx, ry, ra, rb] = SM.record;
    c.save(); c.translate(rx, ry); c.scale(1, rb / ra); c.rotate(t * 3.3);
    for (let k = 0; k < 3; k++) { c.strokeStyle = `rgba(255,236,200,${0.22 + 0.1 * k})`; c.lineWidth = 2.5; c.beginPath(); c.arc(0, 0, ra * (0.5 + 0.18 * k), k * 2.1, k * 2.1 + 0.7); c.stroke(); }
    c.restore();
    // the machine breathes
    steam(c, t, SM.machine[0] - 120, SM.machine[1] + 40, { h: 240, w: 20, a: 0.3, sway: 40, n: 18, per: 0.32, seed: 12 });
  });
  // she, her coat, far in the corner
  if (o.coat !== false) {               // the chair it hangs on is painted, behind the table: keep the coat behind the table top too
    c.save(); camT(c, SP, cam, 1); c.beginPath(); c.rect(2700, 600, 400, 284); c.rect(2864, 884, 240, 400); c.clip(); c.setTransform(1, 0, 0, 1, 0, 0);
    S(c, SP, cam, 'ch_coat', 2874, 752, 1, { s: 0.31 }); c.restore();
  }
  if (o.fig !== false) {
    const fx = 2570, fy = 1092, fs = 0.46;
    S(c, SP, cam, 'cs_saucer', 2664, SM.tops['2'][1] - 2, 1, { s: 0.075 }); S(c, SP, cam, 'cs_cup', 2664, SM.tops['2'][1] - 4, 1, { s: 0.075 });
    S(c, SP, cam, 'ch_chair', fx, fy, 1, { s: fs });
    S(c, SP, cam, 'fig_sit', fx, fy - 4, 1, { s: fs });
    c.save(); camT(c, SP, cam, 1); c.beginPath(); c.rect(fx - 200, fy - 360, 400, 348); c.clip(); c.setTransform(1, 0, 0, 1, 0, 0); S(c, SP, cam, 'ch_chair', fx, fy, 1, { s: fs }); c.restore();
    inSet(c, SP, cam, 1, () => steam(c, t, 2664, SM.tops['2'][1] - 32, { h: 170, w: 10, a: 0.34, sway: 24, n: 16, per: 0.32, seed: 14 }));
  }
  // the lamps: each one comes on when its turn comes, and they all sway together when the song does
  const bt = TM.beat(t);
  SM.lamps.forEach(([x, y, s], k) => {
    const on = lv(k) * (1 + 0.16 * groove * kickN(t, 2, 0, 4)), ang = 0.012 * Math.sin(t * 0.7 + k) + groove * 0.10 * Math.sin(bt * Math.PI + (k % 2 ? 0.5 : 0));
    const [bx, by] = hang(c, SP, cam, 'lamp_pendant', x, y, 0.33 * s, ang, 1);
    inSet(c, SP, cam, 1, () => { lamp(c, bx, by + 4 * s, 400 * s, t, 0.42 * on, { seed: k }); glow(c, bx, Math.min(1900, by + 520 * s), 430 * s, PAL.amber, 0.13 * on, { sy: 0.3 }); });
  });
  inSet(c, SP, cam, 1, () => {           // dust in the light
    for (let k = 0; k < 40; k++) { const u = ((t * 0.02 * (0.5 + hash(k)) + hash(k * 3)) % 1), x = 400 + hash(k * 7) * 2700 + 30 * Math.sin(t * 0.5 + k), y = 500 + 900 * hash(k * 11) + 60 * u; c.fillStyle = `rgba(255,240,210,${0.35 * Math.sin(u * Math.PI)})`; c.beginPath(); c.arc(x, y, 2 + 2 * hash(k), 0, TAU); c.fill(); }
  });
}
// BRIDGE → CH3 「整家店 安静的自由 / 一个人也很完美」: the pull-back the whole song was saving
export function wholeShop(c, t, lt, sh) {
  const z0 = T0(37), on0 = CT(37, 0), cal = T0(38);
  const cam = camK(t, [[sh.t0, 2690, 1040, 1150], [z0 + 3.4, 1760, 1000, 3250, 0, 'io'], [sh.t1, 1728, 985, 3380, 0, 'lin']], { drift: 3 });
  const order = [4, 1, 2, 0, 3, 5], times = order.map((_, k) => beatNear(on0 + 0.1, k));
  const groove = ramp(t, cal - 0.2, 0.8);
  shopRoom(c, cam, t, { lv: (k) => { const tt = times[order.indexOf(k)]; return 0.22 + 0.78 * ramp(t, tt, 0.25, 'out') + 0.5 * Math.exp(-Math.max(0, t - tt) * 5) * (t >= tt ? 1 : 0); }, groove });
  // every table a whole circle
  inSet(c, SP, cam, 1, () => {
    const a = ramp(t, cal, 0.2) * (1 - ramp(t, sh.t1 - 0.7, 0.6));
    if (a > 0.003) Object.entries(SM.tops).forEach(([k, [x, y]], i) => { const sc = (TABLES_Y[k] - SM.vp[1]) / 350, rx = 150 * sc; chalk(c, circlePts(x, y, rx, 56, i, 1.04, 0.24 + 0.05 * sc), ramp(t, CT(38, Math.min(i, 5)) - 0.05, 0.55, 'out'), { a: 0.9 * a, w: 3.5 + 2.5 * sc, seed: i + 1, tremor: 2 }); });
    // a car passes outside: its light comes through the three windows and crosses the floor
    const cu = (t - cal - 0.9) / 2.4;
    if (cu > 0 && cu < 1) { c.save(); c.globalCompositeOperation = 'screen'; const x = lerp(-300, 2700, cu), g = c.createLinearGradient(x, 0, x + 600, 0); g.addColorStop(0, 'rgba(255,238,200,0)'); g.addColorStop(0.5, `rgba(255,238,200,${0.22 * Math.sin(cu * Math.PI)})`); g.addColorStop(1, 'rgba(255,238,200,0)'); c.fillStyle = g; c.transform(1, 0, 0.9, 1, 0, 0); c.fillRect(x - 1400, 1150, 600, 800); c.restore(); }
  });
  return { grade: { warm: 0.3, bloom: 0.45, sat: 1.1, vig: 0.46 } };
}
const TABLES_Y = { 0: 1215, 1: 1235, 2: 1205, 3: 1330, 4: 1440, 5: 1560, 6: 1750 };
// CH3 「不必为谁 收敛口味」: the counter, the record, the steam: the shop keeps its own time
export function shopDetail(c, t, lt, sh) {
  const cam = camK(t, [[sh.t0, 1560, 800, 1500], [sh.t1, 1780, 790, 1250]], { ease: 'io', drift: 3 });
  shopRoom(c, cam, t, { groove: 1 });
  inSet(c, SP, cam, 1, () => { const [rx, ry] = SM.record; for (const b of B) { if (b > t || t - b > 1.2 || b < sh.t0 - 1) continue; ring(c, rx, ry, t - b, { R: 190, life: 1.2, sy: 0.3, col: PAL.warm, a: 0.6, w: 3, rings: 2, blend: 'screen', seed: b }); } });
  return { grade: { warm: 0.32, bloom: 0.45, sat: 1.12 } };
}
