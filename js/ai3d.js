// AI Solutions hero: a 3D neural network that "trains" (forward + backprop pulses) while a log runs,
// then lights up per token as a cloud ops copilot answers plain-English questions. Scripted, not a live model.
// The panels drive the network through "orbit3-ai" events, so the demo still plays when WebGL is unavailable.
let THREE;

const LOG = "[orbit3-ai]";
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const saveData = !!(navigator.connection && navigator.connection.saveData);
const finePointer = window.matchMedia("(pointer: fine)").matches;
const emit = (type, extra = {}) => window.dispatchEvent(new CustomEvent("orbit3-ai", { detail: { type, ...extra } }));

// ---------------------------------------------------------------- panels
function runDemo() {
  const lab = document.querySelector(".ai-lab");
  const dataEl = document.getElementById("aiDemo");
  if (!lab || !dataEl) return;
  if (reduceMotion) { console.log(LOG, "demo static: reduced-motion"); return; }

  const scenarios = JSON.parse(dataEl.textContent);
  const train = lab.querySelector(".ai-train");
  const lines = [...train.querySelectorAll(".hero-term-body > div")];
  const cmds = lines.map((l) => (l.classList.contains("cmd") ? l.querySelector(".t").textContent : null));
  const loss = lab.querySelector(".ai-loss path");
  const [userMsg, botMsg] = lab.querySelectorAll(".ai-msg");
  const q = userMsg.querySelector(".ai-q"), a = botMsg.querySelector(".ai-a");
  const epochs = lines.filter((l) => l.classList.contains("ep")).length;

  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  const awake = async () => { while (document.hidden) await wait(500); };

  lab.classList.add("is-typing");
  train.classList.add("is-typing");
  console.log(LOG, "demo start", { scenarios: scenarios.length, epochs });

  async function trainRun() {
    emit("reset");
    lines.forEach((l, i) => { l.classList.remove("on"); if (cmds[i] !== null) l.querySelector(".t").textContent = ""; });
    loss.style.strokeDashoffset = "100";
    await wait(500);
    let ep = 0;
    for (let i = 0; i < lines.length; i++) {
      await awake();
      const l = lines[i];
      if (l.classList.contains("ep")) {
        ep++;
        emit("epoch", { n: ep, of: epochs });
        await wait(1900);
        loss.style.strokeDashoffset = String(100 - (ep / epochs) * 100);
      }
      l.classList.add("on");
      if (cmds[i] !== null) {
        const t = l.querySelector(".t");
        for (const ch of cmds[i]) { t.textContent += ch; await wait(24 + Math.random() * 40); }
        await wait(400);
      } else {
        await wait(l.classList.contains("slow") ? 1000 : 250);
      }
    }
    console.log(LOG, "training done");
  }

  async function ask({ q: question, a: answer }) {
    [userMsg, botMsg].forEach((m) => m.classList.remove("on", "thinking", "streaming"));
    q.textContent = ""; a.textContent = "";
    await wait(700);
    userMsg.classList.add("on");
    for (const ch of question) { await awake(); q.textContent += ch; await wait(30 + Math.random() * 45); }
    await wait(350);
    emit("prompt");
    botMsg.classList.add("on", "thinking");
    await wait(1100);
    botMsg.classList.replace("thinking", "streaming");
    const chunks = answer.match(/\S+\s*/g) || [];
    for (let i = 0; i < chunks.length; i++) {
      await awake();
      a.textContent += chunks[i];
      if (i % 2 === 0) emit("token");
      await wait(45 + Math.random() * 70);
    }
    botMsg.classList.remove("streaming");
    console.log(LOG, "answered:", question);
    await wait(4200);
  }

  (async function loop() {
    for (;;) {
      await trainRun();
      for (const s of scenarios) await ask(s);
    }
  })();
}

// ---------------------------------------------------------------- network
function dotTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 64;
  const g = c.getContext("2d"), grad = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  grad.addColorStop(0, "rgba(255,255,255,1)");
  grad.addColorStop(0.35, "rgba(255,255,255,0.55)");
  grad.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = grad;
  g.fillRect(0, 0, 64, 64);
  return new THREE.CanvasTexture(c);
}

