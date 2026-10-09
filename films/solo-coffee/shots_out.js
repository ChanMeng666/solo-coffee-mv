// Outside: the street with the one warm window, and the crossing seen from above where the umbrellas go by in pairs.
import { W, H, PAL, rgba, L, S, inSet, camT, camK, toScreen, glow, lamp, rain, ripples, ring, bokeh, pen, chalk, circlePts, MAN, IM, clamp, lerp, sstep, hash, noise1, TAU, E } from './stage.js';
import { TM, B, T0, CT, beatNear, beatIdx, kickN, since, ramp } from './core.js';

// ================================================================ the street
const ST = 'street', M = MAN.st_main, WIN = M.win, WC = [(WIN[0] + WIN[2]) / 2, (WIN[1] + WIN[3]) / 2], NEON = M.neon, PAVE = M.pave_y;
const SAX = [[95, 70], [120, 45], [160, 40], [190, 60], [202, 110], [212, 200], [218, 300], [208, 352], [170, 384], [125, 374], [104, 330], [100, 270], [86, 232]];
function tube(c, pts, col, a, w = 1) {
  c.lineCap = 'round'; c.lineJoin = 'round';
  for (const [lw, al, cl] of [[30, 0.16, col], [14, 0.5, col], [5, 0.95, [255, 240, 236]]]) { c.strokeStyle = rgba(cl, al * a); c.lineWidth = lw * w; c.beginPath(); pts.forEach((p, i) => (i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]))); c.stroke(); }
}
// a neon saxophone in a neon ring, on the wall next door: the only thing out here that keeps time with the song
function neon(c, cam, t, lv) {
  if (lv <= 0.003) return;
  const fl = lv * (0.82 + 0.18 * (noise1(t * 13, 4) > -0.6 ? 1 : 0.2)), ox = NEON[0] + 8, oy = NEON[1] + 8, k = kickN(t, 2, 0, 4);
  inSet(c, ST, cam, 1, () => {
    c.save(); c.globalCompositeOperation = 'screen';
    c.save(); c.translate(ox, oy);
    tube(c, SAX, PAL.rose, fl * (0.8 + 0.2 * k));
    tube(c, [[52, 240], [84, 222], [118, 212]], PAL.rose, fl);
    for (const [x, y] of [[207, 150], [213, 205], [217, 258]]) tube(c, circlePts(x - 16, y, 7, 10), PAL.amber, fl * 0.9, 0.6);
    tube(c, circlePts(156, 212, 186, 48, 0.5, 0.94), [110, 220, 230], fl * (0.7 + 0.3 * k), 0.8);
    c.restore();
    glow(c, ox + 156, oy + 212, 520, PAL.rose, 0.20 * fl); glow(c, ox + 156, PAVE + 250, 420, PAL.rose, 0.16 * fl, { sy: 0.5 });
    c.restore();
  });
}
// a car going by, close: mostly its lights, and what they do to the wet road
function car(c, cam, t, t0, dir = 1) {
  const u = (t - t0) / 1.7; if (u < 0 || u > 1) return;
  const x = dir > 0 ? lerp(-900, 4000, u) : lerp(4000, -900, u), y = 1560;
  inSet(c, ST, cam, 1.25, () => {
    c.save(); c.filter = 'blur(12px)'; c.fillStyle = 'rgba(16,20,34,0.92)';
    c.beginPath(); c.roundRect(x - 420, y - 250, 840, 190, 60); c.fill(); c.beginPath(); c.roundRect(x - 230, y - 370, 440, 160, 70); c.fill();
    c.restore();
    glow(c, x + dir * 430, y - 130, 520, [255, 236, 190], 0.9, { sy: 0.5 }); glow(c, x + dir * 800, y + 40, 700, [255, 236, 190], 0.35, { sy: 0.25 });
    glow(c, x - dir * 420, y - 140, 260, [240, 60, 50], 0.8, { sy: 0.6 });
  });
}
// o: night 0..1, rain 0..1, neonLv, glowLv (the café's light), she: [x, a] on the pavement, inside: bool, wet ripples
function street(c, cam, t, o = {}) {
  const night = o.night ?? 0, rn = o.rain ?? 1, gl = o.glowLv ?? 1;
  L(c, ST, cam, 'st_sky', 0.2);
  if (o.clear) { c.save(); c.setTransform(1, 0, 0, 1, 0, 0); glow(c, W * 0.45, H * 0.32, 1300, [255, 200, 170], 0.30 * o.clear, { sy: 0.45 }); c.restore(); }
  L(c, ST, cam, 'st_far', 0.55);
  L(c, ST, cam, 'st_inside');
  if (o.inside !== false) { if (o.coat !== false) S(c, ST, cam, 'ch_coat', 2030, 985, 1, { s: 0.15 }); S(c, ST, cam, 'fig_sit', 1925, 1140, 1, { s: 0.2 }); }
  L(c, ST, cam, 'st_main');
  L(c, ST, cam, 'st_road');
  if (night > 0.003) { c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.globalCompositeOperation = 'multiply'; c.fillStyle = rgba([92, 100, 150], night); c.fillRect(0, 0, W, H); c.restore(); }
  inSet(c, ST, cam, 1, () => {
    // the window: the light it gives the pavement and the road
    const br = gl * (1 + 0.04 * noise1(t * 5, 2));
    glow(c, WC[0] + 60, WC[1], 620, PAL.amber, (0.22 + 0.35 * night) * br); glow(c, WC[0] + 60, WC[1], 300, PAL.warm, (0.10 + 0.3 * night) * br);
    glow(c, WC[0] + 80, PAVE + 190, 700, PAL.amber, (0.16 + 0.26 * night) * br, { sy: 0.5 });
    for (const [bx, by] of M.brackets) lamp(c, bx, by + 14, 150, t, 0.5 + 0.5 * night, { seed: bx });
    for (const q of M.lit) glow(c, (q[0] + q[2]) / 2, (q[1] + q[3]) / 2, 150, PAL.amber, (0.10 + 0.3 * night) * (0.8 + 0.2 * noise1(t * 0.6, q[0])));
    // rain on the road
    if (rn > 0.02) ripples(c, t, [0, PAVE + 110, 3072, 1728], { n: Math.round(46 * rn), R: 60, sy: 0.32, per: 1.3, a: 0.45, col: [200, 216, 236], w: 2.4, blend: 'screen' });
    // the awning lets go of its drops on the beat
    const [ax0, ay, ax1] = M.awning_edge, bi = beatIdx(t);
    if (rn > 0.02 || o.lastDrips) for (let k = bi - 1; k <= bi + 1; k++) {
      if (k < 0 || k >= B.length) continue;
      const dt = t - B[k], x = lerp(ax0 + 30, ax1 - 30, hash(k * 5.3)); if (dt < -0.4 || dt > 0.42) continue;
      c.fillStyle = rgba([220, 232, 244], 0.85);
      if (dt < 0) { const u = 1 + dt / 0.4; c.beginPath(); c.ellipse(x, ay + 6 + 4 * u, 3 + 3 * u, 4 + 6 * u, 0, 0, TAU); c.fill(); } else { c.beginPath(); c.ellipse(x, ay + 12 + 2700 * dt * dt, 3.5, 10 + 30 * dt, 0, 0, TAU); c.fill(); }
      ring(c, x, PAVE + 6, dt - 0.42, { R: 50, life: 0.7, sy: 0.3, col: [220, 232, 244], a: 0.7, w: 2.5, rings: 2, blend: 'screen', seed: k });
    }
  });
  neon(c, cam, t, o.neonLv ?? 0);
  for (const p of o.walkers || []) S(c, ST, cam, p.name, p.x, PAVE + 16, 1, { s: p.s ?? 0.5, sx: p.flip ? -1 : 1, a: p.a ?? 0.9 });
  if (o.she) {
    const [x, a, bob, fr] = o.she, y = PAVE + 14, nm = 'fig_walk' + (fr || 0);
    S(c, ST, cam, nm, x, y + 6, 1, { s: 0.27, sy: -0.8, a: 0.22 * a });      // on the wet flags
    S(c, ST, cam, nm, x, y - (bob || 0), 1, { s: 0.27, a });
  }
  if (o.car) car(c, cam, t, o.car[0], o.car[1]);
  if (MAN.st_lamp) {
    const lx = 470, ly = 520, on = o.lampLv ?? (0.5 + 0.5 * night);
    S(c, ST, cam, 'st_lamp', lx, ly, 1.3);
    inSet(c, ST, cam, 1.3, () => { lamp(c, lx, ly, 560, t, on, { seed: 8 }); glow(c, lx + 40, 1560, 520, PAL.amber, 0.2 * on, { sy: 0.35 }); });
  }
  if (MAN.st_fg_branch && o.fg !== false) S(c, ST, cam, 'st_fg_branch', 3072 - 40, 30 + 8 * Math.sin(t * 0.8), 1.5, { ax: MAN.st_fg_branch.sw, ay: 0, ox: 0, r: 0.012 * Math.sin(t * 0.8) });
  if (MAN.st_fg_bike && o.fg !== false) S(c, ST, cam, 'st_fg_bike', 2560, 1700, 1.45, { ay: MAN.st_fg_bike.sh });
  if (rn > 0.02) { rain(c, t, { n: Math.round(240 * rn), a: 0.30, len: 80, seed: 3 }); rain(c, t, { n: Math.round(70 * rn), a: 0.45, len: 150, w: 1.8, v: 2300, seed: 9 }); }
}

