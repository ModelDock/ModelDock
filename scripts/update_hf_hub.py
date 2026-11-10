import os

with open('static/js/hf_hub.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update initHFHub
target_init = """  if (btnSearch) {
    btnSearch.addEventListener("click", () => searchHFHub());
  }

  // Instant Live Type-Ahead Listener (Hugging Face, Ollama, Local Models)
  if (queryInput) {
    queryInput.addEventListener("input", (e) => {
      clearTimeout(omniSearchDebounceTimer);
      const q = e.target.value.trim();
      if (!q) {
        hideOmniDropdown();
        return;
      }
      omniSearchDebounceTimer = setTimeout(() => {
        performOmniLiveSearch(q);
      }, 100);
    });

    queryInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        hideOmniDropdown();
        searchHFHub();
      } else if (e.key === "Escape") {
        hideOmniDropdown();
      }
    });

    // Re-open dropdown on focus if input has text
    queryInput.addEventListener("focus", () => {
      const q = queryInput.value.trim();
      if (q) performOmniLiveSearch(q);
    });
  }

  // Dismiss dropdown on outside click
  document.addEventListener("click", (e) => {
    const wrap = document.querySelector(".search-input-wrap");
    if (wrap && !wrap.contains(e.target)) {
      hideOmniDropdown();
    }
  });"""

replacement_init = """  if (btnSearch) {
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
  });"""

# Normalize line breaks for matching
content_norm = content.replace("\r\n", "\n")
target_init_norm = target_init.replace("\r\n", "\n")
replacement_init_norm = replacement_init.replace("\r\n", "\n")

if target_init_norm not in content_norm:
    raise ValueError("target_init not found in static/js/hf_hub.js")

content_norm = content_norm.replace(target_init_norm, replacement_init_norm, 1)

# Helper card rendering methods & searchHFHub replacement
card_helpers_and_search = """function escapeHubHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function renderInstalledCardHTML(m) {
  const safeName = escapeHubHtml(m.name || "Unknown");
  const rawName = (m.name || "Unknown").replace(/'/g, "\\\\'");
  const sizeText = m.size_formatted || "Ready";
  const paramText = m.parameter_size || "Quantized";
  const quantText = m.quantization || "GGUF";
  const archText = m.family || m.architecture || "Local Engine";

  return `
    <div class="model-card model-card-installed" style="border: 1px solid rgba(16, 185, 129, 0.45); background: linear-gradient(180deg, rgba(16, 185, 129, 0.08) 0%, rgba(30, 41, 59, 0.7) 100%);">
      <div class="card-top">
        <div class="card-header-row">
          <div class="card-header-titles">
            <div class="model-name" title="${safeName}" style="display: flex; align-items: center; gap: 0.35rem;">
              <span style="color: #10b981; font-size: 0.95rem;">⚡</span>
              <span>${safeName}</span>
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

function renderHFCardHTML(m) {
  const safeName = escapeHubHtml(m.name || m.id || "Unknown");
  const safeId = escapeHubHtml(m.id || "");
  const rawId = (m.id || "").replace(/'/g, "\\\\'");
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
          ${gatedBadge}
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
  if (title) title.textContent = `🔍 Search Results for "${q}" (GGUF Models)`;
  if (!grid) return;

  const qLower = q.toLowerCase();
  const localMatches = (AppState.localModels || []).filter((m) => {
    const name = (m.name || "").toLowerCase();
    const fn = (m.filename || "").toLowerCase();
    const arch = (m.architecture || "").toLowerCase();
    const fam = (m.family || "").toLowerCase();
    return name.includes(qLower) || fn.includes(qLower) || arch.includes(qLower) || fam.includes(qLower);
  });

  if (localMatches.length > 0) {
    let html = localMatches.map((m) => renderInstalledCardHTML(m)).join("");
    html += `
      <div class="model-card" style="border: 1px dashed var(--border-subtle); display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 180px; text-align: center; color: var(--text-muted); background: rgba(255, 255, 255, 0.01);">
        <div class="loading-spinner-sm" style="margin-bottom: 0.5rem;"></div>
        <span style="font-size: 0.84rem;">Searching Hugging Face Hub for "<strong>${escapeHubHtml(q)}</strong>"...</span>
      </div>
    `;
    grid.innerHTML = html;
  } else {
    grid.innerHTML = `
      <div class="loading-spinner" style="grid-column: 1 / -1; padding: 3rem 1rem;">
        Searching open-source model catalog for "<strong>${escapeHubHtml(q)}</strong>"...
      </div>
    `;
  }
}

async function searchHFHub(customQuery) {
  const queryInput = document.getElementById("hf-search-query");
  const sortSelect = document.getElementById("hf-sort-select");
  const grid = document.getElementById("hf-models-grid");
  const title = document.getElementById("hub-grid-title");

  const query = (typeof customQuery === "string" ? customQuery : (queryInput ? queryInput.value : "")).trim();
  const sort = sortSelect ? sortSelect.value : "downloads";

  if (!query) {
    loadFeaturedHFModels();
    return;
  }

  if (title) title.textContent = `🔍 Search Results for "${query}" (GGUF Models)`;

  // Match locally installed models (0ms)
  const qLower = query.toLowerCase();
  const localMatches = (AppState.localModels || []).filter((m) => {
    const name = (m.name || "").toLowerCase();
    const fn = (m.filename || "").toLowerCase();
    const arch = (m.architecture || "").toLowerCase();
    const fam = (m.family || "").toLowerCase();
    return name.includes(qLower) || fn.includes(qLower) || arch.includes(qLower) || fam.includes(qLower);
  });

  try {
    const res = await fetch(`/api/hf/search?q=${encodeURIComponent(query)}&sort=${sort}&filter=gguf`);
    const results = (await res.json()) || [];

    if (localMatches.length === 0 && results.length === 0) {
      if (grid) {
        grid.innerHTML = `
          <div class="empty-state" style="grid-column: 1 / -1;">
            <h3>No models found matching "${escapeHubHtml(query)}"</h3>
            <p style="margin-top: 0.5rem; color: var(--text-muted);">Try searching for 'llama', 'deepseek', 'qwen', or 'mistral'.</p>
          </div>
        `;
      }
      return;
    }

    let cardsHtml = "";
    if (localMatches.length > 0) {
      cardsHtml += localMatches.map((m) => renderInstalledCardHTML(m)).join("");
    }
    if (results.length > 0) {
      cardsHtml += results.map((m) => renderHFCardHTML(m)).join("");
    }

    if (grid) grid.innerHTML = cardsHtml;
  } catch (err) {
    if (localMatches.length > 0) {
      if (grid) grid.innerHTML = localMatches.map((m) => renderInstalledCardHTML(m)).join("");
    } else if (grid) {
      grid.innerHTML = `<div class="empty-state" style="grid-column: 1 / -1;">Search error: ${escapeHubHtml(err.message)}</div>`;
    }
  }
}"""

# Find target searchHFHub
target_search = """async function searchHFHub() {
  const queryInput = document.getElementById("hf-search-query");
  const sortSelect = document.getElementById("hf-sort-select");
  const grid = document.getElementById("hf-models-grid");
  const title = document.getElementById("hub-grid-title");

  const query = queryInput ? queryInput.value.trim() : "";
  const sort = sortSelect ? sortSelect.value : "downloads";

  if (!query) {
    loadFeaturedHFModels();
    return;
  }

  if (title) title.textContent = `🔍 Search Results for "${query}" (GGUF Models)`;
  if (grid) grid.innerHTML = '<div class="loading-spinner">Searching Open-Source Model Catalog...</div>';

  try {
    const res = await fetch(`/api/hf/search?q=${encodeURIComponent(query)}&sort=${sort}&filter=gguf`);
    const results = await res.json();

    if (!results || results.length === 0) {
      grid.innerHTML = `<div class="empty-state">No models found matching "${query}". Try searching for 'llama', 'deepseek', 'qwen', or 'mistral'.</div>`;
      return;
    }

    grid.innerHTML = results
      .map((m) => {
        const gatedBadge = m.gated
          ? '<span class="badge badge-gated">🔒 Gated</span>'
          : '<span class="badge badge-cyan">GGUF</span>';

        return `
        <div class="model-card" onclick="openInspectModal('${m.id}')" style="cursor: pointer;" title="Click to inspect model specs and download weights">
          <div class="card-top">
            <div class="card-header-row">
              <div class="card-header-titles">
                <div class="model-name" title="${m.name}">${m.name}</div>
                <div class="model-author" title="${m.id}">${m.id}</div>
              </div>
              ${gatedBadge}
            </div>
            <div class="tags-row">
              ${(m.tags || []).slice(0, 3).map((t) => `<span class="badge">${t}</span>`).join("")}
            </div>
          </div>
          <div class="card-footer">
            <div class="card-stats">
              <span class="card-stat-item" title="${m.likes.toLocaleString()} likes">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" style="color: #f43f5e;"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
                <span>${m.likes.toLocaleString()}</span>
              </span>
              <span class="stat-sep">•</span>
              <span class="card-stat-item" title="${m.downloads.toLocaleString()} downloads">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="color: #38bdf8;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                <span>${m.downloads.toLocaleString()}</span>
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
  } catch (err) {
    grid.innerHTML = `<div class="empty-state">Search error: ${err.message}</div>`;
  }
}"""

target_search_norm = target_search.replace("\r\n", "\n")
card_helpers_and_search_norm = card_helpers_and_search.replace("\r\n", "\n")

if target_search_norm not in content_norm:
    raise ValueError("target_search not found in static/js/hf_hub.js")

content_norm = content_norm.replace(target_search_norm, card_helpers_and_search_norm, 1)

# Ensure hideOmniDropdown always keeps dropdown hidden
content_norm = content_norm.replace(
    'function hideOmniDropdown() {\n  const dd = document.getElementById("omni-search-dropdown");\n  if (dd) dd.classList.add("hidden");\n}',
    'function hideOmniDropdown() {\n  const dd = document.getElementById("omni-search-dropdown");\n  if (dd) {\n    dd.classList.add("hidden");\n    dd.style.display = "none";\n  }\n}'
)

with open('static/js/hf_hub.js', 'w', encoding='utf-8', newline='') as f:
    f.write(content_norm.replace("\n", "\r\n"))

print("static/js/hf_hub.js updated successfully!")
