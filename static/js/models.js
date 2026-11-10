/**
 * ModelDock Studio - Local Model Library & Management
 */

function initModels() {
  const btnRefresh = document.getElementById("btn-refresh-lib");
  if (btnRefresh) {
    btnRefresh.onclick = () => refreshLocalModels(btnRefresh);
  }

  const btnImportModal = document.getElementById("btn-import-gguf-modal");
  if (btnImportModal) {
    btnImportModal.addEventListener("click", openImportModal);
  }

  const btnSubmitImport = document.getElementById("btn-submit-import");
  if (btnSubmitImport) {
    btnSubmitImport.addEventListener("click", handleLocalImport);
  }

  const aliasInput = document.getElementById("alias-model-input");
  if (aliasInput) {
    aliasInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") saveModelAlias();
      else if (e.key === "Escape") closeModelAliasModal();
    });
  }
}

// Rescan models directory and reload library with visual button feedback
async function refreshLocalModels(triggerBtn) {
  const btn = triggerBtn || document.getElementById("btn-refresh-lib");
  let origHtml = "";
  if (btn) {
    origHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `
      <svg class="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right: 4px;"><path d="M23 4v6h-6"></path><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
      Scanning...
    `;
  }

  try {
    await loadLocalModels();
    if (btn) {
      btn.innerHTML = `✓ Refreshed (${AppState.localModels.length} models)`;
      setTimeout(() => {
        btn.innerHTML = origHtml || `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 4px;"><path d="M23 4v6h-6"></path><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg> Refresh`;
        btn.disabled = false;
      }, 1200);
    }
  } catch (err) {
    console.error("Refresh error:", err);
    if (btn) {
      btn.innerHTML = origHtml || "Refresh";
      btn.disabled = false;
    }
  }
}

