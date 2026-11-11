/**
 * ModelDock Prompt Studio & AI Prompt Enhancer Popover
 * Provides interactive floating prompt styles (Photorealistic 8K, Cinematic, Studio, Concept Art),
 * automatic typo fixing (e.g. 'healmat' -> 'helmet'), and zero textarea shrinking.
 */

const RANDOM_IDEAS = [
  "sleek glossy black motorcycle helmet on a rustic oak table",
  "vintage 1968 red sports car on wet asphalt street at night with neon reflections",
  "cyberpunk samurai warrior standing in rainy neo-tokyo alleyway",
  "mythical crystalline dragon perched on snowy mountain summit at sunrise",
  "cozy coffee shop interior with rain trickling down windows and warm fairy lights",
  "astronaut floating in deep cosmos with glowing spiral galaxy reflections on visor",
  "macro photograph of a colorful hummingbird sipping nectar from an exotic flower",
  "modern minimalist luxury villa with infinity pool overlooking ocean cliffs",
  "antique brass pocket watch resting on aged leather book with soft golden illumination",
  "futuristic robot barista serving steaming matcha latte in sleek futuristic cafe"
];

let currentStudioMode = 'image';
let isPopoverOpen = false;

/**
 * Toggle the Floating Prompt Enhancer Popover
 */
function togglePromptEnhancerPopover() {
  const popover = document.getElementById('popover-prompt-enhancer');
  if (!popover) return;

  if (isPopoverOpen && !popover.classList.contains('hidden')) {
    closePromptEnhancerPopover();
  } else {
    openPromptEnhancerPopover();
  }
}

/**
 * Open the Prompt Enhancer Popover with 4 live enhanced styles
 */
async function openPromptEnhancerPopover() {
  const popover = document.getElementById('popover-prompt-enhancer');
  const chatInput = document.getElementById('user-input');
  if (!popover) return;

  const rawText = chatInput ? chatInput.value.trim() : '';
  const conceptToEnhance = rawText || 'sleek motorcycle helmet on a wooden table';

  popover.classList.remove('hidden');
  isPopoverOpen = true;

  const listContainer = document.getElementById('popover-variations-list');
  const typoNotice = document.getElementById('popover-typo-notice');

  if (listContainer) {
    listContainer.innerHTML = `
      <div class="popover-loading">
        <svg class="spin-anim" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle><path d="M12 2a10 10 0 0 1 10 10"></path></svg>
        <span>Synthesizing 4 prompt styles for "${escapeHtml(conceptToEnhance.slice(0, 35))}${conceptToEnhance.length > 35 ? '...' : ''}"...</span>
      </div>
    `;
  }

  if (typoNotice) typoNotice.classList.add('hidden');

  try {
    const res = await fetch('/api/prompt/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        concept: conceptToEnhance,
        style: 'photorealistic',
        lighting: 'golden_hour',
        camera: '85mm_portrait'
      })
    });

    const data = await res.json();
    if (!data.success) throw new Error(data.error || 'Failed to synthesize prompts');

    // Show typo corrections banner inside popover if any
    if (typoNotice) {
      if (data.typos_corrected && data.typos_corrected.length > 0) {
        const fixes = data.typos_corrected.map(c => `<strong>"${escapeHtml(c.original)}"</strong> &rarr; <strong>"${escapeHtml(c.corrected)}"</strong>`).join(' &bull; ');
        typoNotice.innerHTML = `<span>💡 Typo auto-fixed: ${fixes}</span>`;
        typoNotice.classList.remove('hidden');
      } else {
        typoNotice.classList.add('hidden');
      }
    }

    // Render the 4 distinct variations
    if (listContainer) {
      listContainer.innerHTML = '';

      const badgeClasses = ['badge-purple', 'badge-cyan', 'badge-success', 'badge-warning'];

      data.variations.forEach((v, idx) => {
        const card = document.createElement('div');
        card.className = 'popover-var-card';
        const badgeClass = badgeClasses[idx % badgeClasses.length];

        card.innerHTML = `
          <div class="popover-var-header">
            <div class="popover-var-title">
              <span>${escapeHtml(v.title)}</span>
              <span class="badge ${badgeClass}" style="font-size: 0.68rem;">${escapeHtml(v.badge)}</span>
            </div>
            <div class="popover-var-actions">
              <button class="btn-pop-btn" onclick="event.stopPropagation(); copyPromptText('${escapeAttr(v.prompt)}', this)" title="Copy prompt">
                Copy
              </button>
              <button class="btn-pop-btn btn-pop-use" onclick="event.stopPropagation(); selectPopoverPrompt('${escapeAttr(v.prompt)}', false)" title="Replace input text with this prompt">
                ✓ Use This
              </button>
              <button class="btn-pop-btn btn-pop-render" onclick="event.stopPropagation(); selectPopoverPrompt('${escapeAttr(v.prompt)}', true)" title="Render 8K image immediately!">
                🚀 Render 8K
              </button>
            </div>
          </div>
          <p class="popover-prompt-text">${escapeHtml(v.prompt)}</p>
        `;

        // Clicking anywhere on card applies the prompt
        card.onclick = () => selectPopoverPrompt(v.prompt, false);

        listContainer.appendChild(card);
      });
    }

  } catch (err) {
    console.error('Failed to load popover prompts:', err);
    if (listContainer) {
      listContainer.innerHTML = `
        <div style="padding: 1.5rem; text-align: center; color: #f87171; font-size: 0.85rem;">
          ⚠️ Failed to generate prompt variations: ${escapeHtml(err.message)}
        </div>
      `;
    }
  }
}

