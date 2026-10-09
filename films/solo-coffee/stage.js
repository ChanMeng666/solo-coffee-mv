// Stage kit for 独身主义的咖啡: loads the painted layers, stacks them under a parallax camera, and adds what a painting
// cannot do alone: light, rain, steam, ripples, drawn-on lines. Every function is a pure function of its arguments.
import { clamp, lerp, sstep, hash, hash2, noise1, noise2, loadImage, makeCanvas, TAU, E } from '/lib/mv.js';

export const W = 1920, H = 1080;
export const MAN = {}, IM = {};
export const PAL = { amber: [255, 190, 96], warm: [255, 214, 150], persimmon: [226, 96, 52], teal: [52, 108, 124], rose: [236, 120, 140], cream: [250, 240, 216], ink: [42, 30, 28], rain: [196, 214, 226] };
export const rgba = (c, a = 1) => `rgba(${c[0]},${c[1]},${c[2]},${a})`;

export async function loadArt(base = './art/') {
  Object.assign(MAN, await (await fetch(base + 'manifest.json')).json());
  await Promise.all(Object.entries(MAN).map(async ([k, e]) => { IM[k] = await loadImage(base + e.f); }));
}

// ---------------------------------------------------------------- camera
// A set is a painted world of sw x sh sheet pixels. A camera is { x, y, w, r }: the sheet point at the centre of the
// frame, the width of sheet it sees, and a roll. Depth p: 1 = the plane the set was painted on, <1 farther, >1 nearer.
export const SETS = { table: [3072, 1728], street: [3072, 1728], umbrella: [3072, 1728], chair: [2560, 1440], window: [2880, 1620], corner: [2880, 1620], shop: [3456, 1944], cup: [2560, 1440] };
export function camT(c, set, cam, p = 1) {
  const [sw, sh] = SETS[set], s0 = W / sw, s = W / cam.w, sp = s0 * Math.pow(s / s0, p);
  c.translate(W / 2, H / 2);
  if (cam.r) c.rotate(cam.r);
  c.scale(sp, sp);
  c.translate(-(sw / 2 + (cam.x - sw / 2) * p), -(sh / 2 + (cam.y - sh / 2) * p));
}
// sheet point → frame pixel, at depth p
export function toScreen(set, cam, x, y, p = 1) {
  const [sw, sh] = SETS[set], s0 = W / sw, s = W / cam.w, sp = s0 * Math.pow(s / s0, p);
  let dx = (x - (sw / 2 + (cam.x - sw / 2) * p)) * sp, dy = (y - (sh / 2 + (cam.y - sh / 2) * p)) * sp;
  if (cam.r) { const cr = Math.cos(cam.r), sr = Math.sin(cam.r); [dx, dy] = [dx * cr - dy * sr, dx * sr + dy * cr]; }
  return [W / 2 + dx, H / 2 + dy];
}
// camera from keys [[t, x, y, w, r?], ...]: eased between keys, zoom in log space; ease per segment via key[5] (default inOutCubic-ish smoothstep)
export function camK(lt, keys, o = {}) {
  let i = 0; while (i < keys.length - 2 && lt >= keys[i + 1][0]) i++;
  const a = keys[i], b = keys[Math.min(i + 1, keys.length - 1)];
  let u = b[0] > a[0] ? clamp((lt - a[0]) / (b[0] - a[0])) : 0;
  const ez = b[5] || o.ease || 'io';
  u = ez === 'lin' ? u : ez === 'out' ? E.outCubic(u) : ez === 'in' ? E.inCubic(u) : ez === 'outq' ? E.outQuad(u) : u * u * (3 - 2 * u);
  const cam = { x: lerp(a[1], b[1], u), y: lerp(a[2], b[2], u), w: Math.exp(lerp(Math.log(a[3]), Math.log(b[3]), u)), r: lerp(a[4] || 0, b[4] || 0, u) };
  if (o.drift) { const d = o.drift, sp = o.driftSp ?? 0.11, sd = o.seed ?? 1; cam.x += noise1(lt * sp, sd) * d * cam.w / 1920; cam.y += noise1(lt * sp * 1.13 + 40, sd + 3) * d * 0.7 * cam.w / 1920; cam.r += noise1(lt * sp * 0.8 + 9, sd + 5) * (o.roll ?? 0.0015); }
  return cam;
}

