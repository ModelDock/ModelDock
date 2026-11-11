/**
 * ModelDock Studio - Hugging Face Hub Explorer & Model Downloader
 */

let omniSearchDebounceTimer = null;

function initHFHub() {
  const btnSearch = document.getElementById("btn-hf-search");
  const queryInput = document.getElementById("hf-search-query");
  const sortSelect = document.getElementById("hf-sort-select");
  const btnFeatured = document.getElementById("btn-show-featured");

  if (btnSearch) {
    btnSearch.addEventListener("click", () => {
      clearTimeout(omniSearchDebounceTimer);
      hideOmniDropdown();
      searchHFHub();
    });
  }

  // Instant Live Type-Ahead Listener: Renders model cards directly in the grid with every single character typed
  if (queryInput) {
    queryInput.addEventListener("input", (e) => {
      clearTimeout(omniSearchDebounceTimer);
      hideOmniDropdown();
      const q = e.target.value.trim();
      if (!q) {
        loadFeaturedHFModels();
        return;
      }
      // Instant 0ms local match card preview directly in the main grid
      renderLiveSearchPreview(q);
      // Debounce Hugging Face & Catalog model search
      omniSearchDebounceTimer = setTimeout(() => {
        searchHFHub(q);
      }, 180);
    });

    queryInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        clearTimeout(omniSearchDebounceTimer);
        hideOmniDropdown();
        searchHFHub();
      } else if (e.key === "Escape") {
        queryInput.value = "";
        hideOmniDropdown();
        loadFeaturedHFModels();
      }
    });
  }

  // Dismiss any legacy dropdown
  document.addEventListener("click", () => {
    hideOmniDropdown();
  });

  if (sortSelect) {
    sortSelect.addEventListener("change", () => searchHFHub());
  }

  const platformSelect = document.getElementById("hub-platform-filter");
  if (platformSelect) {
    platformSelect.addEventListener("change", (e) => {
      setPlatformFilter(e.target.value);
    });
  }

  if (btnFeatured) {
    btnFeatured.addEventListener("click", () => {
      if (queryInput) queryInput.value = "";
      hideOmniDropdown();
      loadFeaturedHFModels();
    });
  }

  // Ollama Pull Button
  const btnOllamaPull = document.getElementById("btn-ollama-pull");
  const ollamaPullInput = document.getElementById("ollama-pull-input");
  if (btnOllamaPull) {
    btnOllamaPull.addEventListener("click", pullOllamaModel);
  }
  if (ollamaPullInput) {
    ollamaPullInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") pullOllamaModel();
    });
  }

  // Clear Completed Downloads Button
  const btnClearDL = document.getElementById("btn-clear-completed-dl");
  if (btnClearDL) {
    btnClearDL.addEventListener("click", clearCompletedDownloads);
  }
}

// --- Instant Type-Ahead Dropdown Controller ---
function hideOmniDropdown() {
  const dd = document.getElementById("omni-search-dropdown");
  if (dd) {
    dd.classList.add("hidden");
    dd.style.display = "none";
  }
}

async function performOmniLiveSearch(query) {
  const dd = document.getElementById("omni-search-dropdown");
  if (!dd) return;

  try {
    const res = await fetch(`/api/search/omni?q=${encodeURIComponent(query)}`);
    if (!res.ok) return;
    const data = await res.json();

    const localList = data.local || [];
    const catalogList = data.catalog || [];
    const hfList = data.huggingface || [];

    const totalResults = localList.length + catalogList.length + hfList.length;
    if (totalResults === 0) {
      dd.innerHTML = `<div style="padding: 0.85rem; font-size: 0.82rem; color: var(--text-muted); text-align: center;">No matches for "${query}". Hit Enter to search full Hugging Face Hub.</div>`;
      dd.classList.remove("hidden");
      return;
    }

    let html = "";

    // 1. Locally Installed Models (Instant 0ms Run)
    if (localList.length > 0) {
      html += `<div class="omni-search-group">⚡ Installed on this PC (Ready to Run)</div>`;
      html += localList
        .map(
          (m) => `
        <div class="omni-search-item" onclick="selectOmniLocal('${m.name}')">
          <div class="omni-item-left">
            <span class="omni-item-icon">⚡</span>
            <div class="omni-item-details">
              <span class="omni-item-title">${m.name}</span>
              <span class="omni-item-sub">${m.size_formatted} • ${m.quantization || "GGUF"}</span>
            </div>
          </div>
          <div class="omni-item-right">
            <span class="omni-badge-local">Installed</span>
            <button class="btn-primary btn-sm" style="padding: 0.2rem 0.5rem; font-size: 0.72rem;">Run in Chat 💬</button>
          </div>
        </div>
      `
        )
        .join("");
    }

    // 2. Curated Open-Source Models (Ollama / Hugging Face Catalog)
    if (catalogList.length > 0) {
      html += `<div class="omni-search-group">🦙 Open-Source Catalog (1-Click Pull)</div>`;
      html += catalogList
        .map(
          (m) => `
        <div class="omni-search-item" onclick="selectOmniCatalog('${m.id}', '${m.tag}')">
          <div class="omni-item-left">
            <span class="omni-item-icon">📦</span>
            <div class="omni-item-details">
              <span class="omni-item-title">${m.name}</span>
              <span class="omni-item-sub">${m.id} • ${m.type || "LLM"}</span>
            </div>
          </div>
          <div class="omni-item-right">
            <span class="omni-badge-ollama">${m.size}</span>
            <button class="btn-secondary btn-sm" style="padding: 0.2rem 0.5rem; font-size: 0.72rem;">Inspect GGUF</button>
          </div>
        </div>
      `
        )
        .join("");
    }

    // 3. Live Hugging Face Hub Repositories
    if (hfList.length > 0) {
      html += `<div class="omni-search-group">🤗 Hugging Face Hub Repositories</div>`;
      html += hfList
        .map(
          (m) => `
        <div class="omni-search-item" onclick="selectOmniHF('${m.id}')">
          <div class="omni-item-left">
            <span class="omni-item-icon">🤗</span>
            <div class="omni-item-details">
              <span class="omni-item-title">${m.name}</span>
              <span class="omni-item-sub">${m.author} • ⬇️ ${m.downloads.toLocaleString()}</span>
            </div>
          </div>
          <div class="omni-item-right">
            ${m.gated ? '<span class="badge" style="color: #fbbf24;">🔒 Gated</span>' : '<span class="omni-badge-hf">GGUF</span>'}
            <button class="btn-secondary btn-sm" style="padding: 0.2rem 0.5rem; font-size: 0.72rem;">Inspect</button>
          </div>
        </div>
      `
        )
        .join("");
    }

    dd.innerHTML = html;
    dd.classList.remove("hidden");
  } catch (err) {
    console.error("Live search error:", err);
  }
}

