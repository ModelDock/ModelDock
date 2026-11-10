with open('static/js/models.js', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update initModels to add alias input listener
target_init = """  const btnSubmitImport = document.getElementById("btn-submit-import");
  if (btnSubmitImport) {
    btnSubmitImport.addEventListener("click", handleLocalImport);
  }
}"""

replacement_init = """  const btnSubmitImport = document.getElementById("btn-submit-import");
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
}"""

target_init_norm = target_init.replace("\r\n", "\n")
replacement_init_norm = replacement_init.replace("\r\n", "\n")
text_norm = text.replace("\r\n", "\n")

if target_init_norm not in text_norm:
    raise ValueError("target_init not found")

text_norm = text_norm.replace(target_init_norm, replacement_init_norm, 1)

# 2. Update chatSelect in loadLocalModels
target_chat_select = """        const prevValue = chatSelect.value;
        chatSelect.innerHTML = AppState.localModels
          .map((m) => `<option value="${m.name}">${m.name} (${m.parameter_size || m.size_formatted})</option>`)
          .join("");"""

replacement_chat_select = """        const prevValue = chatSelect.value;
        chatSelect.innerHTML = AppState.localModels
          .map((m) => {
            const displayName = m.alias || m.name;
            return `<option value="${m.name}">${displayName} (${m.parameter_size || m.size_formatted})</option>`;
          })
          .join("");"""

target_chat_select_norm = target_chat_select.replace("\r\n", "\n")
replacement_chat_select_norm = replacement_chat_select.replace("\r\n", "\n")

if target_chat_select_norm not in text_norm:
    raise ValueError("target_chat_select not found")

text_norm = text_norm.replace(target_chat_select_norm, replacement_chat_select_norm, 1)

# 3. Update grid.innerHTML in loadLocalModels
target_grid = """      grid.innerHTML = AppState.localModels
        .map((m) => {
          return `
          <div class="model-card">
            <div class="card-top">
              <div class="card-header-row">
                <div class="card-header-titles">
                  <div class="model-name" title="${m.name}">${m.name}</div>
                  <div class="model-author" title="Source: ${m.source}">Source: ${m.source}</div>
                </div>
                <span class="badge badge-success flex-shrink-0">Installed</span>
              </div>
              <div class="tags-row">
                <span class="badge badge-cyan">${m.parameter_size || "Standard"}</span>
                <span class="badge">${m.quantization || "Quantized"}</span>
                <span class="badge">${m.context_formatted || "4K ctx"}</span>
                <span class="badge">${m.size_formatted}</span>
                <span class="badge">${m.family || m.architecture}</span>
              </div>
            </div>
            <div class="card-footer">
              <button class="btn-danger btn-sm" onclick="deleteModel('${m.name}')" title="Delete model from disk">
                Delete
              </button>
              <button class="btn-secondary btn-sm" onclick="showModelDetails('${m.name}')" title="Inspect model specifications, layers, and context">
                🔍 Specs
              </button>
              <button class="btn-primary btn-sm" onclick="selectModelAndChat('${m.name}')">
                Run in Chat 💬
              </button>
            </div>
          </div>
        `;
        })
        .join("");"""

replacement_grid = """      grid.innerHTML = AppState.localModels
        .map((m) => {
          const hasAlias = Boolean(m.alias);
          const displayName = m.alias || m.name;
          const subInfo = hasAlias ? `File: ${m.filename}` : `Source: ${m.source}`;
          const aliasBadge = hasAlias ? `<span class="badge" style="background: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.4); font-size: 0.68rem; font-weight: 600;" title="Custom Alias: ${m.alias}">🏷️ Alias</span>` : "";
          const rawAlias = (m.alias || "").replace(/'/g, "\\\\'");
          const rawName = (m.name || "").replace(/'/g, "\\\\'");

          return `
          <div class="model-card">
            <div class="card-top">
              <div class="card-header-row">
                <div class="card-header-titles">
                  <div class="model-name" title="${hasAlias ? m.alias + ' (' + m.name + ')' : m.name}" style="display: flex; align-items: center; gap: 0.35rem;">
                    <span>${displayName}</span>
                    ${aliasBadge}
                  </div>
                  <div class="model-author" title="${subInfo}">${subInfo}</div>
                </div>
                <span class="badge badge-success flex-shrink-0">Installed</span>
              </div>
              <div class="tags-row">
                <span class="badge badge-cyan">${m.parameter_size || "Standard"}</span>
                <span class="badge">${m.quantization || "Quantized"}</span>
                <span class="badge">${m.context_formatted || "4K ctx"}</span>
                <span class="badge">${m.size_formatted}</span>
                <span class="badge">${m.family || m.architecture}</span>
              </div>
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
        .join("");"""

target_grid_norm = target_grid.replace("\r\n", "\n")
replacement_grid_norm = replacement_grid.replace("\r\n", "\n")

if target_grid_norm not in text_norm:
    raise ValueError("target_grid not found")

text_norm = text_norm.replace(target_grid_norm, replacement_grid_norm, 1)

# 4. Append alias controller functions and getModelDisplayName
alias_controllers = """
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
"""

text_norm += alias_controllers

with open('static/js/models.js', 'w', encoding='utf-8', newline='') as f:
    f.write(text_norm.replace('\n', '\r\n'))

print("Updated static/js/models.js with model alias support!")
