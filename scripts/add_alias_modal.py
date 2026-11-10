with open('static/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

target = """  <!-- Model Specifications & Details Modal -->
  <div id="modal-model-details" class="modal-backdrop hidden">"""

alias_modal = """  <!-- User Model Alias Customization Modal -->
  <div id="modal-model-alias" class="modal-backdrop hidden" onclick="if(event.target === this) closeModelAliasModal()">
    <div class="modal-card" style="max-width: 480px;">
      <div class="modal-header">
        <div class="modal-title-row">
          <span style="font-size: 1.25rem;">🏷️</span>
          <h3>Set Model Alias</h3>
        </div>
        <button class="btn-close" onclick="closeModelAliasModal()" title="Close">✕</button>
      </div>
      <div class="modal-body" style="padding: 1.25rem 1.5rem;">
        <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 1rem; line-height: 1.45;">
          Give this model a friendly display nickname. The alias will replace the long filename across the Chat selector, navbar, message badges, and library.
        </p>
        <div class="form-group" style="margin-bottom: 1rem;">
          <label style="display: block; font-size: 0.78rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.35rem;">Original Model File</label>
          <input type="text" id="alias-model-original-name" class="input-text" readonly style="background: rgba(255,255,255,0.03); opacity: 0.8; font-family: monospace; font-size: 0.8rem; cursor: not-allowed; width: 100%; box-sizing: border-box;" />
        </div>
        <div class="form-group" style="margin-bottom: 0.5rem;">
          <label for="alias-model-input" style="display: block; font-size: 0.78rem; font-weight: 600; color: var(--text-primary); text-transform: uppercase; margin-bottom: 0.35rem;">Custom Friendly Alias</label>
          <input type="text" id="alias-model-input" class="input-text" placeholder="e.g. Qwen 2.5 Coder 7B, DeepSeek R1, Fast Chat 0.5B..." autofocus autocomplete="off" style="width: 100%; box-sizing: border-box;" />
          <span style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.35rem; display: block;">Leave blank or click Revert to restore the default filename.</span>
        </div>
      </div>
      <div class="modal-footer" style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 1.5rem;">
        <button type="button" class="btn-danger btn-sm" onclick="clearModelAlias()" id="btn-clear-alias" title="Remove alias and revert to default filename">
          Revert to Default
        </button>
        <div style="display: flex; gap: 0.5rem;">
          <button type="button" class="btn-secondary btn-sm" onclick="closeModelAliasModal()">Cancel</button>
          <button type="button" class="btn-primary btn-sm" onclick="saveModelAlias()">Save Alias</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Model Specifications & Details Modal -->
  <div id="modal-model-details" class="modal-backdrop hidden">"""

target_norm = target.replace("\r\n", "\n")
alias_modal_norm = alias_modal.replace("\r\n", "\n")
text_norm = text.replace("\r\n", "\n")

if target_norm not in text_norm:
    raise ValueError("target not found in static/index.html")

text_norm = text_norm.replace(target_norm, alias_modal_norm, 1)

with open('static/index.html', 'w', encoding='utf-8', newline='') as f:
    f.write(text_norm.replace('\n', '\r\n'))

print("Added modal-model-alias to static/index.html!")
