/**
 * INASRA hosted solver bootstrap.
 *
 * The main INASRA Flask route will inject window.INASRA_SOLVE before this file
 * loads. When that config is absent, this script stays inert and the upstream
 * solver behavior remains unchanged.
 */
window.InasraSolver = (() => {
  function getConfig() {
    const config = window.INASRA_SOLVE;
    return config && typeof config === "object" ? config : null;
  }

  function isHostedMode() {
    return Boolean(getConfig());
  }

  function ensureThemeStylesheet() {
    if (!isHostedMode()) {
      return;
    }

    let link = document.getElementById("inasra-solver-css");
    if (!link) {
      link = document.createElement("link");
      link.id = "inasra-solver-css";
      link.rel = "stylesheet";
      link.href = "./css/inasra-solver.css";
    } else {
      link.remove();
    }

    document.head.appendChild(link);
  }

  function textOrFallback(value, fallback) {
    return typeof value === "string" && value.trim() ? value.trim() : fallback;
  }

  function applyBodyState(config) {
    document.documentElement.classList.add("inasra-hosted");
    document.body.classList.add("inasra-hosted");

    if (config.theme) {
      document.body.dataset.inasraTheme = config.theme;
    }
  }

  function setText(selector, value) {
    const element = document.querySelector(selector);
    if (element) {
      element.textContent = value || "";
    }
  }

  function applyChrome(config, manifest = {}) {
    const title = textOrFallback(config.publicTitle || config.title || manifest.public_title || manifest.title, "INASRA Crossword");
    const username = textOrFallback(config.username || config.author || manifest.author, "");

    setText("#inasra-puzzle-title", title);
    setText("#inasra-puzzle-author", username ? `by ${username}` : "");

    if (title) {
      document.title = `${title} · INASRA Crossword`;
    }
  }

  async function fetchManifest(config) {
    if (!config.manifestUrl) {
      return null;
    }

    try {
      const response = await fetch(config.manifestUrl, {
        headers: { "Accept": "application/json" },
        cache: config.manifestCache || "no-store"
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.warn("[INASRA] Could not load puzzle manifest:", error);
      return null;
    }
  }

  async function boot() {
    const config = getConfig();
    if (!config) {
      return;
    }

    applyBodyState(config);
    ensureThemeStylesheet();
    applyChrome(config);

    const manifest = await fetchManifest(config);
    if (manifest) {
      applyChrome(config, manifest);
    }

    const wallpaperManifest = config.wallpaperManifest || manifest?.wallpaper_manifest || manifest?.wallpaper || manifest;
    if (window.InasraWallpaper) {
      window.InasraWallpaper.init(wallpaperManifest || { images: [] });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }

  return { boot, getConfig, isHostedMode, ensureThemeStylesheet, fetchManifest };
})();
