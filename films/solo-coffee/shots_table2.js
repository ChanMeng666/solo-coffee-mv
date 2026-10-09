// More visits to the table: the chorus's small pleasures, the phone turned face down, the spoon on the rim,
// sugar in orbit, the table after she has gone, and the end card.
import { W, H, PAL, rgba, L, S, inSet, camK, glow, lamp, ring, pen, chalk, circlePts, MAN, IM, clamp, lerp, sstep, hash, noise1, TAU, E } from './stage.js';
import { TM, B, T0, CT, beatNear, kickN, since, ramp } from './core.js';
import { SET, CUP, COF_R, CUP_R, SUGAR, PHONE, coffee, cupRings, still, topSteam, warmTable } from './shots_table.js';

const cubeAt = (u, from, to, h = 150) => [lerp(from[0], to[0], u), lerp(from[1], to[1], u) - h * Math.sin(u * Math.PI)];
const tableLamp = (c, cam, t, lv) => inSet(c, SET, cam, 1, () => lamp(c, CUP[0] - 420, CUP[1] - 560, 900, t, lv));

// CH1 「一个人也很完美 / 不必为谁 收敛口味 / 糖多一点 还是不加也无所谓」: one shot, three small pleasures.
export function chorusTable(c, t, lt, sh) {
  const m0 = T0(10), s0 = T0(11), no = CT(11, 7);            // 不加
  const cam = camK(t, [[sh.t0, 1600, 870, 2500, -0.07], [m0 - 0.3, 1560, 880, 2300, 0.0], [m0 + 1.6, CUP[0] + 20, CUP[1], 1080, 0.05], [s0 - 0.2, CUP[0] + 40, CUP[1] - 10, 1040, 0.07], [s0 + 1.0, CUP[0] + 300, CUP[1] - 150, 1700, 0.02], [sh.t1, CUP[0] + 260, CUP[1] - 130, 1560, -0.02]], { drift: 4 });
  const milk = ramp(t, m0 + 0.5, 2.2, 'out');
  const theta = 0.5 * t + 2.6 * (1 - Math.exp(-Math.max(0, t - m0 - 0.4) * 0.9));
  still(c, cam, t, {});
  coffee(c, cam, t, theta, { swirl: 1 + 0.6 * milk, milk });
  // the milk: a small jug comes in over the rim, pours, and goes
  const pour = ramp(t, m0 + 0.25, 0.3) * (1 - ramp(t, m0 + 2.2, 0.4)), jin = ramp(t, m0 - 0.55, 0.7, 'out') * (1 - ramp(t, m0 + 2.5, 0.8, 'in'));
  if (jin > 0.003) {
    const jx = CUP[0] + 96 + 1300 * (1 - jin), jy = CUP[1] - 70 - 200 * (1 - jin), tilt = -0.16 * pour;
    if (pour > 0.01) inSet(c, SET, cam, 1, () => {
      const lx = CUP[0] + 44 + 5 * Math.sin(t * 9), ly = CUP[1] - 40;
      c.strokeStyle = rgba([255, 250, 236], 0.95 * pour); c.lineWidth = 13; c.lineCap = 'round'; c.beginPath(); c.moveTo(jx + 2, jy + 2); c.quadraticCurveTo(jx - 26, jy + 6, lx, ly); c.stroke();
      glow(c, lx, ly, 54, [255, 250, 236], 0.9 * pour, { blend: 'source-over', mid: 0.5 });
    });
    S(c, SET, cam, 'tt_jug', jx + 14, jy + 22, 1, { r: tilt, a: 0.3, blend: 'multiply' });
    S(c, SET, cam, 'tt_jug', jx, jy, 1, { r: tilt });
    S(c, SET, cam, 'tt_hand_sh', jx + 372, jy + 34, 1, { a: 0.7 });
    S(c, SET, cam, 'tt_hand', jx + 350, jy + 4, 1, { r: 0.05 + tilt });
  }
  // sugar: one, two, three, four on the syllables; then every one of them back out again
  const from = [SUGAR[0], SUGAR[1]], fell = [], back = ramp(t, no, 1.3, 'io');
  for (let k = 0; k < 4; k++) {
    const td = CT(11, k) - 0.34, to = [CUP[0] + 60 * Math.cos(k * 1.7 + 0.4), CUP[1] + 60 * Math.sin(k * 1.7 + 0.4)];
    const u = clamp((t - td) / 0.34); if (u <= 0) continue;
    const ub = clamp(back * 1.3 - k * 0.1);                          // the rewind, last in first out
    const uu = ub > 0 ? 1 - ub : u, [x, y] = cubeAt(uu, from, to, 170);
    if (ub <= 0 && u >= 1) fell.push([td + 0.34, to[0], to[1]]);
    const sink = ub > 0 ? 0 : clamp((t - td - 0.34) / 0.5);
    S(c, SET, cam, 'tt_cube' + (k % 3), x + 10, y + 14 + 20 * Math.sin(uu * Math.PI), 1, { s: 0.85, a: 0.3 * (1 - sink), blend: 'multiply' });
    S(c, SET, cam, 'tt_cube' + (k % 3), x, y, 1, { s: 0.85 * (1 + 0.25 * Math.sin(uu * Math.PI)), r: k + 3 * uu, a: 1 - 0.85 * sink });
  }
  cupRings(c, cam, t, fell, { R: 150, life: 0.9 });
  // 完美: one gesture of the pen round each thing on the table, then round the table itself
  const circ = [[CUP[0], CUP[1], 345, CT(9, 0)], [SUGAR[0], SUGAR[1], 172, CT(9, 2)], [PHONE[0], PHONE[1], 300, CT(9, 3)], [1536, 904, 1010, CT(9, 4)]];
  inSet(c, SET, cam, 1, () => {
    const fade = 1 - ramp(t, m0 - 0.1, 0.8);
    if (fade > 0.003) for (let k = 0; k < circ.length; k++) {
      const [x, y, r, tt] = circ[k], u = ramp(t, tt - 0.05, k === 3 ? 0.85 : 0.5, 'out');
      chalk(c, circlePts(x, y, r, 64, -1.9 + k, 1.03, k === 3 ? 0.69 : 1), u, { a: 0.9 * fade, w: k === 3 ? 10 : 7, seed: k + 2 });
    }
  });
  topSteam(c, cam, t, 0.5);
  tableLamp(c, cam, t, 0.22 + 0.10 * kickN(t, 2));
  return { grade: { ...warmTable, warm: 0.32, sat: 1.06 } };
}

