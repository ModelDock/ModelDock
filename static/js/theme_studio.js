/**
 * ModelDock Studio - Theme, Colors & Appearance Studio
 * Real-time 1000+ color combination engine with live preview, wallpaper backgrounds,
 * granular bubble customization, and persistent theme storage.
 */

const DEFAULT_THEME = {
  name: "Obsidian Pro",
  chatUserBg: "#1e2436",
  chatUserText: "#f8fafc",
  chatUserBorder: "#6366f1",
  chatAiBg: "#181d2c",
  chatAiText: "#f1f5f9",
  chatAiBorder: "#4f46e5",
  chatBgColor: "#0a0c12",
  chatBgPreset: "none",
  chatBgCustomUrl: "",
  chatBgOpacity: 1.0,
  chatBgBlur: 0,
  headerBgColor: "#10131d",
  headerTextColor: "#f8fafc",
  headerBorderColor: "#262c3e",
  sidebarBgColor: "#0d101a",
  sidebarTextColor: "#f8fafc",
  sidebarBorderColor: "#1e2436",
  accentColor: "#6366f1",
  accentViolet: "#8b5cf6",
};

const WALLPAPER_PRESETS = {
  none: "none",
  cosmic: "radial-gradient(circle at 50% 20%, rgba(99, 102, 241, 0.22) 0%, rgba(10, 12, 18, 0.95) 75%), radial-gradient(circle at 80% 80%, rgba(236, 72, 153, 0.15) 0%, rgba(10, 12, 18, 0) 60%)",
  grid: "linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px)",
  tokyo: "radial-gradient(circle at 20% 30%, rgba(6, 182, 212, 0.22) 0%, transparent 50%), radial-gradient(circle at 80% 70%, rgba(217, 70, 239, 0.22) 0%, transparent 50%)",
  starry: "radial-gradient(ellipse at top, #1e1b4b 0%, #0a0c12 70%)",
  emerald: "radial-gradient(circle at 50% 10%, rgba(16, 185, 129, 0.22) 0%, rgba(2, 20, 10, 0.95) 70%)",
  sunset: "radial-gradient(ellipse at bottom, rgba(245, 158, 11, 0.2) 0%, #0a0c12 75%)",
  hexagons: "radial-gradient(circle at 30% 40%, rgba(147, 51, 234, 0.18) 0%, #090b10 80%)",
};