// ---------------------------------------------------------------- layers and sprites
// a full painted layer of the set (its manifest ox/oy place it on the sheet; `at` meta or o.x/o.y can shift it)
export function L(c, set, cam, name, p = 1, o = {}) {
  const m = MAN[name]; if (!m) throw new Error('no art ' + name);
  const a = o.a ?? 1; if (a <= 0.003) return;
  c.save(); camT(c, set, cam, p);
  c.globalAlpha *= a; if (o.blend) c.globalCompositeOperation = o.blend;
  const at = m.at || [0, 0];
  c.drawImage(IM[name], m.ox + at[0] + (o.x || 0), m.oy + at[1] + (o.y || 0));
  c.restore();
}
// a sprite placed by its anchor at sheet point (x, y)
export function S(c, set, cam, name, x, y, p = 1, o = {}) {
  const m = MAN[name]; if (!m) throw new Error('no art ' + name);
  const a = o.a ?? 1; if (a <= 0.003) return;
  c.save(); camT(c, set, cam, p);
  c.translate(x, y); if (o.r) c.rotate(o.r);
  const s = o.s ?? 1; c.scale(s * (o.sx ?? 1), s * (o.sy ?? 1));
  if (o.kx) c.transform(1, 0, o.kx, 1, 0, 0);
  c.globalAlpha *= a; if (o.blend) c.globalCompositeOperation = o.blend;
  c.drawImage(IM[name], m.ox - (o.ax ?? m.ax ?? m.sw / 2), m.oy - (o.ay ?? m.ay ?? m.sh / 2));
  c.restore();
}
// run fn(c) in sheet coordinates at depth p
export function inSet(c, set, cam, p, fn) { c.save(); camT(c, set, cam, p); fn(c); c.restore(); }
export function fill(c, color, a = 1, blend = 'source-over') {
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = a; c.globalCompositeOperation = blend; c.fillStyle = color; c.fillRect(0, 0, W, H); c.restore();
}

// ---------------------------------------------------------------- light
// soft disc of light in the current transform (sheet coords inside inSet, frame px otherwise)
export function glow(c, x, y, R, col, a = 1, o = {}) {
  if (a <= 0.003 || R <= 0) return;
  c.save(); c.translate(x, y); c.scale(1, o.sy ?? 1); if (o.r) c.rotate(o.r);
  const g = c.createRadialGradient(0, 0, 0, 0, 0, R);
  g.addColorStop(0, rgba(col, a)); g.addColorStop(o.mid ?? 0.35, rgba(col, a * 0.45)); g.addColorStop(1, rgba(col, 0));
  c.globalCompositeOperation = o.blend || 'screen'; c.fillStyle = g; c.fillRect(-R, -R, R * 2, R * 2);
  c.restore();
}
// a lamp: wide halo, tight core, and a breath of flicker
export function lamp(c, x, y, R, t, level = 1, o = {}) {
  const fl = 1 + 0.035 * noise1(t * 7, o.seed ?? 5) + 0.02 * noise1(t * 19, (o.seed ?? 5) + 1), col = o.col || PAL.amber;
  glow(c, x, y, R * fl, col, 0.55 * level * fl, o);
  glow(c, x, y, R * 0.38 * fl, PAL.warm, 0.85 * level * fl, o);
  glow(c, x, y, R * 0.10, [255, 244, 220], 0.9 * level, { ...o, blend: 'lighter' });
}
// darken everything but a pool (multiply): for "the lamp is the only light"
export function shadePool(c, x, y, r0, r1, dark = 'rgb(70,60,80)', a = 1) {
  c.save(); c.globalCompositeOperation = 'multiply'; c.globalAlpha = a;
  const g = c.createRadialGradient(x, y, r0, x, y, r1); g.addColorStop(0, '#fff'); g.addColorStop(1, dark);
  c.fillStyle = g; c.fillRect(x - r1 * 3, y - r1 * 3, r1 * 6, r1 * 6); c.restore();
}