// V2 「手机调静音 / 让世界自己去吵」
export function phone(c, t, lt, sh) {
  const flipT = CT(20, 2) - 0.1, fl = ramp(t, flipT, 0.5, 'io');
  const cam = camK(t, [[sh.t0, PHONE[0] + 120, PHONE[1] + 60, 1500, 0.04], [flipT + 0.4, PHONE[0] + 160, PHONE[1] + 80, 1380, 0.02], [T0(21) + 1.0, 1280, 800, 1800, -0.01], [sh.t1, CUP[0] - 40, CUP[1], 1350, -0.04]], { drift: 4 });
  const buzzing = t < flipT ? 1 : 0, bz = buzzing * Math.sin(t * 150) * 5 * (0.5 + 0.5 * Math.sin(t * 9.1) ** 2);
  still(c, cam, t, { flip: fl, phoneDx: bz, phoneR: bz * 0.002 });
  // the lit screen and its pile of messages (grey bars: nothing worth reading)
  if (fl < 0.5) inSet(c, SET, cam, 1, () => {
    const sx = Math.abs(Math.cos(fl * Math.PI));
    c.save(); c.translate(PHONE[0] + bz, PHONE[1] - 26 * Math.sin(fl * Math.PI)); c.rotate(0.14); c.scale(0.62 * sx, 0.62);
    c.fillStyle = 'rgba(206,226,240,0.92)'; c.beginPath(); c.roundRect(-150, -312, 300, 624, 26); c.fill();
    const n = Math.min(7, Math.floor((t - sh.t0) / 0.42) + 1);
    for (let k = 0; k < n; k++) {
      const born = sh.t0 + k * 0.42, u = E.outBack(clamp((t - born) / 0.25)), y = 230 - (n - 1 - k) * 78;
      if (y < -290) continue;
      c.fillStyle = k % 3 === 0 ? 'rgba(90,150,170,0.95)' : 'rgba(250,250,250,0.98)'; c.beginPath(); c.roundRect(-128, y - 30 * u, 256 * (0.6 + 0.4 * hash(k)), 60 * u, 14); c.fill();
      c.fillStyle = 'rgba(60,70,90,0.45)'; c.fillRect(-112, y - 10, 150 * (0.4 + 0.6 * hash(k * 3)), 7); c.fillRect(-112, y + 6, 100 * (0.4 + 0.6 * hash(k * 5)), 7);
    }
    c.restore();
    glow(c, PHONE[0], PHONE[1], 520, [190, 220, 240], 0.30 * (1 - fl * 2));
    // it shivers on the wood
    for (let k = 0; k < 3; k++) { const u = ((t * 2.4 + k / 3) % 1); c.strokeStyle = rgba([210, 230, 240], 0.5 * (1 - u)); c.lineWidth = 4; for (const sd of [-1, 1]) { c.beginPath(); c.arc(PHONE[0], PHONE[1], 290 + 90 * u, sd > 0 ? -0.5 : Math.PI - 0.5, sd > 0 ? 0.5 : Math.PI + 0.5); c.stroke(); } }
  });
  // the hand that turns it over
  // the world goes on making its noise, but out there, and smaller, and it leaves
  inSet(c, SET, cam, 1, () => {
    for (let k = 0; k < 16; k++) {
      const born = flipT + 0.35 + k * 0.32, age = t - born; if (age < 0 || age > 3.2) continue;
      const u = age / 3.2, an = -2.6 + k * 0.83, d = 360 + 950 * E.outQuad(u), x = PHONE[0] + Math.cos(an) * d, y = PHONE[1] + Math.sin(an) * d * 0.8, sc = (1 - 0.6 * u) * 84;
      const pts = Array.from({ length: 6 }, (_, q) => [x + (q - 2.5) * sc * 0.5, y + (q % 2 ? -1 : 1) * sc * 0.5 * (0.6 + 0.4 * hash(k + q))]);
      pen(c, pts, clamp(age / 0.25), { color: rgba([232, 238, 246], 0.9 * (1 - u) * (1 - u)), w: 9 * (1 - 0.5 * u), seed: k, tremor: 3 });
    }
  });
  const quiet = ramp(t, flipT + 0.5, 3);
  coffee(c, cam, t, 0.3 * t, { swirl: 0.7 });
  // the hand that turns it over: fingertips on the phone's near edge
  const hu = ramp(t, flipT - 0.9, 0.8, 'out') * (1 - ramp(t, flipT + 0.75, 0.9, 'in'));
  if (hu > 0.003) { const hx = PHONE[0] + 112 + 760 * (1 - hu) - 40 * Math.sin(fl * Math.PI), hy = PHONE[1] + 60 + 560 * (1 - hu) - 30 * Math.sin(fl * Math.PI); S(c, SET, cam, 'tt_hand_sh', hx + 20, hy + 26, 1, { a: 0.7 }); S(c, SET, cam, 'tt_hand', hx, hy, 1, { r: -0.2 }); }
  topSteam(c, cam, t, 0.5 + 0.5 * quiet);
  tableLamp(c, cam, t, 0.22);
  return { grade: { ...warmTable, sat: lerp(0.92, 1.04, quiet) } };
}