const THEME_PRESETS = [
  {
    id: "obsidian",
    name: "Obsidian Indigo (Default)",
    previewColors: ["#0a0c12", "#6366f1", "#1e2436", "#181d2c"],
    theme: { ...DEFAULT_THEME },
  },
  {
    id: "cyberpunk",
    name: "Midnight Cyberpunk",
    previewColors: ["#090d16", "#06b6d4", "#1b2a47", "#121b2f"],
    theme: {
      name: "Midnight Cyberpunk",
      chatUserBg: "#162846",
      chatUserText: "#e0f2fe",
      chatUserBorder: "#06b6d4",
      chatAiBg: "#0f172a",
      chatAiText: "#f8fafc",
      chatAiBorder: "#ec4899",
      chatBgColor: "#070a12",
      chatBgPreset: "tokyo",
      chatBgCustomUrl: "",
      chatBgOpacity: 1.0,
      chatBgBlur: 0,
      headerBgColor: "#0b1120",
      headerTextColor: "#38bdf8",
      headerBorderColor: "#1e293b",
      sidebarBgColor: "#080c18",
      sidebarTextColor: "#f1f5f9",
      sidebarBorderColor: "#1e293b",
      accentColor: "#06b6d4",
      accentViolet: "#ec4899",
    },
  },
  {
    id: "oled",
    name: "OLED True Black",
    previewColors: ["#000000", "#10b981", "#121212", "#080808"],
    theme: {
      name: "OLED True Black",
      chatUserBg: "#18181b",
      chatUserText: "#ffffff",
      chatUserBorder: "#27272a",
      chatAiBg: "#09090b",
      chatAiText: "#f4f4f5",
      chatAiBorder: "#18181b",
      chatBgColor: "#000000",
      chatBgPreset: "none",
      chatBgCustomUrl: "",
      chatBgOpacity: 1.0,
      chatBgBlur: 0,
      headerBgColor: "#000000",
      headerTextColor: "#ffffff",
      headerBorderColor: "#27272a",
      sidebarBgColor: "#000000",
      sidebarTextColor: "#e4e4e7",
      sidebarBorderColor: "#27272a",
      accentColor: "#10b981",
      accentViolet: "#34d399",
    },
  },
  {
    id: "ocean",
    name: "Deep Oceanic Navy",
    previewColors: ["#061325", "#0ea5e9", "#0c284d", "#081d38"],
    theme: {
      name: "Deep Oceanic Navy",
      chatUserBg: "#0c2b53",
      chatUserText: "#e0f2fe",
      chatUserBorder: "#38bdf8",
      chatAiBg: "#071c36",
      chatAiText: "#f0f9ff",
      chatAiBorder: "#0284c7",
      chatBgColor: "#030c18",
      chatBgPreset: "cosmic",
      chatBgCustomUrl: "",
      chatBgOpacity: 1.0,
      chatBgBlur: 0,
      headerBgColor: "#05162c",
      headerTextColor: "#7dd3fc",
      headerBorderColor: "#0c3260",
      sidebarBgColor: "#041122",
      sidebarTextColor: "#e0f2fe",
      sidebarBorderColor: "#0c3260",
      accentColor: "#0ea5e9",
      accentViolet: "#38bdf8",
    },
  },
  {
    id: "synthwave",
    name: "Tokyo Synthwave",
    previewColors: ["#120924", "#d946ef", "#2a124e", "#1b0b33"],
    theme: {
      name: "Tokyo Synthwave",
      chatUserBg: "#2e1257",
      chatUserText: "#fae8ff",
      chatUserBorder: "#d946ef",
      chatAiBg: "#1c0b36",
      chatAiText: "#fdf4ff",
      chatAiBorder: "#a855f7",
      chatBgColor: "#0f061f",
      chatBgPreset: "tokyo",
      chatBgCustomUrl: "",
      chatBgOpacity: 1.0,
      chatBgBlur: 0,
      headerBgColor: "#160a2d",
      headerTextColor: "#f0abfc",
      headerBorderColor: "#3b176f",
      sidebarBgColor: "#0e051c",
      sidebarTextColor: "#f5d0fe",
      sidebarBorderColor: "#3b176f",
      accentColor: "#d946ef",
      accentViolet: "#c084fc",
    },
  },
  {
    id: "matrix",
    name: "Emerald Matrix",
    previewColors: ["#02140a", "#10b981", "#082e18", "#041c0e"],
    theme: {
      name: "Emerald Matrix",
      chatUserBg: "#06381c",
      chatUserText: "#d1fae5",
      chatUserBorder: "#10b981",
      chatAiBg: "#032010",
      chatAiText: "#ecfdf5",
      chatAiBorder: "#059669",
      chatBgColor: "#010d06",
      chatBgPreset: "emerald",
      chatBgCustomUrl: "",
      chatBgOpacity: 1.0,
      chatBgBlur: 0,
      headerBgColor: "#031c0e",
      headerTextColor: "#6ee7b7",
      headerBorderColor: "#064e26",
      sidebarBgColor: "#021208",
      sidebarTextColor: "#d1fae5",
      sidebarBorderColor: "#064e26",
      accentColor: "#10b981",
      accentViolet: "#34d399",
    },
  },
  {
    id: "amber",
    name: "Sunset Amber",
    previewColors: ["#160f0d", "#f59e0b", "#361c14", "#24130d"],
    theme: {
      name: "Sunset Amber",
      chatUserBg: "#3b1f15",
      chatUserText: "#fef3c7",
      chatUserBorder: "#f59e0b",
      chatAiBg: "#22120b",
      chatAiText: "#fffbeb",
      chatAiBorder: "#d97706",
      chatBgColor: "#100907",
      chatBgPreset: "sunset",
      chatBgCustomUrl: "",
      chatBgOpacity: 1.0,
      chatBgBlur: 0,
      headerBgColor: "#1a100c",
      headerTextColor: "#fcd34d",
      headerBorderColor: "#452417",
      sidebarBgColor: "#120a07",
      sidebarTextColor: "#fef3c7",
      sidebarBorderColor: "#452417",
      accentColor: "#f59e0b",
      accentViolet: "#fbbf24",
    },
  },
  {
    id: "rose",
    name: "Rosé Velvet",
    previewColors: ["#190d16", "#f43f5e", "#38162c", "#240e1c"],
    theme: {
      name: "Rosé Velvet",
      chatUserBg: "#401732",
      chatUserText: "#ffe4e6",
      chatUserBorder: "#f43f5e",
      chatAiBg: "#250d1d",
      chatAiText: "#fff1f2",
      chatAiBorder: "#e11d48",
      chatBgColor: "#12080f",
      chatBgPreset: "starry",
      chatBgCustomUrl: "",
      chatBgOpacity: 1.0,
      chatBgBlur: 0,
      headerBgColor: "#1c0d18",
      headerTextColor: "#fda4af",
      headerBorderColor: "#4c1a3b",
      sidebarBgColor: "#130810",
      sidebarTextColor: "#ffe4e6",
      sidebarBorderColor: "#4c1a3b",
      accentColor: "#f43f5e",
      accentViolet: "#fb7185",
    },
  },
  {
    id: "nord",
    name: "Nord Arctic Frost",
    previewColors: ["#1e222a", "#88c0d0", "#2e3440", "#252a35"],
    theme: {
      name: "Nord Arctic Frost",
      chatUserBg: "#2e3440",
      chatUserText: "#eceff4",
      chatUserBorder: "#88c0d0",
      chatAiBg: "#242933",
      chatAiText: "#e5e9f0",
      chatAiBorder: "#81a1c1",
      chatBgColor: "#191d24",
      chatBgPreset: "none",
      chatBgCustomUrl: "",
      chatBgOpacity: 1.0,
      chatBgBlur: 0,
      headerBgColor: "#212630",
      headerTextColor: "#88c0d0",
      headerBorderColor: "#3b4252",
      sidebarBgColor: "#1c2028",
      sidebarTextColor: "#eceff4",
      sidebarBorderColor: "#3b4252",
      accentColor: "#88c0d0",
      accentViolet: "#81a1c1",
    },
  },
  {
    id: "royal",
    name: "Royal Cobalt",
    previewColors: ["#091124", "#3b82f6", "#14254f", "#0d1938"],
    theme: {
      name: "Royal Cobalt",
      chatUserBg: "#172b5c",
      chatUserText: "#eff6ff",
      chatUserBorder: "#3b82f6",
      chatAiBg: "#0f1c3d",
      chatAiText: "#f8fafc",
      chatAiBorder: "#2563eb",
      chatBgColor: "#050b18",
      chatBgPreset: "cosmic",
      chatBgCustomUrl: "",
      chatBgOpacity: 1.0,
      chatBgBlur: 0,
      headerBgColor: "#0a1329",
      headerTextColor: "#93c5fd",
      headerBorderColor: "#1e3a78",
      sidebarBgColor: "#070d1d",
      sidebarTextColor: "#eff6ff",
      sidebarBorderColor: "#1e3a78",
      accentColor: "#3b82f6",
      accentViolet: "#60a5fa",
    },
  },
  {
    id: "solarized",
    name: "Solarized Espresso",
    previewColors: ["#073642", "#b58900", "#094555", "#062b35"],
    theme: {
      name: "Solarized Espresso",
      chatUserBg: "#0a4c5e",
      chatUserText: "#fdf6e3",
      chatUserBorder: "#b58900",
      chatAiBg: "#06303a",
      chatAiText: "#eee8d5",
      chatAiBorder: "#2aa198",
      chatBgColor: "#04242c",
      chatBgPreset: "none",
      chatBgCustomUrl: "",
      chatBgOpacity: 1.0,
      chatBgBlur: 0,
      headerBgColor: "#07323d",
      headerTextColor: "#cb4b16",
      headerBorderColor: "#0b5163",
      sidebarBgColor: "#052730",
      sidebarTextColor: "#93a1a1",
      sidebarBorderColor: "#0b5163",
      accentColor: "#b58900",
      accentViolet: "#2aa198",
    },
  },
  {
    id: "monochrome",
    name: "Monochrome Minimal",
    previewColors: ["#18181b", "#ffffff", "#27272a", "#202023"],
    theme: {
      name: "Monochrome Minimal",
      chatUserBg: "#27272a",
      chatUserText: "#ffffff",
      chatUserBorder: "#52525b",
      chatAiBg: "#1f1f23",
      chatAiText: "#f4f4f5",
      chatAiBorder: "#3f3f46",
      chatBgColor: "#111113",
      chatBgPreset: "none",
      chatBgCustomUrl: "",
      chatBgOpacity: 1.0,
      chatBgBlur: 0,
      headerBgColor: "#18181b",
      headerTextColor: "#ffffff",
      headerBorderColor: "#27272a",
      sidebarBgColor: "#141416",
      sidebarTextColor: "#e4e4e7",
      sidebarBorderColor: "#27272a",
      accentColor: "#a1a1aa",
      accentViolet: "#d4d4d8",
    },
  },
];

