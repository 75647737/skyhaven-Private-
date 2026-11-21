// Skyhaven character rig: every character is built from the same parts and a fixed spec,
// so they render identically in every scene and episode. draw(spec, opts) returns an SVG <g> string
// with the feet at (0,0). opts: {mouth:'smile'|'open'|'o', blink:0..1, armL:deg, armR:deg, look:-1..1}
const INK = '#2b2420';
const C = (s, k, d) => (s[k] !== undefined ? s[k] : d);

function draw(s, o = {}) {
  const H = s.height, kid = s.age === 'kid' || s.age === 'little';
  const r = H * (s.age === 'little' ? 0.2 : kid ? 0.17 : 0.125);       // head radius
  const hy = -H + r;                                                   // head centre y
  const sh = -H + 2 * r + r * 0.18;                                    // shoulder line
  const hip = sh + (H - 2 * r) * (kid ? 0.42 : 0.44);
  const tw = r * (s.build === 'broad' ? 2.5 : s.build === 'slim' ? 1.9 : 2.2);   // torso width
  const lw = r * (kid ? 0.5 : 0.46), aw = r * (kid ? 0.42 : 0.4);
  const skin = s.skin, sw = 4;
  const p = [];
  const look = C(o, 'look', 0) * r * 0.08;
  // ---- legs + shoes
  const legTop = hip - 6, legBot = -r * 0.32;
  if (s.dress) {
    p.push(`<rect x="${-tw * 0.28 - lw / 2}" y="${legTop}" width="${lw}" height="${legBot - legTop}" rx="${lw / 2}" fill="${skin}" stroke="${INK}" stroke-width="${sw}"/>`);
    p.push(`<rect x="${tw * 0.28 - lw / 2}" y="${legTop}" width="${lw}" height="${legBot - legTop}" rx="${lw / 2}" fill="${skin}" stroke="${INK}" stroke-width="${sw}"/>`);
  } else {
    for (const sx of [-1, 1]) p.push(`<rect x="${sx * tw * 0.24 - lw / 2 - (sx < 0 ? 2 : -2)}" y="${legTop}" width="${lw + 4}" height="${legBot - legTop + 4}" rx="${lw / 3}" fill="${s.pants}" stroke="${INK}" stroke-width="${sw}"/>`);
  }
  for (const sx of [-1, 1]) p.push(`<path d="M${sx * tw * 0.24 - lw * 0.7},${-2} q0,-${r * 0.36} ${lw * 0.7},-${r * 0.36} h${lw * 0.2} q${lw * 0.8},0 ${lw * 0.8},${r * 0.36} z" fill="${s.shoes}" stroke="${INK}" stroke-width="${sw}" stroke-linejoin="round"/>`);
  // ---- arms (behind torso), rotated at the shoulder
  const armLen = (hip - sh) * 1.0 + r * 0.25;
  const arm = (side, deg) => {
    const x = side * (tw / 2 - aw * 0.25);
    return `<g transform="translate(${x},${sh + aw * 0.5}) rotate(${deg})">
      <rect x="${-aw / 2}" y="${-aw / 2}" width="${aw}" height="${armLen}" rx="${aw / 2}" fill="${s.sleeves || s.top}" stroke="${INK}" stroke-width="${sw}"/>
      <circle cx="0" cy="${armLen - aw * 0.1}" r="${aw * 0.62}" fill="${skin}" stroke="${INK}" stroke-width="${sw}"/>
      ${side > 0 && s.hold ? s.hold(armLen, aw) : ''}${side < 0 && s.holdL ? s.holdL(armLen, aw) : ''}</g>`;
  };
  p.push(arm(-1, C(o, 'armL', 8)));
  p.push(arm(1, C(o, 'armR', -8)));
  // ---- torso
  if (s.dress) {
    p.push(`<path d="M${-tw / 2},${sh + r * 0.2} q0,-${r * 0.22} ${r * 0.25},-${r * 0.22} h${tw - r * 0.5} q${r * 0.25},0 ${r * 0.25},${r * 0.22} L${tw / 2 + r * 0.45},${legTop + (legBot - legTop) * 0.42} q0,${r * 0.12} -${r * 0.15},${r * 0.12} H${-tw / 2 - r * 0.3} q-${r * 0.15},0 -${r * 0.15},-${r * 0.12} Z" fill="${s.top}" stroke="${INK}" stroke-width="${sw}" stroke-linejoin="round"/>`);
    if (s.belt) p.push(`<rect x="${-tw / 2 - 2}" y="${hip - r * 0.32}" width="${tw + 4}" height="${r * 0.18}" fill="${s.belt}" stroke="${INK}" stroke-width="3"/>`);
  } else {
    p.push(`<rect x="${-tw / 2}" y="${sh - r * 0.02}" width="${tw}" height="${hip - sh + r * 0.18}" rx="${r * 0.32}" fill="${s.top}" stroke="${INK}" stroke-width="${sw}"/>`);
  }
  if (s.jacket) { // open jacket over shirt + optional tie
    p.push(`<path d="M${-tw * 0.12},${sh} L0,${sh + r * 0.75} L${tw * 0.12},${sh} Z" fill="${s.shirt || '#fff'}" stroke="${INK}" stroke-width="3" stroke-linejoin="round"/>`);
    if (s.tie) p.push(`<path d="M0,${sh + r * 0.08} l${r * 0.1},${r * 0.12} l-${r * 0.06},${r * 0.62} l-${r * 0.04},${r * 0.1} l-${r * 0.04},-${r * 0.1} l-${r * 0.06},-${r * 0.62} z" fill="${s.tie}" stroke="${INK}" stroke-width="3" stroke-linejoin="round"/>`);
    p.push(`<line x1="0" y1="${sh + r * 0.75}" x2="0" y2="${hip + r * 0.1}" stroke="${INK}" stroke-width="3"/>`);
    p.push(`<circle cx="${-r * 0.12}" cy="${sh + r * 1.05}" r="${r * 0.06}" fill="${INK}"/>`);
  }
  if (s.apron) p.push(`<path d="M${-tw * 0.32},${sh + r * 0.45} h${tw * 0.64} v${hip - sh + r * 0.6} q0,${r * 0.15} -${r * 0.15},${r * 0.15} h-${tw * 0.64 - r * 0.3} q-${r * 0.15},0 -${r * 0.15},-${r * 0.15} z" fill="${s.apron}" stroke="${INK}" stroke-width="3"/><rect x="${-tw * 0.12}" y="${hip - r * 0.05}" width="${tw * 0.24}" height="${r * 0.28}" rx="5" fill="none" stroke="${INK}" stroke-width="3"/>`);
  if (s.necklace) for (let i = 0; i < 9; i++) { const a = Math.PI * (0.15 + 0.7 * i / 8); p.push(`<circle cx="${Math.cos(a) * r * 0.42}" cy="${sh + Math.sin(a) * r * 0.32 - r * 0.02}" r="${r * 0.055}" fill="#f6f1e6" stroke="${INK}" stroke-width="1.5"/>`); }
  if (s.badge) p.push(`<rect x="${tw * 0.12}" y="${sh + r * 0.45}" width="${r * 0.4}" height="${r * 0.22}" rx="3" fill="${s.badge}" stroke="${INK}" stroke-width="2.5"/>`);
  if (s.collar) p.push(`<path d="M${-r * 0.42},${sh - r * 0.02} L0,${sh + r * 0.3} L${r * 0.42},${sh - r * 0.02}" fill="none" stroke="${INK}" stroke-width="3.5" stroke-linejoin="round"/>`);
  // ---- neck + head
  p.push(`<rect x="${-r * 0.26}" y="${hy + r * 0.75}" width="${r * 0.52}" height="${r * 0.5}" fill="${skin}" stroke="${INK}" stroke-width="${sw}"/>`);
  if (s.hairBack) p.push(s.hairBack(r, hy));
  for (const sx of [-1, 1]) p.push(`<ellipse cx="${sx * r * 0.98}" cy="${hy + r * 0.08}" rx="${r * 0.18}" ry="${r * 0.24}" fill="${skin}" stroke="${INK}" stroke-width="${sw}"/>`);
  p.push(`<ellipse cx="0" cy="${hy}" rx="${r}" ry="${r * 1.04}" fill="${skin}" stroke="${INK}" stroke-width="${sw}"/>`);
  // face
  const ey = hy + r * 0.05, ex = r * 0.38, er = r * (kid ? 0.2 : 0.16);
  const bl = C(o, 'blink', 0);
  for (const sx of [-1, 1]) {
    if (bl > 0.5) p.push(`<path d="M${sx * ex - er},${ey} q${er},${er * 0.7} ${er * 2},0" fill="none" stroke="${INK}" stroke-width="4" stroke-linecap="round"/>`);
    else { p.push(`<ellipse cx="${sx * ex}" cy="${ey}" rx="${er}" ry="${er * 1.15}" fill="#fff" stroke="${INK}" stroke-width="3"/>`);
      p.push(`<circle cx="${sx * ex + look}" cy="${ey + er * 0.1}" r="${er * 0.6}" fill="${s.eyes || '#3b2a20'}"/><circle cx="${sx * ex + look + er * 0.2}" cy="${ey - er * 0.15}" r="${er * 0.18}" fill="#fff"/>`); }
    const bt = s.brow || 'flat', by = ey - er * 1.7;
    p.push(`<path d="M${sx * ex - er * 1.05},${by + (bt === 'raised' ? 2 : 0)} q${sx * 0 + er},${bt === 'stern' ? (sx > 0 ? 3 : 3) : -er * 0.5} ${er * 2.1},${bt === 'stern' ? -2 : 0}" fill="none" stroke="${s.browColor || INK}" stroke-width="${r * 0.08}" stroke-linecap="round"/>`);
  }
  if (s.glasses) p.push(`<g fill="none" stroke="${s.glasses}" stroke-width="4"><circle cx="${-ex}" cy="${ey}" r="${er * 1.6}"/><circle cx="${ex}" cy="${ey}" r="${er * 1.6}"/><line x1="${-ex + er * 1.6}" y1="${ey}" x2="${ex - er * 1.6}" y2="${ey}"/></g>`);
  p.push(`<path d="M${-r * 0.05},${hy + r * 0.2} q${r * 0.12},${r * 0.2} 0,${r * 0.28}" fill="none" stroke="${INK}" stroke-width="3" stroke-linecap="round"/>`);
  for (const sx of [-1, 1]) p.push(`<ellipse cx="${sx * r * 0.58}" cy="${hy + r * 0.42}" rx="${r * 0.15}" ry="${r * 0.09}" fill="${s.blush || '#e8897c'}" opacity=".45"/>`);
  const my = hy + r * 0.62, mw = r * (kid ? 0.34 : 0.3), m = C(o, 'mouth', s.mouth || 'smile');
  if (m === 'open') p.push(`<path d="M${-mw},${my - r * 0.04} q${mw},${r * 0.42} ${mw * 2},0 z" fill="#7a2c2c" stroke="${INK}" stroke-width="3" stroke-linejoin="round"/><path d="M${-mw * 0.6},${my + r * 0.12} q${mw * 0.6},${r * 0.12} ${mw * 1.2},0" fill="#e57a7a"/>`);
  else if (m === 'o') p.push(`<ellipse cx="0" cy="${my + r * 0.06}" rx="${r * 0.11}" ry="${r * 0.14}" fill="#7a2c2c" stroke="${INK}" stroke-width="3"/>`);
  else if (m === 'grin') p.push(`<path d="M${-mw},${my - r * 0.02} q${mw},${r * 0.3} ${mw * 2},0 z" fill="#fff" stroke="${INK}" stroke-width="3" stroke-linejoin="round"/>`);
  else p.push(`<path d="M${-mw},${my} q${mw},${r * 0.26} ${mw * 2},0" fill="none" stroke="${INK}" stroke-width="4" stroke-linecap="round"/>`);
  if (s.beard) p.push(s.beard(r, hy));
  if (s.hair) p.push(s.hair(r, hy));
  if (s.hat) p.push(s.hat(r, hy));
  return `<g>${p.join('')}</g>`;
}

