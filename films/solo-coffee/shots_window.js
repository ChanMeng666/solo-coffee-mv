// The window by the corner seat: rain on the glass, the clock on the wall, the people who pass, the fog she draws in.
import { W, H, PAL, rgba, L, S, inSet, camT, camK, toScreen, glow, lamp, rain, ring, bokeh, steam, pen, along, MAN, clamp, lerp, sstep, hash, noise1, makeCanvas, TAU, E } from './stage.js';
import { TM, B, T0, CT, LN, beatNear, beatIdx, kickN, since, ramp } from './core.js';

const SET = 'window';
const [maskCv, maskCx] = makeCanvas(960, 540), [wipeCv, wipeCx] = makeCanvas(960, 540);
const half = (cx) => { cx.setTransform(0.5, 0, 0, 0.5, 0, 0); cx.globalAlpha = 1; cx.globalCompositeOperation = 'source-over'; cx.clearRect(0, 0, W, H); return cx; };
const CLOCK = [2570, 520];

// ---------------------------------------------------------------- pieces
function outside(c, cam, t, o = {}) {
  L(c, SET, cam, 'wn_out', 0.4);
  if (o.dusk) { c.save(); c.globalCompositeOperation = 'multiply'; c.fillStyle = rgba([150, 160, 200], o.dusk); c.fillRect(0, 0, W, H); c.restore(); }
  bokeh(c, t, { n: o.bokeh ?? 34, a: o.bokehA ?? 0.42, y0: H * 0.34, y1: H * 0.82, r: o.bokehR ?? 30, seed: o.seed ?? 11, v: 46 });
  for (const p of o.passers || []) S(c, SET, cam, p.name, p.x, p.y ?? 1160, 0.62, { s: p.s ?? 0.92, sx: p.flip ? -1 : 1, a: p.a ?? 0.92 });
  if (o.rain !== 0) rain(c, t, { n: 150, a: 0.22 * (o.rain ?? 1), len: 70, seed: 5 });
}
function panesMask(cam, holes) {
  const m = half(maskCx);
  inSet(m, SET, cam, 1, () => { m.fillStyle = '#fff'; for (const p of MAN.wn_frame.panes) m.fillRect(p[0] - 3, p[1] - 3, p[2] - p[0] + 6, p[3] - p[1] + 6); });
  if (holes) holes(m);
  return maskCv;
}
// drops that gather on the awning's scallops and let go on the beat
function awningDrips(c, cam, t, a = 1) {
  const tips = MAN.wn_awn.tips, y0 = MAN.wn_awn.tip_y;
  inSet(c, SET, cam, 0.85, () => {
    const bi = beatIdx(t);
    for (let k = bi - 2; k <= bi + 2; k++) {
      if (k < 0 || k >= B.length) continue;
      const tb = B[k], x = tips[Math.floor(hash(k * 3.71) * tips.length)] + 4, dt = t - tb;
      if (dt < -0.62) continue;
      if (dt < 0) {                                        // swelling on the tip
        const u = 1 + dt / 0.62; c.fillStyle = rgba([226, 238, 244], 0.85 * a);
        c.beginPath(); c.ellipse(x, y0 + 6 + 5 * u, 5 + 4 * u, 6 + 8 * u, 0, 0, TAU); c.fill();
        c.fillStyle = rgba([255, 255, 255], 0.9 * a); c.beginPath(); c.arc(x - 2, y0 + 5 + 4 * u, 2, 0, TAU); c.fill();
      } else if (dt < 0.6) {                               // falling
        const y = y0 + 12 + 2600 * dt * dt; c.fillStyle = rgba([226, 238, 244], 0.8 * a);
        c.beginPath(); c.ellipse(x, y, 5, 13 + 40 * dt, 0, 0, TAU); c.fill();
      }
    }
  });
}
function clock(c, cam, t, o = {}) {
  const [x, y] = CLOCK, bt = TM.beat(t);
  S(c, SET, cam, 'wn_clock', x, y);
  S(c, SET, cam, 'wn_pend', x, y + 205, 1, { r: 0.30 * Math.cos(bt * Math.PI) });        // a full swing every two beats
  inSet(c, SET, cam, 1, () => {
    c.lineCap = 'round';
    const hand = (ang, len, w, col) => { c.strokeStyle = col; c.lineWidth = w; c.beginPath(); c.moveTo(x - Math.sin(ang) * len * 0.14, y + Math.cos(ang) * len * 0.14); c.lineTo(x + Math.sin(ang) * len, y - Math.cos(ang) * len); c.stroke(); };
    const sec = Math.floor(bt), f = bt - sec, tick = (sec + (f < 0.12 ? E.outBack(f / 0.12) - 1 : 0)) * TAU / 60;   // the second hand jumps on the beat
    hand(TAU * (5.72 / 12) + (o.fast || 0) / 12, 82, 9, rgba(PAL.ink, 0.92)); hand(TAU * 0.72 + (o.fast || 0), 122, 6, rgba(PAL.ink, 0.92)); hand(tick + 1.1, 132, 2.6, 'rgba(150,60,40,0.95)');
    c.fillStyle = rgba(PAL.ink); c.beginPath(); c.arc(x, y, 8, 0, TAU); c.fill();
  });
}
function room(c, cam, t, o = {}) {
  L(c, SET, cam, 'wn_frame');
  // the lamp inside, mirrored faintly in the panes, and its warmth on the wall
  inSet(c, SET, cam, 1, () => { glow(c, 330, 520, 760, PAL.amber, 0.20 * (o.lamp ?? 1)); });
  clock(c, cam, t, o);
  const lx = 330 + 10 * Math.sin(t * 0.7), ly = 430;
  S(c, SET, cam, 'lamp_pendant', lx, ly, 1.22, { r: 0.012 * Math.sin(t * 0.7) });
  inSet(c, SET, cam, 1.22, () => lamp(c, lx, ly + 10, 520, t, 0.75 * (o.lamp ?? 1)));
}