let currentActiveTheme = { ...DEFAULT_THEME };

// --- Theme Application Engine ---
function applyTheme(theme, updateUI = true) {
  if (!theme) return;
  currentActiveTheme = { ...DEFAULT_THEME, ...theme };
  const root = document.documentElement;

  // 1. User Prompt Bubble
  root.style.setProperty("--chat-user-bg", currentActiveTheme.chatUserBg);
  root.style.setProperty("--chat-user-text", currentActiveTheme.chatUserText);
  root.style.setProperty("--chat-user-border", currentActiveTheme.chatUserBorder);

  // 2. AI Response Bubble
  root.style.setProperty("--chat-ai-bg", currentActiveTheme.chatAiBg);
  root.style.setProperty("--chat-ai-text", currentActiveTheme.chatAiText);
  root.style.setProperty("--chat-ai-border", currentActiveTheme.chatAiBorder);

  // 3. Canvas & Wallpaper Background
  root.style.setProperty("--chat-bg-color", currentActiveTheme.chatBgColor);
  let bgImgVal = "none";
  if (currentActiveTheme.chatBgPreset === "custom" && currentActiveTheme.chatBgCustomUrl) {
    bgImgVal = `url("${currentActiveTheme.chatBgCustomUrl}")`;
  } else if (WALLPAPER_PRESETS[currentActiveTheme.chatBgPreset]) {
    bgImgVal = WALLPAPER_PRESETS[currentActiveTheme.chatBgPreset];
  }
  root.style.setProperty("--chat-bg-image", bgImgVal);
  root.style.setProperty("--chat-bg-opacity", currentActiveTheme.chatBgOpacity ?? 1.0);
  root.style.setProperty("--chat-bg-blur", `${currentActiveTheme.chatBgBlur ?? 0}px`);

  // 4. Header & Topbar
  root.style.setProperty("--header-bg-color", currentActiveTheme.headerBgColor);
  root.style.setProperty("--header-text-color", currentActiveTheme.headerTextColor);
  root.style.setProperty("--header-border-color", currentActiveTheme.headerBorderColor);

  // 5. Sidebar & Drawers
  root.style.setProperty("--sidebar-bg-color", currentActiveTheme.sidebarBgColor);
  root.style.setProperty("--sidebar-text-color", currentActiveTheme.sidebarTextColor);
  root.style.setProperty("--sidebar-border-color", currentActiveTheme.sidebarBorderColor);

  // 6. Accent Colors
  root.style.setProperty("--accent-primary", currentActiveTheme.accentColor);
  root.style.setProperty("--accent-color", currentActiveTheme.accentColor);
  root.style.setProperty("--accent-violet", currentActiveTheme.accentViolet);

  if (updateUI) {
    syncInputsWithTheme(currentActiveTheme);
    updateLiveThemePreview(currentActiveTheme);
  }
}

