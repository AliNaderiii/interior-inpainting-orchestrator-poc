"use strict";

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const SAMPLE = Object.freeze({
  image: "assets/before-synthetic.png",
  mask: "assets/mask-white-edit-synthetic.png",
  after: "assets/after-deterministic-demo-not-ai.png",
});
const MAX_BROWSER_PIXELS = 4_000_000;
const MAX_BROWSER_BYTES = 12 * 1024 * 1024;
const SUPPORTED_IMAGE_TYPES = new Set(["image/png", "image/jpeg", "image/webp"]);

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

function initTheme() {
  const root = document.documentElement;
  const toggle = $("[data-theme-toggle]");
  let preferred = "dark";
  try {
    preferred = localStorage.getItem("poc-theme") ||
      (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
  } catch {
    preferred = "dark";
  }
  root.dataset.theme = preferred;

  toggle?.addEventListener("click", () => {
    const next = root.dataset.theme === "dark" ? "light" : "dark";
    root.dataset.theme = next;
    try {
      localStorage.setItem("poc-theme", next);
    } catch {
      // Theme persistence is optional when storage is unavailable.
    }
  });
}

function initNavigation() {
  const header = $("[data-header]");
  const toggle = $("[data-nav-toggle]");
  const nav = $("[data-nav]");

  const updateHeader = () => header?.classList.toggle("is-scrolled", window.scrollY > 18);
  updateHeader();
  window.addEventListener("scroll", updateHeader, { passive: true });

  const setNavigationOpen = (open) => {
    toggle?.setAttribute("aria-expanded", String(open));
    nav?.classList.toggle("is-open", open);
  };

  toggle?.addEventListener("click", () => {
    setNavigationOpen(toggle.getAttribute("aria-expanded") !== "true");
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && toggle?.getAttribute("aria-expanded") === "true") {
      setNavigationOpen(false);
      toggle.focus();
    }
  });

  $$("a", nav).forEach((link) => link.addEventListener("click", () => {
    setNavigationOpen(false);
  }));
}

function initReveal() {
  const items = $$(".reveal");
  if (!("IntersectionObserver" in window) || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    items.forEach((item) => item.classList.add("is-visible"));
    return;
  }
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  items.forEach((item) => observer.observe(item));
}