/**
 * Close the Prompt Enhancer Popover
 */
function closePromptEnhancerPopover() {
  const popover = document.getElementById('popover-prompt-enhancer');
  if (popover) {
    popover.classList.add('hidden');
  }
  isPopoverOpen = false;
}

/**
 * Select a prompt from the popover: places it in chat box
 */
function selectPopoverPrompt(promptText, autoRender = false) {
  const chatInput = document.getElementById('user-input');
  if (chatInput) {
    chatInput.value = promptText;
    chatInput.classList.add('prompt-enhanced-glow');
    setTimeout(() => chatInput.classList.remove('prompt-enhanced-glow'), 1200);

    // Auto-resize
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 180) + 'px';
  }

  closePromptEnhancerPopover();

  if (autoRender) {
    const sendBtn = document.getElementById('btn-send');
    if (sendBtn) {
      setTimeout(() => sendBtn.click(), 100);
    }
  } else {
    if (chatInput) chatInput.focus();
    showPromptToast('✨ Enhanced prompt selected!', 'success');
  }
}

/**
 * Open the Full Studio Modal from Popover
 */
function openFullStudioFromPopover() {
  const chatInput = document.getElementById('user-input');
  const text = chatInput ? chatInput.value.trim() : '';
  closePromptEnhancerPopover();
  openPromptStudioModal(text);
}

/**
 * Open the Full Prompt Generator Studio Modal
 */
function openPromptStudioModal(initialText = '') {
  const modal = document.getElementById('modal-prompt-studio');
  if (!modal) return;

  const chatInput = document.getElementById('user-input');
  const conceptInput = document.getElementById('prompt-input-concept');

  const textToUse = initialText || (chatInput ? chatInput.value.trim() : '');
  if (conceptInput) {
    if (textToUse) {
      conceptInput.value = textToUse;
    } else if (!conceptInput.value.trim()) {
      conceptInput.value = 'helmet on the table';
    }
  }

  modal.classList.remove('hidden');
  modal.style.display = 'flex';

  setTimeout(() => {
    if (conceptInput) conceptInput.focus();
  }, 100);
}

/**
 * Close the Prompt Studio Modal
 */
function closePromptStudioModal() {
  const modal = document.getElementById('modal-prompt-studio');
  if (modal) {
    modal.classList.add('hidden');
    modal.style.display = 'none';
  }
}

/**
 * Generate Variations in the Studio Modal
 */