async function loadLocalModels() {
  const grid = document.getElementById("local-models-grid");
  const countBadge = document.getElementById("installed-count");
  const chatSelect = document.getElementById("chat-model-select");

  try {
    const res = await fetch(`/api/models/local?_t=${Date.now()}`, { cache: "no-store" });
    const models = await res.json();
    AppState.localModels = models || [];

    if (countBadge) {
      countBadge.textContent = AppState.localModels.length;
      countBadge.classList.toggle("hidden", AppState.localModels.length === 0);
    }

    // Update Chat Dropdown
    if (chatSelect) {
      if (AppState.localModels.length === 0) {
        chatSelect.innerHTML = '<option value="" disabled selected>No local models found (Download from HF Hub)</option>';
      } else {
        const prevValue = chatSelect.value;
        chatSelect.innerHTML = AppState.localModels
          .map((m) => {
            const displayName = m.alias || m.name;
            const splitTag = m.is_incomplete_split ? " ⚠️ [Incomplete Split]" : "";
            return `<option value="${m.name}">${displayName}${splitTag} (${m.parameter_size || m.size_formatted})</option>`;
          })
          .join("");

        if (prevValue && AppState.localModels.some((m) => m.name === prevValue)) {
          chatSelect.value = prevValue;
        } else {
          chatSelect.value = AppState.localModels[0].name;
        }
      }
    }

    // Render Library Grid
    if (grid) {
      if (AppState.localModels.length === 0) {
        grid.innerHTML = `
          <div class="empty-state" style="grid-column: 1 / -1;">
            <h3>No Local Models Found</h3>
            <p>You can search and 1-click download open-source models from Hugging Face or import existing GGUF files.</p>
            <button class="btn-primary" style="margin-top: 1rem;" onclick="switchTab('hf-hub')">
              Browse Hugging Face Hub
            </button>
          </div>
        `;
        return;
      }

      grid.innerHTML = AppState.localModels
        .map((m) => {
          const hasAlias = Boolean(m.alias);
          const displayName = m.alias || m.name;
          const subInfo = hasAlias ? `File: ${m.filename}` : `Source: ${m.source}`;
          const aliasBadge = hasAlias ? `<span class="badge" style="background: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.4); font-size: 0.68rem; font-weight: 600;" title="Custom Alias: ${m.alias}">🏷️ Alias</span>` : "";
          const splitBadge = m.is_incomplete_split ? `<span class="badge" style="background: rgba(234, 179, 8, 0.2); color: #facc15; border: 1px solid rgba(234, 179, 8, 0.4); font-size: 0.68rem; font-weight: 600;" title="${m.split_warning}">⚠️ Incomplete Split</span>` : "";
          const rawAlias = (m.alias || "").replace(/'/g, "\'");
          const rawName = (m.name || "").replace(/'/g, "\'");

          return `
          <div class="model-card ${m.is_incomplete_split ? 'model-card-warning' : ''}">
            <div class="card-top">
              <div class="card-header-row">
                <div class="card-header-titles">
                  <div class="model-name" title="${hasAlias ? m.alias + ' (' + m.name + ')' : m.name}" style="display: flex; align-items: center; gap: 0.35rem; flex-wrap: wrap;">
                    <span>${displayName}</span>
                    ${aliasBadge}
                    ${splitBadge}
                  </div>
                  <div class="model-author" title="${subInfo}">${subInfo}</div>
                </div>
                <span class="badge ${m.is_incomplete_split ? 'badge-warning' : 'badge-success'} flex-shrink-0">${m.is_incomplete_split ? 'Split Shard' : 'Installed'}</span>
              </div>
              <div class="tags-row">
                <span class="badge badge-cyan">${m.parameter_size || "Standard"}</span>
                <span class="badge">${m.quantization || "Quantized"}</span>
                <span class="badge">${m.context_formatted || "4K ctx"}</span>
                <span class="badge">${m.size_formatted}</span>
                <span class="badge">${m.family || m.architecture}</span>
              </div>
              ${m.is_incomplete_split ? `<div style="font-size: 0.76rem; color: #facc15; margin-top: 0.45rem; line-height: 1.3; background: rgba(234,179,8,0.1); padding: 0.35rem 0.6rem; border-radius: 6px; border-left: 3px solid #facc15;">⚠️ ${m.split_warning}</div>` : ''}
            </div>
            <div class="card-footer" style="display: flex; gap: 0.4rem; justify-content: flex-end; align-items: center;">
              <button class="btn-danger btn-sm" onclick="deleteModel('${rawName}')" title="Delete model from disk">
                Delete
              </button>
              <button class="btn-secondary btn-sm" onclick="openModelAliasModal('${rawName}', '${rawAlias}')" title="Set or change friendly alias for this model">
                🏷️ Alias
              </button>
              <button class="btn-secondary btn-sm" onclick="showModelDetails('${rawName}')" title="Inspect model specifications, layers, and context">
                🔍 Specs
              </button>
              <button class="btn-primary btn-sm" onclick="selectModelAndChat('${rawName}')">
                Run in Chat 💬
              </button>
            </div>
          </div>
        `;
        })
        .join("");
    }
  } catch (err) {
    if (grid) grid.innerHTML = `<div class="empty-state">Error loading local models: ${err.message}</div>`;
  }
}

async function selectModelAndChat(modelName) {
  const chatSelect = document.getElementById("chat-model-select");
  if (chatSelect) {
    chatSelect.value = modelName;
  }
  switchTab("chat");

  // Proactively warm up / load model in native engine
  try {
    fetch("/api/engine/load", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: modelName }),
    }).catch(() => {});
  } catch (e) {
    // Non-blocking background load
  }
}

async function deleteModel(name) {
  if (!confirm(`Are you sure you want to delete '${name}' from local storage? This will free up its disk space.`)) return;

  try {
    const res = await fetch("/api/models/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });

    const data = await res.json();
    if (res.ok && data.success) {
      await loadLocalModels();
    } else {
      alert(`Delete failed: ${data.error || "Unknown error"}`);
    }
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
}

// Import Local GGUF Modal
function openImportModal() {
  const modal = document.getElementById("modal-import-local");
  const statusMsg = document.getElementById("import-status-msg");
  if (statusMsg) statusMsg.textContent = "";
  if (modal) modal.classList.remove("hidden");
}

function closeImportModal() {
  const modal = document.getElementById("modal-import-local");
  if (modal) modal.classList.add("hidden");
}

async function handleLocalImport() {
  const pathInput = document.getElementById("import-file-path");
  const nameInput = document.getElementById("import-model-name");
  const ctxSelect = document.getElementById("import-ctx-len");
  const statusMsg = document.getElementById("import-status-msg");
  const btnSubmit = document.getElementById("btn-submit-import");

  const filePath = pathInput ? pathInput.value.trim() : "";
  const modelName = nameInput ? nameInput.value.trim() : "";
  const ctxLen = ctxSelect ? parseInt(ctxSelect.value) : 4096;

  if (!filePath) {
    alert("Please provide the full path to the .gguf file.");
    return;
  }
  if (!modelName) {
    alert("Please enter a model name.");
    return;
  }

  btnSubmit.disabled = true;
  btnSubmit.textContent = "Registering...";
  statusMsg.innerHTML = '<span style="color: var(--accent-cyan);">Generating Modelfile and registering into local runtime...</span>';

  try {
    const res = await fetch("/api/models/import-local", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        file_path: filePath,
        model_name: modelName,
        context_length: ctxLen,
      }),
    });

    const data = await res.json();
    if (res.ok && data.success) {
      statusMsg.innerHTML = `<span style="color: var(--accent-green);">Success! Model '${modelName}' is now registered and ready to run.</span>`;
      setTimeout(() => {
        closeImportModal();
        loadLocalModels();
        selectModelAndChat(modelName);
      }, 1200);
    } else {
      statusMsg.innerHTML = `<span style="color: var(--accent-red);">Error: ${data.error || data.detail || "Registration failed"}</span>`;
    }
  } catch (err) {
    statusMsg.innerHTML = `<span style="color: var(--accent-red);">Request error: ${err.message}</span>`;
  } finally {
    btnSubmit.disabled = false;
    btnSubmit.textContent = "Register Model";
  }
}

