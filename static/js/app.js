/**
 * ModelDock Studio - Main App State & Navigation Controller
 */

const AppState = {
  currentTab: "chat",
  localModels: [],
  selectedModel: null,
  hfUser: null,
  isAuthenticated: false,
  downloadTasks: {},
};

// Tab Switching
function switchTab(tabId) {
  if (tabId === "auth") {
    openAuthSettings();
    return;
  }
  if (tabId === "library") {
    tabId = "models";
  }

  AppState.currentTab = tabId;

  // Update navbar buttons
  document.querySelectorAll(".nav-tab").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tabId);
  });

  // Update tab content sections
  document.querySelectorAll(".tab-content").forEach((section) => {
    section.classList.toggle("active", section.id === `tab-${tabId}`);
  });

  // Tab specific refreshes
  if (tabId === "models") {
    loadLocalModels();
  } else if (tabId === "hf-hub") {
    if (!window.hfHubLoaded) {
      loadFeaturedHFModels();
      window.hfHubLoaded = true;
    }
  } else if (tabId === "downloads") {
    pollDownloadTasks();
  } else if (tabId === "system") {
    refreshTelemetry();
  } else if (tabId === "settings") {
    loadSettings();
    if (typeof checkAuthStatus === "function") {
      checkAuthStatus();
    }
  }
}

// Open Settings directly at Profile & Identity
function openProfileSettings() {
  switchTab("settings");
  if (typeof switchSettingsCategory === "function") {
    switchSettingsCategory("profile");
  }
}

// Open Settings directly at Authentication & Keys
function openAuthSettings() {
  switchTab("settings");
  if (typeof switchSettingsCategory === "function") {
    switchSettingsCategory("auth");
  }
  setTimeout(() => {
    const tokenInput = document.getElementById("hf-token-input") || document.getElementById("hf-token");
    if (tokenInput) {
      tokenInput.scrollIntoView({ behavior: "smooth", block: "center" });
      tokenInput.focus();
      tokenInput.classList.add("input-pulse-highlight");
      setTimeout(() => tokenInput.classList.remove("input-pulse-highlight"), 2500);
    }
  }, 150);
}

// Open Hugging Face token page in a new browser tab AND navigate to Auth settings
function openHuggingFaceTokenPageAndAuth() {
  try {
    window.open("https://huggingface.co/settings/tokens", "_blank", "noopener,noreferrer");
  } catch (e) {
    console.warn("Failed to open popup tab:", e);
  }
  openAuthSettings();
}

// Switch Navigation Position (Left, Top, Right, or Bottom / Down)
function applyNavPosition(pos) {
  let target = (pos || "left").toLowerCase().trim();
  if (target === "down") target = "bottom";
  if (!["left", "top", "right", "bottom"].includes(target)) {
    target = "left";
  }

  // Clear all position classes
  document.body.classList.remove(
    "layout-nav-left",
    "layout-nav-top",
    "layout-nav-right",
    "layout-nav-bottom",
    "layout-nav-down"
  );
  // Add active layout class
  document.body.classList.add(`layout-nav-${target}`);

  const select = document.getElementById("setting-nav-position");
  if (select && select.value !== target) {
    select.value = target;
  }
  const badge = document.getElementById("nav-pos-badge");
  if (badge) {
    const titles = {
      left: "Active: Left Sidebar",
      top: "Active: Top Header",
      right: "Active: Right Sidebar",
      bottom: "Active: Bottom Dock",
    };
    badge.textContent = titles[target] || "Active: Left Sidebar";
    badge.className = target === "left" ? "badge badge-cyan" : "badge badge-success";
  }
  try {
    localStorage.setItem("modeldock_nav_position", target);
  } catch (e) {}
}

// Global Initialization
document.addEventListener("DOMContentLoaded", () => {
  // Apply saved or default Navigation Position (Default: Left Side)
  const savedPos = (localStorage.getItem("modeldock_nav_position") || localStorage.getItem("omnimodel_nav_position")) || "left";
  applyNavPosition(savedPos);

  // Tab click bindings
  document.querySelectorAll(".nav-tab").forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });

  // Initialize Sub-Systems
  initMonitor();
  initAuth();
  initHFHub();
  initModels();
  initChat();
  initSettings();

  // Load initial settings & profile
  loadSettings();
  if (typeof updateUserProfileInSidebar === "function") {
    updateUserProfileInSidebar();
  }

  // Load initial local models
  loadLocalModels();
});
