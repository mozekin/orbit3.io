// Home hero: wireframe globe with network arcs (three.js) + a Terraform terminal that types itself out.
// Falls back to the static CSS hero when WebGL is unavailable, the visitor prefers reduced motion or has Save-Data on.
// three.js is imported lazily so visitors who fall back never download it.
let THREE;

const LOG = "[orbit3-3d]";
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const saveData = !!(navigator.connection && navigator.connection.saveData);
const finePointer = window.matchMedia("(pointer: fine)").matches;

// ---------------------------------------------------------------- terminal
function runTerminal() {
  const term = document.querySelector(".hero-term");
  if (!term) return;
  if (reduceMotion) { console.log("[orbit3-term] static: reduced-motion"); return; }
  const lines = [...term.querySelectorAll(".hero-term-body > div")];
  const cmds = lines.map((l) => (l.classList.contains("cmd") ? l.querySelector(".t").textContent : null));
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  const visible = () => !document.hidden;

  term.classList.add("is-typing");
  console.log("[orbit3-term] start");

  (async function loop() {
    for (;;) {
      lines.forEach((l, i) => { l.classList.remove("on"); if (cmds[i] !== null) l.querySelector(".t").textContent = ""; });
      await wait(600);
      for (let i = 0; i < lines.length; i++) {
        while (!visible()) await wait(500);
        const l = lines[i];
        l.classList.add("on");
        if (cmds[i] !== null) {
          const t = l.querySelector(".t");
          for (const ch of cmds[i]) { t.textContent += ch; await wait(28 + Math.random() * 45); }
          await wait(450);
        } else {
          await wait(l.classList.contains("slow") ? 1100 : 180);
        }
      }
      await wait(5000);
    }
  })();
}

// ---------------------------------------------------------------- globe
const CITIES = [
  [51.5, -0.13], [53.35, -6.26], [50.11, 8.68], [59.33, 18.07], [38.9, -77.4], [45.6, -121.2],
  [-23.5, -46.6], [19.1, 72.9], [1.35, 103.8], [35.7, 139.7], [-33.9, 151.2], [-26.2, 28.0],
];

function latLon(lat, lon, r = 1) {
  const phi = THREE.MathUtils.degToRad(90 - lat), theta = THREE.MathUtils.degToRad(lon + 180);
  return new THREE.Vector3(-r * Math.sin(phi) * Math.cos(theta), r * Math.cos(phi), r * Math.sin(phi) * Math.sin(theta));
}

function graticule(step = 15, seg = 96) {
  const pts = [];
  const push = (a, b) => pts.push(a.x, a.y, a.z, b.x, b.y, b.z);
  for (let lat = -90 + step; lat < 90; lat += step)
    for (let i = 0; i < seg; i++) push(latLon(lat, (i / seg) * 360), latLon(lat, ((i + 1) / seg) * 360));
  for (let lon = 0; lon < 360; lon += step)
    for (let i = 0; i < seg; i++) push(latLon(-90 + (i / seg) * 180, lon), latLon(-90 + ((i + 1) / seg) * 180, lon));
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(pts, 3));
  return g;
}

const ARC_SEG = 64;
function arcPoints(a, b) {
  const va = latLon(...a), vb = latLon(...b);
  const lift = 0.12 + 0.35 * (va.angleTo(vb) / Math.PI);
  const q = new THREE.Quaternion(), qa = new THREE.Quaternion(), qb = new THREE.Quaternion().setFromUnitVectors(va, vb);
  const out = new Float32Array((ARC_SEG + 1) * 3);
  for (let i = 0; i <= ARC_SEG; i++) {
    const t = i / ARC_SEG;
    q.slerpQuaternions(qa, qb, t);
    const p = va.clone().applyQuaternion(q).multiplyScalar(1 + lift * Math.sin(Math.PI * t));
    out.set([p.x, p.y, p.z], i * 3);
  }
  return out;
}