// ---------------------------------------------------------------- weather (closed form in t)
// falling rain in frame px. o: n, seed, a, len, slant, v, col, w
export function rain(c, t, o = {}) {
  const n = o.n ?? 160, seed = o.seed ?? 3, a = o.a ?? 0.3, len = o.len ?? 60, sl = o.slant ?? -0.10, v = o.v ?? 1700, col = o.col || PAL.rain;
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.lineCap = 'round'; if (o.blend) c.globalCompositeOperation = o.blend;
  for (let i = 0; i < n; i++) {
    const h1 = hash(seed * 13 + i), h2 = hash(seed * 29 + i * 1.7), sp = 0.7 + 0.6 * h2;
    const y = ((h1 * (H + 240) + v * sp * t) % (H + 240)) - 120, x = ((h2 * (W + 300) + sl * v * sp * t) % (W + 300) + W + 300) % (W + 300) - 150;
    c.strokeStyle = rgba(col, a * (0.3 + 0.7 * h1)); c.lineWidth = (o.w ?? 1) * (0.7 + 1.5 * h2);
    c.beginPath(); c.moveTo(x, y); c.lineTo(x + sl * len * sp, y + len * sp); c.stroke();
  }
  c.restore();
}
// rings on water, in the current transform. Each of n sites fires every `per` seconds at its own phase.
// box: [x0, y0, x1, y1]; sy squashes the ring for perspective. A site can be forced onto beats with o.at (array of times).
export function ripples(c, t, box, o = {}) {
  const n = o.n ?? 24, seed = o.seed ?? 7, per = o.per ?? 1.6, R = o.R ?? 60, sy = o.sy ?? 1, col = o.col || PAL.rain, a = o.a ?? 0.5;
  c.save(); if (o.blend) c.globalCompositeOperation = o.blend;
  for (let i = 0; i < n; i++) {
    const ph = hash(seed * 7 + i * 3.3), k = Math.floor(t / per + ph), u = t / per + ph - k;
    const x = lerp(box[0], box[2], hash(seed + i * 1.7 + k * 5.3)), y = lerp(box[1], box[3], hash(seed * 3 + i * 2.9 + k * 9.1));
    const rr = R * (0.5 + 0.8 * hash(i + k * 1.3 + seed));
    for (let q = 0; q < 2; q++) {
      const uu = u - q * 0.16; if (uu <= 0) continue;
      const r = rr * E.outCubic(uu), al = a * (1 - uu) * (1 - uu) * (q ? 0.5 : 1);
      c.strokeStyle = rgba(col, al); c.lineWidth = (o.w ?? 2.2) * (1 - 0.5 * uu);
      c.beginPath(); c.ellipse(x, y, r, r * sy, 0, 0, TAU); c.stroke();
    }
  }
  c.restore();
}
// one ring at a known moment (a tap, a drop): u = seconds since the event
export function ring(c, x, y, dt, o = {}) {
  const life = o.life ?? 1.6; if (dt < 0 || dt > life) return;
  const u = dt / life, R = (o.R ?? 300) * E.outCubic(u), col = o.col || PAL.cream, sy = o.sy ?? 1;
  c.save(); if (o.blend) c.globalCompositeOperation = o.blend;
  for (let q = 0; q < (o.rings ?? 3); q++) {
    const r = R * (1 - q * 0.22); if (r <= 2) continue;
    c.strokeStyle = rgba(col, (o.a ?? 0.8) * (1 - u) * (1 - u) * (1 - q * 0.3)); c.lineWidth = (o.w ?? 3) * (1 - 0.6 * u);
    // a hand-drawn ring: slightly open, slightly wobbling
    c.beginPath();
    for (let k = 0; k <= 64; k++) { const an = k / 64 * TAU * 0.985 + q * 1.3 + (o.rot ?? 0), wob = 1 + 0.012 * noise1(k * 0.35 + q * 9, (o.seed ?? 1) + q); const px = x + Math.cos(an) * r * wob, py = y + Math.sin(an) * r * wob * sy; k ? c.lineTo(px, py) : c.moveTo(px, py); }
    c.stroke();
  }
  c.restore();
}
// out-of-focus lights behind wet glass, frame px. Drifts sideways slowly (traffic); some discs blink like signals.
export function bokeh(c, t, o = {}) {
  const n = o.n ?? 40, seed = o.seed ?? 11, a = o.a ?? 0.5, y0 = o.y0 ?? H * 0.3, y1 = o.y1 ?? H * 0.75, cols = o.cols || [PAL.amber, PAL.warm, PAL.rose, PAL.teal, [150, 200, 220]];
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.globalCompositeOperation = o.blend || 'screen';
  for (let i = 0; i < n; i++) {
    const h1 = hash(seed + i * 1.9), h2 = hash(seed * 3 + i * 4.7), h3 = hash(seed * 5 + i * 7.3), h4 = hash(seed * 11 + i * 2.3);
    const v = (h3 - 0.5) * (o.v ?? 40) * (h4 > 0.6 ? 3 : 0.3);
    const x = (((h1 * (W + 400) + v * t) % (W + 400)) + W + 400) % (W + 400) - 200 + (o.dx || 0) * (0.5 + h2), y = lerp(y0, y1, h2 * h2 * (h3 > 0.5 ? 1 : 0.6) + (1 - h2) * 0.2 * h3);
    const r = (o.r ?? 34) * (0.45 + 1.1 * h4), col = cols[Math.floor(h3 * cols.length) % cols.length];
    const tw = 0.7 + 0.3 * Math.sin(t * (0.6 + 2 * h2) + h1 * 30) * (h4 > 0.8 ? 1 : 0.3);
    const g = c.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, rgba(col, a * tw * 0.75)); g.addColorStop(0.72, rgba(col, a * tw * 0.6)); g.addColorStop(0.86, rgba(col, a * tw * 0.8)); g.addColorStop(1, rgba(col, 0));
    c.fillStyle = g; c.fillRect(x - r, y - r, r * 2, r * 2);
  }
  c.restore();
}