// ================================================================ shots
// V1 「窗外在滴答 / 像谁的钟在催」: the drops keep time; so does the clock; neither is hers.
export function drops(c, t, lt, sh) {
  const tk = CT(1, 3);                                    // 钟
  const cam = camK(t, [[sh.t0, 1400, 650, 2500], [T0(1) - 0.7, 1400, 640, 2060], [tk - 0.1, 2120, 600, 1500], [sh.t1 + 0.8, 2560, 524, 620, 0, 'in']], { drift: 4 });
  outside(c, cam, t, { passers: [{ name: 'wn_single', x: 3000 - (t - sh.t0) * 150, s: 0.9 }] });
  L(c, SET, cam, 'wn_awn', 0.85);
  awningDrips(c, cam, t);
  room(c, cam, t);
  return { glass: { rain: 0.62, beads: 0.42, fog: 0.22, mask: panesMask(cam) }, grade: { warm: 0.12, bloom: 0.6 } };
}

// CH1 「不等谁来陪 / 我和自己先约会」: pairs go by outside; she lifts her cup to the only other person here.
export function toast(c, t, lt, sh) {
  const a0 = T0(14), b0 = T0(15), clink = CT(15, 5), fogUp = ramp(t, clink + 2.6, 3.2);
  const cam = camK(t, [[sh.t0, 1560, 700, 2360], [b0, 1380, 700, 2080], [clink + 0.3, 1330, 690, 1900], [sh.t1, 1360, 640, 1500]], { drift: 5 });
  const raise = ramp(t, b0 + 0.2, clink - b0 - 0.2, 'out') * (1 - 0.0), back = ramp(t, clink + 1.6, 1.2);
  const fx = 1010, fy = 1300, ar = lerp(1.05, -0.12, raise) + 1.25 * back;                   // arm angle at the shoulder
  const pas = [{ name: 'wn_pair', x: 3300 - (t - a0 + 1.5) * 330, s: 0.95 }, { name: 'wn_pair', x: -500 + (t - a0 - 2.2) * 290, s: 0.86, flip: true, a: 0.8 }, { name: 'wn_single', x: 3900 - (t - a0) * 250, s: 0.8, a: 0.8 }];
  outside(c, cam, t, { passers: pas, seed: 14 });
  L(c, SET, cam, 'wn_awn', 0.85);
  // her reflection in the glass: fainter, smaller, a little higher. It raises its cup too.
  const gs = 0.80, gx = fx + 60, gy = fy - 250, ga = (0.26 + 0.14 * raise) * (1 - back) * (1 - fogUp);
  c.save(); c.filter = 'blur(2px) brightness(1.5)';
  S(c, SET, cam, 'fig_arm', gx + 220 * gs, gy + 60 * gs, 1, { r: ar, s: gs, a: ga, blend: 'screen' });
  S(c, SET, cam, 'fig_back', gx, gy, 1, { s: gs, a: ga, blend: 'screen' });
  c.restore();
  inSet(c, SET, cam, 1, () => glow(c, gx + 120, gy - 330, 420, PAL.amber, 0.22));          // the lamp behind her, in the glass
  room(c, cam, t);
  const holes = (m) => { S(m, SET, cam, 'fig_back', fx, fy, 1.18, { blend: 'destination-out' }); S(m, SET, cam, 'fig_arm', fx + 250, fy + 70, 1.18, { r: ar, blend: 'destination-out' }); };
  S(c, SET, cam, 'fig_arm', fx + 250, fy + 70, 1.18, { r: ar });
  S(c, SET, cam, 'fig_back', fx, fy, 1.18);
  // glass against glass: one small bright ring where the two cups meet
  const [sx, sy] = toScreen(SET, cam, fx + 250 + 780 * Math.cos(ar) + 520 * Math.sin(ar), fy + 70 + 780 * Math.sin(ar) - 520 * Math.cos(ar), 1.18);
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0);
  ring(c, sx, sy, t - clink, { R: 260, life: 1.5, col: PAL.warm, a: 0.9, w: 4, blend: 'screen', seed: 4 });
  glow(c, sx, sy, 150, PAL.warm, 0.8 * Math.exp(-Math.max(0, t - clink) * 4) * (t >= clink ? 1 : 0));
  c.restore();
  return { glass: { rain: 0.6, beads: 0.42, fog: lerp(0.26, 0.96, fogUp), mask: panesMask(cam, holes), seed: 20 }, grade: { warm: 0.2, bloom: 0.7 } };
}