// INTRO: the street, the rain, the one warm window. The title; then in through the glass.
export function open(c, t, lt, sh) {
  const cam = camK(t, [[0, 1500, 566, 2200], [4.6, 1520, 590, 2200], [7.6, 1620, 950, 2360, 0, 'io'], [sh.t1 + 0.6, WC[0], WC[1] - 10, 760, 0, 'in']], { drift: 3 });
  street(c, cam, t, { night: 0.12, coat: false, neonLv: ramp(t, 4.2, 0.3) * (t < 4.7 && Math.sin(t * 60) > 0 ? 0.3 : 1), walkers: [{ name: 'wn_pair', x: 2750 - t * 240, s: 0.5 }, { name: 'wn_single', x: -500 + t * 130, s: 0.46, flip: true }] });
  return { grade: { warm: 0.0, bloom: 0.9, sat: 1.05, vig: 0.55 } };
}
// CH2 「不必为谁 收敛口味 / 糖多一点 还是不加也无所谓」: night. The camera comes down to the road, where the window is doubled.
export function nightStreet(c, t, lt, sh) {
  const d0 = T0(27);
  const cam = camK(t, [[sh.t0, 1350, 960, 2300], [d0 - 0.2, 1560, 1000, 1900], [d0 + 2.0, 1740, 1300, 1500], [sh.t1, 1780, 1340, 1380]], { drift: 4 });
  street(c, cam, t, { night: 0.55, neonLv: 1, glowLv: 1 + 0.25 * kickN(t, 2), car: [sh.t0 + 1.2, 1] });
  // sugar or none: drops land in the puddle on the syllables, and the window's reflection shakes and comes back
  inSet(c, 'street', cam, 1, () => { for (let k = 0; k < 4; k++) ring(c, 1600 + 130 * k + 60 * hash(k), 1470 + 40 * hash(k * 3), t - CT(27, k), { R: 190, life: 1.5, sy: 0.32, col: PAL.warm, a: 0.9, w: 4, blend: 'screen', seed: k }); });
  return { grade: { warm: 0.05, bloom: 1.2, sat: 1.18, vig: 0.6 } };
}
// CH2 「在舌尖慢慢化开了防备」: the window's warmth runs out over the street like a wash that was laid too wet
export function meltOut(c, t, lt, sh) {
  const u = ramp(t, sh.t0, sh.len, 'io');
  const cam = camK(t, [[sh.t0, WC[0], WC[1] + 20, 1100], [sh.t1, 1560, 900, 2950]], { drift: 3 });
  street(c, cam, t, { night: 0.55 * (1 - 0.5 * u), neonLv: 1, glowLv: 1 + 0.5 * u });
  const [sx, sy] = toScreen(ST, cam, WC[0], WC[1]);
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0); glow(c, sx, sy, 300 + 1500 * u, PAL.amber, 0.20 * u); c.restore();
  return { grade: { sat: 0.72, cold: 0.25, satIn: 1.3, wave: [sx / H, sy / H, lerp(0.25, 2.3, u)], warm: 0.15 + 0.3 * u, bloom: 0.75, vig: 0.55 } };
}
// CH3 → OUTRO 「我和自己先约会」: the rain has stopped. She comes out with her coat on and her umbrella shut, and goes.
export function exit(c, t, lt, sh) {
  const go = T0(44) + 1.5, w = Math.max(0, t - go), ph = w * 2.5;                 // two and a half half-steps a second: a stroll
  const cam = camK(t, [[sh.t0, 2170, 1060, 1250], [go, 2120, 1050, 1420], [go + 6.5, 1420, 930, 2900, 0, 'io'], [sh.t1, 1440, 900, 3000, 0, 'lin']], { drift: 3 });
  const x = 2190 - 205 * w - 26 * ramp(t, sh.t0 + 0.2, 1.0, 'out'), fr = w > 0 ? Math.floor(ph) % 2 : 1, bob = w > 0 ? 4 * Math.abs(Math.sin(ph * Math.PI)) : 0;
  const lit = beatNear(go + 2.2);
  street(c, cam, t, { night: 0.30, rain: 0, lastDrips: true, clear: ramp(t, sh.t0, 6), neonLv: 1, inside: false, she: [x, 1, bob, fr], lampLv: 0.15 + 0.85 * ramp(t, lit, 0.2) * (t < lit + 0.5 && Math.sin(t * 50) > 0.2 ? 0.4 : 1) });
  // the door behind her: a slab of light that narrows as it swings to
  inSet(c, ST, cam, 1, () => { const d = M.door, op = 1 - ramp(t, sh.t0 + 0.3, 1.6); glow(c, (d[0] + d[2]) / 2, d[3] + 60, 380, PAL.warm, 0.5 * op, { sy: 0.5 }); });
  return { grade: { warm: 0.22, bloom: 1.1, sat: 1.1, vig: 0.5 } };
}

