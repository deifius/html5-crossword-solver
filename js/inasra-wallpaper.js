/**
 * INASRA solver wallpaper layer.
 *
 * This file is intentionally independent from the crossword engine. It accepts a
 * wallpaper manifest and paints a read-only Ken Burns style background behind
 * the solver. Missing/empty manifests are treated as a no-op.
 */
window.InasraWallpaper = (() => {
  const DEFAULT_SETTINGS = {
    enabled: true,
    opacity: 0.32,
    transition_seconds: 8,
    hold_seconds: 12,
    pan_strength: 0.12,
    motion: "gentle",
    fit: "cover"
  };

  let timer = null;
  let activeIndex = -1;
  let activeSlide = 0;
  let slides = [];
  let images = [];
  let settings = { ...DEFAULT_SETTINGS };

  function coerceManifest(rawManifest) {
    if (!rawManifest || typeof rawManifest !== "object") {
      return { images: [], settings: { ...DEFAULT_SETTINGS } };
    }

    const manifest = rawManifest.wallpaper_manifest || rawManifest.wallpaper || rawManifest;
    return {
      images: Array.isArray(manifest.images) ? manifest.images : [],
      settings: { ...DEFAULT_SETTINGS, ...(manifest.settings || {}) }
    };
  }

  function getImageSource(image) {
    if (typeof image === "string") {
      return image;
    }

    if (!image || typeof image !== "object") {
      return null;
    }

    return image.src || image.url || image.href || null;
  }

  function prefersReducedMotion() {
    return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function ensureLayer() {
    let layer = document.getElementById("inasra-wallpaper-layer");
    if (!layer) {
      layer = document.createElement("div");
      layer.id = "inasra-wallpaper-layer";
      layer.setAttribute("aria-hidden", "true");
      document.body.prepend(layer);
    }

    layer.innerHTML = '<div class="inasra-wallpaper-slide"></div><div class="inasra-wallpaper-slide"></div>';
    slides = Array.from(layer.querySelectorAll(".inasra-wallpaper-slide"));
    return layer;
  }

  function preload(src) {
    if (!src) {
      return Promise.resolve();
    }

    return new Promise(resolve => {
      const img = new Image();
      img.onload = resolve;
      img.onerror = resolve;
      img.src = src;
    });
  }

  function stop() {
    if (timer) {
      window.clearTimeout(timer);
      timer = null;
    }
  }

  function nextTransform(index) {
    if (prefersReducedMotion()) {
      return "scale(1.02) translate3d(0, 0, 0)";
    }

    const strength = Number(settings.pan_strength) || DEFAULT_SETTINGS.pan_strength;
    const direction = index % 4;
    const offset = Math.round(strength * 100);
    const scale = 1 + Math.max(0.04, strength);

    if (direction === 0) return `scale(${scale}) translate3d(-${offset}px, -${offset / 2}px, 0)`;
    if (direction === 1) return `scale(${scale}) translate3d(${offset}px, -${offset}px, 0)`;
    if (direction === 2) return `scale(${scale}) translate3d(${offset / 2}px, ${offset}px, 0)`;
    return `scale(${scale}) translate3d(-${offset}px, ${offset}px, 0)`;
  }

  async function showNext() {
    if (!images.length || !slides.length) {
      return;
    }

    activeIndex = (activeIndex + 1) % images.length;
    const image = images[activeIndex];
    const src = getImageSource(image);
    if (!src) {
      scheduleNext();
      return;
    }

    await preload(src);

    activeSlide = activeSlide === 0 ? 1 : 0;
    const incoming = slides[activeSlide];
    const outgoing = slides[activeSlide === 0 ? 1 : 0];
    const fit = settings.fit || DEFAULT_SETTINGS.fit;
    const opacity = Number(settings.opacity ?? DEFAULT_SETTINGS.opacity);
    const transitionSeconds = Number(settings.transition_seconds) || DEFAULT_SETTINGS.transition_seconds;
    const holdSeconds = Number(settings.hold_seconds) || DEFAULT_SETTINGS.hold_seconds;
    const animationSeconds = Math.max(transitionSeconds + holdSeconds, holdSeconds + 2);

    incoming.style.backgroundImage = `url("${src.replace(/"/g, '%22')}")`;
    incoming.style.backgroundSize = fit;
    incoming.style.transitionDuration = `${transitionSeconds}s`;
    incoming.style.animationDuration = `${animationSeconds}s`;
    incoming.style.opacity = String(opacity);
    incoming.style.transform = nextTransform(activeIndex);
    incoming.classList.add("is-active");

    outgoing.style.transitionDuration = `${transitionSeconds}s`;
    outgoing.style.opacity = "0";
    outgoing.classList.remove("is-active");

    preload(getImageSource(images[(activeIndex + 1) % images.length]));
    scheduleNext();
  }

  function scheduleNext() {
    stop();
    const holdSeconds = Number(settings.hold_seconds) || DEFAULT_SETTINGS.hold_seconds;
    const transitionSeconds = Number(settings.transition_seconds) || DEFAULT_SETTINGS.transition_seconds;
    timer = window.setTimeout(showNext, (holdSeconds + transitionSeconds) * 1000);
  }

  function init(rawManifest) {
    stop();

    const manifest = coerceManifest(rawManifest);
    settings = manifest.settings;
    images = manifest.images.filter(image => Boolean(getImageSource(image)));

    const layer = ensureLayer();
    layer.style.setProperty("--inasra-wallpaper-opacity", String(settings.opacity));
    layer.classList.toggle("is-disabled", !settings.enabled || images.length === 0);

    if (!settings.enabled || images.length === 0) {
      return;
    }

    showNext();
  }

  return { init, stop, coerceManifest };
})();
