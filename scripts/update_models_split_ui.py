from pathlib import Path

p = Path(r"a:\AI_Project_work\ollama_2nd_copy\static\js\models.js")
content = p.read_text(encoding="utf-8")

# 1. Update chatSelect dropdown mapping to show split badge
old_chat_map = '''        chatSelect.innerHTML = AppState.localModels
          .map((m) => {
            const displayName = m.alias || m.name;
            return `<option value="${m.name}">${displayName} (${m.parameter_size || m.size_formatted})</option>`;
          })
          .join("");'''

new_chat_map = '''        chatSelect.innerHTML = AppState.localModels
          .map((m) => {
            const displayName = m.alias || m.name;
            const splitTag = m.is_incomplete_split ? " ⚠️ [Incomplete Split]" : "";
            return `<option value="${m.name}">${displayName}${splitTag} (${m.parameter_size || m.size_formatted})</option>`;
          })
          .join("");'''

assert old_chat_map in content, "old_chat_map not found"
content = content.replace(old_chat_map, new_chat_map, 1)

# 2. Update library grid mapping
old_grid_map = '''      grid.innerHTML = AppState.localModels
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
        .join("");'''

# Let's check how rawAlias is escaped in current content
if "replace(/'/g, \"\\'\")" in content:
    old_grid_map = old_grid_map.replace("\\\\'", "\\'")

new_grid_map = '''      grid.innerHTML = AppState.localModels
        .map((m) => {
          const hasAlias = Boolean(m.alias);
          const displayName = m.alias || m.name;
          const subInfo = hasAlias ? `File: ${m.filename}` : `Source: ${m.source}`;
          const aliasBadge = hasAlias ? `<span class="badge" style="background: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.4); font-size: 0.68rem; font-weight: 600;" title="Custom Alias: ${m.alias}">🏷️ Alias</span>` : "";
          const splitBadge = m.is_incomplete_split ? `<span class="badge" style="background: rgba(234, 179, 8, 0.2); color: #facc15; border: 1px solid rgba(234, 179, 8, 0.4); font-size: 0.68rem; font-weight: 600;" title="${m.split_warning}">⚠️ Incomplete Split</span>` : "";
          const rawAlias = (m.alias || "").replace(/'/g, "\\'");
          const rawName = (m.name || "").replace(/'/g, "\\'");

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
        .join("");'''

assert old_grid_map in content, "old_grid_map not found in models.js"
content = content.replace(old_grid_map, new_grid_map, 1)

p.write_text(content, encoding="utf-8")
print("Updated models.js with split warnings and badge indicators.")
