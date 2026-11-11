/**
 * ModelDock Studio - Podman-Style Settings & Resource Preferences
 */

let currentSettingsCategory = "profile";

function getInitials(name) {
  if (!name) return "AI";
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function updateProfilePreview() {
  const nameInput = document.getElementById("setting-user-name");
  const titleInput = document.getElementById("setting-user-title");
  const namePrev = document.getElementById("settings-name-preview");
  const titlePrev = document.getElementById("settings-title-preview");
  const avatarPrev = document.getElementById("settings-avatar-preview");

  const name = (nameInput && nameInput.value.trim()) || "Local AI User";
  const title = (titleInput && titleInput.value.trim()) || "Local AI • Pro";

  if (namePrev) namePrev.textContent = name;
  if (titlePrev) titlePrev.textContent = title;
  if (avatarPrev) {
    avatarPrev.textContent = getInitials(name);
  }
}

async function saveUserProfile() {
  const nameInput = document.getElementById("setting-user-name");
  const titleInput = document.getElementById("setting-user-title");
  const statusSpan = document.getElementById("profile-save-status");

  const userName = nameInput ? nameInput.value.trim() || "Local AI User" : "Local AI User";
  const userTitle = titleInput ? titleInput.value.trim() || "Local AI • Pro" : "Local AI • Pro";

  try {
    localStorage.setItem("modeldock_user_name", userName);
    localStorage.setItem("modeldock_user_title", userTitle);
  } catch (e) {}

  // Save to backend configuration
  try {
    await fetch("/api/settings/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_name: userName, user_title: userTitle }),
    });
  } catch (e) {}

  if (typeof updateUserProfileInSidebar === "function") {
    updateUserProfileInSidebar();
  }

  updateProfilePreview();

  if (statusSpan) {
    statusSpan.classList.remove("hidden");
    setTimeout(() => statusSpan.classList.add("hidden"), 3000);
  }
}

function initSettings() {
  // Sidebar category switching
  document.querySelectorAll(".settings-nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const cat = btn.dataset.category;
      switchSettingsCategory(cat);
    });
  });

  // User Profile bindings
  const btnSaveProfile = document.getElementById("btn-save-profile");
  if (btnSaveProfile) btnSaveProfile.addEventListener("click", saveUserProfile);

  const nameInput = document.getElementById("setting-user-name");
  const titleInput = document.getElementById("setting-user-title");
  if (nameInput) nameInput.addEventListener("input", updateProfilePreview);
  if (titleInput) titleInput.addEventListener("input", updateProfilePreview);

  // Action button bindings
  const btnSave = document.getElementById("btn-save-settings");
  if (btnSave) btnSave.addEventListener("click", saveSettings);

  const btnBrowseModels = document.getElementById("btn-browse-models-dir");
  if (btnBrowseModels) btnBrowseModels.addEventListener("click", () => selectFolderDialog("models"));

  const btnOpenModels = document.getElementById("btn-open-models-dir");
  if (btnOpenModels) btnOpenModels.addEventListener("click", () => openFolder("models"));

  const btnBrowseDownloads = document.getElementById("btn-browse-downloads-dir");
  if (btnBrowseDownloads) btnBrowseDownloads.addEventListener("click", () => selectFolderDialog("downloads"));

  const btnOpenDownloads = document.getElementById("btn-open-downloads-dir");
  if (btnOpenDownloads) btnOpenDownloads.addEventListener("click", () => openFolder("downloads"));

  const btnPrune = document.getElementById("btn-prune-cache");
  if (btnPrune) btnPrune.addEventListener("click", pruneDownloadsCache);

  // Dynamic sliders
  const cpuSlider = document.getElementById("setting-cpu-threads");
  const cpuVal = document.getElementById("setting-cpu-val");
  if (cpuSlider && cpuVal) {
    cpuSlider.addEventListener("input", () => {
      cpuVal.textContent = cpuSlider.value;
    });
  }

  const gpuMode = document.getElementById("setting-gpu-mode");
  const gpuLayersWrap = document.getElementById("setting-gpu-layers-wrap");
  if (gpuMode && gpuLayersWrap) {
    gpuMode.addEventListener("change", () => {
      gpuLayersWrap.style.display = gpuMode.value === "custom" ? "block" : "none";
    });
  }

  const tempSlider = document.getElementById("setting-default-temp");
  const tempVal = document.getElementById("setting-temp-val");
  if (tempSlider && tempVal) {
    tempSlider.addEventListener("input", () => {
      tempVal.textContent = tempSlider.value;
    });
  }

  // Navigation Bar Position Switcher (Left Side vs Top Header)
  const navPosSelect = document.getElementById("setting-nav-position");
  if (navPosSelect) {
    navPosSelect.addEventListener("change", () => {
      const pos = navPosSelect.value;
      if (typeof applyNavPosition === "function") {
        applyNavPosition(pos);
      }
      fetch("/api/settings/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nav_position: pos }),
      }).catch(() => {});
    });
  }
}