// V2 「小勺碰杯沿的声响 / 刚刚好 盖过心跳」: each tap on the rim sends a ring out, wider than the last.
export function tap(c, t, lt, sh) {
  const taps = B.filter((b, i) => b >= T0(22) - 0.05 && b < sh.t1 + 1.5 && (b < T0(23) ? (i % 2 === 0 || b > CT(22, 4)) : true));
  const cam = camK(t, [[sh.t0, CUP[0] + 60, CUP[1] + 10, 980, 0.05], [T0(23), CUP[0] + 30, CUP[1], 1500, 0.0], [sh.t1 + 1, CUP[0], CUP[1], 2500, -0.08]], { drift: 3 });
  const ta = -0.62, tx = CUP[0] + Math.cos(ta) * (CUP_R - 8), ty = CUP[1] + Math.sin(ta) * (CUP_R - 8);
  const dt = since(t, taps), nxt = taps.find((b) => b > t), pre = nxt ? clamp(1 - (nxt - t) / 0.16) : 0;
  still(c, cam, t, { flip: 1 });
  coffee(c, cam, t, 0.2 * t, { swirl: 0.5 });
  cupRings(c, cam, t, taps.filter((b) => b <= t).map((b) => [b, CUP[0], CUP[1]]), { R: COF_R, life: 0.9, a: 0.4 });
  // before the taps there is only her own pulse in the lamplight: two beats, a rest
  const hb = (1 - ramp(t, T0(22), 2.5)) * (Math.exp(-((t * 1.15) % 1) * 9) + 0.6 * Math.exp(-((t * 1.15 + 0.78) % 1) * 9));
  inSet(c, SET, cam, 1, () => glow(c, CUP[0] + 300, CUP[1] + 240, 520, PAL.rose, 0.16 * hb));
  // the spoon, held by the handle, knocking the rim
  const lift = 0.5 + 0.5 * (1 - pre) * (1 - Math.exp(-Math.min(dt, 9) * 9));
  const hx = tx + 380, hy = ty + 250, ang = Math.atan2(hy - ty, hx - tx), kx = tx + 20 * lift * Math.cos(ang - 1.3), ky = ty + 20 * lift * Math.sin(ang - 1.3) - 16 * lift;
  S(c, SET, cam, 'tt_spoon', kx + 12, ky + 18, 1, { r: ang, sx: 0.98, a: 0.3, blend: 'multiply' });
  S(c, SET, cam, 'tt_spoon', kx, ky, 1, { r: ang, sx: 0.98 });
  S(c, SET, cam, 'tt_hand_sh', hx + 30, hy + 30, 1, { a: 0.7 });
  S(c, SET, cam, 'tt_hand', hx - 4 * lift, hy - 12 * lift, 1, { r: 0.02 });
  inSet(c, SET, cam, 1, () => {
    taps.forEach((b, k) => { ring(c, tx, ty, t - b, { R: 520 + 150 * k, life: 2.3, col: k % 2 ? PAL.warm : PAL.cream, a: 0.75, w: 5, rings: 3, blend: 'screen', seed: k + 1, rot: k }); });
    glow(c, tx, ty, 90, PAL.warm, 0.9 * Math.exp(-dt * 7));
  });
  tableLamp(c, cam, t, 0.22);
  return { grade: { ...warmTable, sat: 1.04 } };
}