async function initGlobe() {
  const host = document.querySelector(".hero-3d");
  if (!host) return console.log(LOG, "fallback: no-container");
  if (reduceMotion) return console.log(LOG, "fallback: reduced-motion");
  if (saveData) return console.log(LOG, "fallback: save-data");
  const probe = document.createElement("canvas").getContext("webgl2");
  if (!probe) return console.log(LOG, "fallback: no-webgl");
  probe.getExtension("WEBGL_lose_context")?.loseContext();

  const t0 = performance.now();
  try {
    THREE = await import("./vendor/three.module.min.js");
  } catch (e) {
    return console.log(LOG, "fallback: import-failed", e.message);
  }
  console.log(LOG, `three loaded in ${Math.round(performance.now() - t0)}ms`);

  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "low-power" });
  } catch (e) {
    return console.log(LOG, "fallback: no-webgl", e.message);
  }
  const mobile = window.matchMedia("(max-width: 720px)").matches;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, mobile ? 1.5 : 2));
  renderer.setClearColor(0x000000, 0);
  host.appendChild(renderer.domElement);

  const accent = new THREE.Color("#2dd4bf"), cyan = new THREE.Color("#22d3ee"), blue = new THREE.Color("#5b8def");
  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog(0x0a0d12, 2.6, 4.6);
  const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 50);
  camera.position.set(0, 0, 3.6);

  const globe = new THREE.Group();
  globe.rotation.x = 0.38;
  scene.add(globe);

  globe.add(new THREE.LineSegments(graticule(mobile ? 20 : 15, mobile ? 64 : 96),
    new THREE.LineBasicMaterial({ color: accent, transparent: true, opacity: 0.22, fog: true })));

  const cityGeo = new THREE.BufferGeometry().setFromPoints(CITIES.map((c) => latLon(...c, 1.005)));
  globe.add(new THREE.Points(cityGeo, new THREE.PointsMaterial({ color: accent, size: 0.035, transparent: true, opacity: 0.95, fog: true })));

  const palette = [accent, cyan, blue];
  const arcs = Array.from({ length: mobile ? 5 : 9 }, (_, i) => {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array((ARC_SEG + 1) * 3), 3));
    const line = new THREE.Line(geo, new THREE.LineBasicMaterial({ color: palette[i % 3], transparent: true, opacity: 0.85, fog: true }));
    const headGeo = new THREE.BufferGeometry();
    headGeo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(3), 3));
    const head = new THREE.Points(headGeo, new THREE.PointsMaterial({ color: 0xffffff, size: 0.04, transparent: true, fog: true }));
    globe.add(line, head);
    const arc = { line, head, t: -Math.random() * 3, dur: 2.2 + Math.random() * 1.6 };
    reroute(arc);
    return arc;
  });

  function reroute(arc) {
    const a = Math.floor(Math.random() * CITIES.length);
    let b = Math.floor(Math.random() * (CITIES.length - 1));
    if (b >= a) b++;
    const attr = arc.line.geometry.getAttribute("position");
    attr.array.set(arcPoints(CITIES[a], CITIES[b]));
    attr.needsUpdate = true;
    arc.line.geometry.computeBoundingSphere();
    arc.line.geometry.setDrawRange(0, 0);
  }

  function stepArc(arc, dt) {
    arc.t += dt / arc.dur;
    if (arc.t >= 2.4) { arc.t = 0; reroute(arc); }
    const t = Math.max(arc.t, 0);
    const headIdx = Math.floor(Math.min(t, 1) * ARC_SEG), tailIdx = Math.floor(Math.min(Math.max(t - 1, 0), 1) * ARC_SEG);
    arc.line.geometry.setDrawRange(tailIdx, headIdx - tailIdx + 1);
    const src = arc.line.geometry.getAttribute("position").array;
    const h = arc.head.geometry.getAttribute("position");
    h.array.set(src.subarray(headIdx * 3, headIdx * 3 + 3));
    h.needsUpdate = true;
    arc.head.visible = t > 0 && t < 1;
  }

  // Size the globe to the hero: radius ~40% of the short side, centred slightly above middle.
  function resize() {
    const w = host.clientWidth, h = host.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    const rPx = Math.min(w, h) * (mobile ? 0.46 : 0.4);
    const dist = h / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * rPx);
    camera.position.z = dist;
    camera.position.y = -0.12 * (h / rPx);
    scene.fog.near = dist - 0.4;
    scene.fog.far = dist + 1.4;
    camera.updateProjectionMatrix();
  }
  new ResizeObserver(resize).observe(host);
  resize();

  let running = false, inView = true, lost = false, last = 0, spin = 0;
  const baseX = 0.38, baseY = -Math.PI / 2 + THREE.MathUtils.degToRad(10);

  // Pointer tilt (fine pointers only) and scroll progress through the hero, both eased in frame().
  const tilt = { x: 0, y: 0, tx: 0, ty: 0 };
  let scroll = 0, scrollTarget = 0;
  if (finePointer) {
    window.addEventListener("pointermove", (e) => {
      tilt.tx = (e.clientY / window.innerHeight - 0.5) * 0.25;
      tilt.ty = (e.clientX / window.innerWidth - 0.5) * 0.45;
    }, { passive: true });
  }
  const onScroll = () => { scrollTarget = Math.min(Math.max(window.scrollY / (host.clientHeight || 1), 0), 1); };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // Adaptive quality: if frames average slower than ~40fps after warm-up, drop to 1x pixel ratio once.
  let frames = 0, avgDt = 1 / 60, downgraded = renderer.getPixelRatio() <= 1;

  function frame(now) {
    if (!running) return;
    const dt = Math.min((now - last) / 1000, 0.05);
    last = now;
    spin += dt;

    const k = 1 - Math.exp(-dt * 4);
    tilt.x += (tilt.tx - tilt.x) * k;
    tilt.y += (tilt.ty - tilt.y) * k;
    scroll += (scrollTarget - scroll) * k;
    globe.rotation.x = baseX + tilt.x + scroll * 0.25;
    globe.rotation.y = baseY + spin * 0.05 + tilt.y + scroll * 1.2;
    globe.position.y = -scroll * 0.5;

    arcs.forEach((a) => stepArc(a, dt));
    renderer.render(scene, camera);

    if (!downgraded && ++frames > 30) {
      avgDt += (dt - avgDt) * 0.05;
      if (frames > 120 && avgDt > 1 / 40) {
        downgraded = true;
        renderer.setPixelRatio(1);
        resize();
        console.log(LOG, `quality: dpr 1 (avg ${Math.round(1000 * avgDt)}ms/frame)`);
      }
    }
    requestAnimationFrame(frame);
  }
  function sync() {
    const should = inView && !document.hidden && !lost;
    if (should === running) return;
    running = should;
    console.log(LOG, running ? "resumed" : "paused");
    if (running) requestAnimationFrame((now) => { last = now; frames = 0; requestAnimationFrame(frame); });
  }

  new IntersectionObserver(([e]) => { inView = e.isIntersecting; sync(); }).observe(host);
  document.addEventListener("visibilitychange", sync);
  renderer.domElement.addEventListener("webglcontextlost", (e) => { e.preventDefault(); lost = true; host.classList.remove("is-ready"); console.log(LOG, "context lost"); sync(); });
  renderer.domElement.addEventListener("webglcontextrestored", () => { lost = false; host.classList.add("is-ready"); console.log(LOG, "context restored"); sync(); });

  console.log(LOG, "init", { three: THREE.REVISION, mobile, arcs: arcs.length, dpr: renderer.getPixelRatio(), pointerTilt: finePointer });
  sync();
  requestAnimationFrame(() => host.classList.add("is-ready"));
}

runTerminal();
// Start the globe once the main thread is idle so it never competes with the hero text for LCP.
(window.requestIdleCallback || ((cb) => setTimeout(cb, 200)))(() => initGlobe(), { timeout: 1500 });