function switchSettingsCategory(cat) {
  if (cat === "registries") cat = "auth";
  currentSettingsCategory = cat;
  document.querySelectorAll(".settings-nav-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.category === cat);
  });

  document.querySelectorAll(".settings-pane").forEach((pane) => {
    pane.classList.toggle("active", pane.id === `settings-pane-${cat}`);
  });

  if (cat === "auth" && typeof checkAuthStatus === "function") {
    checkAuthStatus();
  }

  if (cat === "appearance" && typeof updateLiveThemePreview === "function" && typeof currentActiveTheme !== "undefined") {
    updateLiveThemePreview(currentActiveTheme);
  }
}

async function loadSettings() {
  try {
    const res = await fetch("/api/settings");
    if (!res.ok) return;
    const data = await res.json();

    // CPU Threads
    const cpuSlider = document.getElementById("setting-cpu-threads");
    const cpuVal = document.getElementById("setting-cpu-val");
    const cpuMax = document.getElementById("setting-cpu-max");
    if (cpuSlider && data.cpu_threads !== undefined) {
      if (data.system_cpu_count) {
        cpuSlider.max = data.system_cpu_count;
        if (cpuMax) cpuMax.textContent = `${data.system_cpu_count} logical cores available`;
      }
      cpuSlider.value = data.cpu_threads;
      if (cpuVal) cpuVal.textContent = data.cpu_threads;
    }

    // GPU Mode & Layers
    const gpuMode = document.getElementById("setting-gpu-mode");
    const gpuLayers = document.getElementById("setting-gpu-layers");
    const gpuLayersWrap = document.getElementById("setting-gpu-layers-wrap");
    if (gpuMode) {
      gpuMode.value = data.gpu_mode || "auto";
      if (gpuLayersWrap) {
        gpuLayersWrap.style.display = gpuMode.value === "custom" ? "block" : "none";
      }
    }
    if (gpuLayers && data.gpu_layers !== undefined) {
      gpuLayers.value = data.gpu_layers;
    }

    // Context Length & Temperature
    const ctxSelect = document.getElementById("setting-default-ctx");
    if (ctxSelect && data.default_context_length) {
      ctxSelect.value = String(data.default_context_length);
    }

    const tempSlider = document.getElementById("setting-default-temp");
    const tempVal = document.getElementById("setting-temp-val");
    if (tempSlider && data.default_temperature !== undefined) {
      tempSlider.value = data.default_temperature;
      if (tempVal) tempVal.textContent = data.default_temperature;
    }

    // System Prompt
    const promptInput = document.getElementById("setting-system-prompt");
    if (promptInput && data.system_prompt) {
      promptInput.value = data.system_prompt;
    }

    // Directories
    const modelsDir = document.getElementById("setting-models-dir");
    if (modelsDir && data.models_dir) modelsDir.value = data.models_dir;

    const dlDir = document.getElementById("setting-downloads-dir");
    if (dlDir && data.downloads_dir) dlDir.value = data.downloads_dir;

    // User Profile & Identity
    const userName = data.user_name || (localStorage.getItem("modeldock_user_name") || localStorage.getItem("omnimodel_user_name")) || "Local AI User";
    const userTitle = data.user_title || (localStorage.getItem("modeldock_user_title") || localStorage.getItem("omnimodel_user_title")) || "Local AI • Pro";
    const nameInput = document.getElementById("setting-user-name");
    const titleInput = document.getElementById("setting-user-title");
    if (nameInput) nameInput.value = userName;
    if (titleInput) titleInput.value = userTitle;
    updateProfilePreview();
    if (typeof updateUserProfileInSidebar === "function") {
      updateUserProfileInSidebar();
    }

    // Navigation Position (Left Sidebar Dock vs Top Header)
    const navPos = data.nav_position || (localStorage.getItem("modeldock_nav_position") || localStorage.getItem("omnimodel_nav_position")) || "left";
    if (typeof applyNavPosition === "function") {
      applyNavPosition(navPos);
    }

    // Server Host & Port
    const sHost = document.getElementById("setting-server-host");
    if (sHost && data.server_host) sHost.value = data.server_host;

    const sPort = document.getElementById("setting-server-port");
    if (sPort && data.server_port) sPort.value = data.server_port;

    // HF Token preview
    const hfPreview = document.getElementById("setting-hf-preview");
    if (hfPreview) {
      if (data.has_hf_token) {
        hfPreview.innerHTML = `<span class="badge badge-success">Connected (${data.hf_token_preview})</span>`;
      } else {
        hfPreview.innerHTML = `<span class="badge">No token saved (Public models only)</span>`;
      }
    }
  } catch (err) {
    console.error("Failed to load settings:", err);
  }
}

