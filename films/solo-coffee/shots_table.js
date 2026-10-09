// The table from straight above. One painted set, many visits: the stir, the sugar, the phone, the tap on the rim,
// and at the very end the ring the cup leaves.
import { W, H, PAL, rgba, L, S, inSet, camK, glow, lamp, ring, steam, pen, circlePts, toScreen, clamp, lerp, sstep, hash, noise1, TAU, E } from './stage.js';
import { TM, B, T0, CT, LN, beatNear, kickN, since, ramp } from './core.js';

export const SET = "table";
export const CUP = [1536, 880], COF_R = 178, CUP_R = 205;
export const SUGAR = [2210, 520], PHONE = [900, 640], NAPKIN = [1010, 1240];

// ---------------------------------------------------------------- the coffee, alive
// theta: how far the surface has turned. milk 0..1: a spiral of milk; calm 0..1 flattens the swirl
export function coffee(c, cam, t, theta, o = {}) {
  const [cx, cy] = CUP, R = COF_R, milk = o.milk ?? 0, sw = o.swirl ?? 1;
  inSet(c, SET, cam, 1, () => {
    c.save(); c.beginPath(); c.arc(cx, cy, R, 0, TAU); c.clip();
    if (o.level != null && o.level < 1) {          // an emptying cup: the bottom shows through
      const lv = o.level;
      c.fillStyle = rgba([238, 226, 200], (1 - lv) * 0.96); c.fillRect(cx - R, cy - R, R * 2, R * 2);
      c.fillStyle = rgba([92, 58, 40], 0.55 * (1 - lv)); c.beginPath(); c.arc(cx + 12, cy + 16, R * (0.25 + 0.45 * lv), 0, TAU); c.fill();     // the last sip
      c.strokeStyle = rgba([120, 80, 52], 0.5 * (1 - lv)); c.lineWidth = 3;
      for (let k = 0; k < 3; k++) { c.beginPath(); c.arc(cx, cy, R * (0.93 - k * 0.11), 0.3 + k, 0.3 + k + 3.6 + k * 0.5); c.stroke(); }                  // tide marks
    }
    // crema: pale arms wound into a spiral, turning with the stir. Each arm is one soft stroke, laid three times.
    c.lineCap = 'round'; c.lineJoin = 'round';
    const arms = 5, lvA = o.level != null ? clamp(o.level * 1.5) : 1;
    const arm = (j, off, r0, r1) => { c.beginPath(); for (let k = 0; k <= 44; k++) { const u = k / 44, r = R * lerp(r0, r1, u), a = theta + j * TAU / arms + 0.6 * hash(j) + off + u * (2.4 + sw * 2.2) + 0.25 * noise1(u * 3 + j * 7, 3); const x = cx + Math.cos(a) * r, y = cy + Math.sin(a) * r; k ? c.lineTo(x, y) : c.moveTo(x, y); } };
    c.save(); c.filter = 'blur(3px)';
    for (let j = 0; j < arms; j++) for (const [lw, al] of [[34, 0.05], [18, 0.08], [7, 0.10]]) { arm(j, 0, 0.10, 1.0); c.strokeStyle = rgba([214, 160, 104], al * (0.7 + 0.9 * sw) * (0.7 + 0.5 * hash(j * 9)) * lvA); c.lineWidth = lw * (0.7 + 0.6 * hash(j * 3)); c.stroke(); }
    if (milk > 0.01) for (let j = 0; j < arms; j++) {          // the milk goes in at the middle and is wound outward
      const mu = clamp(milk * 1.5 - j * 0.07); if (mu <= 0) continue;
      for (const [lw, al] of [[52, 0.16], [30, 0.22], [13, 0.30]]) { arm(j, 0.5, 0.04, lerp(0.2, 1.0, mu)); c.strokeStyle = rgba([250, 238, 214], al * mu); c.lineWidth = lw * (0.7 + 0.5 * hash(j * 5 + 1)); c.stroke(); }
    }
    c.restore();
    if (milk > 0.3) { c.fillStyle = rgba([226, 190, 150], (milk - 0.3) * 0.5); c.fillRect(cx - R, cy - R, R * 2, R * 2); }
    // what the surface reflects: the window (cool), the lamp (a warm coin that trembles)
    c.globalCompositeOperation = 'screen';
    c.fillStyle = rgba([170, 200, 214], 0.16 * lvA); c.beginPath(); c.ellipse(cx - 70, cy - 86, 62, 26, -0.7, 0, TAU); c.fill();
    const lx = cx + 46 + 5 * noise1(t * 1.3, 2) * (1 + sw), ly = cy - 40 + 4 * noise1(t * 1.7, 5) * (1 + sw);
    glow(c, lx, ly, 44, PAL.warm, 0.5 * lvA, { blend: 'screen' });
    c.restore();
  });
  S(c, SET, cam, 'tt_cup_in', CUP[0], CUP[1]);
}
// rings on the coffee from a drop or a tap, clipped to the cup
export function cupRings(c, cam, t, times, o = {}) {
  inSet(c, SET, cam, 1, () => {
    c.save(); c.beginPath(); c.arc(CUP[0], CUP[1], COF_R, 0, TAU); c.clip();
    for (const [tt, x, y] of times) ring(c, x ?? CUP[0], y ?? CUP[1], t - tt, { R: o.R ?? 200, life: o.life ?? 1.3, col: [236, 200, 150], a: o.a ?? 0.55, w: 3.5, rings: 3, blend: 'screen', seed: tt });
    c.restore();
  });
}