// --- Model Specifications & Details Modal ---
let currentModalModel = null;

async function showModelDetails(modelName) {
  const modal = document.getElementById("modal-model-details");
  if (!modal) return;

  // Find in AppState.localModels or fetch from API
  let model = (AppState.localModels || []).find((m) => m.name === modelName || m.filename === modelName);

  if (!model) {
    try {
      const res = await fetch("/api/models/details", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: modelName }),
      });
      model = await res.json();
    } catch (e) {
      console.error("Failed to fetch model details:", e);
    }
  }

  if (!model) return;
  currentModalModel = model;

  // Header & Badges
  const titleEl = document.getElementById("md-title");
  if (titleEl) titleEl.textContent = model.name;

  const archBadge = document.getElementById("md-badge-arch");
  if (archBadge) archBadge.textContent = `Architecture: ${model.family || model.architecture || "LLM"}`;

  const quantBadge = document.getElementById("md-badge-quant");
  if (quantBadge) quantBadge.textContent = model.quantization || "Quantized";

  const paramsBadge = document.getElementById("md-badge-params");
  if (paramsBadge) paramsBadge.textContent = `Parameters: ${model.parameter_size || "Standard"}`;

  const verBadge = document.getElementById("md-badge-version");
  if (verBadge) verBadge.textContent = `Format: GGUF v${model.gguf_version || 3}`;

  // Hyperparameters
  const ctxEl = document.getElementById("md-ctx");
  if (ctxEl) ctxEl.textContent = model.context_formatted || (model.context_length ? `${model.context_length.toLocaleString()} tokens` : "4,096 tokens");

  const layersEl = document.getElementById("md-layers");
  if (layersEl) layersEl.textContent = model.block_count ? `${model.block_count} layers` : "N/A";

  const embedEl = document.getElementById("md-embed");
  if (embedEl) embedEl.textContent = model.embedding_length ? `${model.embedding_length} dims` : "N/A";

  const headsEl = document.getElementById("md-heads");
  if (headsEl) headsEl.textContent = model.head_count ? `${model.head_count} heads` : "N/A";

  const headsSubEl = document.getElementById("md-heads-sub");
  if (headsSubEl) headsSubEl.textContent = model.head_count_kv ? `${model.head_count_kv} KV heads` : "Standard multi-head";

  const ffnEl = document.getElementById("md-ffn");
  if (ffnEl) ffnEl.textContent = model.feed_forward_length ? `${model.feed_forward_length} dims` : "N/A";

  const tensorsEl = document.getElementById("md-tensors");
  if (tensorsEl) tensorsEl.textContent = model.tensor_count ? `${model.tensor_count} tensors` : "N/A";

  // VRAM & Hardware
  const vramText = document.getElementById("md-vram-text");
  if (vramText) vramText.textContent = model.estimated_vram || "Standard VRAM requirement";

  const vramSub = document.getElementById("md-vram-sub");
  if (vramSub) {
    vramSub.textContent = `Native offload recommendation: Pure standalone llama.cpp binary execution with GPU tensor cores.`;
  }

  // Disk location
  const pathInput = document.getElementById("md-filepath");
  if (pathInput) pathInput.value = model.file_path || "";

  const sizeEl = document.getElementById("md-filesize");
  if (sizeEl) sizeEl.textContent = `${model.size_formatted} (${(model.size_bytes || 0).toLocaleString()} bytes)`;

  const feedback = document.getElementById("md-copy-feedback");
  if (feedback) feedback.textContent = "";

  modal.classList.remove("hidden");
}

function closeModelDetailsModal() {
  const modal = document.getElementById("modal-model-details");
  if (modal) modal.classList.add("hidden");
}