async function saveSettings() {
  const btnSave = document.getElementById("btn-save-settings");
  const statusMsg = document.getElementById("settings-status-msg");

  const cpuSlider = document.getElementById("setting-cpu-threads");
  const gpuMode = document.getElementById("setting-gpu-mode");
  const gpuLayers = document.getElementById("setting-gpu-layers");
  const ctxSelect = document.getElementById("setting-default-ctx");
  const tempSlider = document.getElementById("setting-default-temp");
  const promptInput = document.getElementById("setting-system-prompt");
  const modelsDir = document.getElementById("setting-models-dir");
  const dlDir = document.getElementById("setting-downloads-dir");
  const sHost = document.getElementById("setting-server-host");
  const sPort = document.getElementById("setting-server-port");
  const navPosSelect = document.getElementById("setting-nav-position");

  const payload = {
    cpu_threads: cpuSlider ? parseInt(cpuSlider.value) : undefined,
    gpu_mode: gpuMode ? gpuMode.value : undefined,
    gpu_layers: gpuLayers ? parseInt(gpuLayers.value) : undefined,
    default_context_length: ctxSelect ? parseInt(ctxSelect.value) : undefined,
    default_temperature: tempSlider ? parseFloat(tempSlider.value) : undefined,
    system_prompt: promptInput ? promptInput.value.trim() : undefined,
    models_dir: modelsDir ? modelsDir.value.trim() : undefined,
    downloads_dir: dlDir ? dlDir.value.trim() : undefined,
    server_host: sHost ? sHost.value.trim() : undefined,
    server_port: sPort ? parseInt(sPort.value) : undefined,
    nav_position: navPosSelect ? navPosSelect.value : undefined,
  };

  if (btnSave) {
    btnSave.disabled = true;
    btnSave.textContent = "Saving...";
  }

  try {
    const res = await fetch("/api/settings/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (res.ok && data.success) {
      if (typeof loadLocalModels === "function") {
        try {
          await loadLocalModels();
        } catch (e) {
          console.warn("Model list refresh after save:", e);
        }
      }
      if (statusMsg) {
        statusMsg.innerHTML = '<span style="color: var(--accent-green);">✓ Settings saved! Model folder updated and rescanned.</span>';
        setTimeout(() => {
          statusMsg.innerHTML = "";
        }, 3000);
      }
    } else {
      if (statusMsg) {
        statusMsg.innerHTML = `<span style="color: var(--accent-red);">Failed to save: ${data.error || "Unknown error"}</span>`;
      }
    }
  } catch (err) {
    if (statusMsg) {
      statusMsg.innerHTML = `<span style="color: var(--accent-red);">Error: ${err.message}</span>`;
    }
  } finally {
    if (btnSave) {
      btnSave.disabled = false;
      btnSave.textContent = "Save Changes";
    }
  }
}

async function selectFolderDialog(folderType) {
  const inputEl = document.getElementById(folderType === "models" ? "setting-models-dir" : "setting-downloads-dir");
  const btn = document.getElementById(folderType === "models" ? "btn-browse-models-dir" : "btn-browse-downloads-dir");
  const originalHtml = btn ? btn.innerHTML : "";
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span>⏳ Selecting...</span>`;
  }

  try {
    const res = await fetch("/api/settings/select-folder", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ folder: folderType }),
    });
    const data = await res.json();
    if (res.ok && data.success && data.path) {
      if (inputEl) {
        inputEl.value = data.path;
        inputEl.style.borderColor = "var(--accent-primary, #6366f1)";
      }
      await saveSettings();
    } else if (!data.cancelled) {
      alert(`Could not select folder: ${data.error || "Operation was not completed."}`);
    }
  } catch (err) {
    console.error("Folder selection failed:", err);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = originalHtml;
    }
  }
}

async function openFolder(folderType) {
  try {
    const res = await fetch("/api/settings/open-folder", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ folder: folderType }),
    });
    const data = await res.json();
    if (!data.success) {
      alert(`Could not open folder: ${data.error}`);
    }
  } catch (e) {
    alert(`Error: ${e.message}`);
  }
}

async function pruneDownloadsCache() {
  if (!confirm("Clean temporary or interrupted download fragments (.tmp, .part) from the downloads folder?")) return;

  try {
    const res = await fetch("/api/settings/prune-downloads", { method: "POST" });
    const data = await res.json();
    if (res.ok && data.success) {
      alert(`Cache pruned! Cleaned ${data.deleted_count} temporary files and reclaimed ${data.freed_mb} MB of disk space.`);
    } else {
      alert("Prune completed.");
    }
  } catch (e) {
    alert(`Error: ${e.message}`);
  }
}
