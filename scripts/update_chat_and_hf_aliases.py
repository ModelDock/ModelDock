with open('static/js/chat.js', 'r', encoding='utf-8') as f:
    chat_text = f.read()

# 1. Update authorName in appendMessageUI
target_author = 'const authorName = isUser ? (customName || "You") : "ModelDock Assistant";'
rep_author = 'const authorName = isUser ? (customName || "You") : ((metrics && metrics.model && typeof getModelDisplayName === "function") ? getModelDisplayName(metrics.model) : "ModelDock Assistant");'

# 2. Update Engine: in appendMessageUI
target_engine1 = '<span>Engine: <strong>${metrics.model || "--"}</strong></span>'
rep_engine1 = '<span>Engine: <strong>${(typeof getModelDisplayName === "function" ? getModelDisplayName(metrics.model || "--") : (metrics.model || "--"))}</strong></span>'

# 3. Update Engine: in final chunk
target_engine2 = '<span>Engine: <strong>${m.model}</strong></span>'
rep_engine2 = '<span>Engine: <strong>${(typeof getModelDisplayName === "function" ? getModelDisplayName(m.model) : m.model)}</strong></span>'

# 4. Update createAssistantBubbleUI
target_bubble_meta = '<span>${model || "ModelDock Assistant"}</span>'
rep_bubble_meta = '<span>${(typeof getModelDisplayName === "function" ? getModelDisplayName(model) : model) || "ModelDock Assistant"}</span>'

assert target_author in chat_text, "target_author not found"
assert target_engine1 in chat_text, "target_engine1 not found"
assert target_engine2 in chat_text, "target_engine2 not found"
assert target_bubble_meta in chat_text, "target_bubble_meta not found"

chat_text = chat_text.replace(target_author, rep_author, 1)
chat_text = chat_text.replace(target_engine1, rep_engine1, 1)
chat_text = chat_text.replace(target_engine2, rep_engine2, 1)
chat_text = chat_text.replace(target_bubble_meta, rep_bubble_meta, 1)

with open('static/js/chat.js', 'w', encoding='utf-8', newline='') as f:
    f.write(chat_text)

print("Updated static/js/chat.js successfully!")

with open('static/js/hf_hub.js', 'r', encoding='utf-8') as f:
    hf_text = f.read()

target_installed_card = """function renderInstalledCardHTML(m) {
  const safeName = escapeHubHtml(m.name || "Unknown");"""

rep_installed_card = """function renderInstalledCardHTML(m) {
  const displayName = m.alias || m.name || "Unknown";
  const safeName = escapeHubHtml(displayName);
  const aliasBadge = m.alias ? `<span class="badge" style="background: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.4); font-size: 0.68rem; font-weight: 600;">🏷️ ${escapeHubHtml(m.name)}</span>` : "";"""

target_card_title = """            <div class="model-name" title="${safeName}" style="display: flex; align-items: center; gap: 0.35rem;">
              <span style="color: #10b981; font-size: 0.95rem;">⚡</span>
              <span>${safeName}</span>
            </div>"""

rep_card_title = """            <div class="model-name" title="${escapeHubHtml(m.name)}" style="display: flex; align-items: center; gap: 0.35rem;">
              <span style="color: #10b981; font-size: 0.95rem;">⚡</span>
              <span>${safeName}</span>
              ${aliasBadge}
            </div>"""

target_search_filter = """  const localMatches = (AppState.localModels || []).filter((m) => {
    const name = (m.name || "").toLowerCase();
    const fn = (m.filename || "").toLowerCase();
    const arch = (m.architecture || "").toLowerCase();
    const fam = (m.family || "").toLowerCase();
    return name.includes(qLower) || fn.includes(qLower) || arch.includes(qLower) || fam.includes(qLower);
  });"""

rep_search_filter = """  const localMatches = (AppState.localModels || []).filter((m) => {
    const name = (m.name || "").toLowerCase();
    const alias = (m.alias || "").toLowerCase();
    const fn = (m.filename || "").toLowerCase();
    const arch = (m.architecture || "").toLowerCase();
    const fam = (m.family || "").toLowerCase();
    return name.includes(qLower) || alias.includes(qLower) || fn.includes(qLower) || arch.includes(qLower) || fam.includes(qLower);
  });"""

target_installed_card_norm = target_installed_card.replace("\r\n", "\n")
rep_installed_card_norm = rep_installed_card.replace("\r\n", "\n")
target_card_title_norm = target_card_title.replace("\r\n", "\n")
rep_card_title_norm = rep_card_title.replace("\r\n", "\n")
target_search_filter_norm = target_search_filter.replace("\r\n", "\n")
rep_search_filter_norm = rep_search_filter.replace("\r\n", "\n")

hf_text_norm = hf_text.replace("\r\n", "\n")

assert target_installed_card_norm in hf_text_norm, "target_installed_card not found"
assert target_card_title_norm in hf_text_norm, "target_card_title not found"
assert target_search_filter_norm in hf_text_norm, "target_search_filter not found"

hf_text_norm = hf_text_norm.replace(target_installed_card_norm, rep_installed_card_norm, 1)
hf_text_norm = hf_text_norm.replace(target_card_title_norm, rep_card_title_norm, 1)
# Replace both occurrences in preview and full search
hf_text_norm = hf_text_norm.replace(target_search_filter_norm, rep_search_filter_norm)

with open('static/js/hf_hub.js', 'w', encoding='utf-8', newline='') as f:
    f.write(hf_text_norm.replace('\n', '\r\n'))

print("Updated static/js/hf_hub.js successfully!")