async function initNetwork() {
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

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 60);
  // `orient` turns the whole network vertical on portrait screens; `net` handles sway, tilt and scroll.
  const orient = new THREE.Group(), net = new THREE.Group();
  net.rotation.x = 0.12;
  orient.add(net);
  scene.add(orient);

  const accent = new THREE.Color("#2dd4bf"), cyan = new THREE.Color("#22d3ee"), amber = new THREE.Color("#fbbf24"), white = new THREE.Color("#ffffff");
  const sprite = dotTexture();

  // Layers are rings of nodes in the y-z plane, spaced along x.
  const LAYERS = mobile ? [4, 6, 8, 6, 4] : [6, 9, 12, 9, 6];
  const SPAN_X = 4.4;
  const nodes = [], layerNodes = [];
  LAYERS.forEach((n, l) => {
    const x = -SPAN_X / 2 + (l * SPAN_X) / (LAYERS.length - 1), r = 0.3 + n * 0.075, ids = [];
    for (let i = 0; i < n; i++) {
      const ang = (i / n) * Math.PI * 2 + l * 0.3;
      ids.push(nodes.length);
      nodes.push({ pos: new THREE.Vector3(x, r * Math.cos(ang), r * Math.sin(ang) * 0.7), act: 0 });
    }
    layerNodes.push(ids);
  });

  const edges = [], edgesByGap = LAYERS.slice(1).map(() => []);
  for (let l = 0; l < LAYERS.length - 1; l++)
    for (const a of layerNodes[l]) for (const b of layerNodes[l + 1]) {
      edgesByGap[l].push(edges.length);
      edges.push({ a, b, w0: Math.random() ** 2, w: 0 });
    }

  const edgePos = new Float32Array(edges.length * 6), edgeCol = new Float32Array(edges.length * 6);
  edges.forEach((e, i) => { edgePos.set([...nodes[e.a].pos.toArray(), ...nodes[e.b].pos.toArray()], i * 6); });
  const edgeGeo = new THREE.BufferGeometry();
  edgeGeo.setAttribute("position", new THREE.BufferAttribute(edgePos, 3));
  edgeGeo.setAttribute("color", new THREE.BufferAttribute(edgeCol, 3));
  net.add(new THREE.LineSegments(edgeGeo, new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false })));

  const pointMat = (size) => new THREE.PointsMaterial({ size, map: sprite, vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false });
  const nodePos = new Float32Array(nodes.length * 3), nodeCol = new Float32Array(nodes.length * 3);
  nodes.forEach((n, i) => nodePos.set(n.pos.toArray(), i * 3));
  const nodeGeo = new THREE.BufferGeometry();
  nodeGeo.setAttribute("position", new THREE.BufferAttribute(nodePos, 3));
  nodeGeo.setAttribute("color", new THREE.BufferAttribute(nodeCol, 3));
  net.add(new THREE.Points(nodeGeo, pointMat(mobile ? 0.2 : 0.17)));

  // Pulse pool: each pulse travels one edge, forward (a -> b) or backward (b -> a), after a delay.
  const POOL = mobile ? 90 : 180;
  const pulses = Array.from({ length: POOL }, () => ({ live: false, edge: 0, dir: 1, t: 0, delay: 0, col: cyan }));
  const pulsePos = new Float32Array(POOL * 3).fill(1000), pulseCol = new Float32Array(POOL * 3);
  const pulseGeo = new THREE.BufferGeometry();
  pulseGeo.setAttribute("position", new THREE.BufferAttribute(pulsePos, 3));
  pulseGeo.setAttribute("color", new THREE.BufferAttribute(pulseCol, 3));
  const pulsePoints = new THREE.Points(pulseGeo, pointMat(mobile ? 0.14 : 0.12));
  pulsePoints.frustumCulled = false;
  net.add(pulsePoints);

  function spawnWave(dir, perGap, col, baseDelay = 0) {
    const gaps = edgesByGap.length;
    for (let k = 0; k < gaps; k++) {
      const gap = dir > 0 ? k : gaps - 1 - k, list = edgesByGap[gap];
      for (let j = 0; j < perGap; j++) {
        const p = pulses.find((x) => !x.live);
        if (!p) return;
        Object.assign(p, { live: true, edge: list[Math.floor(Math.random() * list.length)], dir, t: 0, delay: baseDelay + k * 0.3 + Math.random() * 0.12, col });
      }
    }
  }

  let train = 0, trainTarget = 0, ambient = 0;
  window.addEventListener("orbit3-ai", ({ detail }) => {
    if (detail.type === "reset") { trainTarget = 0; edges.forEach((e) => (e.w = 0)); }
    else if (detail.type === "epoch") {
      trainTarget = detail.n / detail.of;
      spawnWave(1, mobile ? 3 : 5, cyan);
      spawnWave(-1, mobile ? 3 : 5, amber, 1.1);
    } else if (detail.type === "prompt") layerNodes[0].forEach((i) => (nodes[i].act = 1.2));
    else if (detail.type === "token") spawnWave(1, mobile ? 1 : 2, white);
  });

  function step(dt) {
    train += (trainTarget - train) * (1 - Math.exp(-dt * 1.5));
    ambient -= dt;
    if (ambient <= 0) { spawnWave(1, 1, accent); ambient = 1.4; }

    pulses.forEach((p, i) => {
      if (!p.live) return;
      if (p.delay > 0) { p.delay -= dt; pulsePos[i * 3 + 1] = 1000; return; }
      p.t += dt / 0.42;
      const e = edges[p.edge], from = nodes[p.dir > 0 ? e.a : e.b].pos, to = nodes[p.dir > 0 ? e.b : e.a].pos;
      if (p.t >= 1) {
        p.live = false;
        nodes[p.dir > 0 ? e.b : e.a].act = Math.min(nodes[p.dir > 0 ? e.b : e.a].act + 0.7, 1.4);
        if (p.dir < 0) e.w = Math.min(e.w + 0.25, 1);
        pulsePos[i * 3 + 1] = 1000;
        return;
      }
      pulsePos[i * 3] = from.x + (to.x - from.x) * p.t;
      pulsePos[i * 3 + 1] = from.y + (to.y - from.y) * p.t;
      pulsePos[i * 3 + 2] = from.z + (to.z - from.z) * p.t;
      pulseCol.set([p.col.r, p.col.g, p.col.b], i * 3);
    });
    pulseGeo.attributes.position.needsUpdate = pulseGeo.attributes.color.needsUpdate = true;

    const decay = Math.exp(-dt * 2.5);
    nodes.forEach((n, i) => {
      n.act *= decay;
      const base = 0.3 + 0.35 * train, glow = Math.min(n.act, 1);
      nodeCol.set([accent.r * base + glow * 0.8, accent.g * base + glow * 0.8, accent.b * base + glow * 0.8], i * 3);
    });
    nodeGeo.attributes.color.needsUpdate = true;

    // Edge brightness = learned weight (grows with training and backprop hits) + activity at either end.
    edges.forEach((e, i) => {
      const k = 0.035 + 0.3 * e.w0 * train + 0.15 * e.w + 0.12 * (nodes[e.a].act + nodes[e.b].act);
      edgeCol.set([cyan.r * k, cyan.g * k, cyan.b * k, cyan.r * k, cyan.g * k, cyan.b * k], i * 6);
      e.w *= Math.exp(-dt * 0.15);
    });
    edgeGeo.attributes.color.needsUpdate = true;
  }

  // Fit the network's bounding box into the hero, centred above middle (behind the heading, clear of the panels).
  // On portrait screens it runs top-to-bottom so it fills the tall mobile hero instead of shrinking to fit the width.
  let portrait = false;
  function resize() {
    const w = host.clientWidth, h = host.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    const was = portrait;
    portrait = camera.aspect < 0.8;
    orient.rotation.z = portrait ? -Math.PI / 2 : 0;
    const tan2 = 2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
    const long = SPAN_X + 1.4, short = 2.9;
    const dist = portrait
      ? Math.max(short / 0.95 / (tan2 * camera.aspect), long / 0.6 / tan2)
      : Math.max(long / 0.9 / (tan2 * camera.aspect), short / 0.6 / tan2);
    camera.position.set(0, -0.16 * dist * tan2, dist);
    camera.updateProjectionMatrix();
    if (was !== portrait) console.log(LOG, "layout:", portrait ? "portrait" : "landscape");
  }
  new ResizeObserver(resize).observe(host);
  resize();

  let running = false, inView = true, lost = false, last = 0, time = 0;
  const tilt = { x: 0, y: 0, tx: 0, ty: 0 };
  if (finePointer) {
    window.addEventListener("pointermove", (e) => {
      tilt.tx = (e.clientY / window.innerHeight - 0.5) * 0.2;
      tilt.ty = (e.clientX / window.innerWidth - 0.5) * 0.35;
    }, { passive: true });
  }
  let scroll = 0, scrollTarget = 0;
  const onScroll = () => { scrollTarget = Math.min(Math.max(window.scrollY / (host.clientHeight || 1), 0), 1); };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  let frames = 0, avgDt = 1 / 60, downgraded = renderer.getPixelRatio() <= 1;
  function frame(now) {
    if (!running) return;
    const dt = Math.min((now - last) / 1000, 0.05);
    last = now;
    time += dt;
    const k = 1 - Math.exp(-dt * 4);
    tilt.x += (tilt.tx - tilt.x) * k;
    tilt.y += (tilt.ty - tilt.y) * k;
    scroll += (scrollTarget - scroll) * k;
    const sway = Math.sin(time * 0.15) * 0.35;
    if (portrait) {
      // Spin the rings around the (now vertical) flow axis rather than tipping the column toward the viewer.
      net.rotation.x = sway * 1.5 + scroll * 0.9;
      net.rotation.y = 0.12;
    } else {
      net.rotation.x = 0.12 + tilt.x + scroll * 0.3;
      net.rotation.y = sway + tilt.y + scroll * 0.9;
    }
    orient.position.y = -scroll * 0.6;
    step(dt);
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

  console.log(LOG, "init", { three: THREE.REVISION, mobile, portrait, layers: LAYERS, edges: edges.length, dpr: renderer.getPixelRatio(), pointerTilt: finePointer });
  sync();
  requestAnimationFrame(() => host.classList.add("is-ready"));
}

runDemo();
(window.requestIdleCallback || ((cb) => setTimeout(cb, 200)))(() => initNetwork(), { timeout: 1500 });