function syncInputsWithTheme(t) {
  setFieldVal("theme-user-bg", t.chatUserBg);
  setFieldVal("theme-user-text", t.chatUserText);
  setFieldVal("theme-user-border", t.chatUserBorder);

  setFieldVal("theme-ai-bg", t.chatAiBg);
  setFieldVal("theme-ai-text", t.chatAiText);
  setFieldVal("theme-ai-border", t.chatAiBorder);

  setFieldVal("theme-chat-bg", t.chatBgColor);
  setFieldVal("theme-wallpaper-preset", t.chatBgPreset || "none");
  setFieldVal("theme-wallpaper-url", t.chatBgCustomUrl || "");

  const opSlider = document.getElementById("theme-wallpaper-opacity");
  const opVal = document.getElementById("theme-wallpaper-opacity-val");
  if (opSlider) opSlider.value = Math.round((t.chatBgOpacity ?? 1) * 100);
  if (opVal) opVal.textContent = `${Math.round((t.chatBgOpacity ?? 1) * 100)}%`;

  const blurSlider = document.getElementById("theme-wallpaper-blur");
  const blurVal = document.getElementById("theme-wallpaper-blur-val");
  if (blurSlider) blurSlider.value = t.chatBgBlur ?? 0;
  if (blurVal) blurVal.textContent = `${t.chatBgBlur ?? 0}px`;

  setFieldVal("theme-header-bg", t.headerBgColor);
  setFieldVal("theme-header-text", t.headerTextColor);
  setFieldVal("theme-header-border", t.headerBorderColor);

  setFieldVal("theme-sidebar-bg", t.sidebarBgColor);
  setFieldVal("theme-sidebar-text", t.sidebarTextColor);
  setFieldVal("theme-sidebar-border", t.sidebarBorderColor);

  setFieldVal("theme-accent-color", t.accentColor);
  setFieldVal("theme-accent-violet", t.accentViolet);

  const customWrap = document.getElementById("theme-custom-wallpaper-wrap");
  if (customWrap) {
    customWrap.style.display = t.chatBgPreset === "custom" ? "block" : "none";
  }
}

