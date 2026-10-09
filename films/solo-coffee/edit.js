// The edit decision list: when each shot starts and how the previous one turns into it.
// Transition types (post.js): 0 cut, 1 dissolve, 2 bloom from a point, 3 brush across, 4 iris open, 5 run, 6 iris close.
import { TM, DUR, B, T0, CT, beatNear as b } from './core.js';
import * as TB from './shots_table.js';
import * as T2 from './shots_table2.js';
import * as WN from './shots_window.js';
import * as RM from './shots_room.js';
import * as OUT from './shots_out.js';

export const EDIT = [
  // intro
  { id: 'open', t0: 0, shot: OUT.open },
  // verse 1
  { id: 'drops', t0: b(10.0), shot: WN.drops, tr: { type: 2, dur: 1.0, ctr: [0.5, 0.5] } },
  { id: 'stir', t0: b(19.6), shot: TB.stir, tr: { type: 4, dur: 0.7, ctr: [0.5, 0.5] } },
  { id: 'corner', t0: b(30.6), shot: RM.corner, tr: { type: 3, dur: 0.9 } },
  { id: 'oneSeat', t0: T0(5) - 0.1, shot: T2.oneSeat },
  { id: 'corner2', t0: b(39.4), shot: RM.corner },
  { id: 'coatPOV', t0: T0(6) - 0.12, shot: RM.coatPOV },
  // chorus 1: the pleasures, indoors
  { id: 'hero', t0: T0(8) - 1.9, shot: RM.hero, tr: { type: 2, dur: 1.5, ctr: [0.8, 0.85] } },
  { id: 'chorusTable', t0: T0(9) - 0.1, shot: T2.chorusTable },
  { id: 'sip', t0: T0(12) - 0.12, shot: RM.sip },
  { id: 'toast', t0: CT(13, 5) - 0.1, shot: WN.toast, tr: { type: 5, dur: 2.4 } },
  // verse 2
  { id: 'heart', t0: T0(16) - 0.7, shot: WN.heart, tr: { type: 1, dur: 0.9 } },
  { id: 'phone', t0: b(108.2), shot: T2.phone, tr: { type: 3, dur: 0.8 } },
  { id: 'tap', t0: b(118.7), shot: T2.tap },
  // chorus 2: outside, at night
  { id: 'umbrellas', t0: b(129.2), shot: OUT.umbrellas, tr: { type: 4, dur: 0.8, ctr: [0.5, 0.5] } },
  { id: 'nightStreet', t0: T0(26) - 0.1, shot: OUT.nightStreet, tr: { type: 3, dur: 0.6 } },
  { id: 'sipNight', t0: T0(28) - 0.1, shot: RM.sipNight },
  { id: 'meltOut', t0: T0(29) - 0.1, shot: OUT.meltOut, tr: { type: 1, dur: 0.7 } },
  { id: 'emptyCross', t0: T0(30) - 0.15, shot: OUT.emptyCross, tr: { type: 2, dur: 0.8, ctr: [0.5, 0.5] } },
  // bridge: the grey of other people's questions, then the colour back
  { id: 'bridgeChair', t0: 162.4, shot: RM.bridgeChair, tr: { type: 5, dur: 2.2 } },
  { id: 'sipWarm', t0: T0(34) - 0.1, shot: RM.sipWarm },
  { id: 'iHave', t0: T0(35) - 0.1, shot: RM.iHave, tr: { type: 1, dur: 0.6 } },
  { id: 'wholeShop', t0: T0(37) - 0.35, shot: RM.wholeShop, tr: { type: 2, dur: 1.0, ctr: [0.72, 0.6] } },
  // chorus 3: the whole shop is hers
  { id: 'shopDetail', t0: T0(39) - 0.1, shot: RM.shopDetail },
  { id: 'orbit', t0: T0(40) - 0.1, shot: T2.orbit },
  { id: 'lastSip', t0: T0(41) - 0.1, shot: RM.lastSip },
  { id: 'heartDone', t0: T0(42) - 0.25, shot: WN.heartDone, tr: { type: 1, dur: 0.5 } },
  { id: 'leave', t0: T0(43) - 0.1, shot: RM.leave, tr: { type: 2, dur: 0.8, ctr: [0.5, 0.45] } },
  { id: 'bareChair', t0: T0(43) + 1.95, shot: RM.bareChair },
  // outro
  { id: 'exit', t0: T0(44) - 0.15, shot: OUT.exit, tr: { type: 3, dur: 0.7 } },
  { id: 'after', t0: b(230.6), shot: T2.after, tr: { type: 1, dur: 1.4 } },
  { id: 'card', t0: b(239.4), shot: T2.card, tr: { type: 6, dur: 1.3, ctr: [0.5, 0.4] } },
];