// ---------------------------------------------------------------- the heart on the glass
// frame px. The left half is drawn first; then a smile; the right half only in the last chorus.
const HC = [960, 500], HS = 250;
function heartPts(a0, a1, n = 80) {          // classic heart curve; a = 0 at the bottom tip going up the left lobe
  const out = [];
  for (let k = 0; k <= n; k++) { const a = Math.PI + lerp(a0, a1, k / n), sx = 16 * Math.sin(a) ** 3, sy = 13 * Math.cos(a) - 5 * Math.cos(2 * a) - 2 * Math.cos(3 * a) - Math.cos(4 * a); out.push([HC[0] + sx * HS / 16, HC[1] - sy * HS / 16 - 20]); }
  return out;
}
const LEFT = heartPts(Math.PI, 0), RIGHT = heartPts(Math.PI, TAU);     // both halves start at the dip and come down to the point
const SMILE = Array.from({ length: 24 }, (_, k) => { const u = k / 23; return [HC[0] - 105 + 210 * u, HC[1] - 10 + 62 * Math.sin(u * Math.PI)]; });
const EYES = [[HC[0] - 84, HC[1] - 112], [HC[0] + 84, HC[1] - 112]];
function strokeTo(cx, pts, u, w, a = 1) {
  if (u <= 0) return null;
  cx.strokeStyle = `rgba(255,255,255,${a})`; cx.lineWidth = w; cx.lineCap = 'round'; cx.lineJoin = 'round';
  const n = pts.length - 1, f = clamp(u) * n, i1 = Math.floor(f);
  cx.beginPath(); cx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i <= i1; i++) cx.lineTo(pts[i][0], pts[i][1]);
  let hx = pts[i1][0], hy = pts[i1][1];
  if (i1 < n) { hx = lerp(pts[i1][0], pts[i1 + 1][0], f - i1); hy = lerp(pts[i1][1], pts[i1 + 1][1], f - i1); cx.lineTo(hx, hy); }
  cx.stroke();
  return [hx, hy];
}
// water runs from a line drawn in breath: thin clear tracks that lengthen
function drips(cx, pts, u, t, tDrawn, seed, a = 1) {
  const n = pts.length - 1;
  for (let k = 3; k < n; k += 5) {
    if (k / n > u) break;
    const h = hash(k * 3.3 + seed); if (h < 0.45) continue;
    const age = t - tDrawn(k / n) - 0.6 - h; if (age <= 0) continue;
    const len = (60 + 240 * hash(k + seed * 7)) * (1 - Math.exp(-age * 0.35)), x = pts[k][0], y = pts[k][1];
    cx.strokeStyle = `rgba(255,255,255,${0.75 * a})`; cx.lineWidth = 7 + 5 * h; cx.lineCap = 'round';
    cx.beginPath(); cx.moveTo(x, y);
    for (let q = 1; q <= 8; q++) cx.lineTo(x + 5 * Math.sin(q * 0.9 + k) * (q / 8), y + len * q / 8);
    cx.stroke();
    cx.fillStyle = `rgba(255,255,255,${0.9 * a})`; cx.beginPath(); cx.ellipse(x + 5 * Math.sin(7.2 + k), y + len, 6 + 3 * h, 9 + 4 * h, 0, 0, TAU); cx.fill();
  }
}
function fogView(c, t, cam, o = {}) {
  outside(c, cam, t, { bokeh: 46, bokehA: 0.6, bokehR: 44, passers: o.passers, seed: 23, rain: o.rain, dusk: o.dusk });
  if (o.memory) {            // the lamp across the street they once stood under
    const [lx, ly] = toScreen(SET, cam, o.memory[0], o.memory[1], 0.62);
    c.save(); c.setTransform(1, 0, 0, 1, 0, 0); glow(c, lx, ly - 360, 420, PAL.amber, 0.5 * o.memory[2]); glow(c, lx, ly, 300, PAL.amber, 0.22 * o.memory[2], { sy: 0.25 }); c.restore();
  }
}