async function initComparison() {
  const canvas = $("[data-compare-canvas]");
  const range = $("[data-compare-range]");
  const output = $("[data-compare-output]");
  const maskToggle = $("[data-mask-toggle]");
  const loading = $("[data-compare-loading]");
  if (!canvas || !range || !output || !maskToggle) return;

  try {
    const [before, after, mask] = await Promise.all([
      loadImage(SAMPLE.image),
      loadImage(SAMPLE.after),
      loadImage(SAMPLE.mask),
    ]);
    const context = canvas.getContext("2d", { alpha: false });
    if (!context) throw new Error("Canvas is not available.");
    canvas.width = before.naturalWidth;
    canvas.height = before.naturalHeight;

    const maskLayer = document.createElement("canvas");
    maskLayer.width = canvas.width;
    maskLayer.height = canvas.height;
    const maskContext = maskLayer.getContext("2d");
    maskContext.drawImage(mask, 0, 0, canvas.width, canvas.height);
    const maskData = maskContext.getImageData(0, 0, canvas.width, canvas.height);
    for (let index = 0; index < maskData.data.length; index += 4) {
      const editable = (maskData.data[index] + maskData.data[index + 1] + maskData.data[index + 2]) / 3 >= 128;
      maskData.data[index] = 70;
      maskData.data[index + 1] = 239;
      maskData.data[index + 2] = 163;
      maskData.data[index + 3] = editable ? 128 : 0;
    }
    maskContext.putImageData(maskData, 0, 0);

    let showMask = false;
    const render = () => {
      const split = Number(range.value) / 100;
      const splitX = Math.round(canvas.width * split);
      context.clearRect(0, 0, canvas.width, canvas.height);
      context.drawImage(before, 0, 0, canvas.width, canvas.height);
      context.save();
      context.beginPath();
      context.rect(splitX, 0, canvas.width - splitX, canvas.height);
      context.clip();
      context.drawImage(after, 0, 0, canvas.width, canvas.height);
      context.restore();
      if (showMask) context.drawImage(maskLayer, 0, 0);

      context.save();
      context.strokeStyle = "rgba(255,255,255,.94)";
      context.lineWidth = Math.max(2, canvas.width / 480);
      context.shadowColor = "rgba(0,0,0,.45)";
      context.shadowBlur = 8;
      context.beginPath();
      context.moveTo(splitX, 0);
      context.lineTo(splitX, canvas.height);
      context.stroke();
      context.shadowBlur = 0;
      context.fillStyle = "rgba(5,18,14,.88)";
      context.beginPath();
      context.arc(splitX, canvas.height / 2, 18, 0, Math.PI * 2);
      context.fill();
      context.strokeStyle = "#77f2b5";
      context.lineWidth = 2;
      context.beginPath();
      context.moveTo(splitX - 7, canvas.height / 2);
      context.lineTo(splitX - 2, canvas.height / 2 - 5);
      context.moveTo(splitX - 7, canvas.height / 2);
      context.lineTo(splitX - 2, canvas.height / 2 + 5);
      context.moveTo(splitX + 7, canvas.height / 2);
      context.lineTo(splitX + 2, canvas.height / 2 - 5);
      context.moveTo(splitX + 7, canvas.height / 2);
      context.lineTo(splitX + 2, canvas.height / 2 + 5);
      context.stroke();
      context.restore();
      output.value = `${range.value}%`;
    };

    range.addEventListener("input", render);
    maskToggle.addEventListener("click", () => {
      showMask = !showMask;
      maskToggle.setAttribute("aria-pressed", String(showMask));
      maskToggle.lastChild.textContent = showMask ? " Hide authorized mask" : " Show authorized mask";
      render();
    });
    render();
    loading?.classList.add("is-hidden");
  } catch (error) {
    if (loading) loading.textContent = error instanceof Error ? error.message : "Artifact unavailable.";
  }
}

function createLabState() {
  return {
    source: null,
    mask: null,
    sourceObjectUrl: null,
    maskObjectUrl: null,
    downloadUrl: null,
    isSample: true,
  };
}

async function imageFromFile(file) {
  if (!SUPPORTED_IMAGE_TYPES.has(file.type)) {
    throw new Error("Choose a PNG, JPEG, or WebP image.");
  }
  if (file.size > MAX_BROWSER_BYTES) {
    throw new Error("Browser lab limit: use a file no larger than 12 MB.");
  }
  const url = URL.createObjectURL(file);
  try {
    const image = await loadImage(url);
    return { image, url };
  } catch (error) {
    URL.revokeObjectURL(url);
    throw error;
  }
}

function revokeIfBlob(url) {
  if (url?.startsWith("blob:")) URL.revokeObjectURL(url);
}

function setStatus(element, state, label) {
  if (!element) return;
  element.classList.remove("is-running", "is-pass", "is-error");
  if (state) element.classList.add(`is-${state}`);
  element.lastChild.textContent = ` ${label}`;
}

function drawContained(canvas, image) {
  canvas.width = image.naturalWidth;
  canvas.height = image.naturalHeight;
  const context = canvas.getContext("2d", { alpha: false });
  context.drawImage(image, 0, 0);
}