function selectOmniLocal(modelName) {
  hideOmniDropdown();
  selectModelAndChat(modelName);
}

function selectOmniCatalog(repoId, tag) {
  hideOmniDropdown();
  openInspectModal(repoId);
}

function selectOmniHF(repoId) {
  hideOmniDropdown();
  openInspectModal(repoId);
}

// Quick Ollama Model selection helper
function setOllamaPullModel(name) {
  const input = document.getElementById("ollama-pull-input");
  if (input) {
    input.value = name;
    pullOllamaModel();
  }
}

async function pullOllamaModel() {
  const input = document.getElementById("ollama-pull-input");
  const modelName = input ? input.value.trim() : "";
  if (!modelName) {
    alert("Please enter a model name to pull (e.g. llama3.2:1b, deepseek-r1:1.5b).");
    return;
  }

  const btn = document.getElementById("btn-ollama-pull");
  if (btn) btn.disabled = true;

  try {
    const res = await fetch("/api/downloads/pull-ollama", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model_name: modelName }),
    });

    const data = await res.json();
    if (res.ok && data.success) {
      if (input) input.value = "";
      pollDownloadTasks();
      switchTab("downloads");
    } else {
      alert(`Ollama pull error: ${data.detail || data.error || "Failed to start"}`);
    }
  } catch (err) {
    alert(`Request error: ${err.message}`);
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function pauseDownload(taskId) {
  try {
    const res = await fetch("/api/downloads/pause", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_id: taskId }),
    });
    if (res.ok) {
      pollDownloadTasks();
    }
  } catch (err) {
    console.error("Pause error:", err);
  }
}

async function resumeDownload(taskId) {
  try {
    const res = await fetch("/api/downloads/resume", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_id: taskId }),
    });
    if (res.ok) {
      pollDownloadTasks();
    }
  } catch (err) {
    console.error("Resume error:", err);
  }
}

async function cancelDownload(taskId) {
  if (!confirm("Are you sure you want to cancel this download?")) return;
  try {
    const res = await fetch("/api/downloads/cancel", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_id: taskId }),
    });
    if (res.ok) {
      pollDownloadTasks();
    }
  } catch (err) {
    console.error("Cancel error:", err);
  }
}

function clearCompletedDownloads() {
  const container = document.getElementById("downloads-list");
  if (container) {
    container.querySelectorAll(".card-ready, .card-cancelled, .card-failed").forEach((el) => el.remove());
  }
}

function setPlatformFilter(platform) {
  const select = document.getElementById("hub-platform-filter");
  if (select && select.value !== platform) {
    select.value = platform;
  }
  document.querySelectorAll(".platform-chip").forEach((chip) => {
    if (chip.getAttribute("data-platform") === platform) {
      chip.classList.add("active");
    } else {
      chip.classList.remove("active");
    }
  });

  const queryInput = document.getElementById("hf-search-query");
  const q = queryInput ? queryInput.value.trim() : "";
  if (q) {
    searchHFHub(q);
  } else {
    loadFeaturedHFModels();
  }
}

async function loadFeaturedHFModels() {
  const grid = document.getElementById("hf-models-grid");
  const title = document.getElementById("hub-grid-title");
  const platformSelect = document.getElementById("hub-platform-filter");
  const platform = platformSelect ? platformSelect.value : "all";

  const platformTitle = platform === "ollama" ? "Ollama Library" : (platform === "huggingface" ? "Hugging Face Hub" : "Hugging Face & Ollama");
  if (title) title.textContent = `⭐ Featured & Popular Open-Source Models (${platformTitle})`;
  if (grid) grid.innerHTML = `<div class="loading-spinner">Loading ${platformTitle} catalog...</div>`;

  try {
    let hfPromise = Promise.resolve([]);
    let ollamaPromise = Promise.resolve([]);

    if (platform === "all" || platform === "huggingface") {
      hfPromise = fetch("/api/hf/featured").then((r) => r.json()).catch(() => []);
    }
    if (platform === "all" || platform === "ollama") {
      ollamaPromise = fetch("/api/ollama/featured").then((r) => r.json()).catch(() => []);
    }

    const [hfModels, ollamaModels] = await Promise.all([hfPromise, ollamaPromise]);
    let cardsHtml = "";
    if (ollamaModels && ollamaModels.length > 0) {
      cardsHtml += ollamaModels.map((m) => renderOllamaCardHTML(m)).join("");
    }
    if (hfModels && hfModels.length > 0) {
      cardsHtml += renderFeaturedCards(hfModels);
    }
    if (!cardsHtml) {
      if (grid) grid.innerHTML = '<div class="empty-state">No models found.</div>';
    } else {
      if (grid) grid.innerHTML = cardsHtml;
    }
  } catch (err) {
    if (grid) grid.innerHTML = `<div class="empty-state">Failed to load models: ${err.message}</div>`;
  }
}