async function generatePromptsFromStudio() {
  const conceptInput = document.getElementById('prompt-input-concept');
  const concept = conceptInput ? conceptInput.value.trim() : '';

  if (!concept) {
    showPromptToast('Please enter an idea or subject first', 'error');
    if (conceptInput) conceptInput.focus();
    return;
  }

  const style = document.getElementById('prompt-select-style')?.value || 'photorealistic';
  const lighting = document.getElementById('prompt-select-lighting')?.value || 'golden_hour';
  const camera = document.getElementById('prompt-select-camera')?.value || '85mm_portrait';

  const btn = document.getElementById('btn-generate-prompts');
  const origHtml = btn ? btn.innerHTML : '';
  if (btn) {
    btn.innerHTML = `<svg class="spin-anim" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle><path d="M12 2a10 10 0 0 1 10 10"></path></svg> <span>Synthesizing Master Prompts...</span>`;
    btn.disabled = true;
  }

  try {
    const res = await fetch('/api/prompt/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ concept, style, lighting, camera })
    });

    const data = await res.json();
    if (!data.success) throw new Error(data.error || 'Failed to generate variations');

    // Typo banner
    const typoBanner = document.getElementById('studio-typo-banner');
    const typoText = document.getElementById('studio-typo-text');
    if (typoBanner && typoText) {
      if (data.typos_corrected && data.typos_corrected.length > 0) {
        const corrList = data.typos_corrected.map(c => `<strong>"${escapeHtml(c.original)}"</strong> &rarr; <strong>"${escapeHtml(c.corrected)}"</strong>`).join(' &bull; ');
        typoText.innerHTML = `<span>Typo auto-fixed: ${corrList}</span>`;
        typoBanner.classList.remove('hidden');
      } else {
        typoBanner.classList.add('hidden');
      }
    }

    // Render variations
    const container = document.getElementById('prompt-variations-container');
    const list = document.getElementById('prompt-variations-list');
    if (container && list) {
      list.innerHTML = '';
      const badgeClasses = ['badge-purple', 'badge-cyan', 'badge-success', 'badge-warning'];

      data.variations.forEach((v, idx) => {
        const card = document.createElement('div');
        card.className = 'prompt-variation-card';
        card.innerHTML = `
          <div class="prompt-variation-header">
            <div class="prompt-variation-title">
              <span class="prompt-v-name">${escapeHtml(v.title)}</span>
              <span class="badge ${badgeClasses[idx % badgeClasses.length]}">${escapeHtml(v.badge)}</span>
            </div>
            <div class="prompt-variation-actions">
              <button class="btn-p-action btn-p-copy" onclick="copyPromptText('${escapeAttr(v.prompt)}', this)" title="Copy Prompt">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                <span>Copy</span>
              </button>
              <button class="btn-p-action btn-p-chat" onclick="applyPromptToChat('${escapeAttr(v.prompt)}', false)" title="Insert into chat box">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                <span>Use in Chat</span>
              </button>
              <button class="btn-p-action btn-p-render" onclick="applyPromptToChat('${escapeAttr(v.prompt)}', true)" title="Generate this 8K image now!">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                <span>Render 8K</span>
              </button>
            </div>
          </div>
          <div class="prompt-variation-body">
            <p class="prompt-text-display">${escapeHtml(v.prompt)}</p>
            ${v.negative_prompt ? `<div class="prompt-neg-display"><strong>Negative:</strong> ${escapeHtml(v.negative_prompt)}</div>` : ''}
          </div>
        `;
        list.appendChild(card);
      });

      container.classList.remove('hidden');
    }

  } catch (err) {
    console.error('Failed to generate prompt variations:', err);
    showPromptToast('Error generating prompts: ' + err.message, 'error');
  } finally {
    if (btn) {
      btn.innerHTML = origHtml;
      btn.disabled = false;
    }
  }
}

/**
 * Apply prompt into the main chat box
 */
function applyPromptToChat(promptText, autoGenerate = false) {
  const chatInput = document.getElementById('user-input');
  if (chatInput) {
    chatInput.value = promptText;
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 180) + 'px';
  }

  closePromptStudioModal();

  if (autoGenerate) {
    if (typeof switchTab === 'function') switchTab('chat');
    setTimeout(() => {
      const sendBtn = document.getElementById('btn-send');
      if (sendBtn) sendBtn.click();
    }, 150);
  } else {
    if (chatInput) chatInput.focus();
  }
}

/**
 * Copy text to clipboard
 */
function copyPromptText(text, btnElement) {
  navigator.clipboard.writeText(text).then(() => {
    if (btnElement) {
      const originalHtml = btnElement.innerHTML;
      btnElement.innerHTML = `✓ Copied!`;
      btnElement.style.color = '#34d399';
      setTimeout(() => {
        btnElement.innerHTML = originalHtml;
        btnElement.style.color = '';
      }, 1500);
    }
  }).catch(() => {
    showPromptToast('Failed to copy', 'error');
  });
}

/**
 * Pick a random creative idea
 */
function randomizeStudioIdea() {
  const conceptInput = document.getElementById('prompt-input-concept');
  if (!conceptInput) return;
  const pick = RANDOM_IDEAS[Math.floor(Math.random() * RANDOM_IDEAS.length)];
  conceptInput.value = pick;
  conceptInput.focus();
}

/**
 * Switch mode between Image Diffusion and LLM System Prompts
 */