// CH3 「糖多一点 还是不加也无所谓」: the cubes never land. They go round her cup like small moons.
export function orbit(c, t, lt, sh) {
  const go = CT(40, 7), calm = CT(40, 10);
  const cam = camK(t, [[sh.t0, CUP[0], CUP[1], 1500, 0.2], [sh.t1, CUP[0], CUP[1], 1750, -0.25]], { ease: 'lin', drift: 3 });
  still(c, cam, t, { phone: false });
  coffee(c, cam, t, 1.3 * t, { swirl: 1.4, milk: 0.75 });
  const away = ramp(t, go, 1.1, 'in');
  inSet(c, SET, cam, 1, () => {
    for (let k = 0; k < 2; k++) chalk(c, circlePts(CUP[0], CUP[1], 420 + 130 * k, 72, k * 2 + t * (k ? -0.3 : 0.4), 1), ramp(t, sh.t0 + 0.1 + 0.25 * k, 0.7, 'out'), { a: 0.6 * (1 - away), w: 5, seed: 5 + k });
    ring(c, CUP[0], CUP[1], t - calm, { R: 900, life: 2.2, col: PAL.warm, a: 0.8, w: 6, blend: 'screen', seed: 9 });
  });
  for (let k = 0; k < 7; k++) {
    const inn = E.outBack(clamp((t - sh.t0 - 0.06 * k) / 0.45)), rad = (k % 2 ? 550 : 420) * inn + 1500 * away * (0.7 + 0.6 * hash(k)), an = k * TAU / 7 + (k % 2 ? -1.5 : 2.0) * (t - sh.t0);
    const x = CUP[0] + Math.cos(an) * rad, y = CUP[1] + Math.sin(an) * rad;
    S(c, SET, cam, 'tt_cube' + (k % 3), x + 14, y + 20, 1, { s: 0.85, a: 0.3, blend: 'multiply' });
    S(c, SET, cam, 'tt_cube' + (k % 3), x, y, 1, { s: 0.85 + 0.06 * kickN(t, 1), r: an * 1.5 + k });
  }
  topSteam(c, cam, t, 0.6);
  tableLamp(c, cam, t, 0.28 + 0.1 * kickN(t, 1));
  return { grade: { warm: 0.4, bloom: 0.8, vig: 0.5, sat: 1.1 } };
}