function renderFeaturedCards(models) {
  if (!models || models.length === 0) return "";

  return models
    .map((m) => {
      const gatedBadge = m.gated
        ? '<span class="badge badge-gated">🔒 Gated</span>'
        : '<span class="badge badge-cyan">Open Access</span>';

      return `
      <div class="model-card" onclick="openInspectModal('${m.id}')" style="cursor: pointer;" title="Click to inspect model specs and download weights">
        <div class="card-top">
          <div class="card-header-row">
            <div class="card-header-titles">
              <div class="model-name" title="${m.name}">${m.name}</div>
              <div class="model-author" title="${m.id}">${m.id}</div>
            </div>
            <div style="display: flex; gap: 0.35rem; align-items: center;">
              <span class="badge" style="background: rgba(251, 146, 60, 0.15); color: #fb923c; border: 1px solid rgba(251, 146, 60, 0.35);">🤗 Hugging Face</span>
              ${gatedBadge}
            </div>
          </div>
          <p class="card-desc" title="${m.description}">${m.description}</p>
          <div class="tags-row">
            <span class="badge badge-cyan">${m.category}</span>
            <span class="badge">${m.parameters} Params</span>
            <span class="badge badge-rec" title="${m.quant_rec}">Rec: ${m.quant_rec}</span>
          </div>
        </div>
        <div class="card-footer">
          <div class="card-stats">
            <span class="card-stat-item" title="${m.likes.toLocaleString()} likes">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" style="color: #f43f5e;"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
              <span>${m.likes.toLocaleString()}</span>
            </span>
            <span class="stat-sep">•</span>
            <span class="card-stat-item" title="${m.downloads} downloads">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="color: #38bdf8;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
              <span>${m.downloads}</span>
            </span>
          </div>
          <button class="btn-inspect-action" onclick="event.stopPropagation(); openInspectModal('${m.id}')">
            <span>Inspect & Get</span>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"></polyline></svg>
          </button>
        </div>
      </div>
    `;
    })
    .join("");
}

function escapeHubHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function renderInstalledCardHTML(m) {
  const displayName = m.alias || m.name || "Unknown";
  const safeName = escapeHubHtml(displayName);
  const aliasBadge = m.alias ? `<span class="badge" style="background: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.4); font-size: 0.68rem; font-weight: 600;">🏷️ ${escapeHubHtml(m.name)}</span>` : "";
  const rawName = (m.name || "Unknown").replace(/'/g, "\\'");
  const sizeText = m.size_formatted || "Ready";
  const paramText = m.parameter_size || "Quantized";
  const quantText = m.quantization || "GGUF";
  const archText = m.family || m.architecture || "Local Engine";

  return `
    <div class="model-card model-card-installed" style="border: 1px solid rgba(16, 185, 129, 0.45); background: linear-gradient(180deg, rgba(16, 185, 129, 0.08) 0%, rgba(30, 41, 59, 0.7) 100%);">
      <div class="card-top">
        <div class="card-header-row">
          <div class="card-header-titles">
            <div class="model-name" title="${escapeHubHtml(m.name)}" style="display: flex; align-items: center; gap: 0.35rem;">
              <span style="color: #10b981; font-size: 0.95rem;">⚡</span>
              <span>${safeName}</span>
              ${aliasBadge}
            </div>
            <div class="model-author" title="Installed locally on this PC">Installed on this PC • ${escapeHubHtml(m.source || "Native GGUF")}</div>
          </div>
          <span class="badge badge-success flex-shrink-0" style="background: rgba(16, 185, 129, 0.2); color: #34d399; border-color: rgba(16, 185, 129, 0.4);">✓ Installed</span>
        </div>
        <p class="card-desc" style="color: var(--text-secondary); font-size: 0.8rem; margin: 0.35rem 0;">Ready to run offline right now with zero downloading required.</p>
        <div class="tags-row">
          <span class="badge badge-cyan">${escapeHubHtml(paramText)}</span>
          <span class="badge">${escapeHubHtml(quantText)}</span>
          <span class="badge">${escapeHubHtml(sizeText)}</span>
          <span class="badge">${escapeHubHtml(archText)}</span>
        </div>
      </div>
      <div class="card-footer" style="display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 0.75rem;">
        <button class="btn-secondary btn-sm" onclick="event.stopPropagation(); if (typeof showModelDetails === 'function') showModelDetails('${rawName}')" title="Inspect model specifications">
          🔍 Specs
        </button>
        <button class="btn-primary btn-sm" onclick="event.stopPropagation(); selectModelAndChat('${rawName}')" style="background: linear-gradient(135deg, #059669 0%, #10b981 100%); border-color: #059669; font-weight: 600;">
          Run in Chat 💬
        </button>
      </div>
    </div>
  `;
}

function renderOllamaCardHTML(m) {
  const safeName = escapeHubHtml(m.name || m.tag || "Unknown");
  const safeTag = escapeHubHtml(m.tag || m.id || "");
  const rawTag = (m.tag || m.id || "").replace(/'/g, "\\'");
  const rawName = (m.name || m.tag || "").replace(/'/g, "\\'");
  const repoId = (m.repo_id || m.id || m.tag || "").replace(/'/g, "\\'");
  const inspectTarget = rawTag || repoId;

  // Check if already installed
  const isInstalled = (AppState.localModels || []).some((lm) => {
    const lName = (lm.name || "").toLowerCase();
    const lTag = (m.tag || m.id || "").toLowerCase();
    return lName.includes(lTag) || (lm.alias && lm.alias.toLowerCase().includes(lTag));
  });

  const actionButton = isInstalled
    ? `<button class="btn-primary btn-sm" onclick="event.stopPropagation(); selectModelAndChat('${rawName}')" style="background: linear-gradient(135deg, #059669 0%, #10b981 100%); border-color: #059669; font-weight: 600;">
         <span>Run in Chat</span> 💬
       </button>`
    : `<button class="btn-primary btn-sm" onclick="event.stopPropagation(); pullOllamaDirect('${rawTag}', '${rawName}')" style="background: linear-gradient(135deg, #0284c7 0%, #38bdf8 100%); border-color: #0284c7; font-weight: 600;">
         <span>Pull Model</span> ⬇️
       </button>`;

  return `
    <div class="model-card" onclick="openInspectModal('${inspectTarget}', '${rawTag}')" style="cursor: pointer; border: 1px solid rgba(56, 189, 248, 0.25);" title="Click to view complete ${safeName} specifications, parameters, and architecture">
      <div class="card-top">
        <div class="card-header-row">
          <div class="card-header-titles">
            <div class="model-name" title="${safeName}" style="display: flex; align-items: center; gap: 0.35rem;">
              <span>🦙</span>
              <span>${safeName}</span>
            </div>
            <div class="model-author" title="${safeTag}">${safeTag} • Ollama Library</div>
          </div>
          <span class="badge" style="background: rgba(14, 165, 233, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.35);">🦙 Ollama</span>
        </div>
        <p class="card-desc" title="${escapeHubHtml(m.description || '')}" style="color: var(--text-secondary); font-size: 0.8rem; margin: 0.35rem 0;">
          ${escapeHubHtml(m.description || "Official model optimized for local inference.")}
        </p>
        <div class="tags-row">
          ${m.parameters ? `<span class="badge badge-cyan">${escapeHubHtml(m.parameters)}</span>` : ""}
          ${m.size ? `<span class="badge">💾 ${escapeHubHtml(m.size)}</span>` : ""}
          ${m.family ? `<span class="badge">${escapeHubHtml(m.family)}</span>` : ""}
          ${m.category ? `<span class="badge badge-rec">${escapeHubHtml(m.category)}</span>` : ""}
        </div>
      </div>
      <div class="card-footer" style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.75rem;">
        <div class="card-stats">
          <span class="card-stat-item" title="Popularity in Ollama Library">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="color: #38bdf8;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            <span>${escapeHubHtml(m.pull_count || m.downloads || "Popular")}</span>
          </span>
        </div>
        <div style="display: flex; gap: 0.4rem; align-items: center;">
          <button class="btn-secondary btn-sm" onclick="event.stopPropagation(); openInspectModal('${inspectTarget}', '${rawTag}')" title="Inspect model specifications, context window, and architecture">
            🔍 Specs &amp; Details
          </button>
          ${actionButton}
        </div>
      </div>
    </div>
  `;
}

async function pullOllamaDirect(tag, name) {
  if (!tag) return;
  const displayName = name || tag;
  if (!confirm(`Do you want to 1-click pull "${displayName}" (${tag}) from Ollama Library into your local library?`)) {
    return;
  }
  try {
    const res = await fetch("/api/downloads/pull-ollama", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model_name: tag }),
    });
    const data = await res.json();
    if (res.ok && data.success) {
      if (typeof showToast === "function") {
        showToast(`Started downloading ${displayName}...`, "success");
      }
      pollDownloadTasks();
      switchTab("downloads");
    } else {
      alert(`Pull failed: ${data.detail || data.error || "Unknown error"}`);
    }
  } catch (err) {
    alert(`Pull request error: ${err.message}`);
  }
}

function renderHFCardHTML(m) {
  const safeName = escapeHubHtml(m.name || m.id || "Unknown");
  const safeId = escapeHubHtml(m.id || "");
  const rawId = (m.id || "").replace(/'/g, "\\'");
  const gatedBadge = m.gated
    ? '<span class="badge badge-gated">🔒 Gated</span>'
    : '<span class="badge badge-cyan">GGUF</span>';

  return `
    <div class="model-card" onclick="openInspectModal('${rawId}')" style="cursor: pointer;" title="Click to inspect model specs and download weights">
      <div class="card-top">
        <div class="card-header-row">
          <div class="card-header-titles">
            <div class="model-name" title="${safeName}">${safeName}</div>
            <div class="model-author" title="${safeId}">${safeId}</div>
          </div>
          <div style="display: flex; gap: 0.35rem; align-items: center;">
            <span class="badge" style="background: rgba(251, 146, 60, 0.15); color: #fb923c; border: 1px solid rgba(251, 146, 60, 0.35);">🤗 Hugging Face</span>
            ${gatedBadge}
          </div>
        </div>
        <div class="tags-row">
          ${(m.tags || []).slice(0, 3).map((t) => `<span class="badge">${escapeHubHtml(t)}</span>`).join("")}
        </div>
      </div>
      <div class="card-footer">
        <div class="card-stats">
          <span class="card-stat-item" title="${(m.likes || 0).toLocaleString()} likes">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" style="color: #f43f5e;"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
            <span>${(m.likes || 0).toLocaleString()}</span>
          </span>
          <span class="stat-sep">•</span>
          <span class="card-stat-item" title="${(m.downloads || 0).toLocaleString()} downloads">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="color: #38bdf8;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            <span>${(m.downloads || 0).toLocaleString()}</span>
          </span>
        </div>
        <button class="btn-inspect-action" onclick="event.stopPropagation(); openInspectModal('${rawId}')">
          <span>Inspect & Get</span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"></polyline></svg>
        </button>
      </div>
    </div>
  `;
}

function renderLiveSearchPreview(q) {
  const grid = document.getElementById("hf-models-grid");
  const title = document.getElementById("hub-grid-title");
  const platformSelect = document.getElementById("hub-platform-filter");
  const platform = platformSelect ? platformSelect.value : "all";
  const platformTitle = platform === "ollama" ? "Ollama Library" : (platform === "huggingface" ? "Hugging Face Hub" : "All Platforms");

  if (title) title.textContent = `🔍 Search Results for "${q}" (${platformTitle})`;
  if (!grid) return;

  const qLower = q.toLowerCase();
  const localMatches = (AppState.localModels || []).filter((m) => {
    const name = (m.name || "").toLowerCase();
    const alias = (m.alias || "").toLowerCase();
    const fn = (m.filename || "").toLowerCase();
    const arch = (m.architecture || "").toLowerCase();
    const fam = (m.family || "").toLowerCase();
    return name.includes(qLower) || alias.includes(qLower) || fn.includes(qLower) || arch.includes(qLower) || fam.includes(qLower);
  });

  if (localMatches.length > 0) {
    let html = localMatches.map((m) => renderInstalledCardHTML(m)).join("");
    html += `
      <div class="model-card" style="border: 1px dashed var(--border-subtle); display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 180px; text-align: center; color: var(--text-muted); background: rgba(255, 255, 255, 0.01);">
        <div class="loading-spinner-sm" style="margin-bottom: 0.5rem;"></div>
        <span style="font-size: 0.84rem;">Searching ${platformTitle} for "<strong>${escapeHubHtml(q)}</strong>"...</span>
      </div>
    `;
    grid.innerHTML = html;
  } else {
    grid.innerHTML = `
      <div class="loading-spinner" style="grid-column: 1 / -1; padding: 3rem 1rem;">
        Searching ${platformTitle} for "<strong>${escapeHubHtml(q)}</strong>"...
      </div>
    `;
  }
}

async function searchHFHub(customQuery) {
  const queryInput = document.getElementById("hf-search-query");
  const sortSelect = document.getElementById("hf-sort-select");
  const platformSelect = document.getElementById("hub-platform-filter");
  const grid = document.getElementById("hf-models-grid");
  const title = document.getElementById("hub-grid-title");

  const query = (typeof customQuery === "string" ? customQuery : (queryInput ? queryInput.value : "")).trim();
  const sort = sortSelect ? sortSelect.value : "downloads";
  const platform = platformSelect ? platformSelect.value : "all";

  if (!query) {
    loadFeaturedHFModels();
    return;
  }

  const platformTitle = platform === "ollama" ? "Ollama Library" : (platform === "huggingface" ? "Hugging Face Hub" : "All Platforms");
  if (title) title.textContent = `🔍 Search Results for "${query}" (${platformTitle})`;

  // Match locally installed models (0ms)
  const qLower = query.toLowerCase();
  const localMatches = (AppState.localModels || []).filter((m) => {
    const name = (m.name || "").toLowerCase();
    const alias = (m.alias || "").toLowerCase();
    const fn = (m.filename || "").toLowerCase();
    const arch = (m.architecture || "").toLowerCase();
    const fam = (m.family || "").toLowerCase();
    return name.includes(qLower) || alias.includes(qLower) || fn.includes(qLower) || arch.includes(qLower) || fam.includes(qLower);
  });

  try {
    let hfPromise = Promise.resolve([]);
    let ollamaPromise = Promise.resolve([]);

    if (platform === "all" || platform === "huggingface") {
      hfPromise = fetch(`/api/hf/search?q=${encodeURIComponent(query)}&sort=${sort}&filter=gguf`)
        .then((r) => r.json())
        .catch(() => []);
    }

    if (platform === "all" || platform === "ollama") {
      ollamaPromise = fetch(`/api/ollama/search?q=${encodeURIComponent(query)}`)
        .then((r) => r.json())
        .catch(() => []);
    }

    const [hfResults, ollamaResults] = await Promise.all([hfPromise, ollamaPromise]);
    const totalResults = localMatches.length + (hfResults || []).length + (ollamaResults || []).length;

    if (totalResults === 0) {
      if (grid) {
        grid.innerHTML = `
          <div class="empty-state" style="grid-column: 1 / -1;">
            <h3>No models found matching "${escapeHubHtml(query)}" on ${platformTitle}</h3>
            <p style="margin-top: 0.5rem; color: var(--text-muted);">Try searching for 'llama', 'deepseek', 'qwen', or 'mistral', or select 'All Platforms'.</p>
          </div>
        `;
      }
      return;
    }

    let cardsHtml = "";
    if (localMatches.length > 0) {
      cardsHtml += localMatches.map((m) => renderInstalledCardHTML(m)).join("");
    }
    if (ollamaResults && ollamaResults.length > 0) {
      cardsHtml += ollamaResults.map((m) => renderOllamaCardHTML(m)).join("");
    }
    if (hfResults && hfResults.length > 0) {
      cardsHtml += hfResults.map((m) => renderHFCardHTML(m)).join("");
    }

    if (grid) grid.innerHTML = cardsHtml;
  } catch (err) {
    if (localMatches.length > 0) {
      if (grid) grid.innerHTML = localMatches.map((m) => renderInstalledCardHTML(m)).join("");
    } else if (grid) {
      grid.innerHTML = `<div class="empty-state" style="grid-column: 1 / -1;">Search error: ${escapeHubHtml(err.message)}</div>`;
    }
  }
}

// Modal Inspect GGUF Quantizations & Full Model Specs
async function openInspectModal(repoId, ollamaTag = "") {
  const modal = document.getElementById("modal-repo-inspect");
  const title = document.getElementById("inspect-modal-title");
  const source = document.getElementById("inspect-modal-source");
  const access = document.getElementById("inspect-modal-access");
  const repoBadge = document.getElementById("inspect-modal-repo-id");
  const sourceLink = document.getElementById("inspect-modal-source-link");
  const sourceText = document.getElementById("inspect-modal-source-text");
  const desc = document.getElementById("inspect-modal-desc");
  const list = document.getElementById("inspect-files-list");
  const tagsList = document.getElementById("inspect-tags-list");

  const specArch = document.getElementById("inspect-spec-arch");
  const specParams = document.getElementById("inspect-spec-params");
  const specSize = document.getElementById("inspect-spec-size");
  const specCtx = document.getElementById("inspect-spec-ctx");
  const specLicense = document.getElementById("inspect-spec-license");
  const specTask = document.getElementById("inspect-spec-task");
  const specVram = document.getElementById("inspect-spec-vram");

  const isOllama = Boolean(ollamaTag || (repoId && !repoId.includes("/")));
  const cleanTag = (ollamaTag || repoId || "").trim();

  modal.classList.remove("hidden");
  title.textContent = isOllama ? `${cleanTag} Specifications` : "Loading Model Specifications...";
  repoBadge.textContent = isOllama ? `${cleanTag} • Ollama Library` : repoId;
  if (source) {
    source.textContent = isOllama ? "🦙 Ollama Library" : "🤗 Hugging Face";
    source.className = isOllama ? "badge badge-cyan" : "badge";
  }
  if (access) {
    access.textContent = isOllama ? "🔓 Open Access (Local Pull)" : "Open Access";
    access.className = "badge badge-success";
  }
  if (sourceLink) {
    sourceLink.href = isOllama ? `https://ollama.com/library/${encodeURIComponent(cleanTag)}` : `https://huggingface.co/${repoId}`;
    sourceLink.title = isOllama ? "Open on Ollama Library" : "Open Repository on Hugging Face";
  }
  if (sourceText) {
    sourceText.textContent = isOllama ? "View on Ollama Library" : "View on Hugging Face";
  }

  desc.textContent = isOllama 
    ? `Inspecting official ${cleanTag} architecture, context window, and quantization tiers for Ollama...`
    : "Fetching complete architecture, parameters, license, and GGUF files from source repository...";
  list.innerHTML = `<div class="loading-spinner">Fetching available ${isOllama ? "Ollama model tiers" : "GGUF quantizations"} from source...</div>`;
  if (tagsList) tagsList.innerHTML = "";

  try {
    const res = await fetch(`/api/hf/inspect?repo_id=${encodeURIComponent(repoId)}`);
    const data = await res.json();
    const isActuallyOllama = Boolean(data.is_ollama || isOllama || (data.source_platform && data.source_platform.includes("Ollama")));

    if (data.error) {
      desc.textContent = data.error;
      if (isActuallyOllama) {
        list.innerHTML = `
          <div class="status-banner" style="background: rgba(14, 165, 233, 0.12); border: 1px solid rgba(56, 189, 248, 0.35); padding: 1rem; border-radius: var(--radius-md);">
            <div style="font-weight: 600; color: #38bdf8; display: flex; align-items: center; gap: 0.35rem; margin-bottom: 0.5rem;">
              <span>🦙</span>
              <span>Ollama Library Model: <code>${escapeHubHtml(cleanTag)}</code></span>
            </div>
            <p style="margin: 0 0 0.85rem 0; font-size: 0.84rem; color: var(--text-secondary); line-height: 1.45;">
              This model is available for 1-click execution directly via your local Ollama runtime. No Hugging Face token required.
            </p>
            <button class="btn-primary btn-sm" onclick="closeInspectModal(); pullOllamaDirect('${escapeHubHtml(cleanTag)}', '${escapeHubHtml(cleanTag)}')" style="background: linear-gradient(135deg, #0284c7 0%, #38bdf8 100%); border-color: #0284c7; font-weight: 600;">
              ⬇️ Pull via Ollama (${escapeHubHtml(cleanTag)})
            </button>
          </div>
        `;
        return;
      }

      const isAuthError = /access denied|token|gated|401|403|unauthorized/i.test(data.error);
      list.innerHTML = `
        <div class="status-banner banner-error" style="padding: 0.85rem; border-radius: var(--radius-md);">
          <div style="font-weight: 600; font-size: 0.88rem; color: #fff; margin-bottom: 0.35rem;">⚠️ ${data.error}</div>
          <p style="margin: 0.25rem 0 0.75rem 0; font-size: 0.83rem; color: #fca5a5; line-height: 1.45;">
            ${isAuthError 
              ? "If this is a gated model (like official Meta Llama 3 or Google Gemma 2), ensure you have accepted the repository terms on Hugging Face and connected your User Access Token."
              : "An error occurred while inspecting repository weights."}
          </p>
          <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; margin-top: 0.6rem;">
            <button class="btn-primary btn-sm" onclick="openHuggingFaceTokenPageAndAuth()" title="Opens Hugging Face in new tab and jumps directly to Auth Settings in this app">
              🔑 Get Auth Token &amp; Fill Here ↗
            </button>
            <button class="btn-secondary btn-sm" onclick="openAuthSettings()" title="Go to Auth &amp; Keys in Settings">
              ⚙️ Go to Auth &amp; Keys
            </button>
            <a href="https://huggingface.co/settings/tokens" target="_blank" rel="noopener noreferrer" class="btn-ghost btn-sm" style="color: var(--accent-cyan); text-decoration: underline; font-size: 0.78rem;">
              huggingface.co/settings/tokens ↗
            </a>
          </div>
        </div>
      `;
      return;
    }

    title.textContent = data.name || (repoId.includes("/") ? repoId.split("/")[1] : repoId);
    if (source) {
      source.textContent = isActuallyOllama ? "🦙 Ollama Library" : `🤗 ${data.source_platform || "Hugging Face"}`;
      source.className = isActuallyOllama ? "badge badge-cyan" : "badge";
    }
    if (access) {
      access.textContent = data.gated ? "🔒 Gated Access" : "🔓 Open Access";
      access.className = data.gated ? "badge badge-gated" : "badge badge-success";
    }
    if (sourceLink) {
      sourceLink.href = data.source_url || (isActuallyOllama ? `https://ollama.com/library/${encodeURIComponent(cleanTag)}` : `https://huggingface.co/${repoId}`);
      sourceLink.title = isActuallyOllama ? "View on Ollama Library" : "Open Repository on Hugging Face";
    }
    if (sourceText) {
      sourceText.textContent = isActuallyOllama ? "View on Ollama Library" : "View on Hugging Face";
    }

    // Populate Spec Pills
    if (specArch) specArch.textContent = data.architecture || "Open Transformer";
    if (specParams) specParams.textContent = data.parameters || "7B Params";
    if (specSize) specSize.textContent = data.recommended_size || "--";
    if (specCtx) specCtx.textContent = data.context_length || "32,768 Tokens (32K)";
    if (specLicense) specLicense.textContent = data.license || "Open Source";
    if (specTask) specTask.textContent = (data.pipeline_tag || "Text Generation & Chat").replace("-", " ").toUpperCase();
    if (specVram) specVram.textContent = data.estimated_vram || "Standard VRAM";

    desc.textContent = data.description || "Open-source weight repository optimized for native GGUF inference.";

    // Render Tags Cloud
    if (tagsList && Array.isArray(data.tags)) {
      tagsList.innerHTML = data.tags.slice(0, 10).map((t) => `<span class="tag-badge">#${t}</span>`).join(" ");
    }

    const activeOllamaTag = ollamaTag || data.ollama_tag || "";
    let ollamaBannerHtml = "";
    if (activeOllamaTag) {
      ollamaBannerHtml = `
        <div class="status-banner" style="background: rgba(14, 165, 233, 0.12); border: 1px solid rgba(56, 189, 248, 0.35); padding: 0.85rem 1rem; border-radius: var(--radius-md); margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.6rem;">
          <div>
            <div style="font-weight: 600; color: #38bdf8; display: flex; align-items: center; gap: 0.35rem;">
              <span>🦙</span>
              <span>1-Click Ollama Pull: <code>${escapeHubHtml(activeOllamaTag)}</code></span>
            </div>
            <p style="margin: 0.2rem 0 0; font-size: 0.8rem; color: var(--text-secondary);">Direct download and instant native registration into ModelDock Studio.</p>
          </div>
          <button class="btn-primary btn-sm" onclick="closeInspectModal(); pullOllamaDirect('${escapeHubHtml(activeOllamaTag)}', '${escapeHubHtml(title.textContent)}')" style="background: linear-gradient(135deg, #0284c7 0%, #38bdf8 100%); border-color: #0284c7; font-weight: 600;">
            ⬇️ Pull Model (${escapeHubHtml(activeOllamaTag)})
          </button>
        </div>
      `;
    }

    if (!data.files || data.files.length === 0) {
      list.innerHTML = ollamaBannerHtml + '<div class="empty-state">No .gguf weight files found in this repository.</div>';
      return;
    }

    list.innerHTML = ollamaBannerHtml + data.files
      .map((f) => {
        const isRec = f.recommended;
        const rowClass = isRec ? "file-row recommended-quant" : "file-row";
        const recBadge = isRec ? '<span class="badge badge-success">⭐ Recommended</span>' : "";
        const sizeBadge = f.size_formatted ? `<span class="badge badge-file-size">💾 ${f.size_formatted}</span>` : "";
        const guideText = f.guide ? `<div class="file-guide-text">${f.guide}</div>` : "";

        const actionBtn = (f.download_url && f.download_url.startsWith("ollama pull"))
          ? `<button class="btn-primary btn-sm" onclick="closeInspectModal(); pullOllamaDirect('${escapeHubHtml(activeOllamaTag)}', '${escapeHubHtml(f.filename)}')" style="background: linear-gradient(135deg, #0284c7 0%, #38bdf8 100%); border-color: #0284c7; font-weight: 600;">
               ⬇️ Pull Model
             </button>`
          : `<button class="btn-primary btn-sm" onclick="triggerModelDownload('${f.download_url}', '${f.filename}', '${repoId}')">
               ⬇️ Download &amp; Import
             </button>`;

        return `
        <div class="${rowClass}">
          <div class="file-info">
            <div class="file-name-row">
              <strong class="file-name">${f.filename}</strong>
              <span class="badge badge-cyan">${f.quantization}</span>
              ${sizeBadge}
              ${recBadge}
            </div>
            ${guideText}
          </div>
          ${actionBtn}
        </div>
      `;
      })
      .join("");
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Error fetching details: ${err.message}</div>`;
  }
}

function closeInspectModal() {
  const modal = document.getElementById("modal-repo-inspect");
  if (modal) modal.classList.add("hidden");
}

async function triggerModelDownload(url, filename, repoId) {
  closeInspectModal();

  // Create friendly local model name
  const cleanName = filename.replace(".gguf", "").replace(".GGUF", "").toLowerCase();

  try {
    const res = await fetch("/api/downloads/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: url,
        filename: filename,
        model_name: cleanName,
        auto_register: true,
      }),
    });

    const data = await res.json();
    if (res.ok && data.success) {
      alert(`Download started for ${filename}! You can view live progress in the Downloads tab.`);
      switchTab("downloads");
    } else {
      alert(`Download error: ${data.detail || "Failed to start"}`);
    }
  } catch (err) {
    alert(`Request error: ${err.message}`);
  }
}

// Download Tasks Polling
let downloadPollInterval = null;

async function pollDownloadTasks() {
  try {
    const res = await fetch("/api/downloads/tasks");
    const tasks = await res.json();
    renderDownloadTasks(tasks);

    const taskList = Object.values(tasks);
    const activeCount = taskList.filter((t) => t.status === "downloading" || t.status === "registering" || t.status === "queued").length;
    const totalCount = taskList.length;

    // Update Sidebar Navigation Downloads Badge
    const badge = document.getElementById("active-dl-badge");
    if (badge) {
      if (activeCount > 0) {
        badge.textContent = activeCount;
        badge.title = `${activeCount} active download(s)`;
        badge.classList.remove("hidden");
        badge.classList.add("badge-pulse");
      } else if (totalCount > 0) {
        badge.textContent = totalCount;
        badge.title = `${totalCount} downloaded model(s)`;
        badge.classList.remove("hidden");
        badge.classList.remove("badge-pulse");
      } else {
        badge.textContent = "0";
        badge.classList.add("hidden");
        badge.classList.remove("badge-pulse");
      }
    }

    // Update Downloads Page Header Counter
    const headerCount = document.getElementById("dl-header-count");
    if (headerCount) {
      headerCount.textContent = totalCount;
      headerCount.classList.toggle("hidden", totalCount === 0);
    }

    // Automatically sync and display downloaded models in Library & Dropdown immediately!
    const readyTasks = taskList.filter((t) => t.status === "ready" || t.status === "completed");
    const readyCount = readyTasks.length;
    if (readyCount > 0 && readyCount !== window._lastReadyModelsCount) {
      window._lastReadyModelsCount = readyCount;
      if (typeof loadLocalModels === "function") {
        loadLocalModels();
      }
    }
  } catch (err) {
    // Ignore transient poll error
  }
}

// Start continuous download task polling
setInterval(() => {
  if (AppState.currentTab === "downloads" || document.getElementById("active-dl-badge")) {
    pollDownloadTasks();
  }
}, 1500);

function renderDownloadTasks(tasks) {
  const container = document.getElementById("downloads-list");
  if (!container) return;

  const taskList = Object.values(tasks);
  if (taskList.length === 0) {
    container.innerHTML = '<div class="empty-state"><p>No active downloads. Pull an Ollama model above or search Hugging Face Hub.</p></div>';
    return;
  }

  container.innerHTML = taskList
    .map((t) => {
      const isOllama = t.platform === "ollama";
      const platformBadge = isOllama
        ? '<span class="badge" style="background: rgba(139, 92, 246, 0.15); border-color: rgba(139, 92, 246, 0.4); color: #c4b5fd;">🦙 Ollama</span>'
        : '<span class="badge badge-cyan">🤗 Hugging Face</span>';

      let statusColor = "badge-cyan";
      let cardClass = "download-card";
      let barClass = "progress-bar";

      if (t.status === "paused") {
        statusColor = "badge-gated";
        cardClass += " card-paused";
        barClass += " bar-paused";
      } else if (t.status === "completed" || t.status === "ready") {
        statusColor = "badge-success";
        cardClass += " card-ready";
        barClass += " bar-ready";
      } else if (t.status === "failed") {
        statusColor = "badge-danger";
        cardClass += " card-failed";
        barClass += " bar-failed";
      } else if (t.status === "cancelled") {
        statusColor = "badge";
        cardClass += " card-cancelled";
      }

      const downloadedMB = (t.downloaded_bytes / (1024 * 1024)).toFixed(1);
      const totalMB = t.total_bytes ? (t.total_bytes / (1024 * 1024)).toFixed(1) : "--";

      // Build Action Buttons
      let actionButtons = "";
      if (t.status === "downloading" || t.status === "queued") {
        actionButtons += `
          <button class="btn-dl-action btn-dl-pause" onclick="pauseDownload('${t.task_id}')" title="Pause download">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>
            <span>Pause</span>
          </button>
        `;
      } else if (t.status === "paused") {
        actionButtons += `
          <button class="btn-dl-action btn-dl-resume" onclick="resumeDownload('${t.task_id}')" title="Resume download from where it stopped">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
            <span>Resume</span>
          </button>
        `;
      }

      if (t.status === "ready" || t.status === "completed") {
        actionButtons += `
          <button class="btn-dl-action btn-secondary" onclick="switchTab('models')" title="View model in My Model Library">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect><rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect></svg>
            <span>View in Library</span>
          </button>
          <button class="btn-dl-action btn-dl-run" onclick="selectModelAndChat('${t.model_name}')" title="Start chatting with this model">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
            <span>Run in Chat</span>
          </button>
        `;
      } else if (t.status !== "cancelled") {
        actionButtons += `
          <button class="btn-dl-action btn-dl-cancel" onclick="cancelDownload('${t.task_id}')" title="Cancel download">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            <span>Cancel</span>
          </button>
        `;
      }

      const layerInfo = t.current_layer ? `<span class="dl-layer-info">${t.current_layer}</span>` : "";

      const percentInt = Math.round(t.progress_percent || 0);
      const statusBadgeText = (t.status === "downloading" || t.status === "paused")
        ? `${percentInt}% ${t.status.toUpperCase()}`
        : (t.status === "ready" || t.status === "completed")
        ? `✓ 100% READY`
        : t.status.toUpperCase();

      let errorBlock = "";
      if (t.error) {
        const isAuthError = /access denied|token|gated|401|403|unauthorized/i.test(t.error);
        if (isAuthError) {
          errorBlock = `
            <div class="dl-error-box status-banner banner-error" style="padding: 0.75rem 0.85rem; border-radius: var(--radius-md); margin: 0.6rem 0;">
              <div style="display: flex; align-items: flex-start; gap: 0.65rem; width: 100%;">
                <span style="font-size: 1.25rem; line-height: 1; flex-shrink: 0;">🔒</span>
                <div style="flex: 1; min-width: 0;">
                  <strong style="color: #fff; font-size: 0.86rem; display: block; margin-bottom: 0.25rem;">Hugging Face Access Denied</strong>
                  <div style="font-size: 0.8rem; color: #fca5a5; line-height: 1.4; margin-bottom: 0.6rem;">
                    This model repository requires authentication or access approval. Connect your free Hugging Face User Access Token to continue.
                  </div>
                  <div class="dl-error-actions" style="display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center;">
                    <button class="btn-primary btn-sm dl-auth-btn" onclick="openHuggingFaceTokenPageAndAuth()" title="Opens Hugging Face in new tab and jumps directly to Auth Settings in this app">
                      <span>🔑 Get Auth Token &amp; Fill Here</span>
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-left: 2px;"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                    </button>
                    <button class="btn-secondary btn-sm" onclick="openAuthSettings()" title="Go to Auth &amp; Keys in Settings">
                      <span>⚙️ Go to Auth &amp; Keys</span>
                    </button>
                    <a href="https://huggingface.co/settings/tokens" target="_blank" rel="noopener noreferrer" class="btn-ghost btn-sm" style="color: var(--accent-cyan); text-decoration: underline; font-size: 0.78rem;">
                      huggingface.co/settings/tokens ↗
                    </a>
                  </div>
                </div>
              </div>
            </div>
          `;
        } else {
          errorBlock = `<div class="status-banner banner-error" style="padding: 0.5rem; font-size: 0.8rem; margin: 0.4rem 0;">${t.error}</div>`;
        }
      }

      return `
      <div class="${cardClass}">
        <div class="dl-header">
          <div class="dl-title-group">
            ${platformBadge}
            <strong class="dl-filename" title="${t.filename}">${t.filename}</strong>
          </div>
          <span class="badge ${statusColor}">${statusBadgeText}</span>
        </div>

        <div class="progress-bar-wrap">
          <div class="${barClass}" style="width: ${t.progress_percent || 0}%"></div>
        </div>

        <div class="dl-stats">
          <span class="dl-bytes">${downloadedMB} MB / ${totalMB} MB (${percentInt}%)</span>
          ${(t.status === "ready" || t.status === "completed")
            ? `<span class="dl-speed-eta" style="color: #34d399; font-weight: 600;">✓ 100% Downloaded (${totalMB} MB) • Ready</span>`
            : `<span class="dl-speed-eta">Speed: <strong>${t.speed_mb_s || 0} MB/s</strong> | ETA: <strong>${t.eta_seconds || 0}s</strong></span>`}
        </div>

        ${errorBlock}
        ${t.message ? `<div style="font-size: 0.8rem; color: var(--accent-green); font-weight: 500;">✓ ${t.message}</div>` : ""}
        ${t.message ? `<div style="font-size: 0.8rem; color: var(--accent-green); font-weight: 500;">✓ ${t.message}</div>` : ""}

        <div class="dl-actions-row">
          <div class="dl-actions-left">
            ${layerInfo || `<span class="dl-model-label">Model: <code>${t.model_name}</code></span>`}
          </div>
          <div class="dl-actions-right">
            ${actionButtons}
          </div>
        </div>
      </div>
    `;
    })
    .join("");
}