// the still life. o: phone ('up' | 'down' | angle 0..1 flip), sugar, napkin, hand {x, y, r, a}, spoon {x, y, r, lift}
export function still(c, cam, t, o = {}) {
  L(c, SET, cam, 'tt_bg');
  // the lamp over the table breathes; rain on the window throws slow moving shade across the wood
  inSet(c, SET, cam, 1, () => {
    c.save(); c.globalCompositeOperation = 'multiply';
    for (let i = 0; i < 9; i++) {            // rain shadows: soft diagonal bands that crawl
      const x = ((i * 420 + t * 34 + 200 * noise1(i * 3.1 + t * 0.07, 9)) % 3600) - 300, a = 0.05 + 0.04 * hash(i);
      const g = c.createLinearGradient(x, 0, x + 150, 0); g.addColorStop(0, 'rgba(60,70,110,0)'); g.addColorStop(0.5, `rgba(60,70,110,${a})`); g.addColorStop(1, 'rgba(60,70,110,0)');
      c.fillStyle = g; c.save(); c.transform(1, 0, -0.35, 1, 0, 0); c.fillRect(x, -200, 150, 2200); c.restore();
    }
    c.restore();
  });
  if (o.napkin !== false) S(c, SET, cam, 'tt_napkin', NAPKIN[0], NAPKIN[1], 1, { s: 0.72, r: -0.12 });
  if (o.ring) S(c, SET, cam, 'tt_ring', o.ring[0], o.ring[1], 1, { a: o.ring[2] ?? 1, blend: 'multiply' });
  S(c, SET, cam, 'tt_sugar', SUGAR[0], SUGAR[1], 1, { s: 0.9 });
  if (o.phone !== false) {
    const fl = o.flip ?? 0;                       // 0 = screen up, 1 = face down; in between it turns over its long edge
    const sx = Math.abs(Math.cos(fl * Math.PI)), up = fl < 0.5, lift = Math.sin(fl * Math.PI);
    const px = PHONE[0] + (o.phoneDx || 0), py = PHONE[1] + (o.phoneDy || 0);
    S(c, SET, cam, up ? 'tt_phone' : 'tt_phone_back', px, py - 26 * lift, 1, { s: 0.62 * (1 + 0.06 * lift), sx: Math.max(0.04, sx), r: 0.14 + (o.phoneR || 0) });
    if (up && o.screen) o.screen(c, px, py - 26 * lift, 0.62, 0.14 + (o.phoneR || 0), sx);
  }
  if (o.cup !== false) {
    S(c, SET, cam, 'tt_saucer_sh', CUP[0], CUP[1]);
    S(c, SET, cam, 'tt_saucer', CUP[0], CUP[1]);
    S(c, SET, cam, o.cupEmpty ? 'tt_cup_empty' : 'tt_cup', CUP[0], CUP[1]);
  }
}
// spoon + hand stirring: phi = angle of the bowl round the cup. grip 0..1 lifts the whole thing out
export function stirring(c, cam, t, phi, o = {}) {
  const rad = o.rad ?? 92, lift = o.lift ?? 0, a = o.a ?? 1;
  const bx = CUP[0] + Math.cos(phi) * rad, by = CUP[1] + Math.sin(phi) * rad;
  const hx = CUP[0] + 330 + Math.cos(phi) * 34 + (o.hx || 0), hy = CUP[1] + 236 + Math.sin(phi) * 34 + (o.hy || 0);
  const ang = Math.atan2(hy - by, hx - bx), len = Math.hypot(hx - bx, hy - by);
  const sc = len / 440;                                       // the pinch sits about 440 px up the handle
  S(c, SET, cam, 'tt_spoon', bx + 14 * lift, by + 20 * lift, 1, { r: ang, sx: sc, s: 1, a: 0.35 * a, blend: 'multiply' });   // its shadow
  S(c, SET, cam, 'tt_spoon', bx, by - 24 * lift, 1, { r: ang, sx: sc, a });
  if (lift < 0.5) inSet(c, SET, cam, 1, () => {               // the bowl is under the surface
    c.save(); c.beginPath(); c.arc(CUP[0], CUP[1], COF_R, 0, TAU); c.clip();
    const g = c.createRadialGradient(bx, by, 0, bx, by, 96); g.addColorStop(0, `rgba(70,42,28,${0.82 * (1 - lift * 2) * a})`); g.addColorStop(0.6, `rgba(70,42,28,${0.6 * (1 - lift * 2) * a})`); g.addColorStop(1, 'rgba(70,42,28,0)');
    c.fillStyle = g; c.fillRect(bx - 100, by - 100, 200, 200); c.restore();
  });
  if (o.hand !== false) {
    S(c, SET, cam, 'tt_hand_sh', hx + 20 * lift, hy + 26 * lift, 1, { a: 0.8 * a });
    S(c, SET, cam, 'tt_hand', hx, hy - 20 * lift, 1, { a, r: (ang - 0.62) * 0.35 });
  }
  return [bx, by, hx, hy];
}
export function topSteam(c, cam, t, a = 1) {
  // from above, steam is a slow pale swirl drifting off the cup toward the window
  inSet(c, SET, cam, 1, () => {
    for (let i = 0; i < 7; i++) {
      const per = 5.5, ph = hash(i * 3.7), k = Math.floor(t / per + ph), u = t / per + ph - k;
      const an = hash(i + k * 1.9) * TAU + u * 1.6, r = 30 + 250 * u, x = CUP[0] - 120 * u + Math.cos(an) * r * 0.5, y = CUP[1] - 150 * u + Math.sin(an) * r * 0.5;
      glow(c, x, y, 90 + 240 * u, [255, 250, 240], 0.13 * a * Math.sin(u * Math.PI), { mid: 0.5 });
    }
  });
}

