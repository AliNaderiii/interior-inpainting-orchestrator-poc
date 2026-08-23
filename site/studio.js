"use strict";

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const SAMPLE_IMAGE = "assets/before-synthetic.png";
const SAMPLE_MASK = "assets/mask-white-edit-synthetic.png";
const MAX_BYTES = 12 * 1024 * 1024;
const MAX_PIXELS = 4_000_000;
const SUPPORTED_TYPES = new Set(["image/png", "image/jpeg", "image/webp"]);
const STYLE_PROFILES = Object.freeze({
  "modern-calm": { label: "Modern calm", rgb: [93, 139, 122] },
  "warm-minimal": { label: "Warm minimal", rgb: [158, 124, 88] },
  japandi: { label: "Japandi", rgb: [126, 125, 95] },
  scandinavian: { label: "Scandinavian", rgb: [184, 194, 184] },
  contemporary: { label: "Contemporary", rgb: [100, 111, 116] },
  industrial: { label: "Industrial", rgb: [80, 78, 74] },
});
const ROOM_LABELS = Object.freeze({
  "living-room": "Living room",
  bedroom: "Bedroom",
  "dining-room": "Dining room",
  "home-office": "Home office",
  kitchen: "Kitchen",
});

const state = {
  source: null,
  sourceUrl: null,
  maskUrl: null,
  maskCanvas: document.createElement("canvas"),
  tool: "brush",
  brushSize: 42,
  drawing: false,
  lastPoint: null,
  coverage: 0,
  activeStep: 1,
  intent: null,
  compiledPrompt: "",
  intentHash: "",
  downloadUrl: null,
};

function loadImage(source) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.decoding = "async";
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("The image could not be decoded."));
    image.src = source;
  });
}

function formatNumber(value) {
  return new Intl.NumberFormat("en-US").format(value);
}

function titleFromSlug(value) {
  return value.replaceAll("-", " ").replace(/^./, (letter) => letter.toUpperCase());
}