function switchPromptStudioMode(mode) {
  currentStudioMode = mode;
  const btnImg = document.getElementById('mode-btn-image');
  const btnLlm = document.getElementById('mode-btn-llm');
  const secImg = document.getElementById('prompt-section-image');
  const secLlm = document.getElementById('prompt-section-llm');

  if (mode === 'image') {
    btnImg?.classList.add('active');
    btnLlm?.classList.remove('active');
    secImg?.classList.remove('hidden');
    secLlm?.classList.add('hidden');
  } else {
    btnLlm?.classList.add('active');
    btnImg?.classList.remove('active');
    secLlm?.classList.remove('hidden');
    secImg?.classList.add('hidden');
  }
}

/**
 * Generate Structured System Prompt for LLM Reasoning
 */
async function generateLLMPromptsFromStudio() {
  const taskInput = document.getElementById('llm-task-input');
  const task = taskInput ? taskInput.value.trim() : '';
  if (!task) {
    showPromptToast('Please enter what you want the LLM to do', 'error');
    if (taskInput) taskInput.focus();
    return;
  }

  const role = document.getElementById('llm-role-select')?.value || 'expert';

  try {
    const res = await fetch('/api/prompt/llm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_description: task, role })
    });

    const data = await res.json();
    if (data.success) {
      const container = document.getElementById('llm-result-container');
      const content = document.getElementById('llm-result-content');
      if (container && content) {
        content.innerHTML = `
          <div class="prompt-variation-card">
            <div class="prompt-variation-header">
              <span class="prompt-v-name">🧠 System Prompt Architecture</span>
              <button class="btn-p-action btn-p-copy" onclick="copyPromptText('${escapeAttr(data.system_prompt)}', this)">Copy System</button>
            </div>
            <pre class="prompt-pre-display">${escapeHtml(data.system_prompt)}</pre>
          </div>
          <div class="prompt-variation-card" style="margin-top: 0.75rem;">
            <div class="prompt-variation-header">
              <span class="prompt-v-name">💬 Structured User Request</span>
              <div class="prompt-variation-actions">
                <button class="btn-p-action btn-p-copy" onclick="copyPromptText('${escapeAttr(data.user_prompt)}', this)">Copy</button>
                <button class="btn-p-action btn-p-chat" onclick="applyPromptToChat('${escapeAttr(data.user_prompt)}', false)">Use in Chat</button>
              </div>
            </div>
            <pre class="prompt-pre-display">${escapeHtml(data.user_prompt)}</pre>
          </div>
        `;
        container.classList.remove('hidden');
      }
    }
  } catch (err) {
    showPromptToast('Error generating LLM prompt: ' + err.message, 'error');
  }
}

/**
 * Toast Notification Helper
 */
function showPromptToast(message, type = 'info') {
  const existing = document.getElementById('prompt-studio-toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'prompt-studio-toast';
  toast.className = `prompt-toast prompt-toast-${type}`;
  toast.innerHTML = message;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('visible');
  }, 10);

  setTimeout(() => {
    toast.classList.remove('visible');
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Click-outside listener to dismiss popover
document.addEventListener('click', (e) => {
  const popover = document.getElementById('popover-prompt-enhancer');
  const btn = document.getElementById('btn-magic-enhance');
  if (popover && !popover.classList.contains('hidden') && !popover.contains(e.target) && (!btn || !btn.contains(e.target))) {
    closePromptEnhancerPopover();
  }
});

// Escape key listener
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closePromptEnhancerPopover();
    closePromptStudioModal();
  }
});

// Utility Helpers
function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function escapeAttr(str) {
  if (!str) return '';
  return str.replace(/'/g, "\\'").replace(/"/g, '&quot;').replace(/\n/g, '\\n');
}

// Expose globals for inline event handlers
window.togglePromptEnhancerPopover = togglePromptEnhancerPopover;
window.openPromptEnhancerPopover = openPromptEnhancerPopover;
window.closePromptEnhancerPopover = closePromptEnhancerPopover;
window.selectPopoverPrompt = selectPopoverPrompt;
window.openFullStudioFromPopover = openFullStudioFromPopover;
window.openPromptStudioModal = openPromptStudioModal;
window.closePromptStudioModal = closePromptStudioModal;
window.generatePromptsFromStudio = generatePromptsFromStudio;
window.generateLLMPromptsFromStudio = generateLLMPromptsFromStudio;
window.switchPromptStudioMode = switchPromptStudioMode;
window.randomizeStudioIdea = randomizeStudioIdea;
window.applyPromptToChat = applyPromptToChat;
window.copyPromptText = copyPromptText;