// OUTRO: the table after she has gone. An empty cup is also a circle.
export function after(c, t, lt, sh) {
  // the cup ends exactly where the ring on the end card will be, so the last cut is one circle becoming another
  const cam = camK(t, [[sh.t0, 1500, 880, 2500, -0.10], [sh.t1 + 0.6, CUP[0], CUP[1] + 35, 620, 0.06]], { drift: 3 });
  still(c, cam, t, { phone: false, cupEmpty: true });
  S(c, SET, cam, 'tt_spoon', CUP[0] - 120, CUP[1] + 262, 1, { r: 0.12, s: 0.82, a: 0.3, blend: 'multiply' });
  S(c, SET, cam, 'tt_spoon', CUP[0] - 130, CUP[1] + 250, 1, { r: 0.12, s: 0.82 });
  inSet(c, SET, cam, 1, () => {
    // outside, a car goes by: its light crosses the table once, and the china answers
    const u = (t - sh.t0 - 2.2) / 2.6;
    if (u > 0 && u < 1) { const x = lerp(-600, 3600, u), g = c.createLinearGradient(x, 0, x + 520, 0); g.addColorStop(0, 'rgba(255,240,206,0)'); g.addColorStop(0.5, `rgba(255,240,206,${0.30 * Math.sin(u * Math.PI)})`); g.addColorStop(1, 'rgba(255,240,206,0)'); c.save(); c.globalCompositeOperation = 'screen'; c.fillStyle = g; c.transform(1, 0, -0.4, 1, 0, 0); c.fillRect(x, -200, 520, 2400); c.restore(); glow(c, CUP[0] - 60, CUP[1] - 70, 150, [255, 250, 236], 0.5 * Math.sin(u * Math.PI)); }
    // and the last warmth leaves the cup
    for (let k = 0; k < 3; k++) { const v = (t - sh.t0 - 0.2 - k * 0.9) / 3.4; if (v > 0 && v < 1) glow(c, CUP[0] - 90 * v + 40 * Math.sin(k * 2 + v * 3), CUP[1] - 120 * v, 110 + 260 * v, [255, 250, 240], 0.16 * Math.sin(v * Math.PI) * (1 - k * 0.25), { mid: 0.5 }); }
  });
  tableLamp(c, cam, t, 0.30 + 0.05 * kickN(t, 4, 0, 3));          // evening: the window's light has gone, the lamp's stays
  return { grade: { warm: 0.3, bloom: 0.7, vig: 0.62, sat: 0.96, gain: lerp(1, 0.92, ramp(t, sh.t0, sh.len)) } };
}