function initTheme() {
  const root = document.documentElement;
  const toggle = $("[data-theme-toggle]");
  let theme = "dark";
  try {
    theme = localStorage.getItem("poc-theme") ||
      (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
  } catch {
    theme = "dark";
  }
  root.dataset.theme = theme;
  toggle?.addEventListener("click", () => {
    root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
    try {
      localStorage.setItem("poc-theme", root.dataset.theme);
    } catch {
      // Persistence is optional.
    }
  });
}

function selectedValues(containerSelector) {
  return $$(`${containerSelector} button.is-selected`).map((button) => button.dataset.value);
}

function selectedColors() {
  return $$("[data-palette-row] button.is-selected").map((button) => button.dataset.color);
}

function currentStyle() {
  return $("input[name='style']:checked")?.value || "modern-calm";
}

function canonicalize(value) {
  if (Array.isArray(value)) return `[${value.map((item) => canonicalize(item)).join(",")}]`;
  if (value !== null && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalize(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

async function hashText(value) {
  const bytes = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((part) => part.toString(16).padStart(2, "0")).join("");
}

function compileIntent() {
  const style = currentStyle();
  const room = $("[data-room]").value;
  const palette = selectedColors();
  const materials = selectedValues("[data-materials]");
  const preserve = selectedValues("[data-preserve]");
  const notes = $("[data-notes]").value.trim().replace(/\s+/g, " ");
  const segments = [`Restyle the authorized region of this ${room} in a ${style} direction`];
  if (palette.length) segments.push(`Use a restrained palette centered on ${palette.join(", ")}`);
  if (materials.length) segments.push(`Prefer these material cues: ${materials.join(", ")}`);
  if (preserve.length) {
    segments.push(`Keep the visual identity of these elements where they intersect the edit: ${preserve.join(", ")}`);
  }
  if (notes) segments.push(`Additional design direction: ${notes}`);
  segments.push("Generate a coherent interior finish only; the hard mask is the final geometric authority");

  state.intent = {
    style,
    room_type: room,
    palette,
    materials,
    preserve_semantics: preserve,
    notes: notes || null,
  };
  state.compiledPrompt = `${segments.join(". ")}.`;
  const title = `${STYLE_PROFILES[style].label} · ${ROOM_LABELS[room]}`;
  $("[data-intent-title]").textContent = title;
  $("[data-compiled-prompt]").textContent = state.compiledPrompt;
  $("[data-segment-count]").textContent = `${segments.length} explainable segments`;
  $("[data-review-title]").textContent = title;
  $("[data-review-prompt]").textContent = state.compiledPrompt;
  $("[data-notes-count]").value = `${notes.length} / 240`;

  const canonical = canonicalize(state.intent);
  const pendingCanonical = canonical;
  hashText(canonical).then((hash) => {
    if (canonicalize(state.intent) !== pendingCanonical) return;
    state.intentHash = hash;
    $("[data-intent-hash]").textContent = `intent / ${hash.slice(0, 12)}`;
    $("[data-review-hash]").textContent = hash.slice(0, 12);
    updatePayload();
  });
  invalidateResult();
}

function toggleChip(button) {
  const selected = !button.classList.contains("is-selected");
  const materialContainer = button.closest("[data-materials]");
  if (selected && materialContainer && $$(`button.is-selected`, materialContainer).length >= 4) {
    $("[data-material-message]").textContent = "Four material cues is the contract maximum.";
    return;
  }
  button.classList.toggle("is-selected", selected);
  button.setAttribute("aria-pressed", String(selected));
  if (materialContainer) {
    $("[data-material-message]").textContent = "Select up to four controlled material cues.";
  }
  compileIntent();
}

function initIntentControls() {
  $$(`${"[data-materials], [data-preserve]"}`).forEach((container) => {
    $$(`button`, container).forEach((button) => button.addEventListener("click", () => toggleChip(button)));
  });
  $$(`[data-palette-row] button`).forEach((button) => {
    button.addEventListener("click", () => toggleChip(button));
  });
  $$(`input[name='style']`).forEach((input) => input.addEventListener("change", compileIntent));
  $("[data-room]").addEventListener("change", compileIntent);
  $("[data-notes]").addEventListener("input", compileIntent);
  compileIntent();
}

function updateStep(nextStep) {
  if (nextStep === 3 && state.coverage <= 0) {
    $("[data-editor-message]").textContent = "Paint or import at least one editable pixel before review.";
    nextStep = 2;
  }
  state.activeStep = nextStep;
  $$(`[data-step-panel]`).forEach((panel) => {
    panel.hidden = Number(panel.dataset.stepPanel) !== nextStep;
  });
  $$(`[data-step-item]`).forEach((item) => {
    const itemStep = Number(item.dataset.stepItem);
    item.classList.toggle("is-active", itemStep === nextStep);
    item.classList.toggle("is-complete", itemStep < nextStep);
    const button = $("button", item);
    if (itemStep === nextStep) button.setAttribute("aria-current", "step");
    else button.removeAttribute("aria-current");
  });
  if (nextStep === 3) {
    updateReview();
    drawSourceOnOutput();
  }
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function initStepper() {
  $$(`[data-step-target], [data-next-step]`).forEach((button) => {
    button.addEventListener("click", () => updateStep(Number(button.dataset.stepTarget || button.dataset.nextStep)));
  });
}

function maskContext() {
  return state.maskCanvas.getContext("2d", { willReadFrequently: true });
}

function editorContext() {
  return $("[data-mask-editor]").getContext("2d", { alpha: false });
}

function renderEditor() {
  if (!state.source) return;
  const canvas = $("[data-mask-editor]");
  const context = editorContext();
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.drawImage(state.source, 0, 0, canvas.width, canvas.height);
  context.drawImage(state.maskCanvas, 0, 0);
}

function updateCoverage() {
  if (!state.maskCanvas.width || !state.maskCanvas.height) return;
  const data = maskContext().getImageData(0, 0, state.maskCanvas.width, state.maskCanvas.height).data;
  let editable = 0;
  for (let index = 3; index < data.length; index += 4) {
    if (data[index] >= 32) editable += 1;
  }
  state.coverage = editable / (state.maskCanvas.width * state.maskCanvas.height);
  $("[data-mask-coverage]").textContent = `${(state.coverage * 100).toFixed(2)}%`;
  $("[data-review-coverage]").textContent = `${(state.coverage * 100).toFixed(2)}%`;
  $("[data-editor-message]").textContent = "";
  updatePayload();
  invalidateResult();
}

async function loadMaskImage(image) {
  if (!state.source) return;
  if (image.naturalWidth !== state.source.naturalWidth || image.naturalHeight !== state.source.naturalHeight) {
    throw new Error("Mask dimensions must match the source image exactly.");
  }
  const temporary = document.createElement("canvas");
  temporary.width = image.naturalWidth;
  temporary.height = image.naturalHeight;
  const temporaryContext = temporary.getContext("2d", { willReadFrequently: true });
  temporaryContext.drawImage(image, 0, 0);
  const maskData = temporaryContext.getImageData(0, 0, temporary.width, temporary.height);
  for (let index = 0; index < maskData.data.length; index += 4) {
    const brightness = (maskData.data[index] + maskData.data[index + 1] + maskData.data[index + 2]) / 3;
    maskData.data[index] = 77;
    maskData.data[index + 1] = 239;
    maskData.data[index + 2] = 165;
    maskData.data[index + 3] = brightness >= 128 ? 158 : 0;
  }
  state.maskCanvas.width = temporary.width;
  state.maskCanvas.height = temporary.height;
  maskContext().putImageData(maskData, 0, 0);
  renderEditor();
  updateCoverage();
}

async function loadSample() {
  const [source, mask] = await Promise.all([loadImage(SAMPLE_IMAGE), loadImage(SAMPLE_MASK)]);
  revokeUrl(state.sourceUrl);
  revokeUrl(state.maskUrl);
  state.sourceUrl = null;
  state.maskUrl = null;
  state.source = source;
  const editor = $("[data-mask-editor]");
  editor.width = source.naturalWidth;
  editor.height = source.naturalHeight;
  $("[data-canvas-size]").textContent = `${source.naturalWidth} × ${source.naturalHeight}`;
  $("[data-studio-image-name]").textContent = "Synthetic sample · 960 × 640";
  $("[data-studio-mask-name]").textContent = "Repository white-edit sample mask";
  await loadMaskImage(mask);
}

function pointFromEvent(event) {
  const canvas = $("[data-mask-editor]");
  const bounds = canvas.getBoundingClientRect();
  return {
    x: (event.clientX - bounds.left) * (canvas.width / bounds.width),
    y: (event.clientY - bounds.top) * (canvas.height / bounds.height),
  };
}

function drawMaskStroke(from, to) {
  const context = maskContext();
  context.save();
  context.lineWidth = state.brushSize;
  context.lineCap = "round";
  context.lineJoin = "round";
  if (state.tool === "erase") {
    context.globalCompositeOperation = "destination-out";
    context.strokeStyle = "rgba(0,0,0,1)";
  } else {
    context.globalCompositeOperation = "source-over";
    context.strokeStyle = "rgba(77,239,165,.62)";
  }
  context.beginPath();
  context.moveTo(from.x, from.y);
  context.lineTo(to.x, to.y);
  context.stroke();
  context.restore();
  renderEditor();
}

function initMaskEditor() {
  const canvas = $("[data-mask-editor]");
  canvas.addEventListener("pointerdown", (event) => {
    state.drawing = true;
    state.lastPoint = pointFromEvent(event);
    canvas.setPointerCapture(event.pointerId);
    drawMaskStroke(state.lastPoint, state.lastPoint);
  });
  canvas.addEventListener("pointermove", (event) => {
    if (!state.drawing || !state.lastPoint) return;
    const next = pointFromEvent(event);
    drawMaskStroke(state.lastPoint, next);
    state.lastPoint = next;
  });
  const finish = () => {
    if (!state.drawing) return;
    state.drawing = false;
    state.lastPoint = null;
    updateCoverage();
  };
  canvas.addEventListener("pointerup", finish);
  canvas.addEventListener("pointercancel", finish);

  $$(`[data-mask-tool]`).forEach((button) => {
    button.addEventListener("click", () => {
      state.tool = button.dataset.maskTool;
      $$(`[data-mask-tool]`).forEach((candidate) => {
        const active = candidate === button;
        candidate.classList.toggle("is-active", active);
        candidate.setAttribute("aria-pressed", String(active));
      });
    });
  });
  $("[data-brush-size]").addEventListener("input", (event) => {
    state.brushSize = Number(event.target.value);
    $("[data-brush-output]").value = `${state.brushSize} px`;
  });
  $("[data-clear-mask]").addEventListener("click", () => {
    maskContext().clearRect(0, 0, state.maskCanvas.width, state.maskCanvas.height);
    renderEditor();
    updateCoverage();
  });
  $("[data-reset-mask]").addEventListener("click", async () => {
    try {
      const sampleMask = await loadImage(SAMPLE_MASK);
      if (state.source?.naturalWidth === 960 && state.source?.naturalHeight === 640) {
        await loadMaskImage(sampleMask);
      } else {
        maskContext().clearRect(0, 0, state.maskCanvas.width, state.maskCanvas.height);
        renderEditor();
        updateCoverage();
        $("[data-editor-message]").textContent = "Custom source retained; mask was cleared.";
      }
    } catch (error) {
      $("[data-editor-message]").textContent = error instanceof Error ? error.message : "Reset failed.";
    }
  });
}

function revokeUrl(url) {
  if (url?.startsWith("blob:")) URL.revokeObjectURL(url);
}

async function imageFromFile(file) {
  if (!SUPPORTED_TYPES.has(file.type)) throw new Error("Choose a PNG, JPEG, or WebP image.");
  if (file.size > MAX_BYTES) throw new Error("Choose a file no larger than 12 MB.");
  const url = URL.createObjectURL(file);
  try {
    const image = await loadImage(url);
    if (image.naturalWidth * image.naturalHeight > MAX_PIXELS) {
      throw new Error("Choose an image no larger than four megapixels.");
    }
    return { image, url };
  } catch (error) {
    URL.revokeObjectURL(url);
    throw error;
  }
}

function initAssetInputs() {
  $("[data-studio-image-upload]").addEventListener("change", async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const loaded = await imageFromFile(file);
      revokeUrl(state.sourceUrl);
      state.sourceUrl = loaded.url;
      state.source = loaded.image;
      const editor = $("[data-mask-editor]");
      editor.width = loaded.image.naturalWidth;
      editor.height = loaded.image.naturalHeight;
      state.maskCanvas.width = loaded.image.naturalWidth;
      state.maskCanvas.height = loaded.image.naturalHeight;
      $("[data-studio-image-name]").textContent = `${file.name} · ${loaded.image.naturalWidth} × ${loaded.image.naturalHeight}`;
      $("[data-studio-mask-name]").textContent = "Draw a mask or import an aligned file";
      $("[data-canvas-size]").textContent = `${loaded.image.naturalWidth} × ${loaded.image.naturalHeight}`;
      renderEditor();
      updateCoverage();
    } catch (error) {
      $("[data-editor-message]").textContent = error instanceof Error ? error.message : "Source load failed.";
      event.target.value = "";
    }
  });
  $("[data-studio-mask-upload]").addEventListener("change", async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const loaded = await imageFromFile(file);
      await loadMaskImage(loaded.image);
      revokeUrl(state.maskUrl);
      state.maskUrl = loaded.url;
      $("[data-studio-mask-name]").textContent = `${file.name} · aligned`;
    } catch (error) {
      $("[data-editor-message]").textContent = error instanceof Error ? error.message : "Mask load failed.";
      event.target.value = "";
    }
  });
}

function updatePayload() {
  if (!state.intent) return;
  const payload = {
    endpoint: "POST /poc/v2/jobs",
    source: "multipart:image",
    mask: "multipart:white-edit-mask",
    intent: state.intent,
    idempotency_key: "studio-demo-<client-generated>",
  };
  $("[data-job-payload]").textContent = JSON.stringify(payload, null, 2);
}

function updateReview() {
  compileIntent();
  $("[data-review-coverage]").textContent = `${(state.coverage * 100).toFixed(2)}%`;
  updatePayload();
}

function drawSourceOnOutput() {
  if (!state.source) return;
  const output = $("[data-studio-output]");
  output.width = state.source.naturalWidth;
  output.height = state.source.naturalHeight;
  output.getContext("2d", { alpha: false }).drawImage(state.source, 0, 0);
}

function resetTimeline() {
  $$(`[data-job-state]`).forEach((item) => item.classList.remove("is-active", "is-complete"));
}

function setTimeline(name) {
  const order = ["queued", "running", "compositing", "succeeded"];
  const activeIndex = order.indexOf(name);
  order.forEach((stateName, index) => {
    const item = $(`[data-job-state='${stateName}']`);
    item.classList.toggle("is-active", index === activeIndex);
    item.classList.toggle("is-complete", index < activeIndex || (name === "succeeded" && index === activeIndex));
  });
}

function invalidateResult() {
  revokeUrl(state.downloadUrl);
  state.downloadUrl = null;
  const download = $("[data-download-studio]");
  if (download) download.disabled = true;
  const empty = $("[data-render-empty]");
  empty?.classList.remove("is-hidden");
  const fields = ["[data-studio-protected]", "[data-studio-drift]", "[data-studio-editable]", "[data-studio-job-id]"];
  fields.forEach((selector) => {
    const element = $(selector);
    if (element) element.textContent = "—";
  });
  const proof = $("[data-render-proof]");
  if (proof) proof.textContent = "Run to calculate byte-level boundary evidence.";
  resetTimeline();
}

function parseHexColor(value) {
  return [1, 3, 5].map((start) => Number.parseInt(value.slice(start, start + 2), 16));
}

function renderDeterministicResult() {
  const width = state.source.naturalWidth;
  const height = state.source.naturalHeight;
  const sourceCanvas = document.createElement("canvas");
  sourceCanvas.width = width;
  sourceCanvas.height = height;
  const sourceContext = sourceCanvas.getContext("2d", { willReadFrequently: true });
  sourceContext.drawImage(state.source, 0, 0);
  const original = sourceContext.getImageData(0, 0, width, height);
  const result = new ImageData(new Uint8ClampedArray(original.data), width, height);
  const mask = maskContext().getImageData(0, 0, width, height).data;
  const profile = STYLE_PROFILES[currentStyle()].rgb;
  const colors = selectedColors();
  const palette = colors.length ? parseHexColor(colors[0]) : profile;
  const target = profile.map((value, index) => Math.round(value * .55 + palette[index] * .45));
  let protectedPixels = 0;
  let changedProtected = 0;
  let editableChanged = 0;

  for (let pixel = 0; pixel < width * height; pixel += 1) {
    const index = pixel * 4;
    if (mask[index + 3] < 32) {
      protectedPixels += 1;
      if (
        result.data[index] !== original.data[index] ||
        result.data[index + 1] !== original.data[index + 1] ||
        result.data[index + 2] !== original.data[index + 2]
      ) changedProtected += 1;
      continue;
    }
    const x = pixel % width;
    const y = Math.floor(pixel / width);
    const weave = ((Math.floor(x / 13) + Math.floor(y / 13)) % 2) * 9;
    const wave = Math.round(12 * Math.sin(x * .031) + 9 * Math.cos(y * .039));
    for (let channel = 0; channel < 3; channel += 1) {
      const styled = Math.max(0, Math.min(255, target[channel] + weave + wave * (channel === 0 ? 1 : .45)));
      result.data[index + channel] = Math.round(original.data[index + channel] * .24 + styled * .76);
    }
    if (
      result.data[index] !== original.data[index] ||
      result.data[index + 1] !== original.data[index + 1] ||
      result.data[index + 2] !== original.data[index + 2]
    ) editableChanged += 1;
  }

  const output = $("[data-studio-output]");
  output.width = width;
  output.height = height;
  output.getContext("2d", { alpha: false }).putImageData(result, 0, 0);
  return { protectedPixels, changedProtected, editableChanged, output };
}

function delay(milliseconds) {
  const duration = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 20 : milliseconds;
  return new Promise((resolve) => window.setTimeout(resolve, duration));
}

async function runStudio() {
  const button = $("[data-run-studio]");
  const message = $("[data-render-message]");
  if (!state.source || state.coverage <= 0) {
    message.textContent = "A source image and non-empty mask are required.";
    return;
  }
  message.textContent = "";
  button.disabled = true;
  $("[data-review-status]").textContent = "job running";
  resetTimeline();
  try {
    setTimeline("queued");
    await delay(230);
    setTimeline("running");
    await delay(300);
    const evidence = renderDeterministicResult();
    setTimeline("compositing");
    await delay(260);
    setTimeline("succeeded");
    const jobId = `demo_${crypto.randomUUID().slice(0, 8)}`;
    $("[data-studio-protected]").textContent = formatNumber(evidence.protectedPixels);
    $("[data-studio-drift]").textContent = formatNumber(evidence.changedProtected);
    $("[data-studio-editable]").textContent = formatNumber(evidence.editableChanged);
    $("[data-studio-job-id]").textContent = jobId;
    $("[data-render-empty]").classList.add("is-hidden");
    $("[data-review-status]").textContent = evidence.changedProtected === 0 ? "invariant passed" : "invariant failed";
    $("[data-render-proof]").textContent = evidence.changedProtected === 0
      ? "PASS · every protected pixel is byte-identical."
      : "FAIL · protected-pixel drift detected.";
    revokeUrl(state.downloadUrl);
    const blob = await new Promise((resolve) => evidence.output.toBlob(resolve, "image/png"));
    if (blob) {
      state.downloadUrl = URL.createObjectURL(blob);
      $("[data-download-studio]").disabled = false;
    }
  } catch (error) {
    message.textContent = error instanceof Error ? error.message : "Local simulation failed.";
    $("[data-review-status]").textContent = "job failed";
  } finally {
    button.disabled = false;
  }
}

function initReviewActions() {
  $("[data-run-studio]").addEventListener("click", runStudio);
  $("[data-download-studio]").addEventListener("click", () => {
    if (!state.downloadUrl) return;
    const link = document.createElement("a");
    link.href = state.downloadUrl;
    link.download = "restyle-studio-boundary-proof-non-ai.png";
    link.click();
  });
  $("[data-copy-payload]").addEventListener("click", async (event) => {
    const button = event.currentTarget;
    try {
      await navigator.clipboard.writeText($("[data-job-payload]").textContent);
      button.textContent = "Copied";
    } catch {
      button.textContent = "Select JSON";
    }
    window.setTimeout(() => { button.textContent = "Copy"; }, 1200);
  });
}

async function boot() {
  initTheme();
  initStepper();
  initIntentControls();
  initMaskEditor();
  initAssetInputs();
  initReviewActions();
  try {
    await loadSample();
  } catch (error) {
    $("[data-editor-message]").textContent = error instanceof Error ? error.message : "Sample load failed.";
  }
}

window.addEventListener("pagehide", () => {
  revokeUrl(state.sourceUrl);
  revokeUrl(state.maskUrl);
  revokeUrl(state.downloadUrl);
});
document.addEventListener("DOMContentLoaded", boot);