// V2 「雾气在窗上 / 画一颗偷笑的心 / 画到一半又抹平 / 怕被看见 我的曾经」
export function heart(c, t, lt, sh) {
  const d0 = T0(16) + 0.15, d1 = T0(17) + 0.35, s0 = d1 + 0.4, s1 = s0 + 1.6, r0 = s1 + 0.6, r1 = T0(18) - 0.55;      // half the heart, the smile, then the other half: slower, and not finished
  const w0 = T0(18) + 0.25, w1 = T0(18) + 2.6;                                        // the wipe
  const seen = T0(19), refog = ramp(t, T0(19) + 1.9, 4.2);
  const cam = camK(t, [[sh.t0, 1400, 640, 1250], [w0, 1400, 650, 1120], [seen + 3, 1440, 660, 1040], [sh.t1, 1400, 650, 1100]], { drift: 3 });
  const mem = sstep(w0 + 0.6, seen + 0.4, t) * (1 - refog);
  fogView(c, t, cam, {});
  if (mem > 0.003) {                  // 我的曾经: two under one umbrella, under a lamp, across the street. They walk on.
    const mm = MAN.wn_pair, px = 1420 - 62 * (t - seen), py = 668 + 3 * Math.abs(Math.sin((t - seen) * 4.4)), sc = 0.44;
    c.save(); c.setTransform(1, 0, 0, 1, 0, 0);
    glow(c, px + 30, py - 330, 300, PAL.amber, 0.75 * mem); glow(c, px, py - 20, 260, PAL.amber, 0.35 * mem, { sy: 0.22 });
    c.globalAlpha = 0.95 * mem; c.translate(px, py); c.scale(sc, sc); c.drawImage(IMG('wn_pair'), mm.ox - mm.ax, mm.oy - mm.ay);
    c.restore();
  }
  // --- what the finger has cleared
  const x = wipeCx; x.setTransform(0.5, 0, 0, 0.5, 0, 0); x.globalCompositeOperation = 'source-over'; x.globalAlpha = 1; x.clearRect(0, 0, W, H);
  const uh = ramp(t, d0, d1 - d0, 'lin'), us = ramp(t, s0, s1 - s0, 'lin'), keep = 1 - 0.25 * ramp(t, d1, 8, 'lin');
  const tD = (u) => d0 + u * (d1 - d0);
  x.save(); x.filter = 'blur(2.5px)';
  let tip = strokeTo(x, LEFT, uh, 46, keep) || LEFT[0];
  drips(x, LEFT, uh, t, tD, 1, keep);
  const st = strokeTo(x, SMILE, us, 40, keep); if (st && us < 1) tip = st;
  const ur = 0.46 * E.outQuad(ramp(t, r0, r1 - r0, 'lin')), rt = strokeTo(x, RIGHT, ur, 46, keep); if (rt) tip = rt;
  x.restore();
  drips(x, RIGHT, ur, t, (u) => r0 + (u / 0.46) * (r1 - r0), 5, keep);
  const hop = (a, b, q) => [lerp(a[0], b[0], q), lerp(a[1], b[1], q) - 26 * Math.sin(q * Math.PI)];
  if (t > d1 && t < s0) tip = hop(LEFT[LEFT.length - 1], SMILE[0], ramp(t, d1, s0 - d1));
  if (t > s1 && t < r0) tip = hop(SMILE[SMILE.length - 1], RIGHT[0], ramp(t, s1, r0 - s1));
  // the wipe: the flat of the hand, one long pass, then a shorter one back
  const P1 = [[420, 300], [700, 380], [1000, 470], [1300, 520], [1560, 560]], P2 = [[1520, 700], [1200, 640], [900, 560], [640, 520]];
  const u1 = ramp(t, w0, 1.25, 'io'), u2 = ramp(t, w0 + 1.45, 1.0, 'io');
  const band = (pts, u, w) => {            // five finger-wide tracks, each a little ahead of or behind the others
    if (u <= 0) return;
    x.save(); x.filter = 'blur(7px)'; x.lineCap = 'round'; x.lineJoin = 'round';
    for (let f = 0; f < 5; f++) {
      const off = (f - 2) * w * 0.2, uu = clamp(u * (1.04 - 0.05 * hash(f * 3.1)) + 0.02 * (f === 2)), n = 40;
      x.strokeStyle = `rgba(255,255,255,${(1 - refog) * (0.82 + 0.18 * hash(f))})`; x.lineWidth = w * (0.24 + 0.06 * hash(f * 7));
      x.beginPath();
      for (let k = 0; k <= n * uu; k++) { const [px, py, an] = along(pts, k / n), wob = 9 * noise1(k * 0.3 + f * 5, 3); const qx = px - Math.sin(an) * (off + wob), qy = py + Math.cos(an) * (off + wob); k ? x.lineTo(qx, qy) : x.moveTo(qx, qy); }
      x.stroke();
    }
    x.restore();
  };
  band(P1, u1, 330); band(P2, u2, 300);
  // --- the hand, on our side of the glass
  const m = half(maskCx); m.fillStyle = '#fff'; m.fillRect(0, 0, W, H);
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0);
  const drawHand = (cx, blend) => {
    cx.save(); if (blend) cx.globalCompositeOperation = blend;
    if (t < w0 - 0.2) {                 // the pointing finger: follows the line, lifts off between strokes, then hesitates
      const inA = ramp(t, d0 - 1.0, 0.9, 'out'), lift = Math.max(sstep(d1, d1 + 0.2, t) * (1 - sstep(s0 - 0.2, s0, t)), sstep(s1, s1 + 0.2, t) * (1 - sstep(r0 - 0.2, r0, t))), away = ramp(t, r1 + 0.1, 0.5, 'in');
      const hx = tip[0] + 30 * lift + 260 * away, hy = tip[1] + 30 * lift + 700 * (1 - inA) + 760 * away + 5 * Math.sin(t * 2.1) * (t > r0 + 1.5 ? 1 : 0);
      spr(cx, 'fig_point', hx, hy, 1.0 + 0.05 * lift, -0.10 + 0.05 * noise1(t * 0.8, 3));
    } else {                            // the palm
      const u = t < w0 + 1.35 ? u1 : u2, P = t < w0 + 1.35 ? P1 : P2, [px, py] = along(P, u), out = ramp(t, w1, 1.1, 'in'), inn = ramp(t, w0 - 0.2, 0.45, 'out');
      spr(cx, 'fig_palm', px + 40 + 300 * out, py + 120 + 900 * out + 500 * (1 - inn), 1.05, 0.25 - 0.2 * u);
    }
    cx.restore();
  };
  function spr(cx, name, px, py, s, r) { const mm = MAN[name]; cx.save(); cx.translate(px, py); cx.rotate(r); cx.scale(s, s); cx.drawImage(IMG(name), mm.ox - mm.ax, mm.oy - mm.ay); cx.restore(); }
  drawHand(c); drawHand(m, 'destination-out');
  c.restore();
  return { glass: { rain: 0.5, beads: 0.6, fog: 0.97, wipe: wipeCv, mask: maskCv, scale: 0.8, seed: 31, fogCol: [0.80, 0.85, 0.88] }, grade: { warm: 0.02, bloom: 0.8, sat: 1.08 }, lyric: { y: 104 } };
}

