"use strict";

(() => {
  const story = document.querySelector("[data-cinematic]");
  const hero = document.querySelector(".cinematic-hero");
  if (!story || !hero) return;

  const chapters = [...story.querySelectorAll("[data-cinematic-chapter]")];
  const navItems = [...story.querySelectorAll("[data-cinematic-nav]")];
  const stepOutput = story.querySelector("[data-cinematic-step]");
  const progressBar = story.querySelector("[data-cinematic-bar]");
  const motionPreference = window.matchMedia("(prefers-reduced-motion: reduce)");
  let frameRequested = false;
  let activeChapter = -1;

  const clamp = (value, minimum = 0, maximum = 1) =>
    Math.min(maximum, Math.max(minimum, value));

  const mix = (start, end, amount) => start + (end - start) * amount;

  function range(value, start, end) {
    if (start === end) return value >= end ? 1 : 0;
    return clamp((value - start) / (end - start));
  }

  function smooth(value) {
    const bounded = clamp(value);
    return bounded * bounded * (3 - 2 * bounded);
  }

  function timeline(value, points) {
    if (value <= points[0][0]) return points[0][1];
    for (let index = 1; index < points.length; index += 1) {
      const [endTime, endValue] = points[index];
      const [startTime, startValue] = points[index - 1];
      if (value <= endTime) {
        return mix(startValue, endValue, smooth(range(value, startTime, endTime)));
      }
    }
    return points.at(-1)[1];
  }

  function setChapter(index) {
    if (activeChapter === index) return;
    activeChapter = index;
    chapters.forEach((chapter, chapterIndex) => {
      chapter.classList.toggle("is-active", chapterIndex === index);
    });
    navItems.forEach((item, itemIndex) => {
      const selected = itemIndex === index;
      item.classList.toggle("is-active", selected);
      if (selected) item.setAttribute("aria-current", "step");
      else item.removeAttribute("aria-current");
    });
    if (stepOutput) stepOutput.textContent = String(index + 1).padStart(2, "0");
  }

  function renderHero() {
    const bounds = hero.getBoundingClientRect();
    const progress = clamp(-bounds.top / Math.max(bounds.height * 0.86, 1));
    const analysis = smooth(range(progress, 0.3, 0.98)) * 0.38;
    hero.style.setProperty("--hero-analysis", analysis.toFixed(4));
  }

  function renderStory() {
    if (motionPreference.matches) {
      story.removeAttribute("data-cinematic-active");
      story.style.removeProperty("--cine-analysis");
      story.style.removeProperty("--cine-grid");
      return;
    }

    const bounds = story.getBoundingClientRect();
    const scrollable = Math.max(story.offsetHeight - window.innerHeight, 1);
    const progress = clamp(-bounds.top / scrollable);
    const chapter = Math.min(3, Math.floor(progress * 4));
    const analysis = timeline(progress, [
      [0, 0],
      [0.18, 0],
      [0.34, 0.94],
      [0.5, 1],
      [0.68, 0.46],
      [0.84, 0.24],
      [1, 0.1],
    ]);
    const grid = timeline(progress, [
      [0, 0],
      [0.2, 0],
      [0.32, 1],
      [0.55, 1],
      [0.7, 0.34],
      [0.84, 0.08],
      [1, 0],
    ]);
    const productEntrance = smooth(range(progress, 0.43, 0.68));
    const productExit = smooth(range(progress, 0.8, 0.94));
    const productOpacity = productEntrance * mix(1, 0.12, productExit);
    const planeOpacity = timeline(progress, [
      [0.42, 0],
      [0.56, 0.85],
      [0.73, 0.7],
      [0.88, 0],
      [1, 0],
    ]);
    const proof = smooth(range(progress, 0.76, 0.92));
    const cameraScale = timeline(progress, [
      [0, 1.02],
      [0.32, 1.09],
      [0.65, 1.155],
      [0.84, 1.09],
      [1, 1.065],
    ]);
    const cameraX = timeline(progress, [
      [0, 0],
      [0.35, -22],
      [0.68, -64],
      [1, -40],
    ]);
    const cameraY = timeline(progress, [
      [0, 0],
      [0.5, -8],
      [0.78, -18],
      [1, -10],
    ]);

    story.dataset.cinematicActive = String(chapter + 1);
    story.style.setProperty("--cine-analysis", analysis.toFixed(4));
    story.style.setProperty("--cine-concept", (1 - analysis * 0.34).toFixed(4));
    story.style.setProperty("--cine-grid", grid.toFixed(4));
    story.style.setProperty("--cine-scan-y", `${mix(-22, 82, progress).toFixed(2)}%`);
    story.style.setProperty("--cine-camera-scale", cameraScale.toFixed(4));
    story.style.setProperty("--cine-camera-x", `${cameraX.toFixed(2)}px`);
    story.style.setProperty("--cine-camera-y", `${cameraY.toFixed(2)}px`);
    story.style.setProperty("--cine-product-opacity", productOpacity.toFixed(4));
    story.style.setProperty("--cine-product-x", `${mix(145, -82, productEntrance).toFixed(2)}px`);
    story.style.setProperty("--cine-product-y", `${mix(-105, 72, productEntrance).toFixed(2)}px`);
    story.style.setProperty("--cine-product-scale", mix(0.5, 0.92, productEntrance).toFixed(4));
    story.style.setProperty("--cine-product-rx", `${mix(8, 64, productEntrance).toFixed(2)}deg`);
    story.style.setProperty("--cine-product-rz", `${mix(18, -4, productEntrance).toFixed(2)}deg`);
    story.style.setProperty("--cine-plane-opacity", planeOpacity.toFixed(4));
    story.style.setProperty("--cine-proof", proof.toFixed(4));
    story.style.setProperty("--cine-proof-y", `${mix(22, 0, proof).toFixed(2)}px`);
    if (progressBar) progressBar.style.transform = `scaleX(${progress.toFixed(4)})`;
    setChapter(chapter);
  }

  function updateCinematicHeader() {
    const heroBounds = hero.getBoundingClientRect();
    const storyBounds = story.getBoundingClientRect();
    const insideCinematicZone =
      heroBounds.bottom > 0 ||
      (storyBounds.top < window.innerHeight && storyBounds.bottom > 0);
    document.body.classList.toggle("cinematic-header-active", insideCinematicZone);
  }

  function render() {
    frameRequested = false;
    renderHero();
    renderStory();
    updateCinematicHeader();
  }

  function scheduleRender() {
    if (frameRequested) return;
    frameRequested = true;
    window.requestAnimationFrame(render);
  }

  window.addEventListener("scroll", scheduleRender, { passive: true });
  window.addEventListener("resize", scheduleRender, { passive: true });
  motionPreference.addEventListener("change", scheduleRender);
  story.dataset.cinematicReady = "true";
  setChapter(0);
  render();
})();
