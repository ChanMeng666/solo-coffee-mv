// Lettering: the lyric on its stroke of coffee, the title, the end card.
import { W, H, MAN, IM, PAL, rgba, clamp, lerp, sstep, E, hash, noise1 } from './stage.js';
import { TM, DUR, T0 } from './core.js';

const LEAD = 0.45, TAIL = 0.6;
// o (from the shot): { y, dark } — lift the line off the bottom, or use ink on a pale strip for dark-poor frames
export function drawLyric(c, t, o = {}) {
  let l = null;
  for (const x of TM.lines) if (t >= x.t0 - LEAD && t < x.t1 + TAIL) l = x;
  if (!l) return;
  const nxt = TM.lines[l.i + 1], end = Math.min(l.t1 + TAIL, nxt ? Math.max(nxt.t0 - LEAD, l.t1 - 0.05) : 1e9);
  const a = Math.min(sstep(l.t0 - LEAD, l.t0 - LEAD + 0.35, t), 1 - sstep(end - 0.3, end, t));
  if (a <= 0.003) return;
  const size = 52, y = o.y ?? H - 104, chars = [...l.text];
  c.save();
  c.font = `400 ${size}px "LXGW WenKai"`; c.textBaseline = 'middle'; c.textAlign = 'left';
  const adv = chars.map((ch) => (ch === ' ' ? size * 0.5 : c.measureText(ch).width + size * 0.08));
  const tw = adv.reduce((s, v) => s + v, 0), bw = tw + 230, bh = 118;
  // the stroke is brushed in from the left just before the line is sung
  const wipe = sstep(l.t0 - LEAD, l.t0 - LEAD + 0.5, t);
  c.save(); c.beginPath(); c.rect(W / 2 - bw / 2, y - 90, bw * wipe, 180); c.clip();
  c.globalAlpha = a * 0.90; c.drawImage(IM.ly_band, W / 2 - bw / 2, y - bh / 2 + 2, bw, bh);
  c.restore();
  let x = W / 2 - tw / 2;
  for (let k = 0; k < chars.length; k++) {
    if (chars[k] !== ' ') {
      const u = sstep(l.ct[k] - 0.08, l.ct[k] + 0.2, t), pop = Math.sin(clamp((t - l.ct[k] + 0.08) / 0.45) * Math.PI);
      c.globalAlpha = a * lerp(0.38, 1, u) * sstep(0, 0.15, wipe - (x - (W / 2 - bw / 2)) / bw + 0.1);
      c.fillStyle = u > 0.02 ? rgba([255, 247, 228]) : rgba([226, 208, 184]);
      c.fillText(chars[k], x, y + 2 - 5 * pop);
    }
    x += adv[k];
  }
  c.restore();
}

export function drawTitles(c, t) {
  // opening: the name of the song, lettered into the wet sky
  const a = Math.min(sstep(1.0, 2.4, t), 1 - sstep(5.2, 6.6, t));
  if (a > 0.003) {
    c.save();
    // a darker passage of sky behind the lettering, so the roofs do not argue with it
    { const g = c.createRadialGradient(760, 190, 60, 760, 190, 900); g.addColorStop(0, `rgba(16,20,40,${0.62 * a})`); g.addColorStop(1, 'rgba(16,20,40,0)'); c.save(); c.scale(1, 0.42); c.fillStyle = g; c.fillRect(-200, -400, 2200, 1700); c.restore(); }
    const chars = [...'独身主义的咖啡'], size = 118, gap = 30;
    c.font = `600 ${size}px "Noto Serif SC"`; c.textBaseline = 'middle'; c.textAlign = 'center';
    const tw = chars.length * size + (chars.length - 1) * gap; let x = 250 + size / 2;
    for (let k = 0; k < chars.length; k++) {
      const u = sstep(1.0 + k * 0.14, 1.8 + k * 0.14, t);
      c.globalAlpha = a * u; c.shadowColor = 'rgba(20,24,44,0.55)'; c.shadowBlur = 26;
      c.fillStyle = k >= 5 ? rgba([255, 214, 150]) : rgba([252, 244, 226]);
      c.fillText(chars[k], x, 132 + 14 * (1 - u)); x += size + gap;
    }
    c.shadowBlur = 14; c.globalAlpha = a * sstep(2.4, 3.4, t);
    c.font = 'italic 500 50px "Cormorant Garamond"'; c.textAlign = 'left'; c.fillStyle = rgba([250, 240, 220]); c.shadowColor = 'rgba(10,14,30,0.9)'; c.shadowBlur = 12;
    c.fillText('A Coffee for One', 256, 228);
    c.font = '400 34px "Noto Serif SC"'; c.fillStyle = rgba([240, 230, 212]);
    c.fillText('词 曲   Chan Meng', 258, 288);
    c.restore();
  }
}