function openActiveModelDetails() {
  const chatSelect = document.getElementById("chat-model-select");
  const activeModel = chatSelect ? chatSelect.value : null;
  if (activeModel) {
    showModelDetails(activeModel);
  } else if (AppState.localModels && AppState.localModels.length > 0) {
    showModelDetails(AppState.localModels[0].name);
  } else {
    alert("No local models installed yet. Download a model from Hugging Face Hub first.");
  }
}

function runActiveModalModel() {
  if (currentModalModel) {
    closeModelDetailsModal();
    selectModelAndChat(currentModalModel.name);
  }
}

function copyModelPath() {
  const input = document.getElementById("md-filepath");
  const feedback = document.getElementById("md-copy-feedback");
  if (input && input.value) {
    navigator.clipboard.writeText(input.value).then(() => {
      if (feedback) {
        feedback.textContent = "✓ Copied to clipboard!";
        setTimeout(() => { if (feedback) feedback.textContent = ""; }, 2500);
      }
    }).catch(() => {
      input.select();
      document.execCommand("copy");
      if (feedback) feedback.textContent = "✓ Copied!";
    });
  }
}

async function revealModelFile() {
  const input = document.getElementById("md-filepath");
  const filePath = input ? input.value : "";
  if (!filePath) return;

  try {
    const res = await fetch("/api/models/reveal-file", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file_path: filePath }),
    });
    const data = await res.json();
    if (!data.success) {
      alert(`Could not open folder: ${data.error || "Unknown error"}`);
    }
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
}

// Bind globally for inline onclick handlers
window.showModelDetails = showModelDetails;
window.closeModelDetailsModal = closeModelDetailsModal;
window.openActiveModelDetails = openActiveModelDetails;
window.runActiveModalModel = runActiveModalModel;
window.copyModelPath = copyModelPath;
window.revealModelFile = revealModelFile;
window.deleteModel = deleteModel;
window.selectModelAndChat = selectModelAndChat;
window.openImportModal = openImportModal;
window.closeImportModal = closeImportModal;

// --- Model Alias Customization Controller ---
let currentAliasTargetModel = "";

function openModelAliasModal(modelName, currentAlias) {
  currentAliasTargetModel = modelName;
  const modal = document.getElementById("modal-model-alias");
  const origInput = document.getElementById("alias-model-original-name");
  const aliasInput = document.getElementById("alias-model-input");

  if (origInput) origInput.value = modelName;
  if (aliasInput) {
    aliasInput.value = currentAlias || "";
    setTimeout(() => {
      aliasInput.focus();
      aliasInput.select();
    }, 100);
  }
  if (modal) modal.classList.remove("hidden");
}

function closeModelAliasModal() {
  const modal = document.getElementById("modal-model-alias");
  if (modal) modal.classList.add("hidden");
  currentAliasTargetModel = "";
}

async function saveModelAlias() {
  if (!currentAliasTargetModel) return;
  const aliasInput = document.getElementById("alias-model-input");
  const newAlias = aliasInput ? aliasInput.value.trim() : "";

  try {
    const res = await fetch("/api/models/alias", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model_name: currentAliasTargetModel, alias: newAlias }),
    });

    const stored = JSON.parse(localStorage.getItem("modeldock_model_aliases") || "{}");
    if (newAlias) {
      stored[currentAliasTargetModel] = newAlias;
    } else {
      delete stored[currentAliasTargetModel];
    }
    localStorage.setItem("modeldock_model_aliases", JSON.stringify(stored));

    closeModelAliasModal();
    await loadLocalModels();
  } catch (err) {
    alert("Failed to save alias: " + err.message);
  }
}

async function clearModelAlias() {
  const aliasInput = document.getElementById("alias-model-input");
  if (aliasInput) aliasInput.value = "";
  await saveModelAlias();
}

function getModelDisplayName(modelName) {
  if (!modelName) return "";
  if (window.AppState && AppState.localModels && AppState.localModels.length > 0) {
    const found = AppState.localModels.find(
      (m) => m.name === modelName || m.filename === modelName || (m.alias && m.alias === modelName)
    );
    if (found && found.alias) return found.alias;
  }
  try {
    const stored = JSON.parse(localStorage.getItem("modeldock_model_aliases") || "{}");
    if (stored[modelName]) return stored[modelName];
  } catch (e) {}

  return modelName;
}

window.getModelDisplayName = getModelDisplayName;
window.openModelAliasModal = openModelAliasModal;
window.closeModelAliasModal = closeModelAliasModal;
window.saveModelAlias = saveModelAlias;
window.clearModelAlias = clearModelAlias;