function setFieldVal(id, val) {
  const colorPicker = document.getElementById(id);
  const textInput = document.getElementById(`${id}-text`);
  if (colorPicker) {
    try {
      colorPicker.value = rgbToHex(val);
    } catch (_) {
      colorPicker.value = val;
    }
  }
  if (textInput) textInput.value = val;
}

function rgbToHex(color) {
  if (!color) return "#000000";
  if (color.startsWith("#")) return color.slice(0, 7);
  return color;
}

function updateLiveThemePreview(t) {
  const pHeader = document.getElementById("preview-theme-header");
  const pUserBubble = document.getElementById("preview-theme-user");
  const pAiBubble = document.getElementById("preview-theme-ai");
  const pCanvas = document.getElementById("preview-theme-canvas");
  const pSidebar = document.getElementById("preview-theme-sidebar");

  if (pHeader) {
    pHeader.style.backgroundColor = t.headerBgColor;
    pHeader.style.color = t.headerTextColor;
    pHeader.style.borderColor = t.headerBorderColor;
  }
  if (pSidebar) {
    pSidebar.style.backgroundColor = t.sidebarBgColor;
    pSidebar.style.color = t.sidebarTextColor;
    pSidebar.style.borderColor = t.sidebarBorderColor;
  }
  if (pUserBubble) {
    pUserBubble.style.background = t.chatUserBg;
    pUserBubble.style.color = t.chatUserText;
    pUserBubble.style.borderColor = t.chatUserBorder;
  }
  if (pAiBubble) {
    pAiBubble.style.background = t.chatAiBg;
    pAiBubble.style.color = t.chatAiText;
    pAiBubble.style.borderColor = t.chatAiBorder;
  }
  if (pCanvas) {
    pCanvas.style.backgroundColor = t.chatBgColor;
    let bgImg = "none";
    if (t.chatBgPreset === "custom" && t.chatBgCustomUrl) {
      bgImg = `url("${t.chatBgCustomUrl}")`;
    } else if (WALLPAPER_PRESETS[t.chatBgPreset]) {
      bgImg = WALLPAPER_PRESETS[t.chatBgPreset];
    }
    pCanvas.style.backgroundImage = bgImg;
    pCanvas.style.backgroundSize = t.chatBgPreset === "grid" ? "20px 20px" : "cover";
  }
}