// ---------- hair & hats (r = head radius, y = head centre)
const HAIR = {
  sidePart: (c) => (r, y) => `<path d="M${-r * 1.02},${y - r * 0.05} C${-r * 1.1},${y - r * 1.25} ${r * 0.9},${y - r * 1.45} ${r * 1.04},${y - r * 0.2} C${r * 0.9},${y - r * 0.7} ${r * 0.2},${y - r * 0.62} ${-r * 0.35},${y - r * 0.78} C${-r * 0.6},${y - r * 0.5} ${-r * 0.85},${y - r * 0.45} ${-r * 1.02},${y - r * 0.05} Z" fill="${c}" stroke="${INK}" stroke-width="4" stroke-linejoin="round"/>`,
  longWaves: (c) => (r, y) => `<path d="M${-r * 1.05},${y + r * 0.2} C${-r * 1.25},${y - r * 1.4} ${r * 1.25},${y - r * 1.4} ${r * 1.05},${y + r * 0.2} C${r * 0.95},${y - r * 0.55} ${r * 0.1},${y - r * 0.85} ${-r * 0.2},${y - r * 0.6} C${-r * 0.55},${y - r * 0.4} ${-r * 0.95},${y - r * 0.4} ${-r * 1.05},${y + r * 0.2} Z" fill="${c}" stroke="${INK}" stroke-width="4" stroke-linejoin="round"/>`,
  longBack: (c) => (r, y) => `<path d="M${-r * 1.05},${y} C${-r * 1.35},${y + r * 1.2} ${-r * 1.2},${y + r * 2.0} ${-r * 0.7},${y + r * 2.2} L${r * 0.7},${y + r * 2.2} C${r * 1.2},${y + r * 2.0} ${r * 1.35},${y + r * 1.2} ${r * 1.05},${y} Z" fill="${c}" stroke="${INK}" stroke-width="4" stroke-linejoin="round"/>`,
  messy: (c) => (r, y) => `<path d="M${-r * 1.02},${y - r * 0.1} L${-r * 1.08},${y - r * 0.7} L${-r * 0.75},${y - r * 0.85} L${-r * 0.7},${y - r * 1.2} L${-r * 0.3},${y - r * 1.02} L${-r * 0.05},${y - r * 1.3} L${r * 0.25},${y - r * 1.05} L${r * 0.65},${y - r * 1.2} L${r * 0.75},${y - r * 0.82} L${r * 1.1},${y - r * 0.68} L${r * 1.02},${y - r * 0.1} C${r * 0.7},${y - r * 0.55} ${-r * 0.7},${y - r * 0.55} ${-r * 1.02},${y - r * 0.1} Z" fill="${c}" stroke="${INK}" stroke-width="4" stroke-linejoin="round"/>`,
  pigtails: (c, bow) => (r, y) => `${[-1, 1].map(sx => `<ellipse cx="${sx * r * 1.25}" cy="${y + r * 0.1}" rx="${r * 0.35}" ry="${r * 0.55}" fill="${c}" stroke="${INK}" stroke-width="4"/><circle cx="${sx * r * 1.05}" cy="${y - r * 0.35}" r="${r * 0.16}" fill="${bow}" stroke="${INK}" stroke-width="3"/>`).join('')}<path d="M${-r * 1.02},${y - r * 0.05} C${-r * 1.1},${y - r * 1.35} ${r * 1.1},${y - r * 1.35} ${r * 1.02},${y - r * 0.05} C${r * 0.6},${y - r * 0.6} ${-r * 0.6},${y - r * 0.6} ${-r * 1.02},${y - r * 0.05} Z" fill="${c}" stroke="${INK}" stroke-width="4" stroke-linejoin="round"/>`,
  bun: (c) => (r, y) => `<circle cx="0" cy="${y - r * 1.15}" r="${r * 0.42}" fill="${c}" stroke="${INK}" stroke-width="4"/><path d="M${-r * 1.02},${y - r * 0.05} C${-r * 1.1},${y - r * 1.3} ${r * 1.1},${y - r * 1.3} ${r * 1.02},${y - r * 0.05} C${r * 0.75},${y - r * 0.62} ${-r * 0.75},${y - r * 0.62} ${-r * 1.02},${y - r * 0.05} Z" fill="${c}" stroke="${INK}" stroke-width="4" stroke-linejoin="round"/>`,
  ponytail: (c) => (r, y) => `<path d="M${r * 0.85},${y - r * 0.6} C${r * 1.7},${y - r * 0.4} ${r * 1.6},${y + r * 0.9} ${r * 1.2},${y + r * 1.3} C${r * 1.3},${y + r * 0.5} ${r * 1.1},${y - r * 0.1} ${r * 0.8},${y - r * 0.2} Z" fill="${c}" stroke="${INK}" stroke-width="4" stroke-linejoin="round"/><path d="M${-r * 1.02},${y - r * 0.05} C${-r * 1.1},${y - r * 1.3} ${r * 1.1},${y - r * 1.3} ${r * 1.02},${y - r * 0.05} C${r * 0.5},${y - r * 0.55} ${-r * 0.2},${y - r * 0.9} ${-r * 1.02},${y - r * 0.05} Z" fill="${c}" stroke="${INK}" stroke-width="4" stroke-linejoin="round"/>`,
  curly: (c) => (r, y) => { let s = ''; const n = 13; for (let i = 0; i < n; i++) { const a = Math.PI * (1.02 + 0.96 * i / (n - 1)); s += `<circle cx="${Math.cos(a) * r * 1.02}" cy="${y + Math.sin(a) * r * 1.02 - r * 0.05}" r="${r * 0.3}" fill="${c}" stroke="${INK}" stroke-width="3.5"/>`; } return s + `<path d="M${-r * 0.9},${y - r * 0.2} C${-r * 0.8},${y - r * 1.1} ${r * 0.8},${y - r * 1.1} ${r * 0.9},${y - r * 0.2} C${r * 0.5},${y - r * 0.55} ${-r * 0.5},${y - r * 0.55} ${-r * 0.9},${y - r * 0.2} Z" fill="${c}"/>`; },
  shortCrop: (c) => (r, y) => `<path d="M${-r * 1.0},${y - r * 0.15} C${-r * 1.05},${y - r * 1.2} ${r * 1.05},${y - r * 1.2} ${r * 1.0},${y - r * 0.15} C${r * 0.8},${y - r * 0.55} ${-r * 0.8},${y - r * 0.55} ${-r * 1.0},${y - r * 0.15} Z" fill="${c}" stroke="${INK}" stroke-width="4" stroke-linejoin="round"/>`,
};
const HAT = {
  driverCap: (c) => (r, y) => `<path d="M${-r * 1.0},${y - r * 0.45} C${-r * 1.0},${y - r * 1.25} ${r * 1.0},${y - r * 1.25} ${r * 1.0},${y - r * 0.45} Z" fill="${c}" stroke="${INK}" stroke-width="4" stroke-linejoin="round"/><path d="M${-r * 1.05},${y - r * 0.45} h${r * 2.1} q${r * 0.1},${r * 0.22} -${r * 0.2},${r * 0.22} h-${r * 1.7} q-${r * 0.3},0 -${r * 0.2},-${r * 0.22} z" fill="#1c1c1c" stroke="${INK}" stroke-width="3"/><rect x="${-r * 0.16}" y="${y - r * 0.82}" width="${r * 0.32}" height="${r * 0.2}" rx="3" fill="#d8bf94" stroke="${INK}" stroke-width="2"/>`,
};
const PROPS = {
  phone: (L, a) => `<rect x="${a * 0.2}" y="${L - a * 1.3}" width="${a * 0.7}" height="${a * 1.25}" rx="4" fill="#1d1f24" stroke="${INK}" stroke-width="3"/>`,
  teddy: (L, a) => `<g transform="translate(${a * 0.6},${L + a * 0.4})"><circle cx="0" cy="0" r="${a * 1.0}" fill="#b07a4a" stroke="${INK}" stroke-width="3"/><circle cx="0" cy="${-a * 1.3}" r="${a * 0.75}" fill="#b07a4a" stroke="${INK}" stroke-width="3"/><circle cx="${-a * 0.6}" cy="${-a * 1.9}" r="${a * 0.3}" fill="#b07a4a" stroke="${INK}" stroke-width="3"/><circle cx="${a * 0.6}" cy="${-a * 1.9}" r="${a * 0.3}" fill="#b07a4a" stroke="${INK}" stroke-width="3"/><circle cx="${-a * 0.25}" cy="${-a * 1.4}" r="3" fill="${INK}"/><circle cx="${a * 0.25}" cy="${-a * 1.4}" r="3" fill="${INK}"/></g>`,
  keys: (L, a) => `<g transform="translate(${a * 0.3},${L + a * 0.5})"><circle r="${a * 0.35}" fill="none" stroke="#c9a227" stroke-width="4"/><rect x="${-a * 0.1}" y="${a * 0.3}" width="${a * 0.2}" height="${a * 0.7}" fill="#c9a227"/></g>`,
  book: (L, a) => `<rect x="${-a * 0.2}" y="${L - a * 0.6}" width="${a * 1.4}" height="${a * 1.8}" rx="3" fill="#6c4ab6" stroke="${INK}" stroke-width="3"/>`,
  bag: (L, a) => `<g transform="translate(${a * 0.2},${L})"><path d="M${-a * 0.3},0 q${a * 0.5},-${a * 0.8} ${a},0" fill="none" stroke="${INK}" stroke-width="3"/><rect x="${-a * 0.6}" y="0" width="${a * 1.6}" height="${a * 1.2}" rx="6" fill="#c44b6c" stroke="${INK}" stroke-width="3"/></g>`,
};
function dog(scale = 1) { // Duke, a fluffy cream dog, feet at 0
  const s = scale, I = INK;
  return `<g transform="scale(${s})"><ellipse cx="0" cy="-70" rx="78" ry="48" fill="#f1e2c6" stroke="${I}" stroke-width="4"/>
  ${[-50, -20, 25, 52].map(x => `<rect x="${x - 10}" y="-50" width="20" height="50" rx="9" fill="#f1e2c6" stroke="${I}" stroke-width="4"/>`).join('')}
  <path d="M70,-95 q40,-40 20,-60" fill="none" stroke="${I}" stroke-width="10" stroke-linecap="round"/><path d="M70,-95 q40,-40 20,-60" fill="none" stroke="#f1e2c6" stroke-width="5" stroke-linecap="round"/>
  <circle cx="-70" cy="-120" r="44" fill="#f1e2c6" stroke="${I}" stroke-width="4"/>
  <ellipse cx="-108" cy="-112" rx="16" ry="30" fill="#d9bf95" stroke="${I}" stroke-width="4" transform="rotate(18 -108 -112)"/>
  <ellipse cx="-32" cy="-112" rx="16" ry="30" fill="#d9bf95" stroke="${I}" stroke-width="4" transform="rotate(-18 -32 -112)"/>
  <circle cx="-84" cy="-126" r="6" fill="${I}"/><circle cx="-56" cy="-126" r="6" fill="${I}"/>
  <ellipse cx="-70" cy="-104" rx="11" ry="8" fill="${I}"/><path d="M-80,-92 q10,10 20,0" fill="none" stroke="${I}" stroke-width="3"/>
  <path d="M-96,-82 h52" stroke="#c4161c" stroke-width="9" stroke-linecap="round"/><circle cx="-70" cy="-75" r="7" fill="#d8bf94" stroke="${I}" stroke-width="2"/></g>`;
}
if (typeof module !== 'undefined') module.exports = { draw, HAIR, HAT, PROPS, dog, INK };
