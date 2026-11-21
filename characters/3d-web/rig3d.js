// Skyhaven 3D puppet rig (three.js). Same idea as the 2D rig: every character is built from a fixed
// spec, so they look identical in every shot. Units are metres. build(spec) returns a THREE.Group with
// named joints: hips, spine, neck, head, shL/shR (shoulders), elL/elR (elbows), hipL/hipR, knL/knR.
// pose(char, p) sets joint angles; walk(char, phase, amount) is a ready-made walk cycle.
const R3 = (() => {
  const T = THREE, INK = 0x2b2420;
  const grad = (() => { const d = new Uint8Array([90, 170, 255]); const t = new T.DataTexture(d, 3, 1, T.RedFormat); t.needsUpdate = true; t.minFilter = t.magFilter = T.NearestFilter; return t; })();
  const mats = {};
  const toon = c => mats[c] || (mats[c] = new T.MeshToonMaterial({ color: new T.Color(c), gradientMap: grad }));
  const inkMat = new T.MeshBasicMaterial({ color: INK, side: T.BackSide });
  function part(geo, color, outline = 0.012, cast = true) {      // toon mesh + inverted-hull outline
    const g = new T.Group(), m = new T.Mesh(geo, toon(color)); m.castShadow = cast; m.receiveShadow = true; g.add(m);
    if (outline) { const o = new T.Mesh(geo, inkMat); geo.computeBoundingSphere(); const r = geo.boundingSphere.radius; o.scale.setScalar(1 + outline / r); g.add(o); }
    return g;
  }
  const cap = (r, len, c, o) => part(new T.CapsuleGeometry(r, len, 6, 16), c, o);
  const sph = (r, c, o, sx = 1, sy = 1, sz = 1) => { const p = part(new T.SphereGeometry(r, 32, 20), c, o); p.scale.set(sx, sy, sz); return p; };
  const box = (w, h, d, c, o) => part(new T.BoxGeometry(w, h, d, 2, 2, 2), c, o);
  const joint = (name, parent, x, y, z) => { const j = new T.Group(); j.name = name; j.position.set(x, y, z); parent.add(j); return j; };

  function hair(style, color, hr) {
    const g = new T.Group(), c = color;
    const capG = (sx, sy, sz, y, z, tilt = 0) => { const m = part(new T.SphereGeometry(hr, 32, 16, 0, Math.PI * 2, 0, Math.PI * 0.36), c, 0.01); m.scale.set(sx, sy, sz); m.position.set(0, y + hr * 0.04, z - hr * 0.06); m.rotation.x = tilt - 0.35; g.add(m); return m; };
    if (style === 'sidePart') { capG(1.08, 1.0, 1.08, hr * 0.08, -hr * 0.02, -0.15); const q = sph(hr * 0.45, c, 0.01, 1.4, 0.6, 1); q.position.set(-hr * 0.35, hr * 0.78, hr * 0.45); g.add(q); }
    if (style === 'longWaves') { capG(1.1, 1.05, 1.1, hr * 0.06, 0, -0.1); const back = cap(hr * 0.75, hr * 1.4, c, 0.01); back.position.set(0, -hr * 0.6, -hr * 0.45); back.scale.set(1.35, 1, 0.7); g.add(back);
      for (const s of [-1, 1]) { const side = cap(hr * 0.28, hr * 1.2, c, 0.01); side.position.set(s * hr * 0.92, -hr * 0.45, hr * 0.05); g.add(side); } }
    if (style === 'messy') { capG(1.06, 1.0, 1.06, hr * 0.05, 0); for (let i = 0; i < 9; i++) { const a = i / 9 * Math.PI * 2; const sp = part(new T.ConeGeometry(hr * 0.22, hr * 0.5, 8), c, 0.01); sp.position.set(Math.cos(a) * hr * 0.55, hr * 0.85, Math.sin(a) * hr * 0.55); sp.rotation.set(Math.sin(a) * 0.6, 0, -Math.cos(a) * 0.6); g.add(sp); } }
    if (style === 'shortCrop') capG(1.04, 0.95, 1.04, hr * 0.05, -hr * 0.02, -0.1);
    if (style === 'bun') { capG(1.05, 1.0, 1.05, hr * 0.05, 0); const b = sph(hr * 0.42, c, 0.01); b.position.set(0, hr * 1.05, -hr * 0.25); g.add(b); }
    return g;
  }

  function build(s) {
    const H = s.height, kid = s.age === 'kid' || s.age === 'baby';
    const hr = H * (s.age === 'baby' ? 0.2 : kid ? 0.14 : 0.105);          // head radius
    const legL = H * (s.age === 'baby' ? 0.22 : kid ? 0.36 : 0.44), torso = H - legL - hr * 2.05;
    const tw = hr * (s.build === 'broad' ? 2.1 : s.build === 'slim' ? 1.7 : 1.9), lr = hr * 0.32, ar = hr * 0.26;
    const root = new T.Group(); root.name = s.id || 'char'; root.userData.spec = s;
    const hips = joint('hips', root, 0, legL, 0);
    // legs
    for (const [side, sx] of [['L', 1], ['R', -1]]) {
      const hip = joint('hip' + side, hips, sx * tw * 0.24, 0, 0);
      const th = cap(lr, legL * 0.5 - lr, s.dress ? s.skin : s.pants); th.position.y = -legL * 0.25; hip.add(th);
      const kn = joint('kn' + side, hip, 0, -legL * 0.5, 0);
      const sh = cap(lr * 0.92, legL * 0.5 - lr * 1.6, s.dress ? s.skin : s.pants); sh.position.y = -legL * 0.22; kn.add(sh);
      const shoe = box(lr * 2.1, lr * 1.2, lr * 3.2, s.shoes, 0.008); shoe.position.set(0, -legL * 0.5 + lr * 0.6, lr * 0.6); kn.add(shoe);
    }
    // torso
    const spine = joint('spine', hips, 0, 0, 0);
    const body = cap(tw * 0.5, Math.max(0.01, torso - tw), s.top); body.position.y = torso * 0.5; body.scale.z = 0.72; spine.add(body);
    if (s.dress) { const skirt = part(new T.CylinderGeometry(tw * 0.52, tw * 0.78, legL * 0.42, 24, 1, true), s.top, 0.01); skirt.position.y = -legL * 0.16; skirt.scale.z = 0.8; spine.add(skirt); }
    if (s.apron) { const ap = box(tw * 0.7, torso * 0.8, 0.02, s.apron, 0.006); ap.position.set(0, torso * 0.35, tw * 0.37); spine.add(ap); }
    if (s.jacket) { const sh = box(tw * 0.26, torso * 0.45, 0.02, s.shirt || 0xffffff, 0.005); sh.position.set(0, torso * 0.72, tw * 0.37); spine.add(sh);
      if (s.tie) { const tie = box(tw * 0.09, torso * 0.42, 0.02, s.tie, 0.004); tie.position.set(0, torso * 0.68, tw * 0.385); spine.add(tie); } }
    if (s.collar) { const co = part(new T.TorusGeometry(hr * 0.42, hr * 0.07, 8, 24, Math.PI), s.collarColor || 0xffffff, 0.005); co.rotation.set(Math.PI / 2 + 0.25, 0, Math.PI); co.position.set(0, torso, 0.02); spine.add(co); }
    // arms
    for (const [side, sx] of [['L', 1], ['R', -1]]) {
      const shj = joint('sh' + side, spine, sx * (tw * 0.5 + ar * 0.3), torso - ar * 1.2, 0);
      const ua = cap(ar, torso * 0.42 - ar, s.sleeves || s.top); ua.position.y = -torso * 0.21; shj.add(ua);
      const el = joint('el' + side, shj, 0, -torso * 0.42, 0);
      const fa = cap(ar * 0.9, torso * 0.36 - ar, s.forearm || s.sleeves || s.top); fa.position.y = -torso * 0.18; el.add(fa);
      const hand = sph(ar * 1.15, s.skin, 0.008); hand.position.y = -torso * 0.4; hand.name = 'hand' + side; el.add(hand);
    }
    // head
    const neck = joint('neck', spine, 0, torso, 0);
    const nk = cap(hr * 0.28, hr * 0.2, s.skin, 0.006); nk.position.y = hr * 0.15; neck.add(nk);
    const head = joint('head', neck, 0, hr * 1.15, 0);
    head.add(sph(hr, s.skin, 0.014, 1, 1.04, 0.96));
    for (const sx of [-1, 1]) { const ear = sph(hr * 0.2, s.skin, 0.008, 0.6, 1, 0.8); ear.position.set(sx * hr * 0.98, 0, 0); head.add(ear); }
    const face = new T.Group(); face.name = 'face'; head.add(face);
    const eyeR = hr * (kid ? 0.2 : 0.16);
    for (const sx of [-1, 1]) {
      const eye = new T.Group(); eye.name = sx > 0 ? 'eyeL' : 'eyeR'; eye.position.set(sx * hr * 0.36, hr * 0.08, hr * 0.86); face.add(eye);
      eye.add(sph(eyeR, 0xffffff, 0.006, 1, 1.15, 0.5));
      const pu = new T.Mesh(new T.SphereGeometry(eyeR * 0.58, 16, 12), new T.MeshBasicMaterial({ color: s.eyes || 0x2a1d16 })); pu.position.z = eyeR * 0.32; pu.scale.z = 0.5; pu.name = 'pupil'; eye.add(pu);
      const gl = new T.Mesh(new T.SphereGeometry(eyeR * 0.18, 8, 8), new T.MeshBasicMaterial({ color: 0xffffff })); gl.position.set(eyeR * 0.2, eyeR * 0.22, eyeR * 0.5); eye.add(gl);
      const lid = sph(eyeR * 1.08, s.skin, 0.004, 1, 1.15, 0.55); lid.name = 'lid'; lid.visible = false; eye.add(lid);
      const brow = box(eyeR * 2.1, hr * 0.06, hr * 0.05, s.brow || 0x2b2420, 0); brow.position.set(sx * hr * 0.36, hr * 0.38, hr * 0.86); brow.name = sx > 0 ? 'browL' : 'browR'; face.add(brow);
      const blush = new T.Mesh(new T.CircleGeometry(hr * 0.13, 16), new T.MeshBasicMaterial({ color: 0xe8897c, transparent: true, opacity: 0.45 })); blush.position.set(sx * hr * 0.55, -hr * 0.25, hr * 0.82); blush.rotation.y = sx * 0.55; face.add(blush);
    }
    const nose = sph(hr * 0.11, s.skin, 0.006); nose.position.set(0, -hr * 0.08, hr * 0.97); face.add(nose);
    // mouths: one mesh per shape, toggled for lip-sync
    const mouths = new T.Group(); mouths.name = 'mouths'; mouths.position.set(0, -hr * 0.42, hr * 0.86); face.add(mouths);
    const mk = (name, geo, color, rotX = 0) => { const m = new T.Mesh(geo, new T.MeshBasicMaterial({ color })); m.name = name; m.rotation.x = rotX; m.visible = false; mouths.add(m); return m; };
    const smile = mk('smile', new T.TorusGeometry(hr * 0.22, hr * 0.035, 8, 24, Math.PI), INK); smile.rotation.z = Math.PI;
    mk('open', new T.SphereGeometry(hr * 0.17, 16, 12), 0x7a2c2c).scale.set(1.25, 0.9, 0.35);
    mk('o', new T.SphereGeometry(hr * 0.1, 16, 12), 0x7a2c2c).scale.set(1, 1.3, 0.35);
    mk('flat', new T.BoxGeometry(hr * 0.3, hr * 0.04, hr * 0.03), INK);
    const grin = mk('grin', new T.SphereGeometry(hr * 0.2, 16, 12, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), 0xffffff); grin.scale.set(1.2, 0.8, 0.35);
    smile.visible = true;
    if (s.glasses) { const gm = new T.MeshBasicMaterial({ color: s.glasses }); for (const sx of [-1, 1]) { const r = new T.Mesh(new T.TorusGeometry(eyeR * 1.5, hr * 0.03, 8, 24), gm); r.position.set(sx * hr * 0.36, hr * 0.08, hr * 0.95); face.add(r); } }
    if (s.hair) head.add(hair(s.hair, s.hairColor, hr));
    root.userData.H = H; root.userData.hr = hr;
    return root;
  }
  const J = (c, n) => c.getObjectByName(n);
  function mouth(c, shape) { for (const m of J(c, 'mouths').children) m.visible = m.name === shape; }
  function blink(c, on) { for (const e of ['eyeL', 'eyeR']) { const eye = J(c, e); J(eye, 'lid').visible = on; J(eye, 'pupil').visible = !on; } }
  function look(c, x, y) { for (const e of ['eyeL', 'eyeR']) { const p = J(J(c, e), 'pupil'); p.position.x = x * 0.012; p.position.y = y * 0.012; } }
  // pose angles in radians: arms swing forward/back (x) and out (z); elbows bend (x)
  function pose(c, p = {}) {
    const g = (k, d = 0) => (p[k] !== undefined ? p[k] : d);
    J(c, 'shL').rotation.set(g('shLx'), 0, g('shLz', 0.08)); J(c, 'shR').rotation.set(g('shRx'), 0, -g('shRz', 0.08));
    J(c, 'elL').rotation.x = -g('elL', 0.1); J(c, 'elR').rotation.x = -g('elR', 0.1);
    J(c, 'hipL').rotation.x = g('hipL'); J(c, 'hipR').rotation.x = g('hipR');
    J(c, 'knL').rotation.x = g('knL'); J(c, 'knR').rotation.x = g('knR');
    J(c, 'spine').rotation.set(g('spineX'), g('spineY'), g('spineZ'));
    J(c, 'head').rotation.set(g('headX'), g('headY'), g('headZ'));
    J(c, 'hips').position.y = J(c, 'hips').userData.base ?? (J(c, 'hips').userData.base = J(c, 'hips').position.y);
    J(c, 'hips').position.y += g('bob');
  }
  function walk(c, ph, amt = 1) {        // ph in radians; one stride per 2*PI
    const s = Math.sin(ph), k = a => Math.max(0, a);
    return { hipL: 0.5 * s * amt, hipR: -0.5 * s * amt, knL: k(-Math.sin(ph - 0.9)) * 0.9 * amt, knR: k(Math.sin(ph - 0.9)) * 0.9 * amt,
      shLx: -0.45 * s * amt, shRx: 0.45 * s * amt, elL: 0.35 + 0.2 * amt, elR: 0.35 + 0.2 * amt, bob: Math.abs(Math.cos(ph)) * 0.035 * amt, spineY: 0.06 * s * amt };
  }
  return { build, pose, walk, mouth, blink, look, part, toon, box, sph, cap, INK };
})();