// --- 1000+ Harmonious Color Combination Generator ---
function hslToHex(h, s, l) {
  l /= 100;
  const a = (s * Math.min(l, 1 - l)) / 100;
  const f = (n) => {
    const k = (n + h / 30) % 12;
    const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
    return Math.round(255 * color).toString(16).padStart(2, "0");
  };
  return `#${f(0)}${f(8)}${f(4)}`;
}

function generateRandomTheme() {
  // Random base hue [0, 360)
  const baseH = Math.floor(Math.random() * 360);
  const accentH = (baseH + Math.floor(Math.random() * 120 + 30)) % 360;
  const secondaryH = (accentH + 40) % 360;

  // Harmonious deep dark background colors
  const chatBgColor = hslToHex(baseH, 28, 4);
  const headerBgColor = hslToHex(baseH, 30, 7);
  const sidebarBgColor = hslToHex(baseH, 32, 6);
  const headerBorder = hslToHex(baseH, 25, 14);

  // Chat bubbles with distinct elevation & contrast
  const chatUserBg = hslToHex(accentH, 38, 16);
  const chatUserBorder = hslToHex(accentH, 80, 58);
  const chatUserText = "#f8fafc";

  const chatAiBg = hslToHex(baseH, 28, 11);
  const chatAiBorder = hslToHex(secondaryH, 65, 45);
  const chatAiText = "#f1f5f9";

  const accentColor = hslToHex(accentH, 90, 60);
  const accentViolet = hslToHex(secondaryH, 85, 65);

  const presets = ["none", "cosmic", "grid", "tokyo", "starry", "emerald", "sunset", "hexagons"];
  const randomPreset = presets[Math.floor(Math.random() * presets.length)];

  const randomTheme = {
    name: `Harmonic H-${baseH}°`,
    chatUserBg,
    chatUserText,
    chatUserBorder,
    chatAiBg,
    chatAiText,
    chatAiBorder,
    chatBgColor,
    chatBgPreset: randomPreset,
    chatBgCustomUrl: "",
    chatBgOpacity: 1.0,
    chatBgBlur: 0,
    headerBgColor,
    headerTextColor: "#f8fafc",
    headerBorderColor: headerBorder,
    sidebarBgColor,
    sidebarTextColor: "#f8fafc",
    sidebarBorderColor: headerBorder,
    accentColor,
    accentViolet,
  };

  applyTheme(randomTheme, true);
  if (typeof showToast === "function") {
    showToast(`Generated New Color Combination (${randomTheme.name})!`, "success");
  }
}

