from pathlib import Path

p = Path(r"a:\AI_Project_work\ollama_2nd_copy\static\js\chat.js")
content = p.read_text(encoding="utf-8")

old_block = '''function cancelPromptEdit(msgIndex) {
  const bodyEl = document.getElementById(`msg-body-${msgIndex}`);
  if (!bodyEl) return;
  const prevHtml = bodyEl.getAttribute("data-prev-html");
  if (prevHtml) {
    bodyEl.innerHTML = prevHtml;
    bodyEl.removeAttribute("data-prev-html");
  } else {
    loadSessionMessages();
  }
}

/**
 * Rewinds conversation to this prompt, updates prompt with new text, and runs generation from there.
 */
async function submitEditedPrompt(msgIndex) {
  const textarea = document.getElementById(`inline-edit-input-${msgIndex}`);
  if (!textarea) return;
  const newPrompt = textarea.value.trim();
  if (!newPrompt) {
    alert("Please enter a prompt before submitting.");
    return;
  }

  const originalMsg = chatHistory[msgIndex] || {};
  const preservedAttachments = originalMsg.attachments || [];

  // Rewind conversation history up to msgIndex
  chatHistory = chatHistory.slice(0, msgIndex);
  const currentSession = getActiveSession();
  if (currentSession) {
    currentSession.messages = chatHistory;
    currentSession.timestamp = Date.now();
    saveSessionsToStorage();
  }

  // Cleanly re-render remaining history
  loadSessionMessages();

  // Populate input and send
  const userInput = document.getElementById("user-input");
  if (userInput) {
    userInput.value = newPrompt;
  }
  chatAttachments = preservedAttachments;
  renderAttachmentTray();

  await sendMessage();
}

/**
 * Retries the last user prompt by rewinding the last turn and sending again.
 */
async function retryLastUserPrompt() {
  if (chatHistory.length === 0) return;

  let lastUserIdx = -1;
  for (let i = chatHistory.length - 1; i >= 0; i--) {
    if (chatHistory[i].role === "user") {
      lastUserIdx = i;
      break;
    }
  }

  if (lastUserIdx === -1) return;

  const lastUserMsg = chatHistory[lastUserIdx];
  const promptToRetry = lastUserMsg.content;
  const attachmentsToRetry = lastUserMsg.attachments || [];

  chatHistory = chatHistory.slice(0, lastUserIdx);
  const currentSession = getActiveSession();
  if (currentSession) {
    currentSession.messages = chatHistory;
    currentSession.timestamp = Date.now();
    saveSessionsToStorage();
  }

  loadSessionMessages();

  const userInput = document.getElementById("user-input");
  if (userInput) {
    userInput.value = promptToRetry;
  }
  chatAttachments = attachmentsToRetry;
  renderAttachmentTray();

  await sendMessage();
}'''

new_block = '''function cancelPromptEdit(msgIndex) {
  const bodyEl = document.getElementById(`msg-body-${msgIndex}`);
  if (!bodyEl) return;
  const prevHtml = bodyEl.getAttribute("data-prev-html");
  if (prevHtml) {
    bodyEl.innerHTML = prevHtml;
    bodyEl.removeAttribute("data-prev-html");
  } else {
    loadActiveSession();
  }
}

/**
 * Rewinds conversation to this prompt, updates prompt with new text, and runs generation from there.
 */
async function submitEditedPrompt(msgIndex) {
  const textarea = document.getElementById(`inline-edit-input-${msgIndex}`);
  if (!textarea) return;
  const newPrompt = textarea.value.trim();
  if (!newPrompt) {
    alert("Please enter a prompt before submitting.");
    return;
  }

  if (abortController) {
    try {
      abortController.abort();
    } catch (e) {}
    abortController = null;
  }

  const originalMsg = chatHistory[msgIndex] || {};
  const preservedAttachments = originalMsg.attachments || [];

  // Rewind conversation history up to msgIndex
  chatHistory = chatHistory.slice(0, msgIndex);
  const currentSession = getActiveSession();
  if (currentSession) {
    currentSession.messages = chatHistory;
    currentSession.timestamp = Date.now();
    saveSessionsToStorage();
  }

  // Cleanly re-render remaining history
  loadActiveSession();

  // Populate input and send
  const userInput = document.getElementById("user-input");
  if (userInput) {
    userInput.value = newPrompt;
  }
  chatAttachments = preservedAttachments;
  renderAttachmentTray();

  await sendMessage();
}

/**
 * Retries the last user prompt by rewinding the last turn and sending again.
 */
async function retryLastUserPrompt() {
  if (chatHistory.length === 0) return;

  if (abortController) {
    try {
      abortController.abort();
    } catch (e) {}
    abortController = null;
  }

  let lastUserIdx = -1;
  for (let i = chatHistory.length - 1; i >= 0; i--) {
    if (chatHistory[i].role === "user") {
      lastUserIdx = i;
      break;
    }
  }

  if (lastUserIdx === -1) return;

  const lastUserMsg = chatHistory[lastUserIdx];
  const promptToRetry = lastUserMsg.content;
  const attachmentsToRetry = lastUserMsg.attachments || [];

  chatHistory = chatHistory.slice(0, lastUserIdx);
  const currentSession = getActiveSession();
  if (currentSession) {
    currentSession.messages = chatHistory;
    currentSession.timestamp = Date.now();
    saveSessionsToStorage();
  }

  loadActiveSession();

  const userInput = document.getElementById("user-input");
  if (userInput) {
    userInput.value = promptToRetry;
  }
  chatAttachments = attachmentsToRetry;
  renderAttachmentTray();

  await sendMessage();
}'''

assert old_block in content, "old_block not found in chat.js"
content = content.replace(old_block, new_block, 1)
p.write_text(content, encoding="utf-8")
print("Successfully fixed submitEditedPrompt, cancelPromptEdit, and retryLastUserPrompt in chat.js!")