async function initBoundaryLab() {
  const root = $("[data-lab]");
  if (!root) return;
  const state = createLabState();
  const imageInput = $("[data-image-upload]", root);
  const maskInput = $("[data-mask-upload]", root);
  const imageName = $("[data-image-name]", root);
  const maskName = $("[data-mask-name]", root);
  const sampleButton = $("[data-load-sample]", root);
  const runButton = $("[data-run-demo]", root);
  const canvas = $("[data-output-canvas]", root);
  const status = $("[data-lab-status]", root);
  const errorOutput = $("[data-lab-error]", root);
  const protectedOutput = $("[data-protected-count]", root);
  const driftOutput = $("[data-drift-count]", root);
  const editOutput = $("[data-edit-count]", root);
  const proofMessage = $("[data-proof-message]", root);
  const downloadButton = $("[data-download]", root);
  const prompt = $("[data-prompt]", root);
  const promptCount = $("[data-prompt-count]", root);

  const resetEvidence = () => {
    protectedOutput.textContent = "—";
    driftOutput.textContent = "—";
    editOutput.textContent = "—";
    proofMessage.textContent = "Run the check to calculate evidence.";
    downloadButton.disabled = true;
    revokeIfBlob(state.downloadUrl);
    state.downloadUrl = null;
    setStatus(status, "", "Ready");
  };

  const loadSample = async () => {
    errorOutput.textContent = "";
    try {
      const [source, mask] = await Promise.all([loadImage(SAMPLE.image), loadImage(SAMPLE.mask)]);
      revokeIfBlob(state.sourceObjectUrl);
      revokeIfBlob(state.maskObjectUrl);
      state.source = source;
      state.mask = mask;
      state.sourceObjectUrl = null;
      state.maskObjectUrl = null;
      state.isSample = true;
      imageName.textContent = "Synthetic sample · 960 × 640";
      maskName.textContent = "Aligned white-edit sample mask";
      imageInput.value = "";
      maskInput.value = "";
      drawContained(canvas, source);
      resetEvidence();
    } catch (error) {
      errorOutput.textContent = error instanceof Error ? error.message : "Could not load the sample.";
      setStatus(status, "error", "Load error");
    }
  };

  const handleFile = async (event, kind) => {
    const file = event.target.files?.[0];
    if (!file) return;
    errorOutput.textContent = "";
    try {
      const loaded = await imageFromFile(file);
      const pixels = loaded.image.naturalWidth * loaded.image.naturalHeight;
      if (pixels > MAX_BROWSER_PIXELS) {
        revokeIfBlob(loaded.url);
        throw new Error("Browser lab limit: use an image up to 4 megapixels.");
      }
      if (kind === "source") {
        revokeIfBlob(state.sourceObjectUrl);
        state.source = loaded.image;
        state.sourceObjectUrl = loaded.url;
        imageName.textContent = `${file.name} · ${loaded.image.naturalWidth} × ${loaded.image.naturalHeight}`;
        drawContained(canvas, loaded.image);
      } else {
        revokeIfBlob(state.maskObjectUrl);
        state.mask = loaded.image;
        state.maskObjectUrl = loaded.url;
        maskName.textContent = `${file.name} · ${loaded.image.naturalWidth} × ${loaded.image.naturalHeight}`;
      }
      state.isSample = false;
      resetEvidence();
    } catch (error) {
      errorOutput.textContent = error instanceof Error ? error.message : "The file could not be loaded.";
      event.target.value = "";
      setStatus(status, "error", "Input error");
    }
  };

  imageInput.addEventListener("change", (event) => handleFile(event, "source"));
  maskInput.addEventListener("change", (event) => handleFile(event, "mask"));
  sampleButton.addEventListener("click", loadSample);
  prompt.addEventListener("input", () => {
    promptCount.value = `${prompt.value.length} / 1000`;
  });
  promptCount.value = `${prompt.value.length} / 1000`;

  runButton.addEventListener("click", async () => {
    errorOutput.textContent = "";
    if (!state.source || !state.mask) {
      errorOutput.textContent = "Choose both an image and an aligned mask.";
      setStatus(status, "error", "Missing input");
      return;
    }
    if (state.source.naturalWidth !== state.mask.naturalWidth || state.source.naturalHeight !== state.mask.naturalHeight) {
      errorOutput.textContent = "Image and mask dimensions must match exactly.";
      setStatus(status, "error", "Shape mismatch");
      return;
    }

    runButton.disabled = true;
    setStatus(status, "running", "Calculating");
    await new Promise((resolve) => window.setTimeout(resolve, 80));

    try {
      const width = state.source.naturalWidth;
      const height = state.source.naturalHeight;
      canvas.width = width;
      canvas.height = height;
      const context = canvas.getContext("2d", { willReadFrequently: true, alpha: false });
      context.drawImage(state.source, 0, 0, width, height);
      const original = context.getImageData(0, 0, width, height);
      const result = new ImageData(new Uint8ClampedArray(original.data), width, height);

      const maskCanvas = document.createElement("canvas");
      maskCanvas.width = width;
      maskCanvas.height = height;
      const maskContext = maskCanvas.getContext("2d", { willReadFrequently: true });
      maskContext.drawImage(state.mask, 0, 0, width, height);
      const maskData = maskContext.getImageData(0, 0, width, height).data;

      let protectedPixels = 0;
      let changedProtected = 0;
      let editableChanged = 0;
      for (let pixel = 0; pixel < width * height; pixel += 1) {
        const index = pixel * 4;
        const brightness = (maskData[index] + maskData[index + 1] + maskData[index + 2]) / 3;
        if (brightness < 128) {
          protectedPixels += 1;
          if (
            result.data[index] !== original.data[index] ||
            result.data[index + 1] !== original.data[index + 1] ||
            result.data[index + 2] !== original.data[index + 2] ||
            result.data[index + 3] !== original.data[index + 3]
          ) changedProtected += 1;
          continue;
        }

        const x = pixel % width;
        const y = Math.floor(pixel / width);
        const stripe = (Math.floor(x / 16) + Math.floor(y / 16)) % 2;
        const wave = Math.round(18 * Math.sin(x * 0.035) + 12 * Math.cos(y * 0.041));
        const targetR = Math.max(0, Math.min(255, 50 + stripe * 20 + wave));
        const targetG = Math.max(0, Math.min(255, 154 + stripe * 23 + Math.round(wave * 0.45)));
        const targetB = Math.max(0, Math.min(255, 119 + stripe * 13 - Math.round(wave * 0.35)));
        result.data[index] = Math.round(original.data[index] * 0.24 + targetR * 0.76);
        result.data[index + 1] = Math.round(original.data[index + 1] * 0.24 + targetG * 0.76);
        result.data[index + 2] = Math.round(original.data[index + 2] * 0.24 + targetB * 0.76);
        result.data[index + 3] = original.data[index + 3];
        if (
          result.data[index] !== original.data[index] ||
          result.data[index + 1] !== original.data[index + 1] ||
          result.data[index + 2] !== original.data[index + 2]
        ) editableChanged += 1;
      }

      context.putImageData(result, 0, 0);
      protectedOutput.textContent = formatNumber(protectedPixels);
      driftOutput.textContent = formatNumber(changedProtected);
      editOutput.textContent = formatNumber(editableChanged);
      if (changedProtected === 0) {
        setStatus(status, "pass", "Invariant passed");
        proofMessage.textContent = "PASS · protected pixels are byte-identical.";
      } else {
        setStatus(status, "error", "Invariant failed");
        proofMessage.textContent = "FAIL · protected-pixel drift detected.";
      }

      revokeIfBlob(state.downloadUrl);
      const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
      if (blob) {
        state.downloadUrl = URL.createObjectURL(blob);
        downloadButton.disabled = false;
      }
    } catch (error) {
      errorOutput.textContent = error instanceof Error ? error.message : "The browser check failed.";
      setStatus(status, "error", "Check error");
    } finally {
      runButton.disabled = false;
    }
  });

  downloadButton.addEventListener("click", () => {
    if (!state.downloadUrl) return;
    const link = document.createElement("a");
    link.href = state.downloadUrl;
    link.download = "boundary-check-deterministic-non-ai.png";
    link.click();
  });

  window.addEventListener("pagehide", () => {
    revokeIfBlob(state.sourceObjectUrl);
    revokeIfBlob(state.maskObjectUrl);
    revokeIfBlob(state.downloadUrl);
  });

  await loadSample();
}

function initCopyButton() {
  const button = $("[data-copy-code]");
  const block = $("[data-code-block]");
  if (!button || !block) return;
  button.addEventListener("click", async () => {
    const original = button.textContent;
    try {
      await navigator.clipboard.writeText(block.textContent);
      button.textContent = "Copied";
    } catch {
      button.textContent = "Select code";
    }
    window.setTimeout(() => { button.textContent = original; }, 1400);
  });
}

function boot() {
  initTheme();
  initNavigation();
  initReveal();
  initComparison();
  initBoundaryLab();
  initCopyButton();
}

document.addEventListener("DOMContentLoaded", boot);