function selectThemePreset(presetId) {
  const preset = THEME_PRESETS.find((p) => p.id === presetId);
  if (!preset) return;
  applyTheme(preset.theme, true);
  document.querySelectorAll(".theme-preset-card").forEach((card) => {
    card.classList.toggle("active", card.getAttribute("data-preset-id") === presetId);
  });
  if (typeof showToast === "function") {
    showToast(`Applied preset: ${preset.name}`, "info");
  }
}

function saveCurrentTheme() {
  try {
    localStorage.setItem("modeldock_custom_theme", JSON.stringify(currentActiveTheme));
    if (typeof showToast === "function") {
      showToast("Theme preferences saved permanently!", "success");
    } else {
      alert("Theme saved permanently!");
    }
  } catch (err) {
    console.error("Failed to save theme:", err);
  }
}

function resetThemeToDefault() {
  if (confirm("Reset all appearance and color customizations back to default Obsidian Pro?")) {
    localStorage.removeItem("modeldock_custom_theme");
    applyTheme(DEFAULT_THEME, true);
    if (typeof showToast === "function") {
      showToast("Theme reset to factory defaults.", "info");
    }
  }
}

function exportThemeJSON() {
  const jsonStr = JSON.stringify(currentActiveTheme, null, 2);
  navigator.clipboard.writeText(jsonStr).then(() => {
    alert("Theme configuration copied to clipboard! You can share or save it.");
  }).catch(() => {
    prompt("Copy your theme JSON configuration below:", jsonStr);
  });
}

function importThemeJSON() {
  const raw = prompt("Paste your ModelDock theme JSON configuration here:");
  if (!raw) return;
  try {
    const parsed = JSON.parse(raw);
    applyTheme(parsed, true);
    saveCurrentTheme();
    alert("Theme successfully imported and applied!");
  } catch (e) {
    alert("Invalid theme JSON format. Please verify and try again.");
  }
}

// --- Dynamic Color Picker & Input Listeners Binding ---
function bindThemeInputPair(id, themeKey) {
  const picker = document.getElementById(id);
  const textInput = document.getElementById(`${id}-text`);

  if (picker) {
    picker.addEventListener("input", (e) => {
      const val = e.target.value;
      if (textInput) textInput.value = val;
      currentActiveTheme[themeKey] = val;
      applyTheme(currentActiveTheme, false);
      updateLiveThemePreview(currentActiveTheme);
    });
  }

  if (textInput) {
    textInput.addEventListener("input", (e) => {
      const val = e.target.value.trim();
      if (val.startsWith("#") && (val.length === 4 || val.length === 7)) {
        if (picker) picker.value = val;
      }
      currentActiveTheme[themeKey] = val;
      applyTheme(currentActiveTheme, false);
      updateLiveThemePreview(currentActiveTheme);
    });
  }
}