// ================================================================ the crossing from above
const UM = 'umbrella', DIR = [Math.cos(-0.21), Math.sin(-0.21)], NRM = [-DIR[1], DIR[0]], C0 = [1536, 900], SPAN = 4600;
const WALK = [];
{
  // people go two by two: under two umbrellas that keep together, or under one big one
  const groups = [[[-560, -250], 1, 250], [[100, 410], -1, 215], [[-900], -1, 200], [[740], 1, 270]];
  let id = 0;
  groups.forEach(([offs, dir, v], gi) => {
    for (let k = 0; k < 4; k++) {
      const ph = k * SPAN / 4 + 260 * hash(gi * 5 + k * 7) + gi * 520, big = offs.length === 1 ? hash(gi * 9 + k) > 0.3 : hash(gi * 9 + k) > 0.8;
      const small = () => 'um_' + [0, 1, 2, 4, 5, 6][Math.floor(hash(id * 7.7 + 1.3) * 6)];
      if (big) WALK.push({ id: id++, off: (offs[0] + offs[offs.length - 1]) / 2, dir, v, ph, um: hash(id * 3.1) > 0.45 ? 'um_3' : 'um_7', big });
      else for (const off of offs) WALK.push({ id: id++, off: off + 24 * (hash(id * 3) - 0.5), dir, v, ph: ph + 50 * (hash(id * 5) - 0.5), um: small(), big: false });
    }
  });
}
// o: until (no new walkers start crossing after this time), solo: [x, y, rot, s], part (others keep clear of the solo)
function crossing(c, cam, t, o = {}) {
  L(c, UM, cam, 'um_ground');
  inSet(c, UM, cam, 1, () => {
    const k = 0.75 + 0.25 * kickN(t, 2, 0, 3);
    for (const [x, y] of [[1240, 800], [640, 1440], [1780, 420]]) glow(c, x, y, 620, PAL.amber, 0.26 * k);
    for (const [x, y] of [[2370, 880], [2820, 1400]]) glow(c, x, y, 560, PAL.rose, 0.24 * k);
    glow(c, 400, 500, 520, [110, 220, 230], 0.12 * k);
    ripples(c, t, [0, 0, 3072, 1728], { n: Math.round(90 * (o.rain ?? 1)), R: 54, per: 1.1, a: 0.5, col: [206, 222, 240], w: 2.6, blend: 'screen' });
  });
  const list = [];
  for (const w of WALK) {
    const raw = w.ph + w.v * t, pass = Math.floor(raw / SPAN), s = (raw - pass * SPAN) - SPAN / 2;
    if (o.until != null && (pass * SPAN - w.ph) / w.v > o.until) continue;
    let off = w.off;
    const px = C0[0] + DIR[0] * s * w.dir, py = C0[1] + DIR[1] * s * w.dir;
    let x = px + NRM[0] * off, y = py + NRM[1] * off;
    if (o.solo && o.part) { const dx = x - o.solo[0], dy = y - o.solo[1], d = Math.hypot(dx, dy), push = 330 * Math.exp(-(d * d) / (520 * 520)) * o.part; x += (dx / (d + 1)) * push; y += (dy / (d + 1)) * push; }
    const step = t * 3.6 + w.id * 1.7;
    list.push({ x, y, um: w.um, r: w.id * 1.3 + 0.07 * Math.sin(step), s: 1 + 0.018 * Math.sin(step * 2), dir: w.dir, step, big: w.big });
  }
  if (o.solo) list.push({ x: o.solo[0], y: o.solo[1], um: 'um_solo', r: o.solo[2], s: o.solo[3] ?? 1, solo: true, dir: 0, step: t * 3 });
  list.sort((a, b) => a.y - b.y);
  for (const u of list) { if (!u.um) continue; S(c, UM, cam, 'um_sh', u.x + 34, u.y + 40, 1, { a: 0.8, s: MAN[u.um].r / 180 }); }
  for (const u of list) {
    if (!u.um) continue;
    if (u.dir && MAN.um_feet0) { const f = Math.sin(u.step * 2), r = MAN[u.um].r; S(c, UM, cam, u.um.length % 2 ? 'um_feet0' : 'um_feet1', u.x + DIR[0] * u.dir * (r * 0.78 + 26 * f), u.y + DIR[1] * u.dir * (r * 0.78 + 26 * f), 1.02, { r: Math.atan2(DIR[1] * u.dir, DIR[0] * u.dir) + Math.PI / 2, a: clamp(0.5 + f) }); }
    S(c, UM, cam, u.um, u.x, u.y, 1.06, { r: u.r, s: u.s });
  }
  // rain seen from above: short bright dashes, all leaning the same way
  rain(c, t, { n: Math.round(170 * (o.rain ?? 1)), a: 0.32, len: 20, slant: 0.5, v: 1500, seed: 21, w: 1.4 });
}
// CH2 「下雨天 喝咖啡 / 一个人也很完美」: everyone in twos, going somewhere. One persimmon umbrella takes its time across the lot of them.
export function umbrellas(c, t, lt, sh) {
  const s0 = T0(25) - 2.2, u = ramp(t, s0, sh.t1 - s0 + 4, 'lin');
  const solo = [lerp(1900, 1500, u), lerp(1900, 620, u), 0.4 + (t - s0) * 0.5, 1];
  const cam = camK(t, [[sh.t0, 1500, 880, 2250, -0.06], [T0(25), 1600, 980, 1900, 0.0], [sh.t1, 1560, 900, 1650, 0.07]], { drift: 4 });
  crossing(c, cam, t, { solo: t > s0 ? solo : null, part: 1 });
  inSet(c, UM, cam, 1.06, () => { const a = ramp(t, CT(25, 5), 0.3) * (1 - ramp(t, sh.t1 - 0.5, 0.5)); chalk(c, circlePts(solo[0], solo[1], 235, 64, 1, 1.04), ramp(t, CT(25, 5), 0.7, 'out'), { a: 0.95 * a, w: 8, seed: 2 }); });
  return { grade: { warm: 0.0, bloom: 1.0, sat: 1.15, vig: 0.55 } };
}
// CH2 「不等谁来陪 / 我和自己先约会」: the pairs have crossed. The persimmon umbrella is alone on the crossing, and turns, like a record.
export function emptyCross(c, t, lt, sh) {
  const d0 = T0(31), spin = 0.5 * (t - sh.t0) + 2.2 * Math.max(0, t - d0) ** 1.5;
  const cam = camK(t, [[sh.t0, 1540, 880, 1750, 0.05], [d0, 1540, 880, 2100, 0.0], [sh.t1 + 1.5, 1536, 866, 2380, -0.10]], { drift: 2 });
  const solo = [1540 + 26 * Math.sin(t * 0.6), 880 + 20 * Math.cos(t * 0.5), spin, 1 + 0.04 * kickN(t, 2)];
  crossing(c, cam, t, { solo, part: 0.6, until: T0(30) - 3.2 });
  inSet(c, UM, cam, 1, () => { for (const b of B) { if (b < d0 - 0.1 || b > t || t - b > 2.4) continue; ring(c, solo[0], solo[1], t - b, { R: 760, life: 2.4, col: PAL.warm, a: 0.6, w: 5, rings: 3, blend: 'screen', seed: b, rot: b }); } });
  return { grade: { warm: 0.05, bloom: 1.0, sat: lerp(1.15, 0.7, ramp(t, sh.t1 - 1.5, 3.3)), vig: 0.55 } };
}