// ---------------------------------------------------------------- steam
// A plume of soft puffs rising from (x, y) in the current transform. Closed form: puff i is born every `per` seconds.
// o.bend(u, t) can steer the plume (the saxophone answers the voice: the steam curls).
let PUFF;
export function steam(c, t, x, y, o = {}) {
  if (!PUFF) { const [cv, cx] = makeCanvas(128, 128); const g = cx.createRadialGradient(64, 64, 0, 64, 64, 64); g.addColorStop(0, 'rgba(255,255,255,0.9)'); g.addColorStop(0.45, 'rgba(255,255,255,0.35)'); g.addColorStop(1, 'rgba(255,255,255,0)'); cx.fillStyle = g; cx.fillRect(0, 0, 128, 128); PUFF = cv; }
  const n = o.n ?? 26, per = o.per ?? 0.28, life = n * per, hgt = o.h ?? 420, a = o.a ?? 0.35, w0 = o.w ?? 46, seed = o.seed ?? 2, sway = o.sway ?? 60;
  c.save(); c.globalCompositeOperation = o.blend || 'screen';
  const k0 = Math.floor(t / per);
  for (let j = 0; j < n; j++) {
    const k = k0 - j, age = t - k * per, u = age / life; if (u < 0 || u >= 1 || k < (o.k0 ?? -1e9)) continue;
    const h1 = hash(k * 1.37 + seed), h2 = hash(k * 2.91 + seed * 3);
    const rise = hgt * (1 - Math.pow(1 - u, 1.6));
    let px = x + (h1 - 0.5) * w0 * 0.5 + sway * u * (noise1(u * 2.2 + k * 0.13 + t * 0.12, seed) + 0.5 * Math.sin(u * 5 + t * 0.9 + seed)), py = y - rise;
    if (o.bend) { const b = o.bend(u, t, k); px += b[0]; py += b[1]; }
    const r = w0 * (0.5 + 2.4 * u) * (0.8 + 0.5 * h2), al = a * sstep(0, 0.12, u) * (1 - u) * (1 - u) * (0.6 + 0.6 * h2);
    c.globalAlpha = clamp(al); c.drawImage(PUFF, px - r, py - r * 1.25, r * 2, r * 2.5);
  }
  c.restore();
}
// a ribbon of steam along a path that draws itself: for the sax line. pts(u) → [x, y]; head 0..1, tail length in u
export function ribbon(c, pts, head, tailLen, o = {}) {
  const n = 60, a = o.a ?? 0.5, w = o.w ?? 26, col = o.col || PAL.cream;
  c.save(); c.globalCompositeOperation = o.blend || 'screen'; c.lineCap = 'round';
  for (let i = 0; i < n; i++) {
    const u = head - tailLen * (i / n); if (u < 0 || u > 1) continue;
    const u2 = head - tailLen * ((i + 1) / n), [x0, y0] = pts(u), [x1, y1] = pts(Math.max(0, u2)), f = i / n;
    c.strokeStyle = rgba(col, a * (1 - f) * (1 - f) * sstep(0, 0.1, f + 0.04)); c.lineWidth = w * (0.35 + 1.4 * f);
    c.beginPath(); c.moveTo(x0, y0); c.lineTo(x1, y1); c.stroke();
  }
  c.restore();
}

