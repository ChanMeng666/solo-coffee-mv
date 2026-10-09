// 独身主义的咖啡: the cut. Each row of EDIT is one shot; a shot is a function that paints a frame into a 2D canvas and
// says how the glass, the grade and the lyric should treat it. The WebGL pass in post.js joins the shots.
import { boot, makeCanvas, loadImage, srt } from '/lib/mv.js';
import { W, H, MAN, IM, PAL, rgba, clamp, lerp, sstep, E, hash } from './stage.js';
import { TM, DUR, FPS, B, T0, CT, beatNear } from './core.js';
import { makePost } from './post.js';
import { EDIT } from './edit.js';
import { drawLyric, drawTitles } from './type.js';

const view = document.getElementById('c');
const [cvA, cxA] = makeCanvas(W, H), [cvB, cxB] = makeCanvas(W, H), [cvT, cxT] = makeCanvas(W, H);
const post = makePost(view, W, H, await loadImage('./art/paper.webp'));
window.srt = () => srt(TM);

// rows sorted by time; a row lasts until the next one starts
EDIT.sort((a, b) => a.t0 - b.t0);
EDIT.forEach((s, i) => { s.t1 = i + 1 < EDIT.length ? EDIT[i + 1].t0 : DUR; s.len = s.t1 - s.t0; s.tr = s.tr || { type: 0, dur: 0 }; });
const only = new URLSearchParams(location.search).get('shot');

function paint(cx, sh, t) {
  cx.setTransform(1, 0, 0, 1, 0, 0); cx.globalAlpha = 1; cx.globalCompositeOperation = 'source-over'; cx.filter = 'none';
  cx.fillStyle = '#f8f2e7'; cx.fillRect(0, 0, W, H);
  return sh.shot(cx, t, t - sh.t0, sh) || {};
}

boot({ width: W, height: H, fps: FPS, duration: DUR, render(t) {
  let i = 0; while (i < EDIT.length - 1 && EDIT[i + 1].t0 <= t) i++;
  if (only) i = EDIT.findIndex((s) => s.id === only);
  const cur = EDIT[i], tr = cur.tr, inTr = !only && i > 0 && tr.dur > 0 && t < cur.t0 + tr.dur;
  const f = { t, frame: Math.round(t * FPS), text: cvT };
  if (inTr) {
    const prev = EDIT[i - 1], u = (t - cur.t0) / tr.dur;
    f.a = { cv: cvA, ...paint(cxA, prev, t) }; f.b = { cv: cvB, ...paint(cxB, cur, t) };
    f.mix = tr.ease === 'lin' ? u : tr.ease === 'out' ? E.outCubic(u) : tr.ease === 'in' ? E.inQuad(u) : u * u * (3 - 2 * u);
    f.type = tr.type; f.ctr = tr.ctr;
  } else f.a = { cv: cvA, ...paint(cxA, cur, t) };
  // the lyric and the title live on their own layer, above the glass and the grade, under the paper
  cxT.setTransform(1, 0, 0, 1, 0, 0); cxT.globalAlpha = 1; cxT.globalCompositeOperation = 'source-over'; cxT.clearRect(0, 0, W, H);
  drawTitles(cxT, t);
  drawLyric(cxT, t, (inTr && f.mix > 0.5 ? f.b : f.a).lyric);
  // in from paper, out to the dark
  f.fade = Math.max(1 - sstep(0, 1.4, t), sstep(DUR - 3.2, DUR - 0.4, t));
  f.fadeCol = t < 5 ? [0.972, 0.950, 0.906] : [0.07, 0.05, 0.05];
  post(f);
} });