// END CARD: the ring the cup left, on the paper itself.
export function card(c, t, lt, sh) {
  c.fillStyle = '#f6efe2'; c.fillRect(0, 0, W, H);
  const m = MAN.tt_ring, cx = W / 2, cy = 432, a = ramp(t, sh.t0, 1.0), sc = 1.55 * (1 + 0.035 * ramp(t, sh.t0, sh.len, 'out'));
  c.save(); c.globalCompositeOperation = 'multiply'; c.globalAlpha = a; c.translate(cx, cy); c.rotate(-0.3 + 0.03 * ramp(t, sh.t0, sh.len, 'lin')); c.scale(sc, sc); c.drawImage(IM.tt_ring, m.ox - m.ax, m.oy - m.ay); c.restore();
  // a few drops shaken off the saucer, one to a bar
  for (let k = 0; k < 7; k++) { const tb = beatNear(sh.t0 + 1.2, k * 2), u = clamp((t - tb) / 0.5); if (u <= 0) continue; const an = 0.5 + k * 0.9, d = 330 + 90 * hash(k * 3), x = cx + Math.cos(an) * d, y = cy + Math.sin(an) * d * 0.9, r = (5 + 9 * hash(k)) * E.outBack(u); c.fillStyle = `rgba(112,72,48,${0.5 * u})`; c.beginPath(); c.ellipse(x, y, r, r * 0.92, an, 0, TAU); c.fill(); c.strokeStyle = `rgba(92,56,36,${0.5 * u})`; c.lineWidth = 1.6; c.stroke(); }
  c.save(); c.textAlign = 'center'; c.textBaseline = 'middle';
  const l1 = [...'一个人'], l2 = [...'也很完美'], st = sh.t0 + 1.0;
  c.font = '400 54px "LXGW WenKai"'; c.fillStyle = 'rgb(110,74,52)';
  l1.forEach((ch, k) => { c.globalAlpha = ramp(t, st + k * 0.22, 0.4, 'out'); c.fillText(ch, cx + (k - 1) * 60, cy - 38); });
  l2.forEach((ch, k) => { c.globalAlpha = ramp(t, st + 0.9 + k * 0.22, 0.4, 'out'); c.fillText(ch, cx + (k - 1.5) * 60, cy + 38); });
  const chars = [...'独身主义的咖啡'], size = 88, gap = 26, tw = chars.length * size + (chars.length - 1) * gap;
  c.font = `600 ${size}px "Noto Serif SC"`;
  chars.forEach((ch, k) => { const u = ramp(t, st + 2.4 + k * 0.14, 0.7, 'out'); c.globalAlpha = u; c.fillStyle = k >= 5 ? 'rgb(150,78,40)' : 'rgb(62,44,38)'; c.fillText(ch, W / 2 - tw / 2 + size / 2 + k * (size + gap), 812 + 10 * (1 - u)); });
  c.globalAlpha = ramp(t, st + 4.2, 1.0); c.font = '400 40px "Noto Serif SC"'; c.fillStyle = 'rgb(108,88,76)'; c.fillText('词 曲   Chan Meng', W / 2, 908);
  c.globalAlpha = ramp(t, st + 4.9, 1.0); c.font = 'italic 400 36px "Cormorant Garamond"'; c.fillText('every frame drawn in code', W / 2, 964);
  c.restore();
  return { grade: { warm: 0.1, bloom: 0, vig: 0.5 } };
}

// V1 「只坐得下一个人」: the whole table from above. One cup, one saucer, one spoon; the chalk goes once round the rim.
export function oneSeat(c, t, lt, sh) {
  const cam = camK(t, [[sh.t0, 1536, 900, 2250, 0.10], [sh.t1 + 0.5, 1536, 884, 2760, -0.02]], { ease: 'out', drift: 3 });
  still(c, cam, t, {});
  coffee(c, cam, t, 0.35 * t, { swirl: 0.8 });
  inSet(c, SET, cam, 1, () => chalk(c, circlePts(1536, 904, 1030, 80, 2.2, 1.03, 0.69), ramp(t, CT(5, 4) - 0.25, 1.5, 'io'), { a: 0.9, w: 11, seed: 4 }));
  topSteam(c, cam, t, 0.9);
  tableLamp(c, cam, t, 0.22 + 0.06 * kickN(t, 2));
  return { grade: { ...warmTable } };
}