// ---------------------------------------------------------------- pen
// a wobbly pen stroke drawn by the page (pts in the current transform), revealed to u
export function pen(c, pts, u, o = {}) {
  if (u <= 0) return;
  c.save(); c.lineCap = 'round'; c.lineJoin = 'round'; c.strokeStyle = o.color || rgba(PAL.ink, 0.85);
  const seed = o.seed ?? 1, tr = o.tremor ?? 1.4, w = o.w ?? 3;
  let tot = 0; const seg = [];
  for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(d); tot += d; }
  let acc = 0; const lim = tot * clamp(u);
  for (let i = 1; i < pts.length && acc < lim; i++) {
    const n = Math.max(1, Math.ceil(seg[i - 1] / 8));
    for (let k = 0; k < n; k++) {
      const s0 = acc + seg[i - 1] * k / n; if (s0 >= lim) break;
      const q = (uu) => [lerp(pts[i - 1][0], pts[i][0], uu) + noise1(seed * 9 + (acc + seg[i - 1] * uu) * 0.06, seed) * tr, lerp(pts[i - 1][1], pts[i][1], uu) + noise1(seed * 5 + (acc + seg[i - 1] * uu) * 0.06, seed + 2) * tr];
      const a = q(k / n), b = q(Math.min((k + 1) / n, k / n + (lim - s0) / seg[i - 1]));
      c.lineWidth = w * (0.45 + 0.9 * (0.5 + 0.5 * noise1(s0 * 0.02, seed + 4)));
      c.beginPath(); c.moveTo(a[0], a[1]); c.lineTo(b[0], b[1]); c.stroke();
    }
    acc += seg[i - 1];
  }
  c.restore();
}
// a ring the way chalk or a dry brush would leave it: three passes that do not agree
export function chalk(c, pts, u, o = {}) {
  if (u <= 0) return;
  const w = o.w ?? 6, col = o.col || PAL.cream, a = o.a ?? 0.85;
  c.save(); c.globalCompositeOperation = o.blend || 'screen';
  for (let k = 0; k < 3; k++) pen(c, pts, clamp(u * (1 + 0.04 * k) - 0.02 * k), { color: rgba(col, a * [0.55, 0.36, 0.26][k]), w: w * [1, 0.5, 1.7][k], seed: (o.seed ?? 1) * 7 + k * 3, tremor: (o.tremor ?? 3) * (1 + 0.7 * k) });
  c.restore();
}
export const circlePts = (x, y, r, n = 48, a0 = 0, turn = 1, sy = 1) => Array.from({ length: n + 1 }, (_, k) => { const a = a0 + (k / n) * TAU * turn; return [x + Math.cos(a) * r, y + Math.sin(a) * r * sy]; });
// position along a polyline at u (0..1 by length)
export function along(pts, u) {
  let tot = 0; const seg = [];
  for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(d); tot += d; }
  let s = clamp(u) * tot;
  for (let i = 0; i < seg.length; i++) { if (s <= seg[i] || i === seg.length - 1) { const f = seg[i] ? clamp(s / seg[i]) : 0; return [lerp(pts[i][0], pts[i + 1][0], f), lerp(pts[i][1], pts[i + 1][1], f), Math.atan2(pts[i + 1][1] - pts[i][1], pts[i + 1][0] - pts[i][0])]; } s -= seg[i]; }
  return [...pts[pts.length - 1], 0];
}
export { clamp, lerp, sstep, hash, hash2, noise1, noise2, makeCanvas, TAU, E };