// ================================================================ shots
export const warmTable = { warm: 0.25, bloom: 0.55, vig: 0.5 };

// V1 「可我慢慢搅拌 / 一小匙苦 入口不回嘴」: the clock outside hurries; the spoon does not.
export function stir(c, t, lt, sh) {
  const a0 = T0(2), a1 = T0(3), drip = CT(3, 3) - 0.05;              // 苦: the drop lands
  // slow: one turn every two bars. The surface lags the spoon and keeps turning after it stops.
  const turn = (x) => 0.38 * TAU * (x - a0 + 2.2);
  const stopT = a1 + 0.9, phi = -0.9 + (t < stopT ? turn(t) : turn(stopT) + 0.25 * (1 - Math.exp(-(t - stopT) * 3)));
  const theta = phi - 0.9 + (t > stopT ? 0.6 * (1 - Math.exp(-(t - stopT) * 0.5)) : 0);
  const lift = ramp(t, a1 + 1.0, 0.9, 'out') * (1 - ramp(t, drip + 1.8, 1.2));
  const cam = camK(lt, [[0, CUP[0] + 30, CUP[1] + 10, 1180, -0.05], [sh.len * 0.55, CUP[0] + 60, CUP[1] + 20, 1420, 0.02], [sh.len, CUP[0] + 20, CUP[1] + 40, 1900, 0.06]], { drift: 5 });
  still(c, cam, t, { phone: false });
  coffee(c, cam, t, theta, { swirl: clamp(1.2 - 0.4 * lift) });
  cupRings(c, cam, t, [[drip, CUP[0] + 30, CUP[1] - 20], [drip + 0.5, CUP[0] + 34, CUP[1] - 16]]);
  stirring(c, cam, t, phi, { lift });
  // the one bitter drop that falls back from the spoon
  const du = (t - (drip - 0.42)) / 0.42;
  if (du > 0 && du < 1) inSet(c, SET, cam, 1, () => { c.fillStyle = 'rgba(60,34,22,0.9)'; const r = 9 * (1.4 - 0.5 * du); c.beginPath(); c.ellipse(CUP[0] + 30, CUP[1] - 20 - 30 * (1 - du * du), r * 0.8, r, 0, 0, TAU); c.fill(); });
  topSteam(c, cam, t, 0.8);
  inSet(c, SET, cam, 1, () => lamp(c, CUP[0] - 420, CUP[1] - 560, 900, t, 0.22));
  return { grade: warmTable };
}