function initThemeStudio() {
  // Bind all granular color pairs
  bindThemeInputPair("theme-user-bg", "chatUserBg");
  bindThemeInputPair("theme-user-text", "chatUserText");
  bindThemeInputPair("theme-user-border", "chatUserBorder");

  bindThemeInputPair("theme-ai-bg", "chatAiBg");
  bindThemeInputPair("theme-ai-text", "chatAiText");
  bindThemeInputPair("theme-ai-border", "chatAiBorder");

  bindThemeInputPair("theme-chat-bg", "chatBgColor");
  bindThemeInputPair("theme-header-bg", "headerBgColor");
  bindThemeInputPair("theme-header-text", "headerTextColor");
  bindThemeInputPair("theme-header-border", "headerBorderColor");

  bindThemeInputPair("theme-sidebar-bg", "sidebarBgColor");
  bindThemeInputPair("theme-sidebar-text", "sidebarTextColor");
  bindThemeInputPair("theme-sidebar-border", "sidebarBorderColor");

  bindThemeInputPair("theme-accent-color", "accentColor");
  bindThemeInputPair("theme-accent-violet", "accentViolet");

  // Wallpaper selector
  const wpSelect = document.getElementById("theme-wallpaper-preset");
  const wpCustomWrap = document.getElementById("theme-custom-wallpaper-wrap");
  const wpUrlInput = document.getElementById("theme-wallpaper-url");
  const wpFileInput = document.getElementById("theme-wallpaper-file");

  if (wpSelect) {
    wpSelect.addEventListener("change", (e) => {
      const val = e.target.value;
      currentActiveTheme.chatBgPreset = val;
      if (wpCustomWrap) {
        wpCustomWrap.style.display = val === "custom" ? "block" : "none";
      }
      applyTheme(currentActiveTheme, false);
      updateLiveThemePreview(currentActiveTheme);
    });
  }

  if (wpUrlInput) {
    wpUrlInput.addEventListener("input", (e) => {
      currentActiveTheme.chatBgCustomUrl = e.target.value.trim();
      applyTheme(currentActiveTheme, false);
      updateLiveThemePreview(currentActiveTheme);
    });
  }

  if (wpFileInput) {
    wpFileInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (ev) => {
          currentActiveTheme.chatBgPreset = "custom";
          currentActiveTheme.chatBgCustomUrl = ev.target.result;
          if (wpSelect) wpSelect.value = "custom";
          if (wpCustomWrap) wpCustomWrap.style.display = "block";
          if (wpUrlInput) wpUrlInput.value = "(Local Image Attached)";
          applyTheme(currentActiveTheme, false);
          updateLiveThemePreview(currentActiveTheme);
        };
        reader.readAsDataURL(file);
      }
    });
  }

  // Sliders
  const opSlider = document.getElementById("theme-wallpaper-opacity");
  const opVal = document.getElementById("theme-wallpaper-opacity-val");
  if (opSlider) {
    opSlider.addEventListener("input", (e) => {
      const frac = parseInt(e.target.value) / 100;
      currentActiveTheme.chatBgOpacity = frac;
      if (opVal) opVal.textContent = `${e.target.value}%`;
      applyTheme(currentActiveTheme, false);
    });
  }

  const blurSlider = document.getElementById("theme-wallpaper-blur");
  const blurVal = document.getElementById("theme-wallpaper-blur-val");
  if (blurSlider) {
    blurSlider.addEventListener("input", (e) => {
      const px = parseInt(e.target.value);
      currentActiveTheme.chatBgBlur = px;
      if (blurVal) blurVal.textContent = `${px}px`;
      applyTheme(currentActiveTheme, false);
    });
  }

  // Render Preset Cards in Settings
  renderThemePresetCards();

  // Load saved theme on boot
  try {
    const saved = localStorage.getItem("modeldock_custom_theme");
    if (saved) {
      const parsed = JSON.parse(saved);
      applyTheme(parsed, true);
    } else {
      applyTheme(DEFAULT_THEME, true);
    }
  } catch (_) {
    applyTheme(DEFAULT_THEME, true);
  }
}

function renderThemePresetCards() {
  const container = document.getElementById("theme-presets-grid");
  if (!container) return;

  container.innerHTML = THEME_PRESETS.map((p) => `
    <div class="theme-preset-card ${p.id === 'obsidian' ? 'active' : ''}" data-preset-id="${p.id}" onclick="selectThemePreset('${p.id}')">
      <div class="preset-swatches">
        ${p.previewColors.map((c) => `<span class="preset-color-dot" style="background-color: ${c};"></span>`).join("")}
      </div>
      <div class="preset-name">${p.name}</div>
    </div>
  `).join("");
}

// Global Exports
window.selectThemePreset = selectThemePreset;
window.generateRandomTheme = generateRandomTheme;
window.saveCurrentTheme = saveCurrentTheme;
window.resetThemeToDefault = resetThemeToDefault;
window.exportThemeJSON = exportThemeJSON;
window.importThemeJSON = importThemeJSON;

// Auto-run when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initThemeStudio);
} else {
  initThemeStudio();
}
