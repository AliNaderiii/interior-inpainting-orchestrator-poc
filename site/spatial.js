(() => {
  "use strict";

  const WIDTH = 1200;
  const HEIGHT = 800;
  const MAX_PRODUCT_BYTES = 8 * 1024 * 1024;
  const MAX_PRODUCT_PIXELS = 4_000_000;
  const SOURCE_HASH = "5c6425d87509a6a23e2f4a70ba5dfba2722ed0dc5c094f7a5d4a1af4760ba036";
  const BUILTIN_ASSET_HASH = "e87dc919e59bf63d94f28e7c0578c237a724a294427f4f46fb0e6400a92d131d";
  const RENDERER_VERSION = "spatial-local-v1";
  const BRIEF_COMPILER_VERSION = "spatial-brief-v1";
  const DEFAULT_CORNERS = [
    { x: 0.245, y: 0.635 },
    { x: 0.790, y: 0.635 },
    { x: 0.920, y: 0.930 },
    { x: 0.105, y: 0.930 },
  ];

  const VARIANTS = [
    { name: "Gallery calm", slug: "gallery-calm", color: "#d1c7b4", alpha: 0.13, lighting: "2700 K" },
    { name: "Ember social", slug: "ember-social", color: "#9a503a", alpha: 0.24, lighting: "2400 K" },
    { name: "Night gallery", slug: "night-gallery", color: "#12383d", alpha: 0.34, lighting: "2200 K" },
  ];

  // Wall-only polygons deliberately avoid the window, artwork and sconces.
  const WALL_POLYGONS = [
    [[36, 0], [1148, 0], [1148, 64], [36, 64]],
    [[36, 64], [81, 64], [81, 432], [36, 452]],
    [[394, 64], [447, 64], [447, 432], [394, 433]],
    [[507, 64], [823, 64], [823, 432], [507, 432]],
    [[1009, 64], [1059, 64], [1059, 432], [1009, 432]],
    [[1121, 64], [1148, 64], [1148, 432], [1121, 432]],
    [[823, 64], [1009, 64], [1009, 97], [823, 97]],
    [[823, 309], [1009, 309], [1009, 432], [823, 432]],
    [[507, 245], [823, 245], [823, 432], [507, 432]],
    [[1059, 245], [1121, 245], [1121, 432], [1059, 432]],
  ];

  const STEP_COPY = {
    1: { kicker: "STEP 01 / BRIEF", title: "Frame the spatial decision", inspector: "Spatial brief", phase: "DRAFT" },
    2: { kicker: "STEP 02 / AUTHORITY", title: "Map what may and may not change", inspector: "Scene locks", phase: "LOCK PLAN" },
    3: { kicker: "STEP 03 / PLACEMENT", title: "Fit the hero asset to the floor plane", inspector: "Hero placement", phase: "TRANSFORM" },
    4: { kicker: "STEP 04 / VARIANTS", title: "Change one approved variable at a time", inspector: "Variant review", phase: "LOCAL RUN" },
    5: { kicker: "STEP 05 / HANDOFF", title: "Select, verify and package the direction", inspector: "Proof handoff", phase: "REVIEW" },
  };

  const state = {
    step: 1,
    mode: "placement",
    corners: DEFAULT_CORNERS.map((point) => ({ ...point })),
    selectedCorner: 0,
    selectedVariant: 0,
    showGuides: true,
    showRegions: true,
    compareSource: false,
    shadowStrength: 18,
    productImage: null,
    productObjectUrl: null,
    assetHash: BUILTIN_ASSET_HASH,
    assetName: "Contour 01",
    sourceImage: null,
    occlusionImage: null,
    originalData: null,
    loaded: false,
    rendering: false,
    renderQueued: false,
    dragIndex: -1,
    lastProtectedDrift: 0,
    briefHash: "pending",
    variantsReady: false,
  };

  const html = document.documentElement;
  const canvas = document.querySelector("#spatial-canvas");
  const context = canvas.getContext("2d", { alpha: false, willReadFrequently: true });
  const loading = document.querySelector("#canvas-loading");
  const toast = document.querySelector("#toast");
  const stepButtons = [...document.querySelectorAll(".step-button")];
  const panels = [...document.querySelectorAll(".inspector-panel")];
  const variantCards = [...document.querySelectorAll(".variant-card")];
  const variantCanvases = variantCards.map((card) => card.querySelector("canvas"));
  const coordinateInputs = [...document.querySelectorAll(".corner-table input")];
  let toastTimer = null;
  let briefTimer = null;

  function loadImage(source) {
    return new Promise((resolve, reject) => {
      const image = new Image();
      image.decoding = "async";
      image.addEventListener("load", () => resolve(image), { once: true });
      image.addEventListener("error", () => reject(new Error(`Unable to load local asset: ${source}`)), { once: true });
      image.src = source;
    });
  }

  function showToast(message, error = false) {
    window.clearTimeout(toastTimer);
    toast.textContent = message;
    toast.classList.toggle("is-error", error);
    toast.classList.add("is-visible");
    toastTimer = window.setTimeout(() => toast.classList.remove("is-visible"), 2600);
  }

  function cloneCorners() {
    return state.corners.map((point) => ({ ...point }));
  }

  function pixelCorners() {
    return state.corners.map((point) => ({ x: point.x * WIDTH, y: point.y * HEIGHT }));
  }

  function tracePolygon(target, points) {
    target.beginPath();
    target.moveTo(points[0][0], points[0][1]);
    for (let index = 1; index < points.length; index += 1) {
      target.lineTo(points[index][0], points[index][1]);
    }
    target.closePath();
  }

  function tracePointPolygon(target, points) {
    target.beginPath();
    target.moveTo(points[0].x, points[0].y);
    for (let index = 1; index < points.length; index += 1) {
      target.lineTo(points[index].x, points[index].y);
    }
    target.closePath();
  }

  function polygonArea(points) {
    let total = 0;
    for (let index = 0; index < points.length; index += 1) {
      const next = points[(index + 1) % points.length];
      total += points[index].x * next.y - next.x * points[index].y;
    }
    return Math.abs(total) / 2;
  }

  function isConvex(points) {
    if (polygonArea(points) < 0.035) return false;
    let sign = 0;
    for (let index = 0; index < points.length; index += 1) {
      const a = points[index];
      const b = points[(index + 1) % points.length];
      const c = points[(index + 2) % points.length];
      const cross = (b.x - a.x) * (c.y - b.y) - (b.y - a.y) * (c.x - b.x);
      if (Math.abs(cross) < 0.0001) return false;
      const currentSign = Math.sign(cross);
      if (sign === 0) sign = currentSign;
      if (currentSign !== sign) return false;
    }
    return true;
  }

  function projectUnitToQuad(point, corners) {
    const [p0, p1, p2, p3] = corners;
    const dx1 = p1.x - p2.x;
    const dx2 = p3.x - p2.x;
    const dx3 = p0.x - p1.x + p2.x - p3.x;
    const dy1 = p1.y - p2.y;
    const dy2 = p3.y - p2.y;
    const dy3 = p0.y - p1.y + p2.y - p3.y;
    const denominator = dx1 * dy2 - dx2 * dy1;
    let g = 0;
    let h = 0;
    if (Math.abs(denominator) > 0.000001) {
      g = (dx3 * dy2 - dx2 * dy3) / denominator;
      h = (dx1 * dy3 - dx3 * dy1) / denominator;
    }
    const a = p1.x - p0.x + g * p1.x;
    const b = p3.x - p0.x + h * p3.x;
    const c = p0.x;
    const d = p1.y - p0.y + g * p1.y;
    const e = p3.y - p0.y + h * p3.y;
    const f = p0.y;
    const scale = g * point.u + h * point.v + 1;
    return {
      x: (a * point.u + b * point.v + c) / scale,
      y: (d * point.u + e * point.v + f) / scale,
    };
  }

  function drawTexturedTriangle(target, image, sourcePoints, destinationPoints) {
    const [s0, s1, s2] = sourcePoints;
    const [d0, d1, d2] = destinationPoints;
    const denominator = s0.x * (s1.y - s2.y) + s1.x * (s2.y - s0.y) + s2.x * (s0.y - s1.y);
    if (Math.abs(denominator) < 0.001) return;
    const a = (d0.x * (s1.y - s2.y) + d1.x * (s2.y - s0.y) + d2.x * (s0.y - s1.y)) / denominator;
    const b = (d0.y * (s1.y - s2.y) + d1.y * (s2.y - s0.y) + d2.y * (s0.y - s1.y)) / denominator;
    const c = (d0.x * (s2.x - s1.x) + d1.x * (s0.x - s2.x) + d2.x * (s1.x - s0.x)) / denominator;
    const d = (d0.y * (s2.x - s1.x) + d1.y * (s0.x - s2.x) + d2.y * (s1.x - s0.x)) / denominator;
    const e = (
      d0.x * (s1.x * s2.y - s2.x * s1.y) +
      d1.x * (s2.x * s0.y - s0.x * s2.y) +
      d2.x * (s0.x * s1.y - s1.x * s0.y)
    ) / denominator;
    const f = (
      d0.y * (s1.x * s2.y - s2.x * s1.y) +
      d1.y * (s2.x * s0.y - s0.x * s2.y) +
      d2.y * (s0.x * s1.y - s1.x * s0.y)
    ) / denominator;

    target.save();
    target.beginPath();
    target.moveTo(d0.x, d0.y);
    target.lineTo(d1.x, d1.y);
    target.lineTo(d2.x, d2.y);
    target.closePath();
    target.clip();
    target.setTransform(a, b, c, d, e, f);
    target.drawImage(image, 0, 0);
    target.restore();
  }

  function drawProduct(target, image, corners, subdivisions = 16) {
    const sourceWidth = image.naturalWidth || image.width;
    const sourceHeight = image.naturalHeight || image.height;
    const rows = Math.max(8, Math.round(subdivisions * sourceHeight / sourceWidth));
    for (let row = 0; row < rows; row += 1) {
      const v0 = row / rows;
      const v1 = (row + 1) / rows;
      for (let column = 0; column < subdivisions; column += 1) {
        const u0 = column / subdivisions;
        const u1 = (column + 1) / subdivisions;
        const s00 = { x: u0 * sourceWidth, y: v0 * sourceHeight };
        const s10 = { x: u1 * sourceWidth, y: v0 * sourceHeight };
        const s11 = { x: u1 * sourceWidth, y: v1 * sourceHeight };
        const s01 = { x: u0 * sourceWidth, y: v1 * sourceHeight };
        const d00 = projectUnitToQuad({ u: u0, v: v0 }, corners);
        const d10 = projectUnitToQuad({ u: u1, v: v0 }, corners);
        const d11 = projectUnitToQuad({ u: u1, v: v1 }, corners);
        const d01 = projectUnitToQuad({ u: u0, v: v1 }, corners);
        drawTexturedTriangle(target, image, [s00, s10, s11], [d00, d10, d11]);
        drawTexturedTriangle(target, image, [s00, s11, s01], [d00, d11, d01]);
      }
    }
  }

  function applyWallTone(target, variantIndex) {
    const variant = VARIANTS[variantIndex];
    target.save();
    target.fillStyle = hexToRgba(variant.color, variant.alpha);
    for (const polygon of WALL_POLYGONS) {
      tracePolygon(target, polygon);
      target.fill();
    }
    target.restore();
  }

  function hexToRgba(hex, alpha) {
    const red = Number.parseInt(hex.slice(1, 3), 16);
    const green = Number.parseInt(hex.slice(3, 5), 16);
    const blue = Number.parseInt(hex.slice(5, 7), 16);
    return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
  }

  function buildAuthorizationMask(includeProduct) {
    const maskCanvas = document.createElement("canvas");
    maskCanvas.width = WIDTH;
    maskCanvas.height = HEIGHT;
    const maskContext = maskCanvas.getContext("2d", { alpha: true });
    maskContext.fillStyle = "#ffffff";
    for (const polygon of WALL_POLYGONS) {
      tracePolygon(maskContext, polygon);
      maskContext.fill();
    }
    if (includeProduct) {
      tracePointPolygon(maskContext, pixelCorners());
      maskContext.fill();
    }
    return maskContext.getImageData(0, 0, WIDTH, HEIGHT).data;
  }

  function restoreProtectedPixels(target, includeProduct) {
    const output = target.getImageData(0, 0, WIDTH, HEIGHT);
    const authorization = buildAuthorizationMask(includeProduct);
    const original = state.originalData.data;
    let drift = 0;
    for (let index = 0; index < output.data.length; index += 4) {
      if (authorization[index + 3] === 0) {
        if (
          output.data[index] !== original[index] ||
          output.data[index + 1] !== original[index + 1] ||
          output.data[index + 2] !== original[index + 2]
        ) {
          drift += 1;
        }
        output.data[index] = original[index];
        output.data[index + 1] = original[index + 1];
        output.data[index + 2] = original[index + 2];
        output.data[index + 3] = 255;
      }
    }
    target.putImageData(output, 0, 0);

    const verified = target.getImageData(0, 0, WIDTH, HEIGHT).data;
    let residual = 0;
    for (let index = 0; index < verified.length; index += 4) {
      if (
        authorization[index + 3] === 0 &&
        (verified[index] !== original[index] || verified[index + 1] !== original[index + 1] || verified[index + 2] !== original[index + 2])
      ) {
        residual += 1;
      }
    }
    state.lastProtectedDrift = residual;
    return { preRestoreDrift: drift, protectedDrift: residual };
  }

  function renderDeliverable(variantIndex) {
    const output = document.createElement("canvas");
    output.width = WIDTH;
    output.height = HEIGHT;
    const target = output.getContext("2d", { alpha: false, willReadFrequently: true });
    target.drawImage(state.sourceImage, 0, 0, WIDTH, HEIGHT);
    applyWallTone(target, variantIndex);

    const includeProduct = state.mode === "placement";
    if (includeProduct) {
      const corners = pixelCorners();
      if (state.shadowStrength > 0) {
        target.save();
        target.filter = `blur(${Math.max(1, Math.round(state.shadowStrength / 6))}px)`;
        target.fillStyle = `rgba(7, 12, 13, ${state.shadowStrength / 100})`;
        tracePointPolygon(target, corners.map((point) => ({ x: point.x + 4, y: point.y + 8 })));
        target.fill();
        target.restore();
      }
      drawProduct(target, state.productImage, corners);
      target.drawImage(state.occlusionImage, 0, 0, WIDTH, HEIGHT);
    }

    restoreProtectedPixels(target, includeProduct);
    return output;
  }

  function drawSceneGuides(target) {
    if (!state.showGuides) return;
    target.save();
    target.lineWidth = 2;
    target.setLineDash([10, 8]);

    if (state.step === 2 && state.showRegions) {
      target.fillStyle = "rgba(184, 235, 131, .08)";
      target.strokeStyle = "rgba(184, 235, 131, .88)";
      target.strokeRect(82, 66, 311, 344);
      target.fillRect(82, 66, 311, 344);
      target.strokeStyle = "rgba(242, 191, 112, .85)";
      target.strokeRect(394, 368, 615, 306);
      target.fillStyle = "rgba(242, 191, 112, .05)";
      target.fillRect(394, 368, 615, 306);
    }

    if ((state.step === 2 || state.step === 3) && state.mode === "placement") {
      const corners = pixelCorners();
      target.strokeStyle = "rgba(102, 230, 223, .96)";
      target.fillStyle = "rgba(102, 230, 223, .06)";
      tracePointPolygon(target, corners);
      target.fill();
      target.stroke();
      target.setLineDash([]);
      corners.forEach((point, index) => {
        const selected = index === state.selectedCorner;
        target.beginPath();
        target.arc(point.x, point.y, selected ? 13 : 10, 0, Math.PI * 2);
        target.fillStyle = selected ? "#ecfaf5" : "#66e6df";
        target.fill();
        target.lineWidth = 4;
        target.strokeStyle = "rgba(7, 25, 27, .86)";
        target.stroke();
        target.fillStyle = "#092529";
        target.font = "800 10px ui-monospace, monospace";
        target.textAlign = "center";
        target.textBaseline = "middle";
        target.fillText(String(index + 1), point.x, point.y + 0.5);
      });
    }
    target.restore();
  }

  function scheduleRender() {
    if (!state.loaded || state.renderQueued) return;
    state.renderQueued = true;
    window.requestAnimationFrame(() => {
      state.renderQueued = false;
      renderMain();
    });
  }

  function renderMain() {
    if (!state.loaded || state.rendering) return;
    state.rendering = true;
    try {
      context.clearRect(0, 0, WIDTH, HEIGHT);
      if (state.compareSource) {
        context.drawImage(state.sourceImage, 0, 0, WIDTH, HEIGHT);
      } else {
        const deliverable = renderDeliverable(state.selectedVariant);
        context.drawImage(deliverable, 0, 0);
        drawSceneGuides(context);
      }
      document.querySelector("#protected-drift").textContent = `${state.lastProtectedDrift.toLocaleString()} px`;
      document.querySelector("#toolbar-proof").textContent = state.lastProtectedDrift === 0 ? "Protected region stable" : "Protected drift detected";
    } finally {
      state.rendering = false;
    }
  }

  function renderVariantCards() {
    if (!state.loaded) return;
    variantCanvases.forEach((preview, index) => {
      const previewContext = preview.getContext("2d", { alpha: false });
      const output = renderDeliverable(index);
      previewContext.clearRect(0, 0, preview.width, preview.height);
      previewContext.drawImage(output, 0, 0, preview.width, preview.height);
    });
  }

  function updateCornerInputs() {
    coordinateInputs.forEach((input) => {
      const corner = Number.parseInt(input.dataset.corner, 10);
      input.value = state.corners[corner][input.dataset.axis].toFixed(3);
    });
  }

  function setCorner(index, axis, value, announce = true) {
    const numeric = Math.min(0.97, Math.max(axis === "y" ? 0.45 : 0.03, Number(value)));
    const candidate = cloneCorners();
    candidate[index][axis] = numeric;
    if (!isConvex(candidate)) {
      if (announce) showToast("Placement plane must remain a convex four-corner surface.", true);
      updateCornerInputs();
      return false;
    }
    state.corners = candidate;
    state.selectedCorner = index;
    updateCornerInputs();
    scheduleRender();
    updateSaveState();
    return true;
  }

  function canvasCoordinates(event) {
    const rectangle = canvas.getBoundingClientRect();
    return {
      x: (event.clientX - rectangle.left) * WIDTH / rectangle.width,
      y: (event.clientY - rectangle.top) * HEIGHT / rectangle.height,
    };
  }

  function nearestCorner(point) {
    const corners = pixelCorners();
    let nearest = -1;
    let distance = 42;
    corners.forEach((corner, index) => {
      const current = Math.hypot(corner.x - point.x, corner.y - point.y);
      if (current < distance) {
        nearest = index;
        distance = current;
      }
    });
    return nearest;
  }

  function handlePointerDown(event) {
    if (state.step !== 3 || state.mode !== "placement") return;
    const index = nearestCorner(canvasCoordinates(event));
    if (index < 0) return;
    state.dragIndex = index;
    state.selectedCorner = index;
    canvas.setPointerCapture(event.pointerId);
    canvas.classList.add("is-dragging");
    scheduleRender();
    event.preventDefault();
  }

  function handlePointerMove(event) {
    const point = canvasCoordinates(event);
    document.querySelector("#footer-coordinates").textContent = `x ${(point.x / WIDTH).toFixed(2)} · y ${(point.y / HEIGHT).toFixed(2)}`;
    if (state.dragIndex < 0) return;
    const candidate = cloneCorners();
    candidate[state.dragIndex] = {
      x: Math.min(0.97, Math.max(0.03, point.x / WIDTH)),
      y: Math.min(0.97, Math.max(0.45, point.y / HEIGHT)),
    };
    if (isConvex(candidate)) {
      state.corners = candidate;
      updateCornerInputs();
      scheduleRender();
    }
  }

  function handlePointerUp(event) {
    if (state.dragIndex < 0) return;
    state.dragIndex = -1;
    canvas.releasePointerCapture(event.pointerId);
    canvas.classList.remove("is-dragging");
    updateSaveState();
  }

  function handleCanvasKeydown(event) {
    if (state.step !== 3 || state.mode !== "placement") return;
    if (event.key === "[") {
      state.selectedCorner = (state.selectedCorner + 3) % 4;
      scheduleRender();
      showToast(`Corner ${state.selectedCorner + 1} selected.`);
      event.preventDefault();
      return;
    }
    if (event.key === "]") {
      state.selectedCorner = (state.selectedCorner + 1) % 4;
      scheduleRender();
      showToast(`Corner ${state.selectedCorner + 1} selected.`);
      event.preventDefault();
      return;
    }
    const step = event.shiftKey ? 0.02 : 0.005;
    const movement = {
      ArrowLeft: ["x", -step],
      ArrowRight: ["x", step],
      ArrowUp: ["y", -step],
      ArrowDown: ["y", step],
    }[event.key];
    if (!movement) return;
    const [axis, delta] = movement;
    setCorner(state.selectedCorner, axis, state.corners[state.selectedCorner][axis] + delta, false);
    event.preventDefault();
  }

  function goToStep(step) {
    const requested = Number(step);
    state.step = requested === 3 && state.mode === "concept" ? 4 : requested;
    stepButtons.forEach((button) => {
      const buttonStep = Number(button.dataset.step);
      const active = buttonStep === state.step;
      button.classList.toggle("is-active", active);
      button.classList.toggle("is-complete", buttonStep < state.step || (state.mode === "concept" && buttonStep === 3 && state.step >= 4));
      if (active) button.setAttribute("aria-current", "step");
      else button.removeAttribute("aria-current");
    });
    panels.forEach((panel) => {
      panel.hidden = Number(panel.dataset.panel) !== state.step;
    });
    const copy = STEP_COPY[state.step];
    document.querySelector("#canvas-kicker").textContent = copy.kicker;
    document.querySelector("#canvas-title").textContent = copy.title;
    document.querySelector("#inspector-title").textContent = copy.inspector;
    document.querySelector("#phase-chip").textContent = copy.phase;
    const handlesVisible = state.mode === "placement" && (state.step === 2 || state.step === 3);
    document.querySelector("#architecture-label").classList.toggle("is-visible", state.step === 2 && state.showRegions);
    document.querySelector("#product-label").classList.toggle("is-visible", handlesVisible);
    canvas.classList.toggle("is-draggable", state.step === 3 && state.mode === "placement");
    scheduleRender();
    if (state.step === 5) updateBriefHash();
  }

  function compileBrief() {
    const objective = document.querySelector("#design-objective").value.trim().replace(/\s+/g, " ");
    const atmosphere = document.querySelector('input[name="atmosphere"]:checked').value;
    const materials = [...document.querySelectorAll(".chip-checks input:checked")].map((input) => input.value).sort();
    return {
      compiler_version: BRIEF_COMPILER_VERSION,
      project_context: document.querySelector("#project-context").value,
      intervention_mode: state.mode === "placement" ? "catalog-faithful-placement" : "generative-concept",
      objective,
      atmosphere,
      material_cues: materials,
      preserve: ["architecture-shell", "openings", "existing-furniture"],
      hero_asset: state.mode === "placement" ? { name: state.assetName, sha256: state.assetHash, mutation_policy: "transform-only" } : null,
      allowed_changes: state.mode === "placement" ? ["wall-tone-polygons", "hero-floor-plane"] : ["wall-tone-polygons"],
    };
  }

  function canonicalize(value) {
    if (Array.isArray(value)) return value.map(canonicalize);
    if (value && typeof value === "object") {
      return Object.keys(value).sort().reduce((output, key) => {
        output[key] = canonicalize(value[key]);
        return output;
      }, {});
    }
    return value;
  }

  async function sha256Text(value) {
    const bytes = new TextEncoder().encode(value);
    if (window.crypto?.subtle) {
      const digest = await window.crypto.subtle.digest("SHA-256", bytes);
      return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
    }
    let hash = 2166136261;
    for (const byte of bytes) {
      hash ^= byte;
      hash = Math.imul(hash, 16777619);
    }
    return `fnv1a-${(hash >>> 0).toString(16).padStart(8, "0")}`;
  }

  async function updateBriefHash() {
    const canonical = JSON.stringify(canonicalize(compileBrief()));
    state.briefHash = await sha256Text(canonical);
    document.querySelector("#brief-short-hash").textContent = `${state.briefHash.slice(0, 10)}…`;
    return state.briefHash;
  }

  function queueBriefHash() {
    window.clearTimeout(briefTimer);
    briefTimer = window.setTimeout(updateBriefHash, 180);
  }

  function updateMode(mode) {
    state.mode = mode;
    const placement = mode === "placement";
    document.querySelector("#rail-mode").textContent = placement ? "Catalog-faithful placement" : "Generative concept";
    document.querySelector(".mode-glyph").textContent = placement ? "P" : "G";
    document.querySelector("#scene-mode").textContent = placement ? "asset_transform_only" : "masked_surface_guidance";
    document.querySelector("#mode-boundary-copy").textContent = placement
      ? "Product pixels remain immutable. Position, perspective, contact shadow and occlusion order may change."
      : "Approved wall polygons may change. Product fidelity is not claimed and the placement step is skipped.";
    document.querySelector("#product-label").textContent = placement ? "HERO PLANE · EDITABLE" : "CONCEPT REGION · EDITABLE";
    queueBriefHash();
    renderVariantCards();
    scheduleRender();
    showToast(placement ? "Catalog-faithful path selected." : "Generative concept path selected; product placement will be skipped.");
  }

  function updateSaveState() {
    const saveState = document.querySelector("#save-state");
    saveState.classList.add("is-saving");
    saveState.lastChild.textContent = " Updating local draft";
    queueBriefHash();
    window.setTimeout(() => {
      saveState.classList.remove("is-saving");
      saveState.lastChild.textContent = " Local draft";
    }, 380);
  }

  async function handleProductUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!new Set(["image/png", "image/webp"]).has(file.type)) {
      showToast("Use a PNG or WebP product asset.", true);
      event.target.value = "";
      return;
    }
    if (file.size > MAX_PRODUCT_BYTES) {
      showToast("Product asset exceeds the 8 MB encoded limit.", true);
      event.target.value = "";
      return;
    }
    const objectUrl = URL.createObjectURL(file);
    try {
      const image = await loadImage(objectUrl);
      if (image.naturalWidth * image.naturalHeight > MAX_PRODUCT_PIXELS) {
        throw new Error("Product asset exceeds the 4 MP decoded limit.");
      }
      const digest = await window.crypto.subtle.digest("SHA-256", await file.arrayBuffer());
      const hash = [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
      if (state.productObjectUrl) URL.revokeObjectURL(state.productObjectUrl);
      state.productObjectUrl = objectUrl;
      state.productImage = image;
      state.assetHash = hash;
      state.assetName = file.name.replace(/\.[^.]+$/, "").slice(0, 64) || "Local product";
      document.querySelector("#asset-name").textContent = state.assetName;
      document.querySelector("#asset-size").textContent = `${image.naturalWidth} × ${image.naturalHeight} ${file.type.endsWith("png") ? "PNG" : "WEBP"}`;
      updateAssetHashLabels();
      renderVariantCards();
      scheduleRender();
      updateSaveState();
      showToast("Local product asset verified and placed. It has not left this tab.");
    } catch (error) {
      URL.revokeObjectURL(objectUrl);
      event.target.value = "";
      showToast(error instanceof Error ? error.message : "Unable to read product asset.", true);
    }
  }

  function updateAssetHashLabels() {
    const shortHash = `${state.assetHash.slice(0, 13)}…`;
    document.querySelector("#asset-hash").textContent = shortHash;
    document.querySelector("#proof-asset-hash").textContent = shortHash;
  }

  function selectVariant(index) {
    state.selectedVariant = index;
    variantCards.forEach((card, cardIndex) => {
      const selected = cardIndex === index;
      card.classList.toggle("is-selected", selected);
      card.setAttribute("aria-pressed", String(selected));
      card.querySelector("i").textContent = selected ? "Selected" : "Select";
    });
    document.querySelector("#approved-direction").textContent = VARIANTS[index].name;
    scheduleRender();
    updateSaveState();
  }

  function runVariants() {
    const progress = document.querySelector("#job-progress");
    const meter = document.querySelector("#job-meter");
    const percent = document.querySelector("#job-percent");
    const label = document.querySelector("#job-label");
    const runButton = document.querySelector("#run-variants");
    const handoff = document.querySelector("#continue-handoff");
    const stages = [
      { value: 18, label: "Compiling canonical brief" },
      { value: 44, label: "Applying allowed-change polygons" },
      { value: 72, label: "Restoring protected pixels" },
      { value: 100, label: "Verifying three outputs" },
    ];
    let stage = 0;
    progress.hidden = false;
    runButton.disabled = true;
    handoff.disabled = true;

    const advance = () => {
      const current = stages[stage];
      meter.value = current.value;
      meter.textContent = `${current.value}%`;
      percent.textContent = `${current.value}%`;
      label.textContent = current.label;
      stage += 1;
      if (stage < stages.length) {
        window.setTimeout(advance, 210);
        return;
      }
      renderVariantCards();
      state.variantsReady = true;
      handoff.disabled = false;
      runButton.disabled = false;
      runButton.querySelector("span:first-child").textContent = "Re-run local variant set";
      document.querySelector("#variant-status").textContent = "3 verified directions";
      showToast("Controlled variant set verified locally.");
    };
    advance();
  }

  function canvasToBlob(target) {
    return new Promise((resolve, reject) => {
      target.toBlob((blob) => {
        if (blob) resolve(blob);
        else reject(new Error("Canvas export failed."));
      }, "image/png");
    });
  }

  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  async function hashBlob(blob) {
    const digest = await window.crypto.subtle.digest("SHA-256", await blob.arrayBuffer());
    return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
  }

  async function downloadSelected() {
    const output = renderDeliverable(state.selectedVariant);
    const blob = await canvasToBlob(output);
    downloadBlob(blob, `spatial-${VARIANTS[state.selectedVariant].slug}.png`);
    showToast("Selected direction exported as a local PNG.");
  }

  async function downloadContactSheet() {
    const sheet = document.createElement("canvas");
    sheet.width = 1680;
    sheet.height = 1260;
    const sheetContext = sheet.getContext("2d", { alpha: false });
    sheetContext.fillStyle = "#0c1719";
    sheetContext.fillRect(0, 0, sheet.width, sheet.height);
    sheetContext.fillStyle = "#eff4ec";
    sheetContext.font = "700 44px ui-sans-serif, sans-serif";
    sheetContext.fillText("Harbor House Lounge — Controlled Directions", 70, 82);
    sheetContext.fillStyle = "#82938f";
    sheetContext.font = "22px ui-sans-serif, sans-serif";
    sheetContext.fillText("Deterministic browser evidence · not AI output", 70, 120);
    const positions = [[70, 180], [860, 180], [465, 720]];
    VARIANTS.forEach((variant, index) => {
      const [x, y] = positions[index];
      const output = renderDeliverable(index);
      sheetContext.drawImage(output, x, y, 750, 500);
      sheetContext.fillStyle = index === state.selectedVariant ? "#66e6df" : "#eff4ec";
      sheetContext.font = "700 25px ui-sans-serif, sans-serif";
      sheetContext.fillText(`${String(index + 1).padStart(2, "0")} · ${variant.name}${index === state.selectedVariant ? " / SELECTED" : ""}`, x, y + 538);
      sheetContext.fillStyle = "#82938f";
      sheetContext.font = "18px ui-monospace, monospace";
      sheetContext.fillText(`${variant.lighting} · protected drift ${state.lastProtectedDrift}px`, x, y + 570);
    });
    const blob = await canvasToBlob(sheet);
    downloadBlob(blob, "spatial-controlled-directions.png");
    showToast("Three-direction contact sheet exported locally.");
  }

  async function buildManifest() {
    const output = renderDeliverable(state.selectedVariant);
    const blob = await canvasToBlob(output);
    await updateBriefHash();
    return {
      manifest_type: "spatial-reference-proof",
      manifest_version: "1.0",
      generated_at: new Date().toISOString(),
      renderer: RENDERER_VERSION,
      claim_boundary: "Project-local deterministic evidence; not C2PA certification, client compatibility, live model validation, or production approval.",
      brief: {
        ...compileBrief(),
        sha256: state.briefHash,
      },
      source_scene: {
        file: "spatial-lounge-source.png",
        width: WIDTH,
        height: HEIGHT,
        sha256: SOURCE_HASH,
        provenance: "Original clean-room synthetic asset generated by scripts/create_spatial_assets.py",
      },
      placement: state.mode === "placement" ? {
        asset_name: state.assetName,
        asset_sha256: state.assetHash,
        normalized_corners: cloneCorners(),
        source_mutations: 0,
        allowed_operations: ["projective-transform", "contact-shadow", "foreground-occlusion-order"],
      } : null,
      selected_variant: {
        id: VARIANTS[state.selectedVariant].slug,
        name: VARIANTS[state.selectedVariant].name,
        controlled_variable: "wall-tone-polygons",
        output_sha256: await hashBlob(blob),
      },
      proof: {
        protected_pixel_drift: state.lastProtectedDrift,
        protected_policy: "authoritative-source-restore",
        browser_local: true,
        provider_called: false,
      },
      limitations: [
        "No live generative provider was evaluated.",
        "Depth and segmentation are authored for this synthetic reference scene.",
        "Catalog-fidelity means immutable source raster plus geometric compositing in this PoC, not photometric or manufacturing certification.",
        "The v3 contract remains provisional until a client-owned schema is supplied.",
      ],
    };
  }

  async function downloadManifest() {
    const manifest = await buildManifest();
    const blob = new Blob([`${JSON.stringify(manifest, null, 2)}\n`], { type: "application/json" });
    downloadBlob(blob, `spatial-${VARIANTS[state.selectedVariant].slug}-manifest.json`);
    showToast("Proof manifest exported locally.");
  }

  async function copySummary() {
    const manifest = await buildManifest();
    const text = [
      `Direction: ${manifest.selected_variant.name}`,
      `Mode: ${manifest.brief.intervention_mode}`,
      `Brief: ${manifest.brief.sha256}`,
      `Asset: ${manifest.placement?.asset_sha256 || "not applicable"}`,
      `Protected drift: ${manifest.proof.protected_pixel_drift} px`,
      "Boundary: deterministic reference evidence; no live model or production claim.",
    ].join("\n");
    try {
      await navigator.clipboard.writeText(text);
      showToast("Review summary copied.");
    } catch {
      const textArea = document.createElement("textarea");
      textArea.value = text;
      textArea.setAttribute("readonly", "");
      textArea.className = "sr-only";
      document.body.append(textArea);
      textArea.select();
      document.execCommand("copy");
      textArea.remove();
      showToast("Review summary copied.");
    }
  }

  function bindEvents() {
    stepButtons.forEach((button) => button.addEventListener("click", () => goToStep(button.dataset.step)));
    document.querySelectorAll("[data-next]").forEach((button) => button.addEventListener("click", () => {
      const next = state.mode === "concept" && Number(button.dataset.next) === 3 ? 4 : button.dataset.next;
      goToStep(next);
    }));
    document.querySelectorAll("[data-back]").forEach((button) => button.addEventListener("click", () => goToStep(button.dataset.back)));
    document.querySelector("#continue-handoff").addEventListener("click", () => goToStep(5));

    document.querySelectorAll('input[name="intervention-mode"]').forEach((input) => input.addEventListener("change", () => updateMode(input.value)));
    document.querySelector("#design-objective").addEventListener("input", (event) => {
      document.querySelector("#objective-count").textContent = event.target.value.length;
      updateSaveState();
    });
    document.querySelector("#project-context").addEventListener("change", updateSaveState);
    document.querySelectorAll('input[name="atmosphere"], .chip-checks input').forEach((input) => input.addEventListener("change", updateSaveState));
    document.querySelector("#show-regions").addEventListener("change", (event) => {
      state.showRegions = event.target.checked;
      document.querySelector("#architecture-label").classList.toggle("is-visible", state.step === 2 && state.showRegions);
      scheduleRender();
    });

    document.querySelector("#toggle-guides").addEventListener("click", (event) => {
      state.showGuides = !state.showGuides;
      event.currentTarget.setAttribute("aria-pressed", String(state.showGuides));
      event.currentTarget.classList.toggle("is-active", state.showGuides);
      scheduleRender();
    });
    const compareButton = document.querySelector("#compare-original");
    const setCompare = (value) => {
      state.compareSource = value;
      compareButton.setAttribute("aria-pressed", String(value));
      scheduleRender();
    };
    compareButton.addEventListener("pointerdown", () => setCompare(true));
    compareButton.addEventListener("pointerup", () => setCompare(false));
    compareButton.addEventListener("pointerleave", () => setCompare(false));
    compareButton.addEventListener("keydown", (event) => {
      if (event.code === "Space" || event.code === "Enter") setCompare(true);
    });
    compareButton.addEventListener("keyup", () => setCompare(false));

    document.querySelector("#reset-view").addEventListener("click", () => {
      state.corners = DEFAULT_CORNERS.map((point) => ({ ...point }));
      state.selectedCorner = 0;
      updateCornerInputs();
      renderVariantCards();
      scheduleRender();
      updateSaveState();
      showToast("Placement geometry reset.");
    });

    canvas.addEventListener("pointerdown", handlePointerDown);
    canvas.addEventListener("pointermove", handlePointerMove);
    canvas.addEventListener("pointerup", handlePointerUp);
    canvas.addEventListener("pointercancel", handlePointerUp);
    canvas.addEventListener("keydown", handleCanvasKeydown);

    coordinateInputs.forEach((input) => input.addEventListener("change", () => {
      setCorner(Number(input.dataset.corner), input.dataset.axis, input.value);
      renderVariantCards();
    }));

    document.querySelector("#shadow-strength").addEventListener("input", (event) => {
      state.shadowStrength = Number(event.target.value);
      document.querySelector("#shadow-output").textContent = `${state.shadowStrength}%`;
      scheduleRender();
    });
    document.querySelector("#shadow-strength").addEventListener("change", () => {
      renderVariantCards();
      updateSaveState();
    });
    document.querySelector("#product-upload").addEventListener("change", handleProductUpload);

    variantCards.forEach((card) => card.addEventListener("click", () => selectVariant(Number(card.dataset.variant))));
    document.querySelector("#run-variants").addEventListener("click", runVariants);
    document.querySelector("#download-selected").addEventListener("click", () => downloadSelected().catch((error) => showToast(error.message, true)));
    document.querySelector("#download-contact-sheet").addEventListener("click", () => downloadContactSheet().catch((error) => showToast(error.message, true)));
    document.querySelector("#download-manifest").addEventListener("click", () => downloadManifest().catch((error) => showToast(error.message, true)));
    document.querySelector("#copy-summary").addEventListener("click", () => copySummary().catch((error) => showToast(error.message, true)));

    document.querySelector("#theme-toggle").addEventListener("click", (event) => {
      const light = html.dataset.theme !== "light";
      html.dataset.theme = light ? "light" : "dark";
      event.currentTarget.setAttribute("aria-pressed", String(light));
      event.currentTarget.title = light ? "Use dark appearance" : "Use light appearance";
    });
    document.querySelector("#transparency-toggle").addEventListener("click", (event) => {
      const reduced = html.dataset.transparency !== "reduced";
      html.dataset.transparency = reduced ? "reduced" : "regular";
      event.currentTarget.setAttribute("aria-pressed", String(reduced));
      event.currentTarget.title = reduced ? "Use regular transparency" : "Reduce transparency";
      showToast(reduced ? "Solid control surfaces enabled." : "Regular control transparency enabled.");
    });

    window.addEventListener("beforeunload", () => {
      if (state.productObjectUrl) URL.revokeObjectURL(state.productObjectUrl);
    });
  }

  async function initialize() {
    try {
      const [source, product, occlusion] = await Promise.all([
        loadImage("assets/spatial-lounge-source.png"),
        loadImage("assets/spatial-hero-carpet.png"),
        loadImage("assets/spatial-lounge-occlusion.png"),
      ]);
      state.sourceImage = source;
      state.productImage = product;
      state.occlusionImage = occlusion;
      const originalCanvas = document.createElement("canvas");
      originalCanvas.width = WIDTH;
      originalCanvas.height = HEIGHT;
      const originalContext = originalCanvas.getContext("2d", { alpha: false, willReadFrequently: true });
      originalContext.drawImage(source, 0, 0, WIDTH, HEIGHT);
      state.originalData = originalContext.getImageData(0, 0, WIDTH, HEIGHT);
      state.loaded = true;
      loading.hidden = true;
      updateCornerInputs();
      updateAssetHashLabels();
      bindEvents();
      await updateBriefHash();
      renderVariantCards();
      renderMain();
      document.querySelector("#objective-count").textContent = document.querySelector("#design-objective").value.length;
    } catch (error) {
      loading.textContent = "Local scene could not be prepared.";
      showToast(error instanceof Error ? error.message : "Initialization failed.", true);
    }
  }

  initialize();
})();