// CH3 「在舌尖慢慢化开了防备」: this time she finishes it. Then the whole pane clears from the heart outward.
export function heartDone(c, t, lt, sh) {
  const d0 = T0(42) + 0.05, d1 = d0 + 1.0, d2 = d1 + 1.1, s0 = d2 + 0.22, s1 = s0 + 0.55, e0 = s1 + 0.12, open = ramp(t, CT(42, 5) + 0.9, sh.t1 - CT(42, 5) - 0.7, 'in');
  const cam = camK(t, [[sh.t0, 1400, 650, 1150], [sh.t1, 1400, 640, 1500]], { drift: 3 });
  fogView(c, t, cam, { rain: 0.5 * (1 - open), dusk: 0 });
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.globalCompositeOperation = 'screen';      // the sky lets go: after rain, the low sun
  { const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, rgba([255, 206, 150], 0.62 * open)); g.addColorStop(0.6, rgba([255, 170, 150], 0.40 * open)); g.addColorStop(1, rgba([120, 150, 200], 0.25 * open)); c.fillStyle = g; c.fillRect(0, 0, W, H); }
  glow(c, W * 0.56, H * 0.34, 900, [255, 240, 210], 0.5 * open); c.restore();
  const x = wipeCx; x.setTransform(0.5, 0, 0, 0.5, 0, 0); x.globalCompositeOperation = 'source-over'; x.globalAlpha = 1; x.clearRect(0, 0, W, H);
  const ul = ramp(t, d0, d1 - d0, 'lin'), ur = ramp(t, d1 + 0.2, d2 - d1 - 0.2, 'lin'), us = ramp(t, s0, s1 - s0, 'lin');
  let tip = strokeTo(x, LEFT, ul, 46) || LEFT[0];
  const tr = strokeTo(x, RIGHT, ur, 46); if (tr) tip = tr;
  const ts = strokeTo(x, SMILE, us, 40); if (ts) tip = ts;
  const hop = (a, b, q) => [lerp(a[0], b[0], q), lerp(a[1], b[1], q) - 26 * Math.sin(q * Math.PI)];
  if (t > d1 && t < d1 + 0.2) tip = hop(LEFT[LEFT.length - 1], RIGHT[0], ramp(t, d1, 0.2));
  if (t > d2 && t < s0) tip = hop(RIGHT[RIGHT.length - 1], SMILE[0], ramp(t, d2, s0 - d2));
  for (let k = 0; k < 2; k++) { const a = ramp(t, e0 + k * 0.22, 0.12); if (a > 0) { x.fillStyle = '#fff'; x.beginPath(); x.arc(EYES[k][0], EYES[k][1], 24 * a, 0, TAU); x.fill(); if (a < 1) tip = EYES[k]; } }
  drips(x, LEFT, ul, t, (u) => d0 + u * (d1 - d0), 1); drips(x, RIGHT, ur, t, (u) => d1 + 0.2 + u * (d2 - d1 - 0.2), 5);
  if (open > 0) {                     // the clearing spreads from the heart, ragged
    x.save(); x.filter = 'blur(26px)'; x.fillStyle = '#fff'; x.beginPath();
    for (let k = 0; k <= 72; k++) { const a = k / 72 * TAU, r = 60 + open * 1700 * (0.82 + 0.22 * noise1(k * 0.3, 7)); k ? x.lineTo(HC[0] + Math.cos(a) * r, HC[1] - 60 + Math.sin(a) * r * 0.8) : x.moveTo(HC[0] + r, HC[1] - 60); }
    x.fill(); x.restore();
  }
  const m = half(maskCx); m.fillStyle = '#fff'; m.fillRect(0, 0, W, H);
  const inA = ramp(t, d0 - 0.9, 0.8, 'out'), away = ramp(t, e0 + 0.6, 1.0, 'in');
  for (const [cx, blend] of [[c, null], [m, 'destination-out']]) {
    const mm = MAN.fig_point; cx.save(); if (cx === c) cx.setTransform(1, 0, 0, 1, 0, 0); if (blend) cx.globalCompositeOperation = blend;
    cx.translate(tip[0] + 240 * away, tip[1] + 700 * (1 - inA) + 800 * away); cx.rotate(-0.10); cx.drawImage(IMG('fig_point'), mm.ox - mm.ax, mm.oy - mm.ay); cx.restore();
  }
  return { glass: { rain: 0.5 * (1 - open), beads: 0.6 * (1 - 0.6 * open), fog: 0.97, wipe: wipeCv, mask: maskCv, scale: 0.8, seed: 31 }, grade: { warm: 0.12 + 0.3 * open, bloom: 0.8 + 0.4 * open, sat: 1.08 }, lyric: { y: 104 } };
}
import { IM } from './stage.js';
const IMG = (n) => IM[n];
