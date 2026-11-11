/**
 * ModelDock Studio - Real-Time Streaming Chat Playground & Multi-Session History
 * Modeled after ChatGPT with Left Sidebar, Projects/Recents, Search, and Profile Footer
 */

let chatSessions = [];
let activeSessionId = null;
let chatHistory = [];
let abortController = null;
let chatAttachments = [];
let projects = [];
let expandedProjectIds = new Set();

function initChat() {
  const btnSend = document.getElementById("btn-send");
  const btnStop = document.getElementById("btn-stop");
  const userInput = document.getElementById("user-input");
  const btnClear = document.getElementById("btn-clear-chat");
  const btnToggleParams = document.getElementById("btn-toggle-params");
  const btnChatThink = document.getElementById("btn-chat-think");
  const tempSlider = document.getElementById("param-temp");
  const tempVal = document.getElementById("temp-val");
  const ctxSelect = document.getElementById("param-ctx");
  const ctxVal = document.getElementById("ctx-val");
  const btnRefreshModels = document.getElementById("btn-refresh-models");
  const btnAttach = document.getElementById("btn-attach");
  const fileInput = document.getElementById("chat-file-input");
  const dropContainer = document.getElementById("chat-drop-container");

  // Sidebar Controls
  const btnNewChat = document.getElementById("btn-new-chat");
  const btnToggleSidebar = document.getElementById("btn-toggle-sidebar");
  const btnOpenSidebar = document.getElementById("btn-open-sidebar");
  const btnSearchChats = document.getElementById("btn-search-chats");
  const searchInput = document.getElementById("chat-search-input");
  const btnClearSearch = document.getElementById("btn-clear-search");
  const btnCreateProjectSidebar = document.getElementById("btn-create-project-sidebar");
  const btnProjNewChat = document.getElementById("btn-project-new-chat");
  const btnProjSettings = document.getElementById("btn-project-settings");

  if (btnSend) btnSend.addEventListener("click", sendMessage);
  if (btnStop) btnStop.addEventListener("click", stopGeneration);

  // New Chat Click (Outer Standalone Chat)
  if (btnNewChat) {
    btnNewChat.addEventListener("click", () => createNewSession(null));
  }

  // Create Project in Sidebar
  if (btnCreateProjectSidebar) {
    btnCreateProjectSidebar.onclick = (e) => {
      if (e) e.stopPropagation();
      openNewProjectModal();
    };
  }

  // Banner Actions
  if (btnProjNewChat) {
    btnProjNewChat.onclick = () => {
      const current = getActiveSession();
      if (current && current.projectId) {
        createNewSession(current.projectId);
      }
    };
  }
  if (btnProjSettings) {
    btnProjSettings.onclick = () => {
      const current = getActiveSession();
      if (current && current.projectId) {
        openEditProjectModal(current.projectId);
      }
    };
  }

  // Sidebar Toggle (Collapse / Open)
  if (btnToggleSidebar) {
    btnToggleSidebar.onclick = (e) => {
      if (e) { e.preventDefault(); e.stopPropagation(); }
      toggleSidebar(true);
    };
  }
  if (btnOpenSidebar) {
    btnOpenSidebar.onclick = (e) => {
      if (e) { e.preventDefault(); e.stopPropagation(); }
      toggleSidebar(false);
    };
  }

  // Search in Chats / Projects
  if (btnSearchChats) {
    btnSearchChats.addEventListener("click", () => {
      const box = document.getElementById("sidebar-search-box");
      if (box) {
        box.classList.toggle("hidden");
        if (!box.classList.contains("hidden") && searchInput) {
          searchInput.focus();
        }
      }
    });
  }

  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      renderSidebarSessions(e.target.value.trim().toLowerCase());
    });
  }

  if (btnClearSearch && searchInput) {
    btnClearSearch.addEventListener("click", () => {
      searchInput.value = "";
      renderSidebarSessions();
      const box = document.getElementById("sidebar-search-box");
      if (box) box.classList.add("hidden");
    });
  }

  // Think Button
  if (btnChatThink) {
    btnChatThink.addEventListener("click", () => {
      const panel = document.getElementById("chat-params-panel");
      if (panel) {
        panel.classList.toggle("hidden");
        btnChatThink.classList.toggle("active", !panel.classList.contains("hidden"));
      }
    });
  }

  // Attachment button click
  if (btnAttach && fileInput) {
    btnAttach.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files.length > 0) {
        uploadFiles(e.target.files);
        fileInput.value = "";
      }
    });
  }

  // Drag and Drop files onto chat input
  if (dropContainer) {
    dropContainer.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropContainer.classList.add("drag-active");
    });

    dropContainer.addEventListener("dragleave", (e) => {
      e.preventDefault();
      dropContainer.classList.remove("drag-active");
    });

    dropContainer.addEventListener("drop", (e) => {
      e.preventDefault();
      dropContainer.classList.remove("drag-active");
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        uploadFiles(e.dataTransfer.files);
      }
    });
  }

  // Clipboard Paste Support (Images, Screenshots, Documents)
  document.addEventListener("paste", handlePasteEvent);

  // Clear Active Chat
  if (btnClear) {
    btnClear.addEventListener("click", () => {
      chatHistory = [];
      chatAttachments = [];
      renderAttachmentTray();
      const current = getActiveSession();
      if (current) {
        current.messages = [];
        current.title = "New chat";
        saveSessionsToStorage();
        renderSidebarSessions();
      }
      renderWelcomeScreen();
    });
  }

  if (btnRefreshModels) {
    btnRefreshModels.addEventListener("click", loadLocalModels);
  }

  const chatSelect = document.getElementById("chat-model-select");
  if (chatSelect) {
    chatSelect.addEventListener("change", () => {
      const selectedModel = chatSelect.value;
      if (selectedModel) {
        fetch("/api/engine/load", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ model: selectedModel }),
        }).catch(() => {});
        try {
          localStorage.setItem("modeldock_active_model", selectedModel);
        } catch (e) {}

        // Bind model to active chat session for per-chat memory
        const currSession = getActiveSession();
        if (currSession) {
          currSession.model = selectedModel;
          saveSessionsToStorage();
        }

        // Update Project Banner if currently inside a project
        const bannerModel = document.getElementById("project-banner-model");
        if (bannerModel) {
          bannerModel.textContent = `🤖 ${selectedModel}`;
        }
      }
    });
  }

  if (btnToggleParams) {
    btnToggleParams.addEventListener("click", () => {
      const panel = document.getElementById("chat-params-panel");
      if (panel) panel.classList.toggle("hidden");
    });
  }

  const paramSysPrompt = document.getElementById("param-system-prompt");

  if (tempSlider && tempVal) {
    tempSlider.addEventListener("input", () => {
      tempVal.textContent = tempSlider.value;
      try {
        localStorage.setItem("modeldock_param_temp", tempSlider.value);
        const curr = getActiveSession();
        if (curr) {
          curr.temperature = parseFloat(tempSlider.value);
          saveSessionsToStorage();
        }
      } catch (e) {}
    });
  }

  if (ctxSelect && ctxVal) {
    ctxSelect.addEventListener("change", () => {
      ctxVal.textContent = ctxSelect.value;
      try {
        localStorage.setItem("modeldock_param_ctx", ctxSelect.value);
        const curr = getActiveSession();
        if (curr) {
          curr.contextWindow = parseInt(ctxSelect.value, 10);
          saveSessionsToStorage();
        }
      } catch (e) {}
    });
  }

  if (paramSysPrompt) {
    paramSysPrompt.addEventListener("input", () => {
      try {
        localStorage.setItem("modeldock_param_sys_prompt", paramSysPrompt.value);
        const curr = getActiveSession();
        if (curr) {
          curr.systemPrompt = paramSysPrompt.value;
          saveSessionsToStorage();
        }
      } catch (e) {}
    });
  }

  if (userInput) {
    userInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    // Auto-grow textarea
    userInput.addEventListener("input", () => {
      userInput.style.height = "auto";
      userInput.style.height = Math.min(160, userInput.scrollHeight) + "px";
    });
  }

  // Global Keyboard Shortcuts
  document.addEventListener("keydown", (e) => {
    // Ctrl+K -> Focus Search in Sidebar
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      const activeTab = AppState ? AppState.currentTab : "chat";
      if (activeTab === "chat") {
        e.preventDefault();
        const box = document.getElementById("sidebar-search-box");
        if (box) {
          box.classList.remove("hidden");
          const input = document.getElementById("chat-search-input");
          if (input) input.focus();
        }
      }
    }
    // Ctrl+N -> New Chat
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "n" && !e.shiftKey) {
      const activeTab = AppState ? AppState.currentTab : "chat";
      if (activeTab === "chat") {
        e.preventDefault();
        createNewSession();
      }
    }
    // Ctrl+B or Ctrl+\ -> Toggle Sidebar Collapse
    if ((e.ctrlKey || e.metaKey) && (e.key.toLowerCase() === "b" || e.key === "\\")) {
      const activeTab = AppState ? AppState.currentTab : "chat";
      if (activeTab === "chat") {
        e.preventDefault();
        toggleSidebar();
      }
    }
  });

  // Restore saved sidebar collapsed preference
  try {
    const isCollapsed = (localStorage.getItem("modeldock_sidebar_collapsed") || localStorage.getItem("omnimodel_sidebar_collapsed")) === "true";
    if (isCollapsed) {
      toggleSidebar(true, false);
    }
  } catch (e) {}

  // Initialize Draggable Sidebar Resizer
  initSidebarResizer();

  // Initialize Multi-Session History
  initChatSessions();

  // Update profile card details from AppState / HF if available
  updateUserProfileInSidebar();
}


// --- Sidebar Draggable Resizer Logic ---
function initSidebarResizer() {
  const resizer = document.getElementById("sidebar-resizer");
  const wrapper = document.getElementById("chat-wrapper");
  const sidebar = document.getElementById("chat-sidebar");
  if (!resizer || !wrapper || !sidebar) return;

  const MIN_WIDTH = 190;
  const MAX_WIDTH_CAP = 520;
  const DEFAULT_WIDTH = 260;

  // Restore saved width if present
  try {
    const saved = localStorage.getItem("modeldock_sidebar_width");
    if (saved) {
      const parsed = parseInt(saved, 10);
      if (!isNaN(parsed) && parsed >= MIN_WIDTH && parsed <= MAX_WIDTH_CAP) {
        document.documentElement.style.setProperty("--sidebar-width", `${parsed}px`);
      }
    }
  } catch (e) {}

  let isDragging = false;
  let startX = 0;
  let startWidth = DEFAULT_WIDTH;

  function onMouseDown(e) {
    if (e.button !== 0) return; // Left mouse button only
    if (wrapper.classList.contains("sidebar-collapsed")) return;

    isDragging = true;
    startX = e.clientX;
    const currentComputed = window.getComputedStyle(sidebar).width;
    startWidth = parseInt(currentComputed, 10) || DEFAULT_WIDTH;

    wrapper.classList.add("is-resizing");
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    e.preventDefault();
  }

  function onMouseMove(e) {
    if (!isDragging) return;
    const deltaX = e.clientX - startX;
    let newWidth = startWidth + deltaX;

    const dynamicMax = Math.min(MAX_WIDTH_CAP, Math.floor(window.innerWidth * 0.55));
    if (newWidth < MIN_WIDTH) newWidth = MIN_WIDTH;
    if (newWidth > dynamicMax) newWidth = dynamicMax;

    document.documentElement.style.setProperty("--sidebar-width", `${newWidth}px`);
  }

  function onMouseUp(e) {
    if (!isDragging) return;
    isDragging = false;
    wrapper.classList.remove("is-resizing");
    document.body.style.cursor = "";
    document.body.style.userSelect = "";

    window.removeEventListener("mousemove", onMouseMove);
    window.removeEventListener("mouseup", onMouseUp);

    const currentComputed = window.getComputedStyle(sidebar).width;
    const finalWidth = parseInt(currentComputed, 10);
    if (!isNaN(finalWidth) && finalWidth >= MIN_WIDTH) {
      try {
        localStorage.setItem("modeldock_sidebar_width", String(finalWidth));
      } catch (err) {}
    }
  }

  function onDoubleClick() {
    if (wrapper.classList.contains("sidebar-collapsed")) return;
    document.documentElement.style.setProperty("--sidebar-width", `${DEFAULT_WIDTH}px`);
    try {
      localStorage.setItem("modeldock_sidebar_width", String(DEFAULT_WIDTH));
    } catch (e) {}
  }

  resizer.addEventListener("mousedown", onMouseDown);
  resizer.addEventListener("dblclick", onDoubleClick);
}
window.initSidebarResizer = initSidebarResizer;

// --- Sidebar Toggle Logic ---
function toggleSidebar(forcedState) {
  const wrapper = document.getElementById("chat-wrapper");
  const openBtn = document.getElementById("btn-open-sidebar");
  if (!wrapper) return;

  let shouldCollapse;
  if (typeof forcedState === "boolean") {
    shouldCollapse = forcedState;
  } else {
    shouldCollapse = !wrapper.classList.contains("sidebar-collapsed");
  }

  if (shouldCollapse) {
    wrapper.classList.add("sidebar-collapsed");
    if (openBtn) {
      openBtn.classList.remove("hidden");
      openBtn.style.display = "inline-flex";
    }
    try {
      localStorage.setItem("modeldock_sidebar_collapsed", "true");
    } catch (e) {}
  } else {
    wrapper.classList.remove("sidebar-collapsed");
    if (openBtn) {
      openBtn.classList.add("hidden");
      openBtn.style.display = "none";
    }
    try {
      localStorage.setItem("modeldock_sidebar_collapsed", "false");
    } catch (e) {}
  }
}
window.toggleSidebar = toggleSidebar;

function toggleSidebarGroup(group) {
  const list = document.getElementById(`${group}-chats-list`);
  const arrow = document.getElementById(`${group}-arrow`);
  if (!list) return;
  const isHidden = list.style.display === "none";
  list.style.display = isHidden ? "flex" : "none";
  if (arrow) {
    arrow.style.transform = isHidden ? "rotate(90deg)" : "rotate(0deg)";
  }
}

// --- Projects State & Lifecycle ---
function initProjects() {
  try {
    const raw = (localStorage.getItem("modeldock_projects_v1") || localStorage.getItem("omnimodel_projects_v1"));
    if (raw) {
      projects = JSON.parse(raw);
    }
  } catch (e) {
    projects = [];
  }

  if (!Array.isArray(projects) || projects.length === 0) {
    projects = [
      {
        id: "proj_default",
        name: "Code & Analysis Workspace",
        description: "Project workspace for software engineering, deep reasoning, and document workflows.",
        icon: "📁",
        model: "",
        systemPrompt: "You are an expert technical AI assistant. Deliver concise, well-structured answers with clean code examples, type annotations, and architectural best practices.",
        createdAt: Date.now(),
      },
    ];
    saveProjectsToStorage();
  }
}

function saveProjectsToStorage() {
  try {
    localStorage.setItem("modeldock_projects_v1", JSON.stringify(projects));
  } catch (e) {
    console.warn("Storage quota exceeded for projects:", e);
  }
  syncChatsToServer();
}

function getProject(projectId) {
  if (!projectId) return null;
  return projects.find((p) => p.id === projectId) || null;
}

function openNewProjectModal() {
  const modal = document.getElementById("modal-project");
  if (!modal) return;
  const title = document.getElementById("modal-project-title");
  if (title) title.textContent = "Create New Project";
  const idInput = document.getElementById("project-form-id");
  if (idInput) idInput.value = "";
  const nameInput = document.getElementById("project-form-name");
  if (nameInput) nameInput.value = "";
  const descInput = document.getElementById("project-form-desc");
  if (descInput) descInput.value = "";
  const instInput = document.getElementById("project-form-instructions");
  if (instInput) instInput.value = "";
  const delBtn = document.getElementById("btn-delete-project");
  if (delBtn) delBtn.classList.add("hidden");

  populateProjectModelSelect();
  modal.classList.remove("hidden");
  setTimeout(() => {
    if (nameInput) nameInput.focus();
  }, 60);
}

function openEditProjectModal(projectId) {
  const modal = document.getElementById("modal-project");
  if (!modal) return;
  const proj = getProject(projectId);
  if (!proj) return;

  const title = document.getElementById("modal-project-title");
  if (title) title.textContent = `Project Settings: ${proj.name}`;
  const idInput = document.getElementById("project-form-id");
  if (idInput) idInput.value = proj.id;
  const nameInput = document.getElementById("project-form-name");
  if (nameInput) nameInput.value = proj.name || "";
  const descInput = document.getElementById("project-form-desc");
  if (descInput) descInput.value = proj.description || "";
  const instInput = document.getElementById("project-form-instructions");
  if (instInput) instInput.value = proj.systemPrompt || "";
  const delBtn = document.getElementById("btn-delete-project");
  if (delBtn) delBtn.classList.remove("hidden");

  populateProjectModelSelect(proj.model);
  modal.classList.remove("hidden");
}

function closeProjectModal() {
  const modal = document.getElementById("modal-project");
  if (modal) modal.classList.add("hidden");
}

function populateProjectModelSelect(selectedModel = "") {
  const sel = document.getElementById("project-form-model");
  const chatSel = document.getElementById("chat-model-select");
  if (!sel) return;
  sel.innerHTML = '<option value="">(Inherit Running Model)</option>';
  if (chatSel) {
    Array.from(chatSel.options).forEach((opt) => {
      if (!opt.disabled && opt.value) {
        const option = document.createElement("option");
        option.value = opt.value;
        option.textContent = opt.textContent;
        if (opt.value === selectedModel) option.selected = true;
        sel.appendChild(option);
      }
    });
  }
}

function saveProjectFromModal() {
  const idInput = document.getElementById("project-form-id");
  const nameInput = document.getElementById("project-form-name");
  const descInput = document.getElementById("project-form-desc");
  const modelSelect = document.getElementById("project-form-model");
  const instInput = document.getElementById("project-form-instructions");

  const name = nameInput ? nameInput.value.trim() : "";
  if (!name) {
    alert("Please enter a project name.");
    if (nameInput) nameInput.focus();
    return;
  }

  const projId = idInput && idInput.value ? idInput.value : "proj_" + Date.now();
  const isNew = !idInput || !idInput.value;

  const projectData = {
    id: projId,
    name: name,
    description: descInput ? descInput.value.trim() : "",
    model: modelSelect ? modelSelect.value : "",
    systemPrompt: instInput ? instInput.value.trim() : "",
    icon: "📁",
    updatedAt: Date.now(),
  };

  const existingIdx = projects.findIndex((p) => p.id === projId);
  if (existingIdx >= 0) {
    projects[existingIdx] = { ...projects[existingIdx], ...projectData };
  } else {
    projects.push({ ...projectData, createdAt: Date.now() });
  }

  saveProjectsToStorage();
  closeProjectModal();
  expandedProjectIds.add(projId);

  // If newly created, immediately start a chat inside this project!
  if (isNew) {
    createNewSession(projId);
  } else {
    renderSidebarSessions();
    loadActiveSession();
  }
}

// Global bindings for modal handlers
window.openNewProjectModal = openNewProjectModal;
window.openEditProjectModal = openEditProjectModal;
window.closeProjectModal = closeProjectModal;
window.saveProjectFromModal = saveProjectFromModal;
window.saveProjectForm = saveProjectFromModal;
window.deleteCurrentProject = deleteCurrentProject;

function deleteCurrentProject() {
  const idInput = document.getElementById("project-form-id");
  const projId = idInput ? idInput.value : "";
  if (!projId) return;

  const proj = getProject(projId);
  const projName = proj ? proj.name : "this project";

  if (!confirm(`Are you sure you want to delete "${projName}"? Conversations in this project will be converted to standalone chats.`)) {
    return;
  }

  projects = projects.filter((p) => p.id !== projId);
  expandedProjectIds.delete(projId);
  fetch(`/api/chats/project/${projId}`, { method: "DELETE" }).catch(() => {});

  // Convert project chats to standalone outer chats
  chatSessions.forEach((s) => {
    if (s.projectId === projId) {
      s.projectId = null;
    }
  });

  saveProjectsToStorage();
  saveSessionsToStorage();
  closeProjectModal();
  renderSidebarSessions();
  loadActiveSession();
}

function toggleProjectExpanded(projectId) {
  if (expandedProjectIds.has(projectId)) {
    expandedProjectIds.delete(projectId);
  } else {
    expandedProjectIds.add(projectId);
  }
  try {
    localStorage.setItem("modeldock_expanded_projects", JSON.stringify(Array.from(expandedProjectIds)));
  } catch (e) {}
  renderSidebarSessions();
}

// --- Multi-Session State Management ---
let syncServerTimer = null;
function syncChatsToServer(immediate = false) {
  if (syncServerTimer) clearTimeout(syncServerTimer);
  const doSync = () => {
    fetch("/api/chats/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessions: chatSessions, projects: projects }),
    }).catch((e) => console.warn("Failed to sync chats to server:", e));
  };
  if (immediate) {
    doSync();
  } else {
    syncServerTimer = setTimeout(doSync, 250);
  }
}

async function initChatSessions() {
  initProjects();

  // 1. Restore expanded projects state from localStorage
  try {
    const savedExpanded = JSON.parse((localStorage.getItem("modeldock_expanded_projects") || localStorage.getItem("omnimodel_expanded_projects")) || "[]");
    if (Array.isArray(savedExpanded)) {
      savedExpanded.forEach((id) => expandedProjectIds.add(id));
    }
  } catch (e) {}

  // 2. Synchronous restoration from localStorage for immediate flicker-free display
  try {
    const rawSessions = (localStorage.getItem("modeldock_chat_sessions_v2") || localStorage.getItem("omnimodel_chat_sessions_v2"));
    if (rawSessions) {
      chatSessions = JSON.parse(rawSessions);
    }
  } catch (e) {
    chatSessions = [];
  }

  // Migration from legacy single chat history if sessions is empty
  if (!Array.isArray(chatSessions) || chatSessions.length === 0) {
    chatSessions = [];
    try {
      const legacyRaw = (localStorage.getItem("modeldock_chat_v1") || localStorage.getItem("omnimodel_chat_v1"));
      if (legacyRaw) {
        const legacyMsgs = JSON.parse(legacyRaw);
        if (Array.isArray(legacyMsgs) && legacyMsgs.length > 0) {
          const firstUserMsg = legacyMsgs.find((m) => m.role === "user");
          const title = firstUserMsg ? firstUserMsg.content.slice(0, 28) : "Recent Chat";
          chatSessions.push({
            id: "session_" + Date.now(),
            title: title,
            projectId: null,
            timestamp: Date.now(),
            messages: legacyMsgs,
            pinned: false,
          });
        }
      }
    } catch (e) {}
  }

  // Active session selection
  try {
    const savedActiveId = (localStorage.getItem("modeldock_active_session_id") || localStorage.getItem("omnimodel_active_session_id"));
    const exists = chatSessions.some((s) => s.id === savedActiveId);
    if (exists) {
      activeSessionId = savedActiveId;
    } else {
      // Prioritize last session with actual messages
      const withMsgs = chatSessions.find((s) => s.messages && s.messages.length > 0);
      activeSessionId = withMsgs ? withMsgs.id : (chatSessions[0] ? chatSessions[0].id : null);
    }
  } catch (e) {
    activeSessionId = chatSessions[0] ? chatSessions[0].id : null;
  }

  // If active session belongs to a project, auto-expand that project in sidebar
  const current = getActiveSession();
  if (current && current.projectId) {
    expandedProjectIds.add(current.projectId);
  }

  // Fallback: If still completely empty, start fresh session
  if (chatSessions.length === 0) {
    const freshSession = {
      id: "session_" + Date.now(),
      title: "New chat",
      projectId: null,
      timestamp: Date.now(),
      messages: [],
      pinned: false,
    };
    chatSessions.push(freshSession);
    activeSessionId = freshSession.id;
  }

  renderSidebarSessions();
  loadActiveSession();

  // Restore active model selection dropdown
  const savedModel = (localStorage.getItem("modeldock_active_model") || localStorage.getItem("omnimodel_active_model"));
  const chatSelect = document.getElementById("chat-model-select");
  if (savedModel && chatSelect) {
    chatSelect.value = savedModel;
  }

  // 3. Asynchronously fetch permanent chats from server storage (Disk JSON / Server API)
  try {
    const res = await fetch("/api/chats");
    if (res.ok) {
      const serverData = await res.json();
      let shouldReRender = false;

      // Sync projects from server if present
      if (serverData.projects && Array.isArray(serverData.projects) && serverData.projects.length > 0) {
        projects = serverData.projects;
        try { localStorage.setItem("modeldock_projects_v1", JSON.stringify(projects)); } catch (e) {}
        shouldReRender = true;
      }

      // Sync sessions from server
      if (serverData.sessions && Array.isArray(serverData.sessions) && serverData.sessions.length > 0) {
        // Do not overwrite if currently in-flight generation is active locally
        const hasPendingLocal = chatSessions.some((s) => s.messages && s.messages.some((m) => m.status === "generating"));
        if (!hasPendingLocal) {
          chatSessions = serverData.sessions;
          const currentActive = chatSessions.find((s) => s.id === activeSessionId);
          if (!currentActive) {
            const withMsgs = chatSessions.find((s) => s.messages && s.messages.length > 0);
            activeSessionId = withMsgs ? withMsgs.id : chatSessions[0].id;
          }
          const activeNow = getActiveSession();
          if (activeNow && activeNow.projectId) {
            expandedProjectIds.add(activeNow.projectId);
          }
          shouldReRender = true;
          saveSessionsToStorage();
        }
      } else if (chatSessions.length > 0 && chatSessions.some((s) => s.messages && s.messages.length > 0)) {
        // Server was empty but local has chats -> immediately push to server disk!
        syncChatsToServer(true);
      }

      if (shouldReRender) {
        renderSidebarSessions();
        loadActiveSession();
      }
    }
  } catch (err) {
    // Offline mode: localStorage remains primary
  }
}

function getActiveSession() {
  if (!activeSessionId && chatSessions.length > 0) {
    activeSessionId = chatSessions[0].id;
  }
  return chatSessions.find((s) => s.id === activeSessionId) || chatSessions[0];
}

function createNewSession(projectId = null) {
  const current = getActiveSession();
  const currentProjectId = current ? (current.projectId || null) : null;
  const targetProjectId = projectId || null;

  // If current session is already in the requested project (or both null) and empty, stay on it
  if (current && currentProjectId === targetProjectId && (!current.messages || current.messages.length === 0)) {
    activeSessionId = current.id;
    if (targetProjectId) expandedProjectIds.add(targetProjectId);
    loadActiveSession();
    renderSidebarSessions();
    focusUserInput();
    return;
  }

  // Clean up any other unused empty "New chat" sessions
  chatSessions = chatSessions.filter((s) => s.id === activeSessionId || (s.messages && s.messages.length > 0));

  // Determine model for new chat session
  const chatSelect = document.getElementById("chat-model-select");
  let chosenModel = "";
  if (targetProjectId) {
    const proj = getProject(targetProjectId);
    if (proj && proj.model) {
      chosenModel = proj.model;
      if (chatSelect) chatSelect.value = proj.model;
      try { localStorage.setItem("modeldock_active_model", proj.model); } catch (e) {}
    }
  }
  if (!chosenModel) {
    chosenModel = (chatSelect && chatSelect.value) || localStorage.getItem("modeldock_active_model") || "";
  }

  const newSession = {
    id: "session_" + Date.now(),
    title: "New chat",
    projectId: targetProjectId,
    model: chosenModel,
    timestamp: Date.now(),
    messages: [],
    pinned: false,
  };

  chatSessions.unshift(newSession);
  activeSessionId = newSession.id;
  try {
    localStorage.setItem("modeldock_active_session_id", activeSessionId);
  } catch (e) {}

  // Auto-expand the project in sidebar
  if (targetProjectId) {
    expandedProjectIds.add(targetProjectId);
    try {
      localStorage.setItem("modeldock_expanded_projects", JSON.stringify(Array.from(expandedProjectIds)));
    } catch (e) {}
  }

  saveSessionsToStorage();
  renderSidebarSessions();
  loadActiveSession();
  focusUserInput();
}

function selectSession(sessionId) {
  if (activeSessionId === sessionId) return;
  activeSessionId = sessionId;
  try {
    localStorage.setItem("modeldock_active_session_id", sessionId);
  } catch (e) {}
  
  const current = getActiveSession();
  if (current && current.projectId) {
    expandedProjectIds.add(current.projectId);
    try {
      localStorage.setItem("modeldock_expanded_projects", JSON.stringify(Array.from(expandedProjectIds)));
    } catch (e) {}
  }
  
  saveSessionsToStorage();
  renderSidebarSessions();
  loadActiveSession();
  focusUserInput();
}

function deleteSession(sessionId, e) {
  if (e) e.stopPropagation();
  fetch(`/api/chats/session/${sessionId}`, { method: "DELETE" }).catch(() => {});

  if (chatSessions.length <= 1) {
    // If only 1 session, just clear it
    const s = chatSessions[0];
    s.title = "New chat";
    s.messages = [];
    s.timestamp = Date.now();
    saveSessionsToStorage();
    renderSidebarSessions();
    loadActiveSession();
    return;
  }

  chatSessions = chatSessions.filter((s) => s.id !== sessionId);
  if (activeSessionId === sessionId) {
    activeSessionId = chatSessions[0].id;
  }
  saveSessionsToStorage();
  renderSidebarSessions();
  loadActiveSession();
}

function togglePinSession(sessionId, e) {
  if (e) e.stopPropagation();
  const s = chatSessions.find((item) => item.id === sessionId);
  if (s) {
    s.pinned = !s.pinned;
    saveSessionsToStorage();
    renderSidebarSessions();
    syncChatsToServer();
  }
}

function renameSession(sessionId, newTitle) {
  const clean = (newTitle || "").trim();
  if (!clean) return;
  const s = chatSessions.find((item) => item.id === sessionId);
  if (s) {
    s.title = clean;
    saveSessionsToStorage();
    renderSidebarSessions();
    syncChatsToServer();
  }
}

function moveSessionToProject(sessionId, projectId) {
  const s = chatSessions.find((item) => item.id === sessionId);
  if (s) {
    s.projectId = projectId || null;
    if (projectId) {
      expandedProjectIds.add(projectId);
      try {
        localStorage.setItem("modeldock_expanded_projects", JSON.stringify(Array.from(expandedProjectIds)));
      } catch (e) {}
    }
    saveSessionsToStorage();
    renderSidebarSessions();
    if (activeSessionId === sessionId) {
      loadActiveSession();
    }
    syncChatsToServer();
  }
}

let activeSessionMenu = null;

function closeSessionMenu() {
  if (activeSessionMenu) {
    activeSessionMenu.remove();
    activeSessionMenu = null;
  }
}

function startInlineRename(sessionId) {
  closeSessionMenu();
  const session = chatSessions.find((s) => s.id === sessionId);
  if (!session) return;

  const item = document.querySelector(`.session-item[data-session-id="${sessionId}"]`);
  if (!item) {
    const newTitle = prompt("Rename chat:", session.title);
    if (newTitle && newTitle.trim()) {
      renameSession(sessionId, newTitle.trim());
    }
    return;
  }

  const titleSpan = item.querySelector(".session-title");
  if (!titleSpan) return;

  const currentTitle = session.title || "Chat";
  titleSpan.innerHTML = "";

  const input = document.createElement("input");
  input.type = "text";
  input.className = "session-rename-input";
  input.value = currentTitle;
  input.autocomplete = "off";

  let finished = false;
  const finishRename = () => {
    if (finished) return;
    finished = true;
    const val = input.value.trim();
    if (val && val !== currentTitle) {
      renameSession(sessionId, val);
    } else {
      renderSidebarSessions();
    }
  };

  input.onkeydown = (e) => {
    e.stopPropagation();
    if (e.key === "Enter") {
      input.blur();
    } else if (e.key === "Escape") {
      input.value = currentTitle;
      input.blur();
    }
  };

  input.onclick = (e) => e.stopPropagation();
  input.onblur = finishRename;

  titleSpan.appendChild(input);
  input.focus();
  input.select();
}

function openSessionMenu(sessionId, anchorBtn, e) {
  if (e) {
    e.preventDefault();
    e.stopPropagation();
  }

  if (activeSessionMenu && activeSessionMenu.dataset.sessionId === sessionId) {
    closeSessionMenu();
    return;
  }

  closeSessionMenu();

  const session = chatSessions.find((s) => s.id === sessionId);
  if (!session) return;

  const rect = anchorBtn.getBoundingClientRect();
  const menu = document.createElement("div");
  menu.id = "session-context-menu";
  menu.className = "session-context-menu";
  menu.dataset.sessionId = sessionId;
  menu.onclick = (ev) => ev.stopPropagation();

  // Build Move to Project items
  let projectsSubmenuHtml = "";
  if (projects.length === 0) {
    projectsSubmenuHtml = `
      <div class="chat-submenu-empty">No projects yet</div>
      <button class="chat-menu-item chat-menu-subitem" onclick="openNewProjectModal(); closeSessionMenu();" type="button">
        <span>+ Create Project</span>
      </button>
    `;
  } else {
    projectsSubmenuHtml = projects.map((p) => {
      const isCurrent = session.projectId === p.id;
      return `
        <button class="chat-menu-item chat-menu-subitem ${isCurrent ? 'active-proj-item' : ''}" onclick="moveSessionToProject('${session.id}', '${p.id}'); closeSessionMenu();" type="button">
          <span style="font-size: 0.9rem;">${p.icon || '📁'}</span>
          <span class="chat-menu-text">${escapeHtml(p.name)}</span>
          ${isCurrent ? '<span class="proj-check">✓</span>' : ''}
        </button>
      `;
    }).join("");

    if (session.projectId) {
      projectsSubmenuHtml += `
        <div class="chat-menu-divider"></div>
        <button class="chat-menu-item chat-menu-subitem" onclick="moveSessionToProject('${session.id}', null); closeSessionMenu();" type="button">
          <span style="font-size: 0.85rem;">📤</span>
          <span class="chat-menu-text">Remove from project</span>
        </button>
      `;
    }
  }

  menu.innerHTML = `
    <button class="chat-menu-item" onclick="startInlineRename('${session.id}')" type="button">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
      <span>Rename</span>
    </button>
    <button class="chat-menu-item" onclick="togglePinSession('${session.id}', event); closeSessionMenu();" type="button">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="${session.pinned ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2"><line x1="12" y1="17" x2="12" y2="22"></line><path d="M5 17h14v-1.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V6h1a1 1 0 0 0 0-2H8a1 1 0 0 0 0 2h1v4.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24Z"></path></svg>
      <span>${session.pinned ? 'Unpin chat' : 'Pin'}</span>
    </button>
    <div class="chat-menu-item chat-menu-has-sub" id="menu-item-move-proj">
      <div class="chat-menu-item-inner">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
        <span>Move to project</span>
      </div>
      <svg class="chevron-sub" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"></polyline></svg>
      <div class="chat-menu-sub" id="chat-projects-submenu">
        ${projectsSubmenuHtml}
      </div>
    </div>
    <div class="chat-menu-divider"></div>
    <button class="chat-menu-item chat-menu-danger" onclick="deleteSession('${session.id}', event); closeSessionMenu();" type="button">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
      <span>Delete</span>
    </button>
  `;

  document.body.appendChild(menu);
  activeSessionMenu = menu;

  const menuWidth = 190;
  let left = rect.right + 6;
  if (left + menuWidth > window.innerWidth) {
    left = rect.left - menuWidth - 4;
  }
  let top = rect.top - 4;
  if (top + 220 > window.innerHeight) {
    top = window.innerHeight - 230;
  }
  menu.style.left = `${Math.max(8, left)}px`;
  menu.style.top = `${Math.max(8, top)}px`;
}

// Global click and escape listeners to close context menu
document.addEventListener("click", (e) => {
  if (activeSessionMenu && !activeSessionMenu.contains(e.target)) {
    closeSessionMenu();
  }
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && activeSessionMenu) {
    closeSessionMenu();
  }
});

function saveSessionsToStorage(immediate = false) {
  try {
    // Sanitize sessions to strip out multi-megabyte base64 images from localStorage
    const sanitized = chatSessions.map((s) => ({
      ...s,
      messages: (s.messages || []).map((m) => {
        if (!m.attachments || m.attachments.length === 0) return m;
        return {
          ...m,
          attachments: m.attachments.map((att) => ({
            filename: att.filename,
            file_type: att.file_type || att.doc_type,
            size_formatted: att.size_formatted,
            preview_url: att.preview_url && att.preview_url.length < 50000 ? att.preview_url : "",
            extracted_text: att.extracted_text ? att.extracted_text.slice(0, 4000) : "",
            description: att.description || "",
          })),
        };
      }),
    }));

    localStorage.setItem("modeldock_chat_sessions_v2", JSON.stringify(sanitized));
    localStorage.setItem("modeldock_active_session_id", activeSessionId);
    
    // Legacy sync for backward compatibility
    const current = getActiveSession();
    if (current) {
      localStorage.setItem("modeldock_chat_v1", JSON.stringify(current.messages || []));
    }
  } catch (e) {
    console.warn("Storage quota warning (synced to server):", e);
  }

  // Always sync to persistent disk on backend
  syncChatsToServer(immediate);
}

function loadActiveSession() {
  const current = getActiveSession();
  if (!current) return;

  chatHistory = current.messages || [];
  chatAttachments = [];
  renderAttachmentTray();

  // 1. Restore and synchronize the active model specifically for this session
  const chatSelect = document.getElementById("chat-model-select");
  if (chatSelect && window.AppState && AppState.localModels && AppState.localModels.length > 0) {
    let targetModel = current.model;
    if (!targetModel && current.projectId && typeof getProject === "function") {
      const proj = getProject(current.projectId);
      if (proj && proj.model) targetModel = proj.model;
    }
    if (!targetModel) {
      targetModel = localStorage.getItem("modeldock_active_model");
    }

    if (targetModel && AppState.localModels.some((m) => m.name === targetModel)) {
      chatSelect.value = targetModel;
      current.model = targetModel;
    } else if (!current.model && chatSelect.value) {
      current.model = chatSelect.value;
    }
    try {
      localStorage.setItem("modeldock_active_model", chatSelect.value);
    } catch (e) {}
  }

  // 2. Restore Parameters for this session or fallback to global stored preferences
  const tempSlider = document.getElementById("param-temp");
  const tempVal = document.getElementById("temp-val");
  const ctxSelect = document.getElementById("param-ctx");
  const ctxVal = document.getElementById("ctx-val");
  const paramSysPrompt = document.getElementById("param-system-prompt");

  const sessionTemp = current.temperature !== undefined ? current.temperature : localStorage.getItem("modeldock_param_temp");
  if (tempSlider && sessionTemp !== null && sessionTemp !== undefined) {
    tempSlider.value = sessionTemp;
    if (tempVal) tempVal.textContent = sessionTemp;
  }

  const sessionCtx = current.contextWindow || localStorage.getItem("modeldock_param_ctx");
  if (ctxSelect && sessionCtx) {
    ctxSelect.value = sessionCtx;
    if (ctxVal) ctxVal.textContent = sessionCtx;
  }

  const sessionSysPrompt = current.systemPrompt !== undefined ? current.systemPrompt : localStorage.getItem("modeldock_param_sys_prompt");
  if (paramSysPrompt && sessionSysPrompt !== null && sessionSysPrompt !== undefined) {
    paramSysPrompt.value = sessionSysPrompt;
  }

  // Handle Project Banner in Chat Canvas
  const projectBanner = document.getElementById("project-context-banner");
  const bannerName = document.getElementById("project-banner-name");
  const bannerModel = document.getElementById("project-banner-model");
  const bannerTag = document.getElementById("project-banner-prompt-tag");

  if (current.projectId) {
    const proj = getProject(current.projectId);
    if (proj && projectBanner) {
      projectBanner.classList.remove("hidden");
      if (bannerName) bannerName.textContent = proj.name;
      if (bannerModel) {
        const chatSelect = document.getElementById("chat-model-select");
        const activeModelName = (chatSelect && chatSelect.value) ? chatSelect.value : (proj.model || "Local Model");
        bannerModel.textContent = `🤖 ${activeModelName}`;
      }
      if (bannerTag) {
        if (proj.systemPrompt && proj.systemPrompt.trim()) {
          bannerTag.classList.remove("hidden");
          bannerTag.title = proj.systemPrompt.trim();
        } else {
          bannerTag.classList.add("hidden");
        }
      }
    } else if (projectBanner) {
      projectBanner.classList.add("hidden");
    }
  } else {
    // Outer New Chat -> Hide Project Banner
    if (projectBanner) projectBanner.classList.add("hidden");
  }

  const container = document.getElementById("chat-messages");
  if (!container) return;

  // Detect if generation was in progress or interrupted by refresh
  let pendingGenerationPrompt = null;
  let pendingGenerationModel = null;
  let pendingAssistIndex = -1;

  if (chatHistory.length > 0) {
    const lastMsg = chatHistory[chatHistory.length - 1];
    if (lastMsg.role === "user") {
      // User sent prompt and refreshed before assistant responded:
      pendingGenerationPrompt = lastMsg.augmented_prompt || lastMsg.content;
      pendingGenerationModel = current.model || (typeof getActiveChatModel === "function" ? getActiveChatModel() : "Local AI");
      const assistMsg = {
        role: "assistant",
        content: "",
        status: "generating",
        model: pendingGenerationModel,
        timestamp: new Date().toLocaleTimeString(),
        startedAt: Date.now(),
      };
      chatHistory.push(assistMsg);
      pendingAssistIndex = chatHistory.length - 1;
      current.messages = chatHistory;
      saveSessionsToStorage(true);
    } else if (lastMsg.role === "assistant" && lastMsg.status === "generating") {
      // Refresh happened while assistant was actively generating!
      for (let j = chatHistory.length - 2; j >= 0; j--) {
        if (chatHistory[j].role === "user") {
          pendingGenerationPrompt = chatHistory[j].augmented_prompt || chatHistory[j].content;
          break;
        }
      }
      pendingGenerationModel = lastMsg.model || current.model || (typeof getActiveChatModel === "function" ? getActiveChatModel() : "Local AI");
      pendingAssistIndex = chatHistory.length - 1;
    }
  }

  if (chatHistory.length === 0) {
    renderWelcomeScreen();
  } else {
    container.innerHTML = "";
    for (let i = 0; i < chatHistory.length; i++) {
      const msg = chatHistory[i];
      appendMessageUI(
        msg.role,
        msg.content,
        msg.attachments || [],
        msg.metrics || null,
        msg.timestamp || null,
        i,
        msg.status || null,
        msg.model || current.model || null
      );
    }
    container.scrollTop = container.scrollHeight;
  }

  // If there was an in-progress generation when refreshed, re-activate progress timer and resume stream!
  if (pendingAssistIndex >= 0 && pendingGenerationPrompt) {
    const btnSend = document.getElementById("btn-send");
    const btnStop = document.getElementById("btn-stop");
    if (btnSend) btnSend.classList.add("hidden");
    if (btnStop) btnStop.classList.remove("hidden");

    const assistMsg = chatHistory[pendingAssistIndex];
    startGenerationProgressTimer(pendingAssistIndex, assistMsg.startedAt || Date.now());

    setTimeout(() => {
      resumePendingChatStream(pendingAssistIndex, pendingGenerationPrompt, pendingGenerationModel);
    }, 300);
  }
}

function renderSidebarSessions(filterQuery = "") {
  const recentsList = document.getElementById("recent-chats-list");
  const pinnedList = document.getElementById("pinned-chats-list");
  const projectsList = document.getElementById("projects-chats-list");
  if (!recentsList) return;

  recentsList.innerHTML = "";
  if (pinnedList) pinnedList.innerHTML = "";

  const filtered = chatSessions.filter((s) => {
    if (!filterQuery) return true;
    const matchTitle = s.title && s.title.toLowerCase().includes(filterQuery);
    const matchMsg = s.messages && s.messages.some((m) => m.content && m.content.toLowerCase().includes(filterQuery));
    const proj = s.projectId ? getProject(s.projectId) : null;
    const matchProj = proj && proj.name && proj.name.toLowerCase().includes(filterQuery);
    return matchTitle || matchMsg || matchProj;
  });

  const pinnedItems = filtered.filter((s) => s.pinned);
  // Outer chats: NOT pinned, and NO projectId!
  const recentItems = filtered.filter((s) => !s.pinned && !s.projectId);

  // Render Pinned
  if (pinnedList) {
    if (pinnedItems.length === 0) {
      pinnedList.innerHTML = '<div style="font-size: 0.76rem; color: #71717a; padding: 0.2rem 0.5rem;">No pinned chats</div>';
    } else {
      pinnedItems.forEach((s) => pinnedList.appendChild(createSessionItemElement(s)));
    }
  }

  // Render Projects List
  if (projectsList) {
    projectsList.innerHTML = "";
    if (projects.length === 0) {
      projectsList.innerHTML = `
        <div class="project-empty-hint" onclick="openNewProjectModal()">
          <span>+ Create your first project</span>
        </div>
      `;
    } else {
      projects.forEach((p) => {
        const pSessions = filtered.filter((s) => s.projectId === p.id);
        const isExpanded = expandedProjectIds.has(p.id) || (filterQuery.length > 0 && pSessions.length > 0);
        const isActiveProject = activeSessionId && chatSessions.some((s) => s.id === activeSessionId && s.projectId === p.id);

        const treeItem = document.createElement("div");
        treeItem.className = `project-tree-item ${isActiveProject ? "active-project" : ""}`;

        const headerDiv = document.createElement("div");
        headerDiv.className = "project-tree-header";
        headerDiv.onclick = () => toggleProjectExpanded(p.id);

        headerDiv.innerHTML = `
          <span class="project-folder-icon">${p.icon || '📁'}</span>
          <span class="project-tree-name" title="${p.name}">${p.name}</span>
          <span class="project-count-pill">${pSessions.length}</span>
          <div class="project-actions-row">
            <button class="project-mini-btn" title="New Chat in ${p.name}" onclick="event.stopPropagation(); createNewSession('${p.id}')">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            </button>
            <button class="project-mini-btn" title="Project Settings" onclick="event.stopPropagation(); openEditProjectModal('${p.id}')">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
            </button>
          </div>
        `;

        treeItem.appendChild(headerDiv);

        if (isExpanded) {
          const nestedDiv = document.createElement("div");
          nestedDiv.className = "project-sessions-nested";
          if (pSessions.length === 0) {
            nestedDiv.innerHTML = `
              <div class="project-empty-hint" onclick="createNewSession('${p.id}')">
                <span>+ Chat with models in this project</span>
              </div>
            `;
          } else {
            pSessions.forEach((s) => nestedDiv.appendChild(createSessionItemElement(s, true)));
          }
          treeItem.appendChild(nestedDiv);
        }

        projectsList.appendChild(treeItem);
      });
    }
  }

  // Render Recents (Outer Chats)
  if (recentItems.length === 0) {
    recentsList.innerHTML = '<div style="font-size: 0.76rem; color: #71717a; padding: 0.4rem 0.5rem;">No outer conversations found</div>';
  } else {
    recentItems.forEach((s) => recentsList.appendChild(createSessionItemElement(s, false)));
  }
}

function createSessionItemElement(session, isNested = false) {
  const item = document.createElement("div");
  item.className = "session-item" + (session.id === activeSessionId ? " active" : "") + (isNested ? " nested-session" : "") + (session.pinned ? " is-pinned" : "");
  item.dataset.sessionId = session.id;
  item.onclick = () => selectSession(session.id);
  item.title = session.title || "Chat Session";

  const titleSpan = document.createElement("span");
  titleSpan.className = "session-title";
  titleSpan.textContent = session.title || "Chat Session";

  const actions = document.createElement("div");
  actions.className = "session-actions";

  // 1. Pin icon button
  const pinBtn = document.createElement("button");
  pinBtn.className = "session-action-btn session-pin-btn" + (session.pinned ? " pinned-active" : "");
  pinBtn.title = session.pinned ? "Unpin chat" : "Pin chat";
  pinBtn.setAttribute("type", "button");
  pinBtn.innerHTML = `
    <svg width="13" height="13" viewBox="0 0 24 24" fill="${session.pinned ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <line x1="12" y1="17" x2="12" y2="22"></line>
      <path d="M5 17h14v-1.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V6h1a1 1 0 0 0 0-2H8a1 1 0 0 0 0 2h1v4.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24Z"></path>
    </svg>
  `;
  pinBtn.onclick = (e) => togglePinSession(session.id, e);

  // 2. 3-dots icon button (...)
  const dotsBtn = document.createElement("button");
  dotsBtn.className = "session-action-btn session-dots-btn";
  dotsBtn.title = "Chat options";
  dotsBtn.setAttribute("type", "button");
  dotsBtn.innerHTML = `
    <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
      <circle cx="12" cy="12" r="2.2"></circle>
      <circle cx="19" cy="12" r="2.2"></circle>
      <circle cx="5" cy="12" r="2.2"></circle>
    </svg>
  `;
  dotsBtn.onclick = (e) => openSessionMenu(session.id, dotsBtn, e);

  actions.appendChild(pinBtn);
  actions.appendChild(dotsBtn);

  item.appendChild(titleSpan);
  item.appendChild(actions);
  return item;
}

function focusUserInput() {
  const input = document.getElementById("user-input");
  if (input) {
    input.focus();
  }
}

function updateUserProfileInSidebar() {
  const nameEl = document.getElementById("sidebar-user-name");
  const avatarEl = document.getElementById("sidebar-user-avatar");
  const planEl = document.getElementById("sidebar-user-plan");

  const navNameEl = document.getElementById("nav-user-fullname");
  const navAvatarEl = document.getElementById("nav-user-avatar");
  const navTierEl = document.getElementById("nav-user-tier");

  const customName = (localStorage.getItem("modeldock_user_name") || localStorage.getItem("omnimodel_user_name"));
  const customTitle = (localStorage.getItem("modeldock_user_title") || localStorage.getItem("omnimodel_user_title"));

  const displayName = customName || (AppState && AppState.hfUser ? (AppState.hfUser.fullname || AppState.hfUser.username) : "Local AI User");
  const displayTitle = customTitle || (AppState && AppState.hfUser ? `@${AppState.hfUser.username} • HF Connected` : "Local AI • Pro");

  if (nameEl) nameEl.textContent = displayName;
  if (planEl) planEl.textContent = displayTitle;
  if (navNameEl) navNameEl.textContent = displayName;
  if (navTierEl) navTierEl.textContent = displayTitle;

  const parts = displayName.trim().split(/\s+/);
  const initials = parts.length === 1 ? parts[0].slice(0, 2).toUpperCase() : (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();

  if (avatarEl) {
    if (AppState && AppState.hfUser && AppState.hfUser.avatar_url && !customName) {
      avatarEl.innerHTML = `<img src="${AppState.hfUser.avatar_url}" alt="Avatar" />`;
    } else {
      avatarEl.textContent = initials || "U";
    }
  }

  if (navAvatarEl) {
    if (AppState && AppState.hfUser && AppState.hfUser.avatar_url && !customName) {
      navAvatarEl.innerHTML = `<img src="${AppState.hfUser.avatar_url}" alt="Avatar" style="width:100%;height:100%;border-radius:50%;object-fit:cover;" />`;
    } else {
      navAvatarEl.textContent = initials || "U";
    }
  }
}

// --- Multimodal Clipboard Paste & File Upload Handling ---
function handlePasteEvent(e) {
  const activeTab = AppState ? AppState.currentTab : "chat";
  if (activeTab !== "chat") return;

  const clipboardData = e.clipboardData;
  if (!clipboardData) return;

  const items = clipboardData.items;
  if (!items) return;

  const filesToUpload = [];

  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    if (item.type.indexOf("image") !== -1) {
      // Pasted screenshot or copied image
      const blob = item.getAsFile();
      if (blob) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
        const file = new File([blob], `screenshot_${timestamp}.png`, { type: blob.type });
        filesToUpload.push(file);
      }
    } else if (item.kind === "file") {
      const blob = item.getAsFile();
      if (blob) filesToUpload.push(blob);
    }
  }

  if (filesToUpload.length > 0) {
    uploadFiles(filesToUpload);
  }
}

async function uploadFiles(fileList) {
  const formData = new FormData();
  let count = 0;

  for (let i = 0; i < fileList.length; i++) {
    const file = fileList[i];
    formData.append("files", file);
    count++;
  }

  if (count === 0) return;

  const streamStats = document.getElementById("chat-stream-stats");
  if (streamStats) streamStats.textContent = `Uploading ${count} file(s)...`;

  try {
    const res = await fetch("/api/media/upload", {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    if (res.ok && data.success && data.processed) {
      for (const item of data.processed) {
        chatAttachments.push(item);
      }
      renderAttachmentTray();
      if (streamStats) streamStats.textContent = `Attached ${data.processed.length} item(s)`;
      setTimeout(() => {
        if (streamStats) streamStats.textContent = "";
      }, 3000);
    } else {
      alert(`Upload failed: ${data.detail || data.error || "Unknown server response"}`);
    }
  } catch (err) {
    console.error("Upload failed:", err);
    alert(`File upload failed: ${err.message}`);
  } finally {
    const fileInput = document.getElementById("chat-file-input");
    if (fileInput) fileInput.value = "";
  }
}

function renderAttachmentTray() {
  const tray = document.getElementById("chat-attachment-tray");
  if (!tray) return;

  if (chatAttachments.length === 0) {
    tray.classList.add("hidden");
    tray.innerHTML = "";
    return;
  }

  tray.classList.remove("hidden");
  tray.innerHTML = chatAttachments
    .map((att, idx) => {
      const hasThumb = Boolean(att.preview_url);
      const visual = hasThumb
        ? `<img src="${att.preview_url}" class="chip-thumb" alt="${att.filename}" />`
        : `<span class="chip-icon">${getAttachmentIcon(att)}</span>`;

      return `
        <div class="attachment-chip" title="${att.filename}">
          ${visual}
          <div class="chip-info">
            <span class="chip-name">${att.filename}</span>
            <span class="chip-sub">${att.size_formatted || att.file_type}</span>
          </div>
          <button class="chip-remove" onclick="removeAttachment(${idx})" title="Remove attachment">&times;</button>
        </div>
      `;
    })
    .join("");
}

function removeAttachment(index) {
  chatAttachments.splice(index, 1);
  renderAttachmentTray();
}

function getAttachmentIcon(att) {
  const type = att.file_type || "";
  if (type === "image") return "🖼️";
  if (type === "video") return "🎥";
  if (type === "pdf") return "📄";
  if (type === "excel") return "📊";
  if (type === "csv") return "📈";
  if (type === "document") return "📝";
  return "📎";
}

function formatFileSize(bytes) {
  if (!bytes) return "0 B";
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

// Quick Prompt Sender
function sendQuickPrompt(promptText) {
  const userInput = document.getElementById("user-input");
  if (!userInput) return;
  userInput.value = promptText;
  sendMessage();
}

let activeGenerationTimer = null;
let activeGenerationStartTime = null;

function startGenerationProgressTimer(cardIndex, startTime = Date.now()) {
  if (activeGenerationTimer) clearInterval(activeGenerationTimer);
  activeGenerationStartTime = startTime;

  activeGenerationTimer = setInterval(() => {
    const elapsedSec = ((Date.now() - activeGenerationStartTime) / 1000).toFixed(1);
    const timerEl = document.querySelector(`#chat-progress-timer-${cardIndex} .timer-value`) || document.querySelector(`.chat-progress-timer .timer-value`);
    const statusEl = document.getElementById(`chat-progress-status-${cardIndex}`) || document.querySelector(`.chat-progress-status-text`);

    if (timerEl) {
      timerEl.textContent = `${elapsedSec}s`;
    }
    if (statusEl) {
      const sec = parseFloat(elapsedSec);
      if (sec < 2.5) {
        statusEl.innerHTML = `⚡ Loading model context & initializing GPU weights...`;
      } else if (sec < 6.0) {
        statusEl.innerHTML = `🧠 Neural inference active • Synthesizing response tokens...`;
      } else if (sec < 14.0) {
        statusEl.innerHTML = `🎬 Model generation in progress (${elapsedSec}s) • Deep reasoning & synthesis...`;
      } else {
        statusEl.innerHTML = `⏳ Synthesizing comprehensive output (${elapsedSec}s) • Computing tokens...`;
      }
    }
  }, 100);
}

function stopGenerationProgressTimer() {
  if (activeGenerationTimer) {
    clearInterval(activeGenerationTimer);
    activeGenerationTimer = null;
  }
}

function getActiveChatModel() {
  const modelSelect = document.getElementById("chat-model-select");
  if (modelSelect && modelSelect.value) return modelSelect.value;
  const currentSession = getActiveSession();
  if (currentSession && currentSession.model) return currentSession.model;
  return localStorage.getItem("modeldock_active_model") || (window.AppState && AppState.localModels && AppState.localModels[0] ? AppState.localModels[0].name : "qwen2-0_5b-instruct-q4_k_m");
}

async function sendMessage() {
  const userInput = document.getElementById("user-input");
  const messagesContainer = document.getElementById("chat-messages");
  const btnSend = document.getElementById("btn-send");
  const btnStop = document.getElementById("btn-stop");
  const modelSelect = document.getElementById("chat-model-select");

  const prompt = userInput ? userInput.value.trim() : "";
  const currentAttachments = [...chatAttachments];

  if (!prompt && currentAttachments.length === 0) return;

  let currentModel = modelSelect ? modelSelect.value : "";
  if (!currentModel && window.AppState && AppState.localModels && AppState.localModels.length > 0) {
    currentModel = AppState.localModels[0].name;
    if (modelSelect) modelSelect.value = currentModel;
  }
  if (!currentModel) {
    appendMessageUI("assistant", "⚠️ Please select a model from your installed library first.");
    return;
  }

  // Ensure current session persistently remembers this model
  const currentSession = getActiveSession();
  if (currentSession) {
    currentSession.model = currentModel;
    saveSessionsToStorage();
  }

  // Clear welcome screen on first message
  if (messagesContainer) {
    const welcomeEl = messagesContainer.querySelector(".chat-welcome");
    if (welcomeEl) {
      messagesContainer.innerHTML = "";
    }
  }

  // Auto-Title Session if it is currently "New chat"
  if (currentSession && (currentSession.title === "New chat" || !currentSession.title)) {
    const rawTitle = prompt || (currentAttachments[0] ? currentAttachments[0].filename : "Chat");
    currentSession.title = rawTitle.slice(0, 32).trim();
    renderSidebarSessions();
  }

  // Build Context for LLM with attached document/media metadata
  let augmentedPrompt = prompt;
  if (currentAttachments.length > 0) {
    let mediaPromptPrefix = `\n\n[USER ATTACHED FILES]:\n`;
    for (const att of currentAttachments) {
      mediaPromptPrefix += `\n--- File: ${att.filename} (${att.file_type}) ---\n`;
      if (att.extracted_text) {
        mediaPromptPrefix += `[Extracted Content Preview]:\n${att.extracted_text}\n`;
      }
      if (att.description) {
        mediaPromptPrefix += `[Media Description]: ${att.description}\n`;
      }
    }
    augmentedPrompt = prompt + mediaPromptPrefix;
  }

  // Append User Message to UI & in-memory chatHistory
  const userTime = new Date().toLocaleTimeString();
  const userMsgIndex = chatHistory.length;
  appendMessageUI("user", prompt, currentAttachments, null, userTime, userMsgIndex);

  const userMsgObj = {
    role: "user",
    content: prompt,
    augmented_prompt: augmentedPrompt,
    attachments: currentAttachments,
    timestamp: userTime,
  };
  chatHistory.push(userMsgObj);

  // IMMEDIATELY create & persist the Assistant response entry in chatHistory!
  const assistTime = new Date().toLocaleTimeString();
  const assistIndex = chatHistory.length;
  const assistMsgObj = {
    role: "assistant",
    content: "",
    status: "generating",
    model: currentModel,
    timestamp: assistTime,
    startedAt: Date.now(),
  };
  chatHistory.push(assistMsgObj);

  if (currentSession) {
    currentSession.messages = chatHistory;
    currentSession.timestamp = Date.now();
  }
  saveSessionsToStorage(true);

  // Reset Input and Attachments
  if (userInput) {
    userInput.value = "";
    userInput.style.height = "auto";
  }
  chatAttachments = [];
  renderAttachmentTray();

  // Create Assistant Message Bubble with Progress Card for Streaming
  appendMessageUI("assistant", "", [], null, assistTime, assistIndex, "generating", currentModel);
  startGenerationProgressTimer(assistIndex, assistMsgObj.startedAt);

  // Toggle buttons
  if (btnSend) btnSend.classList.add("hidden");
  if (btnStop) btnStop.classList.remove("hidden");

  // Call the shared streaming runner
  await resumePendingChatStream(assistIndex, augmentedPrompt, currentModel);
}

async function resumePendingChatStream(assistIndex, prompt, model) {
  const currentSession = getActiveSession();
  if (!currentSession) return;
  const assistMsgObj = chatHistory[assistIndex];
  if (!assistMsgObj) return;

  const bodyElement = document.getElementById(`msg-body-${assistIndex}`);
  const bubbleElement = bodyElement ? bodyElement.closest(".message-bubble") : null;
  const btnSend = document.getElementById("btn-send");
  const btnStop = document.getElementById("btn-stop");
  const streamStats = document.getElementById("chat-stream-stats");
  const messagesContainer = document.getElementById("chat-messages");

  // Read Parameters
  const tempSlider = document.getElementById("param-temp");
  const ctxSelect = document.getElementById("param-ctx");
  const systemPromptInput = document.getElementById("param-system-prompt");

  const temperature = tempSlider ? parseFloat(tempSlider.value) : 0.7;
  const numCtx = ctxSelect ? parseInt(ctxSelect.value, 10) : 4096;
  let effectiveSystemPrompt = systemPromptInput ? systemPromptInput.value.trim() : "";

  if (currentSession && currentSession.projectId && typeof getProject === "function") {
    const proj = getProject(currentSession.projectId);
    if (proj && proj.systemPrompt && proj.systemPrompt.trim()) {
      effectiveSystemPrompt = effectiveSystemPrompt
        ? `${proj.systemPrompt.trim()}\n\n${effectiveSystemPrompt}`
        : proj.systemPrompt.trim();
    }
  }

  // Filter messages up to this turn (exclude in-progress empty assistant turn)
  const formattedMessages = chatHistory
    .slice(0, assistIndex)
    .filter((m) => m.role === "user" || (m.role === "assistant" && m.content && m.content.trim()))
    .map((m) => ({
      role: m.role,
      content: m.augmented_prompt || m.content,
    }));

  const activeModel = model || currentSession.model || (typeof getActiveChatModel === "function" ? getActiveChatModel() : "Local AI");

  const payload = {
    model: activeModel,
    messages: formattedMessages,
    temperature: temperature,
    num_ctx: numCtx,
    system_prompt: effectiveSystemPrompt,
  };

  abortController = new AbortController();
  let fullResponse = assistMsgObj.content || "";
  let tokenCount = 0;
  const startTime = assistMsgObj.startedAt || Date.now();
  let lastMetrics = null;
  let isTimedOut = false;
  let lastTokenTime = Date.now();
  let lastSaveTime = Date.now();
  const TIMEOUT_INITIAL_MS = 120000;
  const TIMEOUT_IDLE_MS = 60000;

  startGenerationProgressTimer(assistIndex, startTime);

  const timeoutChecker = setInterval(() => {
    const now = Date.now();
    const totalElapsed = now - startTime;
    const idleElapsed = now - lastTokenTime;

    if (tokenCount === 0 && totalElapsed > TIMEOUT_INITIAL_MS) {
      isTimedOut = true;
      clearInterval(timeoutChecker);
      if (abortController) abortController.abort(new Error("TIMED_OUT"));
    } else if (tokenCount > 0 && idleElapsed > TIMEOUT_IDLE_MS) {
      isTimedOut = true;
      clearInterval(timeoutChecker);
      if (abortController) abortController.abort(new Error("TIMED_OUT"));
    }
  }, 1000);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: abortController.signal,
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Server returned HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.substring(6).trim());

            if (data.error) {
              stopGenerationProgressTimer();
              const progressCard = document.getElementById(`chat-progress-card-${assistIndex}`);
              if (progressCard) progressCard.remove();

              if (bodyElement) {
                bodyElement.innerHTML = `
                  <div class="chat-alert-card chat-error-box">
                    <div class="chat-alert-header">
                      <div class="chat-alert-badge error-badge">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                        <span>Engine Error</span>
                      </div>
                      <span class="chat-alert-time">${new Date().toLocaleTimeString()}</span>
                    </div>
                    <div class="chat-alert-message">${renderMarkdown(data.error)}</div>
                    <div class="chat-alert-actions">
                      <button class="btn-chat-action btn-action-retry" onclick="retryLastUserPrompt()" type="button" title="Resend prompt">
                        <span>Give Prompt Again</span>
                      </button>
                      <button class="btn-chat-action btn-action-edit" onclick="editLastUserPrompt()" type="button" title="Edit prompt">
                        <span>Edit Earlier Prompt</span>
                      </button>
                    </div>
                  </div>
                `;
              }
              assistMsgObj.status = "error";
              saveSessionsToStorage(true);
            }

            if (data.content) {
              lastTokenTime = Date.now();
              fullResponse += data.content;
              tokenCount++;
              assistMsgObj.content = fullResponse;

              const contentArea = document.getElementById(`assist-content-${assistIndex}`);
              if (contentArea) {
                contentArea.innerHTML = renderMarkdown(fullResponse);
              } else if (bodyElement) {
                bodyElement.innerHTML = renderMarkdown(fullResponse);
              }

              const elapsedSec = (Date.now() - startTime) / 1000;
              const liveTps = (tokenCount / Math.max(0.1, elapsedSec)).toFixed(1);
              if (streamStats) streamStats.textContent = `${tokenCount} tokens (${liveTps} t/s)`;

              if (messagesContainer) messagesContainer.scrollTop = messagesContainer.scrollHeight;

              // Throttled persistence (save every 1 sec so refresh never loses text!)
              const now = Date.now();
              if (now - lastSaveTime > 1000) {
                lastSaveTime = now;
                saveSessionsToStorage();
              }
            }

            if (data.done && data.metrics) {
              lastMetrics = data.metrics;
            }
          } catch (e) {}
        }
      }
    }

    clearInterval(timeoutChecker);
    stopGenerationProgressTimer();

    // Clean up progress card
    const progressCard = document.getElementById(`chat-progress-card-${assistIndex}`);
    if (progressCard) progressCard.remove();

    if (bodyElement) {
      bodyElement.innerHTML = renderMarkdown(fullResponse);
    }

    if (lastMetrics && bubbleElement && !bubbleElement.querySelector(".generation-metrics")) {
      const m = lastMetrics;
      const metricsDiv = document.createElement("div");
      metricsDiv.className = "generation-metrics";
      metricsDiv.innerHTML = `
        <span>Speed: <strong class="metric-highlight">${m.tokens_per_sec || "--"} tokens/sec</strong></span>
        <span>Generated: <strong>${m.tokens_generated || "--"} tokens</strong></span>
        <span>Time: <strong>${m.total_time_sec || "--"}s</strong></span>
        <span>Engine: <strong>${(typeof getModelDisplayName === "function" ? getModelDisplayName(m.model || "--") : (m.model || "--"))}</strong></span>
      `;
      bubbleElement.appendChild(metricsDiv);
    }

    assistMsgObj.status = "completed";
    assistMsgObj.content = fullResponse;
    assistMsgObj.metrics = lastMetrics;
    saveSessionsToStorage(true);
    renderSidebarSessions();
  } catch (err) {
    clearInterval(timeoutChecker);
    stopGenerationProgressTimer();
    const wasAbortedByUser = err.name === "AbortError" && !isTimedOut && err.message !== "TIMED_OUT";
    const wasTimeout = isTimedOut || err.message === "TIMED_OUT" || (err.message && err.message.toLowerCase().includes("timeout"));

    const progressCard = document.getElementById(`chat-progress-card-${assistIndex}`);
    if (progressCard) progressCard.remove();

    assistMsgObj.status = wasAbortedByUser ? "stopped" : "error";
    assistMsgObj.content = fullResponse;
    saveSessionsToStorage(true);

    if (bodyElement) {
      if (wasTimeout) {
        bodyElement.innerHTML = `
          <div class="chat-alert-card chat-timeout-box">
            <div class="chat-alert-header">
              <div class="chat-alert-badge timeout-badge">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                <span>Process Stopped (Exceeded Time Limit)</span>
              </div>
              <span class="chat-alert-time">${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="chat-alert-message">
              The model generation was taking longer than expected and was safely stopped. You can give the prompt again or edit your prompt.
            </div>
            <div class="chat-alert-actions">
              <button class="btn-chat-action btn-action-retry" onclick="retryLastUserPrompt()" type="button" title="Resend prompt">
                <span>Give Prompt Again</span>
              </button>
              <button class="btn-chat-action btn-action-edit" onclick="editLastUserPrompt()" type="button" title="Modify your prompt">
                <span>Edit Earlier Prompt</span>
              </button>
            </div>
          </div>
        `;
      } else if (wasAbortedByUser) {
        bodyElement.innerHTML += `
          <div class="chat-alert-card chat-stopped-box">
            <div class="chat-alert-header">
              <div class="chat-alert-badge stopped-badge">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="4" y="4" width="16" height="16" rx="2"></rect></svg>
                <span>Generation Stopped by User</span>
              </div>
              <span class="chat-alert-time">${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="chat-alert-actions">
              <button class="btn-chat-action btn-action-retry" onclick="retryLastUserPrompt()" type="button" title="Resend prompt">
                <span>Give Prompt Again</span>
              </button>
              <button class="btn-chat-action btn-action-edit" onclick="editLastUserPrompt()" type="button" title="Modify your prompt">
                <span>Edit Earlier Prompt</span>
              </button>
            </div>
          </div>
        `;
      } else {
        bodyElement.innerHTML = `
          <div class="chat-alert-card chat-error-box">
            <div class="chat-alert-header">
              <div class="chat-alert-badge error-badge">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                <span>Connection Error</span>
              </div>
              <span class="chat-alert-time">${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="chat-alert-message">${escapeHtml(err.message)}</div>
            <div class="chat-alert-actions">
              <button class="btn-chat-action btn-action-retry" onclick="retryLastUserPrompt()" type="button" title="Resend prompt">
                <span>Give Prompt Again</span>
              </button>
              <button class="btn-chat-action btn-action-edit" onclick="editLastUserPrompt()" type="button" title="Modify your prompt">
                <span>Edit Earlier Prompt</span>
              </button>
            </div>
          </div>
        `;
      }
    }
  } finally {
    clearInterval(timeoutChecker);
    abortController = null;
    if (btnSend) btnSend.classList.remove("hidden");
    if (btnStop) btnStop.classList.add("hidden");
    if (streamStats) streamStats.textContent = "";
    if (messagesContainer) messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }
}

function stopGeneration() {
  stopGenerationProgressTimer();
  if (abortController) {
    abortController.abort();
  }
}

window.sendMessage = sendMessage;
window.stopGeneration = stopGeneration;
window.resumePendingChatStream = resumePendingChatStream;
window.startGenerationProgressTimer = startGenerationProgressTimer;
window.stopGenerationProgressTimer = stopGenerationProgressTimer;

function appendMessageUI(role, content, attachments = [], metrics = null, timestamp = null, msgIndex = null, status = null, model = null) {
  const container = document.getElementById("chat-messages");
  if (!container) return;

  const isUser = role === "user";
  const avatarClass = isUser ? "avatar-user" : "avatar-assistant";
  const customName = (localStorage.getItem("modeldock_user_name") || localStorage.getItem("omnimodel_user_name"));
  let avatarText = "AI";
  if (isUser) {
    if (customName && customName.trim()) {
      const parts = customName.trim().split(/\s+/);
      avatarText = parts.length === 1 ? parts[0].slice(0, 2).toUpperCase() : (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    } else {
      avatarText = "You";
    }
  }
  const effectiveModel = model || (metrics && metrics.model) || (window.AppState && AppState.activeModel) || "ModelDock Assistant";
  const authorName = isUser ? (customName || "You") : ((typeof getModelDisplayName === "function") ? getModelDisplayName(effectiveModel) : effectiveModel);
  const timeStr = timestamp || new Date().toLocaleTimeString();
  const effectiveIndex = (msgIndex !== null && msgIndex !== undefined) ? msgIndex : (isUser ? chatHistory.length : chatHistory.length);

  let attachmentsHtml = "";
  if (attachments && attachments.length > 0) {
    attachmentsHtml = `
      <div class="message-attachments">
        ${attachments
          .map((att) => {
            const hasThumb = Boolean(att.preview_url);
            const visual = hasThumb
              ? `<img src="${att.preview_url}" class="chip-thumb" alt="${att.filename}" />`
              : `<span class="chip-icon">${getAttachmentIcon(att)}</span>`;
            return `
              <div class="attachment-chip" title="${att.filename}">
                ${visual}
                <div class="chip-info">
                  <span class="chip-name">${att.filename}</span>
                  <span class="chip-sub">${att.size_formatted || att.file_type}</span>
                </div>
              </div>
            `;
          })
          .join("")}
      </div>
    `;
  }

  let metricsHtml = "";
  if (metrics) {
    metricsHtml = `
      <div class="generation-metrics">
        <span>Speed: <strong class="metric-highlight">${metrics.tokens_per_sec || "--"} tokens/sec</strong></span>
        <span>Generated: <strong>${metrics.tokens_generated || "--"} tokens</strong></span>
        <span>Time: <strong>${metrics.total_time_sec || "--"}s</strong></span>
        <span>Engine: <strong>${(typeof getModelDisplayName === "function" ? getModelDisplayName(metrics.model || "--") : (metrics.model || "--"))}</strong></span>
      </div>
    `;
  }

  const userMetaRight = isUser
    ? `<div class="user-meta-actions">
        <span>${timeStr}</span>
        <button class="btn-msg-edit" onclick="editPromptAtIndex(${effectiveIndex})" title="Edit earlier prompt and restart from here" type="button">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
          <span>Edit</span>
        </button>
      </div>`
    : `<span>${timeStr}</span>`;

  let bodyHtml = "";
  if (isUser) {
    bodyHtml = renderMarkdown(content);
  } else if (status === "generating") {
    const dispModel = typeof getModelDisplayName === "function" ? getModelDisplayName(effectiveModel) : effectiveModel;
    const partialHtml = content ? `<div class="assistant-content-area" id="assist-content-${effectiveIndex}">${renderMarkdown(content)}</div>` : `<div class="assistant-content-area" id="assist-content-${effectiveIndex}"></div>`;
    const progressHtml = `
      <div class="chat-progress-card" id="chat-progress-card-${effectiveIndex}">
        <div class="chat-progress-header">
          <div class="chat-progress-info">
            <span class="chat-progress-spinner"></span>
            <span>Generating with <strong>${escapeHtml(dispModel)}</strong></span>
          </div>
          <div class="chat-progress-timer" id="chat-progress-timer-${effectiveIndex}">⏱️ <span class="timer-value">0.0s</span></div>
        </div>
        <div class="chat-progress-bar-track">
          <div class="chat-progress-bar-fill"></div>
        </div>
        <div class="chat-progress-status-row">
          <span class="chat-progress-status-text" id="chat-progress-status-${effectiveIndex}">
            ⚡ Processing prompt & synthesizing response tokens...
          </span>
          <button class="chat-progress-stop-btn" onclick="stopGeneration()" type="button" title="Stop response generation">
            ⏹️ Stop
          </button>
        </div>
      </div>
    `;
    bodyHtml = `${partialHtml}${progressHtml}`;
  } else if (status === "stopped") {
    bodyHtml = `${content ? renderMarkdown(content) : ""}
      <div class="chat-alert-card chat-stopped-box">
        <div class="chat-alert-header">
          <div class="chat-alert-badge stopped-badge">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="4" y="4" width="16" height="16" rx="2"></rect></svg>
            <span>Generation Stopped by User</span>
          </div>
          <span class="chat-alert-time">${timeStr}</span>
        </div>
        <div class="chat-alert-actions">
          <button class="btn-chat-action btn-action-retry" onclick="retryLastUserPrompt()" type="button" title="Resend prompt">
            <span>Give Prompt Again</span>
          </button>
          <button class="btn-chat-action btn-action-edit" onclick="editLastUserPrompt()" type="button" title="Edit prompt">
            <span>Edit Earlier Prompt</span>
          </button>
        </div>
      </div>`;
  } else {
    bodyHtml = renderMarkdown(content) || '<span style="color: var(--text-muted); font-style: italic;">No response recorded</span>';
  }

  const row = document.createElement("div");
  row.className = `message-row ${isUser ? "row-user" : "row-assistant"}`;
  row.setAttribute("data-msg-index", effectiveIndex);
  row.innerHTML = `
    <div class="message-avatar ${avatarClass}">${avatarText}</div>
    <div class="message-bubble ${isUser ? "bubble-user" : "bubble-assistant"}">
      <div class="message-meta">
        <span>${authorName}</span>
        ${userMetaRight}
      </div>
      ${attachmentsHtml}
      <div class="message-body" id="msg-body-${effectiveIndex}" data-raw-content="${encodeURIComponent(content || '')}">${bodyHtml}</div>
      ${metricsHtml}
    </div>
  `;

  container.appendChild(row);
  container.scrollTop = container.scrollHeight;

  return {
    row,
    bubbleElement: row.querySelector(".message-bubble"),
    bodyElement: row.querySelector(".message-body"),
  };
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Transforms an earlier user prompt into an interactive inline editor.
 */
function editPromptAtIndex(msgIndex) {
  const bodyEl = document.getElementById(`msg-body-${msgIndex}`);
  if (!bodyEl) return;
  
  if (bodyEl.querySelector(".inline-edit-box")) return;

  const rawEncoded = bodyEl.getAttribute("data-raw-content") || "";
  let rawText = "";
  try {
    rawText = decodeURIComponent(rawEncoded);
  } catch (e) {
    rawText = bodyEl.innerText.trim();
  }

  bodyEl.setAttribute("data-prev-html", bodyEl.innerHTML);

  bodyEl.innerHTML = `
    <div class="inline-edit-box">
      <textarea id="inline-edit-input-${msgIndex}" class="inline-edit-textarea" rows="3" placeholder="Edit your prompt...">${escapeHtml(rawText)}</textarea>
      <div class="inline-edit-footer">
        <span class="inline-edit-hint">Press <kbd>Ctrl+Enter</kbd> to save &amp; resubmit</span>
        <div class="inline-edit-btn-group">
          <button class="btn-inline-cancel" onclick="cancelPromptEdit(${msgIndex})" type="button">Cancel</button>
          <button class="btn-inline-submit" onclick="submitEditedPrompt(${msgIndex})" type="button">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="19" x2="12" y2="5"></line><polyline points="5 12 12 5 19 12"></polyline></svg>
            <span>Save &amp; Submit</span>
          </button>
        </div>
      </div>
    </div>
  `;

  const textarea = document.getElementById(`inline-edit-input-${msgIndex}`);
  if (textarea) {
    textarea.focus();
    textarea.setSelectionRange(textarea.value.length, textarea.value.length);
    textarea.style.height = "auto";
    textarea.style.height = Math.max(70, textarea.scrollHeight) + "px";
    textarea.addEventListener("input", () => {
      textarea.style.height = "auto";
      textarea.style.height = Math.max(70, textarea.scrollHeight) + "px";
    });
    textarea.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        submitEditedPrompt(msgIndex);
      } else if (e.key === "Escape") {
        e.preventDefault();
        cancelPromptEdit(msgIndex);
      }
    });
  }
}

function cancelPromptEdit(msgIndex) {
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
}

/**
 * Finds the last user prompt and opens it in inline edit mode.
 */
function editLastUserPrompt() {
  if (chatHistory.length === 0) {
    const input = document.getElementById("user-input");
    if (input) input.focus();
    return;
  }

  let lastUserIdx = -1;
  for (let i = chatHistory.length - 1; i >= 0; i--) {
    if (chatHistory[i].role === "user") {
      lastUserIdx = i;
      break;
    }
  }

  if (lastUserIdx === -1) {
    const input = document.getElementById("user-input");
    if (input) input.focus();
    return;
  }

  editPromptAtIndex(lastUserIdx);
  const row = document.querySelector(`[data-msg-index="${lastUserIdx}"]`);
  if (row) {
    row.scrollIntoView({ behavior: "smooth", block: "center" });
  }
}

// Expose handlers globally for onclick attributes
window.editPromptAtIndex = editPromptAtIndex;
window.cancelPromptEdit = cancelPromptEdit;
window.submitEditedPrompt = submitEditedPrompt;
window.retryLastUserPrompt = retryLastUserPrompt;
window.editLastUserPrompt = editLastUserPrompt;

function renderWelcomeScreen() {
  const container = document.getElementById("chat-messages");
  if (!container) return;

  const current = getActiveSession();
  const proj = current && current.projectId ? getProject(current.projectId) : null;

  // Project-Specific Welcome Screen (Inside Project Chat)
  if (proj) {
    const instructionSnippet = proj.systemPrompt && proj.systemPrompt.trim()
      ? `<div class="project-welcome-instructions-box">
           <div class="project-welcome-instructions-header">
             <span>💡 Active Project Instructions</span>
             <button class="project-mini-btn" onclick="openEditProjectModal('${proj.id}')" title="Edit Instructions">Edit</button>
           </div>
           <div class="project-welcome-instructions-text">${proj.systemPrompt.trim()}</div>
         </div>`
      : '';

    container.innerHTML = `
      <div class="chat-welcome">
        <div class="welcome-center-brand">
          <div class="welcome-logo-wrap" style="background: rgba(99, 102, 241, 0.15); border-color: rgba(99, 102, 241, 0.35);">
            <span style="font-size: 1.8rem;">📁</span>
          </div>
          <h1 class="welcome-heading">${proj.name}</h1>
          <p class="welcome-subheading">${proj.description || 'Project Workspace • Dedicated chat session with local models'}</p>
          ${instructionSnippet}
        </div>
        <div class="quick-prompts-chatgpt">
          <button class="quick-prompt-card" onclick="sendQuickPrompt('Analyze the core requirements for this project and create a step-by-step roadmap.')" type="button">
            <div class="prompt-card-icon">🎯</div>
            <div class="prompt-card-text">
              <strong>Project Roadmap</strong>
              <span>Outline key milestones and deliverables</span>
            </div>
          </button>
          <button class="quick-prompt-card" onclick="sendQuickPrompt('Generate a clean modular architecture design with tests for this project.')" type="button">
            <div class="prompt-card-icon">⚡</div>
            <div class="prompt-card-text">
              <strong>Modular Architecture</strong>
              <span>Structure codebase and component design</span>
            </div>
          </button>
          <button class="quick-prompt-card" onclick="sendQuickPrompt('Review attached project documents and extract key technical insights.')" type="button">
            <div class="prompt-card-icon">📑</div>
            <div class="prompt-card-text">
              <strong>Review Documentation</strong>
              <span>Summarize specifications, logs, or data</span>
            </div>
          </button>
          <button class="quick-prompt-card" onclick="sendQuickPrompt('Help me debug and optimize performance within this project.')" type="button">
            <div class="prompt-card-icon">🛠️</div>
            <div class="prompt-card-text">
              <strong>Optimize &amp; Debug</strong>
              <span>Benchmark, refine, and resolve issues</span>
            </div>
          </button>
        </div>
      </div>
    `;
    return;
  }

  // Outer Newly Chat Welcome Screen (Standalone Chat)
  container.innerHTML = `
    <div class="chat-welcome">
      <div class="welcome-center-brand">
        <div class="welcome-logo-wrap">
          <img src="/static/logo.svg" onerror="this.onerror=null; this.src='/static/logo.png';" alt="ModelDock Logo" class="welcome-logo-img" />
        </div>
        <h1 class="welcome-heading">Ready when you are.</h1>
        <p class="welcome-subheading">Ask ModelDock anything, analyze documents, images, code, or local workflows.</p>
      </div>
      <div class="quick-prompts-chatgpt">
        <button class="quick-prompt-card" onclick="sendQuickPrompt('Inspect this screenshot/image and explain its layout, components, and implementation.')" type="button">
          <div class="prompt-card-icon">🖼️</div>
          <div class="prompt-card-text">
            <strong>Create an image or vision query</strong>
            <span>Analyze screenshot, UI, or vision queries</span>
          </div>
        </button>
        <button class="quick-prompt-card" onclick="sendQuickPrompt('Write and edit a clean async Python service with type annotations, docstrings, and tests.')" type="button">
          <div class="prompt-card-icon">✏️</div>
          <div class="prompt-card-text">
            <strong>Write or edit</strong>
            <span>Draft code, essays, resumes, or letters</span>
          </div>
        </button>
        <button class="quick-prompt-card" onclick="sendQuickPrompt('Analyze the structure, key metrics, summary, and data insights from this document.')" type="button">
          <div class="prompt-card-icon">📄</div>
          <div class="prompt-card-text">
            <strong>Analyze documentation</strong>
            <span>Process PDF, Excel, CSV, DOCX files</span>
          </div>
        </button>
        <button class="quick-prompt-card" onclick="sendQuickPrompt('Explain how quantization (Q4_K_M vs FP16) works in GGUF models simply.')" type="button">
          <div class="prompt-card-icon">✨</div>
          <div class="prompt-card-text">
            <strong>Deep reasoning</strong>
            <span>Explain complex concepts and models</span>
          </div>
        </button>
      </div>
    </div>
  `;
}

function createAssistantBubbleUI(model) {
  const assistIndex = chatHistory.length;
  return appendMessageUI("assistant", "", [], null, new Date().toLocaleTimeString(), assistIndex, "generating", model);
}

/**
 * High-Resolution Canvas Exporter for AI-generated Visual SVG Artworks.
 * Renders vector SVGs to supersampled retina HTML5 Canvas for crisp PNG download & clipboard copy.
 */
function svgToCanvas(svgElement, scale = 2.5) {
  return new Promise((resolve, reject) => {
    try {
      const clone = svgElement.cloneNode(true);
      if (!clone.getAttribute("xmlns")) {
        clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
      }

      let width = 600;
      let height = 850;
      const viewBox = clone.getAttribute("viewBox");
      if (viewBox) {
        const parts = viewBox.trim().split(/\s+/).map(Number);
        if (parts.length === 4 && parts[2] > 0 && parts[3] > 0) {
          width = parts[2];
          height = parts[3];
        }
      } else {
        width = clone.clientWidth || parseInt(clone.getAttribute("width")) || 600;
        height = clone.clientHeight || parseInt(clone.getAttribute("height")) || 850;
      }

      clone.setAttribute("width", width.toString());
      clone.setAttribute("height", height.toString());

      const svgString = new XMLSerializer().serializeToString(clone);
      const svgBlob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
      const url = URL.createObjectURL(svgBlob);

      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement("canvas");
        canvas.width = Math.round(width * scale);
        canvas.height = Math.round(height * scale);
        const ctx = canvas.getContext("2d");
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = "high";
        ctx.scale(scale, scale);
        ctx.drawImage(img, 0, 0, width, height);
        URL.revokeObjectURL(url);
        resolve(canvas);
      };
      img.onerror = (e) => {
        URL.revokeObjectURL(url);
        reject(new Error("SVG raster image render failed"));
      };
      img.src = url;
    } catch (err) {
      reject(err);
    }
  });
}

/**
 * 1-Click High-Resolution PNG Artwork Download Handler.
 */
async function downloadImageFromCard(btn, filename = "modeldock-artwork") {
  const card = btn.closest(".ai-image-card");
  if (!card) return;
  const svg = card.querySelector(".ai-image-canvas svg");
  if (!svg) return;

  const originalHtml = btn.innerHTML;
  btn.innerHTML = `<span style="display:inline-flex; align-items:center; gap:0.3rem;">⏳ Exporting...</span>`;
  btn.disabled = true;

  try {
    const canvas = await svgToCanvas(svg, 2.5);
    canvas.toBlob((blob) => {
      if (!blob) throw new Error("Canvas blob export failed");
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${filename}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(url), 2000);

      btn.innerHTML = `<span style="display:inline-flex; align-items:center; gap:0.3rem; color:#34d399;">✓ Saved PNG!</span>`;
      setTimeout(() => {
        btn.innerHTML = originalHtml;
        btn.disabled = false;
      }, 2000);
    }, "image/png", 1.0);
  } catch (err) {
    console.warn("Retina PNG fallback to direct SVG download:", err);
    const svgString = new XMLSerializer().serializeToString(svg);
    const blob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${filename}.svg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 2000);

    btn.innerHTML = `<span style="display:inline-flex; align-items:center; gap:0.3rem; color:#34d399;">✓ Saved SVG!</span>`;
    setTimeout(() => {
      btn.innerHTML = originalHtml;
      btn.disabled = false;
    }, 2000);
  }
}

/**
 * 1-Click Clipboard Image Copy Handler (Raster PNG or Vector SVG).
 */
async function copyImageFromCard(btn) {
  const card = btn.closest(".ai-image-card");
  if (!card) return;
  const svg = card.querySelector(".ai-image-canvas svg");
  if (!svg) return;

  const originalHtml = btn.innerHTML;
  btn.innerHTML = `<span style="display:inline-flex; align-items:center; gap:0.3rem;">⏳ Copying...</span>`;
  btn.disabled = true;

  try {
    const canvas = await svgToCanvas(svg, 2.0);
    canvas.toBlob(async (blob) => {
      if (!blob) throw new Error("Could not create image blob");
      let copied = false;
      if (navigator.clipboard && navigator.clipboard.write && window.ClipboardItem) {
        try {
          const item = new ClipboardItem({ "image/png": blob });
          await navigator.clipboard.write([item]);
          copied = true;
        } catch (clipErr) {
          console.warn("Raster clipboard write failed, trying vector markup fallback:", clipErr);
        }
      }
      if (!copied) {
        const svgString = new XMLSerializer().serializeToString(svg);
        await navigator.clipboard.writeText(svgString);
      }
      btn.innerHTML = `<span style="display:inline-flex; align-items:center; gap:0.3rem; color:#34d399;">✓ Copied Image!</span>`;
      setTimeout(() => {
        btn.innerHTML = originalHtml;
        btn.disabled = false;
      }, 2000);
    }, "image/png", 1.0);
  } catch (err) {
    console.warn("Direct copy failed, falling back to SVG text copy:", err);
    try {
      const svgString = new XMLSerializer().serializeToString(svg);
      await navigator.clipboard.writeText(svgString);
      btn.innerHTML = `<span style="display:inline-flex; align-items:center; gap:0.3rem; color:#34d399;">✓ Copied SVG!</span>`;
    } catch (e) {
      btn.innerHTML = `<span style="color:#f87171;">Copy Failed</span>`;
    }
    setTimeout(() => {
      btn.innerHTML = originalHtml;
      btn.disabled = false;
    }, 2000);
  }
}

/**
 * 1-Click Clipboard Copy Handler for Real Local PNG Images.
 */
async function copyRasterImageFromCard(btn) {
  const card = btn.closest(".ai-raster-image-card");
  if (!card) return;
  const img = card.querySelector("img");
  if (!img) return;

  const originalHtml = btn.innerHTML;
  btn.disabled = true;

  try {
    const res = await fetch(img.src);
    const blob = await res.blob();
    if (navigator.clipboard && window.ClipboardItem) {
      await navigator.clipboard.write([
        new ClipboardItem({ [blob.type || "image/png"]: blob })
      ]);
      btn.innerHTML = `<span style="display:inline-flex; align-items:center; gap:0.3rem; color:#34d399;">✓ Copied PNG!</span>`;
    } else {
      await navigator.clipboard.writeText(img.src);
      btn.innerHTML = `<span style="color:#34d399;">✓ Copied Link!</span>`;
    }
  } catch (err) {
    console.warn("Raster clipboard copy failed:", err);
    btn.innerHTML = `<span style="color:#f87171;">Copy Failed</span>`;
  }

  setTimeout(() => {
    btn.innerHTML = originalHtml;
    btn.disabled = false;
  }, 2000);
}

/**
 * 1-Click Code Copy Handler with User Feedback.
 */
function copyCode(btn) {
  const wrapper = btn.closest(".code-block-wrapper");
  if (!wrapper) return;
  const pre = wrapper.querySelector("pre code") || wrapper.querySelector("pre");
  if (!pre) return;

  const text = pre.innerText || pre.textContent;
  navigator.clipboard.writeText(text).then(() => {
    const origHtml = btn.innerHTML;
    btn.innerHTML = `<span style="display:inline-flex; align-items:center; gap:0.25rem; color:#34d399;">✓ Copied!</span>`;
    setTimeout(() => {
      btn.innerHTML = origHtml;
    }, 1800);
  }).catch(() => {
    btn.textContent = "Copied!";
    setTimeout(() => (btn.textContent = "Copy"), 1800);
  });
}

/**
 * Safe, High-Grade Markdown, Code Block & Visual Image Card Renderer.
 * - Displays vector & AI artworks directly as visual high-definition image cards.
 * - Renders isolated, horizontally scrollable code blocks that never break window bounds.
 */
function renderMarkdown(text) {
  if (!text) return "";

  // Guard for in-progress SVG streaming: show elegant live render indicator until closing tag arrives
  if (text.includes("<svg") && !text.includes("</svg>")) {
    return `
      <div class="ai-image-card" style="padding: 1.25rem; text-align: center; border: 1px dashed rgba(99, 102, 241, 0.4); background: #0c101a;">
        <div style="display: flex; align-items: center; justify-content: center; gap: 0.65rem; color: #c7d2fe; font-size: 0.85rem; font-weight: 500;">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="rotating-icon"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a10 10 0 0 1 10 10"></path></svg>
          <span>Rendering high-resolution AI visual artwork in real-time...</span>
        </div>
      </div>
    `;
  }

  // 0. Extract AI Video Cards before HTML escaping
  const videoCards = [];
  const videoCardRegex = /<!-- AI_VIDEO_CARD_START -->\s*([\s\S]*?)\s*<!-- AI_VIDEO_CARD_END -->/gi;
  text = text.replace(videoCardRegex, (match, cardHtml) => {
    const token = `__AI_VIDEO_CARD_TOKEN_${videoCards.length}__`;
    videoCards.push(cardHtml.trim());
    return token;
  });

  // 0b. Extract Real AI Raster Image Cards (PNG/JPEG Direct Renders)
  const realImageCards = [];
  const realImageCardRegex = /<!-- AI_REAL_IMAGE_START -->\s*([\s\S]*?)\s*<!-- AI_REAL_IMAGE_END -->/gi;
  text = text.replace(realImageCardRegex, (match, cardHtml) => {
    const token = `__AI_REAL_IMAGE_TOKEN_${realImageCards.length}__`;
    realImageCards.push(cardHtml.trim());
    return token;
  });

  // 1. Extract SVG Image Blocks before HTML escaping
  const imageCards = [];
  const svgRegex = /(?:```(?:xml|svg|html)?\s*\n)?(<svg[\s\S]*?<\/svg>)(?:\n\s*```)?/gi;
  let processed = text.replace(svgRegex, (match, svgContent) => {
    const token = `__AI_IMAGE_CARD_TOKEN_${imageCards.length}__`;
    // Clean and validate SVG
    const cleanSvg = svgContent.trim();
    const escapedSvg = cleanSvg
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    const cardHtml = `
      <div class="ai-image-card">
        <div class="ai-image-header">
          <div class="ai-image-badge-label">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
            <span>High-Resolution AI Render</span>
            <span class="ai-image-res-pill">Vector &bull; 2.5x Retina</span>
          </div>
          <div class="ai-image-actions">
            <button class="btn-image-action" onclick="copyImageFromCard(this)" title="Copy high-res image to clipboard">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
              <span>Copy Image</span>
            </button>
            <button class="btn-image-action btn-image-download" onclick="downloadImageFromCard(this, 'modeldock-artwork')" title="Download high-resolution PNG">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
              <span>Download Image</span>
            </button>
          </div>
        </div>
        <div class="ai-image-canvas">
          ${cleanSvg}
        </div>
        <details class="code-details-toggle">
          <summary>View Vector Source &amp; Code</summary>
          <div class="code-block-wrapper" style="margin-top: 0.5rem;">
            <div class="code-block-header">
              <span>SVG / XML</span>
              <button class="btn-code-copy" onclick="copyCode(this)">Copy Code</button>
            </div>
            <pre><code>${escapedSvg}</code></pre>
          </div>
        </details>
      </div>
    `;
    imageCards.push(cardHtml);
    return token;
  });

  // 2. Extract standard fenced code blocks ```lang ... ```
  const codeBlocks = [];
  processed = processed.replace(/```([a-zA-Z0-9_\-\+]*)\n([\s\S]*?)```/g, (match, lang, code) => {
    const token = `__CODE_BLOCK_TOKEN_${codeBlocks.length}__`;
    const langLabel = lang ? lang.toUpperCase() : "CODE";
    const escapedCode = code
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    const blockHtml = `
      <div class="code-block-wrapper">
        <div class="code-block-header">
          <span class="code-lang-label">${langLabel}</span>
          <button class="btn-code-copy" onclick="copyCode(this)" title="Copy Code">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
            <span>Copy</span>
          </button>
        </div>
        <pre><code>${escapedCode}</code></pre>
      </div>
    `;
    codeBlocks.push(blockHtml);
    return token;
  });

  // 3. Escape HTML for the regular text prose
  processed = processed
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // 4. Markdown Headers
  processed = processed.replace(/^### (.*$)/gim, '<h4 class="chat-heading">$1</h4>');
  processed = processed.replace(/^## (.*$)/gim, '<h3 class="chat-heading">$1</h3>');
  processed = processed.replace(/^# (.*$)/gim, '<h2 class="chat-heading">$1</h2>');

  // 5. Unordered List Items
  processed = processed.replace(/^\s*[-*]\s+(.*$)/gim, '<div class="chat-list-item">&bull; $1</div>');

  // 6. Inline code `code`
  processed = processed.replace(/`([^`]+)`/g, "<code>$1</code>");

  // 7. Bold **text**
  processed = processed.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");

  // 8. Italic *text*
  processed = processed.replace(/\*([^*]+)\*/g, "<em>$1</em>");

  // 9. Blockquotes > text
  processed = processed.replace(/^>\s+(.*$)/gim, '<blockquote class="chat-quote">$1</blockquote>');

  // 10. Paragraphs & Line Breaks
  processed = processed.replace(/\n\n+/g, "</p><p>");
  processed = processed.replace(/\n/g, "<br>");

  // 11. Restore Code Blocks
  codeBlocks.forEach((block, idx) => {
    processed = processed.replace(`__CODE_BLOCK_TOKEN_${idx}__`, block);
  });

  // 12. Restore AI Image Cards
  imageCards.forEach((card, idx) => {
    processed = processed.replace(`__AI_IMAGE_CARD_TOKEN_${idx}__`, card);
  });

  // 13. Restore AI Video Cards
  videoCards.forEach((card, idx) => {
    processed = processed.replace(`__AI_VIDEO_CARD_TOKEN_${idx}__`, card);
  });

  // 14. Restore Real AI Raster Image Cards (PNG/JPEG)
  realImageCards.forEach((card, idx) => {
    processed = processed.replace(`__AI_REAL_IMAGE_TOKEN_${idx}__`, card);
  });

  return `<p>${processed}</p>`;
}


/**
 * AI Video Player Interactive Controls (Play / Pause & Download)
 */
function toggleVideoPlayback(btn) {
  const card = btn.closest(".ai-video-card");
  if (!card) return;
  const isPaused = card.classList.toggle("is-paused");
  const label = btn.querySelector("span");
  if (label) {
    label.textContent = isPaused ? "Play" : "Pause";
  }
}
window.toggleVideoPlayback = toggleVideoPlayback;

function toggleRealVideoPlayback(btn) {
  const card = btn.closest(".ai-video-card");
  if (!card) return;
  const video = card.querySelector("video.real-ai-video-element");
  const textSpan = btn.querySelector("span");

  if (video && video.style.display !== "none") {
    if (video.paused) {
      video.play();
      card.classList.remove("is-paused");
      if (textSpan) textSpan.textContent = "Pause";
      btn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg><span>Pause</span>`;
    } else {
      video.pause();
      card.classList.add("is-paused");
      if (textSpan) textSpan.textContent = "Play";
      btn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg><span>Play</span>`;
    }
  } else {
    const isPaused = card.classList.toggle("is-paused");
    if (textSpan) textSpan.textContent = isPaused ? "Play" : "Pause";
    if (isPaused) {
      btn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg><span>Play</span>`;
    } else {
      btn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg><span>Pause</span>`;
    }
  }
}
window.toggleRealVideoPlayback = toggleRealVideoPlayback;

function downloadVideoFromCard(btn, filename = "modeldock-cinema") {
  const card = btn.closest(".ai-video-card");
  if (!card) return;
  const svg = card.querySelector(".ai-video-viewport svg");
  if (!svg) return;

  const originalHtml = btn.innerHTML;
  btn.innerHTML = `<span style="color:#a78bfa;">✓ Downloading...</span>`;
  try {
    const svgData = new XMLSerializer().serializeToString(svg);
    const blob = new Blob([svgData], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${filename}.svg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 2000);
    setTimeout(() => { btn.innerHTML = originalHtml; }, 1500);
  } catch (e) {
    btn.innerHTML = originalHtml;
  }
}
window.downloadVideoFromCard = downloadVideoFromCard;

/**
 * ==========================================================================
 * ModelDock High-Resolution Image Zoom & Pan Lightbox Controller
 * ==========================================================================
 */
let lightboxState = {
  isOpen: false,
  mediaType: "image", // "image" | "video"
  scale: 1.0,
  minScale: 0.35,
  maxScale: 8.0,
  translateX: 0,
  translateY: 0,
  isDragging: false,
  dragStartX: 0,
  dragStartY: 0,
  currentSrc: "",
  currentTitle: "",
  baseW: 800,
  baseH: 600,
  naturalW: 0,
  naturalH: 0,
  isCrispMode: false,
  isLooping: true,
  videoPlaybackRate: 1.0
};

function calculateLightboxBaseDimensions() {
  const img = document.getElementById("lightbox-img");
  const vid = document.getElementById("lightbox-video");
  let natW = 800;
  let natH = 600;

  if (lightboxState.mediaType === "video" && vid) {
    natW = vid.videoWidth || 640;
    natH = vid.videoHeight || 480;
  } else if (img) {
    natW = img.naturalWidth || lightboxState.naturalW || 800;
    natH = img.naturalHeight || lightboxState.naturalH || 600;
  }
  lightboxState.naturalW = natW;
  lightboxState.naturalH = natH;

  const maxFitW = Math.max(300, window.innerWidth * 0.88);
  const maxFitH = Math.max(300, window.innerHeight * 0.80);
  const aspect = natW / (natH || 1);

  let w = maxFitW;
  let h = maxFitW / aspect;
  if (h > maxFitH) {
    h = maxFitH;
    w = maxFitH * aspect;
  }
  lightboxState.baseW = Math.round(w);
  lightboxState.baseH = Math.round(h);
}

function openImageLightbox(src, title = "Generated Artwork") {
  if (!src) return;
  const modal = document.getElementById("modal-image-lightbox");
  const img = document.getElementById("lightbox-img");
  const vid = document.getElementById("lightbox-video");
  const titleEl = document.getElementById("lightbox-image-title");
  const dlLink = document.getElementById("lightbox-download-link");
  const dlText = document.getElementById("lightbox-download-text");
  const btnEnhance = document.getElementById("btn-lightbox-enhance");
  const btnCrisp = document.getElementById("btn-lightbox-crisp");
  const btnLoop = document.getElementById("btn-lightbox-loop");
  const btnSpeed = document.getElementById("btn-lightbox-speed");
  const btnCopy = document.getElementById("btn-lightbox-copy");

  if (!modal || !img) return;

  lightboxState.isOpen = true;
  lightboxState.mediaType = "image";
  lightboxState.scale = 1.0;
  lightboxState.translateX = 0;
  lightboxState.translateY = 0;
  lightboxState.currentSrc = src;
  lightboxState.currentTitle = title;

  // Toggle visible controls for image
  const btnPlay = document.getElementById("btn-lightbox-play");
  if (btnPlay) btnPlay.style.display = "none";
  if (vid) {
    vid.pause();
    vid.style.display = "none";
    vid.src = "";
  }
  if (img) img.style.display = "block";
  if (btnEnhance) btnEnhance.style.display = "inline-flex";
  if (btnCrisp) btnCrisp.style.display = "inline-flex";
  if (btnCopy) btnCopy.style.display = "inline-flex";
  if (btnLoop) btnLoop.style.display = "none";
  if (btnSpeed) btnSpeed.style.display = "none";
  if (dlText) dlText.textContent = "Download";

  img.onload = () => {
    calculateLightboxBaseDimensions();
    updateLightboxTransform();
  };

  img.src = src;
  img.alt = title;
  if (img.complete && img.naturalWidth) {
    calculateLightboxBaseDimensions();
  }

  if (titleEl) titleEl.textContent = title || "High-Resolution Render";

  if (dlLink) {
    dlLink.href = src;
    const filename = src.split("/").pop().split("?")[0] || "modeldock_artwork.png";
    dlLink.download = filename;
  }

  updateLightboxTransform();
  modal.classList.remove("hidden");
  document.body.style.overflow = "hidden";
}
window.openImageLightbox = openImageLightbox;

function openVideoLightbox(videoSrc, title = "Cinematic AI Video", fallbackWebp = "", mp4DownloadUrl = "") {
  if (!videoSrc && !fallbackWebp && !mp4DownloadUrl) return;
  const modal = document.getElementById("modal-image-lightbox");
  const img = document.getElementById("lightbox-img");
  const vid = document.getElementById("lightbox-video");
  const titleEl = document.getElementById("lightbox-image-title");
  const dlLink = document.getElementById("lightbox-download-link");
  const dlText = document.getElementById("lightbox-download-text");
  const btnEnhance = document.getElementById("btn-lightbox-enhance");
  const btnCrisp = document.getElementById("btn-lightbox-crisp");
  const btnLoop = document.getElementById("btn-lightbox-loop");
  const btnSpeed = document.getElementById("btn-lightbox-speed");
  const btnCopy = document.getElementById("btn-lightbox-copy");
  const btnPlay = document.getElementById("btn-lightbox-play");
  const playText = document.getElementById("lightbox-play-text");
  const playIcon = document.getElementById("lightbox-play-icon");

  if (!modal) return;

  lightboxState.isOpen = true;
  lightboxState.mediaType = "video";
  lightboxState.scale = 1.0;
  lightboxState.translateX = 0;
  lightboxState.translateY = 0;
  lightboxState.currentTitle = title;

  // Resolve genuine H.264 MP4 stream URL
  let downloadTarget = mp4DownloadUrl || (videoSrc && videoSrc.includes(".mp4") ? videoSrc : "");
  if (!downloadTarget && videoSrc && videoSrc.includes("generated/video_")) {
    downloadTarget = videoSrc.replace(/\.webp($|\?)/, ".mp4$1");
  }
  if (!downloadTarget) downloadTarget = videoSrc || fallbackWebp;
  lightboxState.currentSrc = downloadTarget;

  // Toggle visible controls for video
  if (btnEnhance) btnEnhance.style.display = "none";
  if (btnCrisp) btnCrisp.style.display = "none";
  if (btnCopy) btnCopy.style.display = "none";
  if (btnPlay) {
    btnPlay.style.display = "inline-flex";
    if (playText) playText.textContent = "Play";
  }
  if (btnLoop) btnLoop.style.display = "inline-flex";
  if (btnSpeed) btnSpeed.style.display = "inline-flex";
  if (dlText) dlText.textContent = "Download MP4";

  if (titleEl) titleEl.textContent = title || "Cinematic AI Video Render";

  if (dlLink) {
    dlLink.href = downloadTarget;
    const filename = downloadTarget.split("/").pop().split("?")[0] || "modeldock_cinema.mp4";
    dlLink.download = filename;
  }

  // Resolve playable video source (MP4 / WebM)
  let playSource = "";
  if (downloadTarget && (downloadTarget.includes(".mp4") || downloadTarget.includes(".webm"))) {
    playSource = downloadTarget;
  } else if (videoSrc && (videoSrc.includes(".mp4") || videoSrc.includes(".webm"))) {
    playSource = videoSrc;
  } else if (mp4DownloadUrl && (mp4DownloadUrl.includes(".mp4") || mp4DownloadUrl.includes(".webm"))) {
    playSource = mp4DownloadUrl;
  }

  // Fallback to high-framerate animated WebP only if MP4 cannot be played
  function switchToWebpFallback() {
    if (!fallbackWebp && !videoSrc) return;
    const streamUrl = fallbackWebp || videoSrc;
    if (vid) {
      vid.pause();
      vid.style.display = "none";
      vid.src = "";
    }
    if (img) {
      img.style.display = "block";
      img.onload = () => {
        calculateLightboxBaseDimensions();
        updateLightboxTransform();
      };
      img.src = streamUrl;
      calculateLightboxBaseDimensions();
      updateLightboxTransform();
    }
  }

  if (vid && playSource) {
    if (img) img.style.display = "none";
    vid.style.display = "block";
    vid.controls = true;

    vid.onerror = (e) => {
      console.warn("HTML5 video error, checking fallback:", e);
      if (!playSource.includes(".mp4") && fallbackWebp) {
        switchToWebpFallback();
      }
    };

    vid.onloadedmetadata = () => {
      calculateLightboxBaseDimensions();
      updateLightboxTransform();
    };

    vid.onplay = () => {
      if (playText) playText.textContent = "Pause";
      if (playIcon) playIcon.innerHTML = '<rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect>';
    };

    vid.onpause = () => {
      if (playText) playText.textContent = "Play";
      if (playIcon) playIcon.innerHTML = '<polygon points="5 3 19 12 5 21 5 3"></polygon>';
    };

    vid.src = playSource;
    vid.loop = lightboxState.isLooping;
    vid.playbackRate = lightboxState.videoPlaybackRate;
    
    const playPromise = vid.play();
    if (playPromise !== undefined) {
      playPromise.then(() => {
        if (playText) playText.textContent = "Pause";
        if (playIcon) playIcon.innerHTML = '<rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect>';
      }).catch(() => {
        // Autoplay policy: video stays paused and ready for user click
        if (playText) playText.textContent = "Play";
        if (playIcon) playIcon.innerHTML = '<polygon points="5 3 19 12 5 21 5 3"></polygon>';
      });
    }
  } else {
    switchToWebpFallback();
  }

  calculateLightboxBaseDimensions();
  updateLightboxTransform();
  modal.classList.remove("hidden");
  document.body.style.overflow = "hidden";
}
window.openVideoLightbox = openVideoLightbox;

function toggleLightboxPlayPause() {
  const vid = document.getElementById("lightbox-video");
  const playText = document.getElementById("lightbox-play-text");
  const playIcon = document.getElementById("lightbox-play-icon");
  if (!vid || vid.style.display === "none") return;

  if (vid.paused) {
    vid.play();
    if (playText) playText.textContent = "Pause";
    if (playIcon) playIcon.innerHTML = '<rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect>';
  } else {
    vid.pause();
    if (playText) playText.textContent = "Play";
    if (playIcon) playIcon.innerHTML = '<polygon points="5 3 19 12 5 21 5 3"></polygon>';
  }
}
window.toggleLightboxPlayPause = toggleLightboxPlayPause;

function toggleLightboxVideoLoop() {
  const vid = document.getElementById("lightbox-video");
  const textEl = document.getElementById("lightbox-loop-text");
  if (!vid) return;
  lightboxState.isLooping = !lightboxState.isLooping;
  vid.loop = lightboxState.isLooping;
  if (textEl) textEl.textContent = lightboxState.isLooping ? "Loop: ON" : "Loop: OFF";
}
window.toggleLightboxVideoLoop = toggleLightboxVideoLoop;

function cycleLightboxVideoSpeed() {
  const vid = document.getElementById("lightbox-video");
  const textEl = document.getElementById("lightbox-speed-text");
  if (!vid) return;
  const speeds = [1.0, 1.5, 2.0, 0.5];
  const idx = speeds.indexOf(lightboxState.videoPlaybackRate);
  lightboxState.videoPlaybackRate = speeds[(idx + 1) % speeds.length];
  vid.playbackRate = lightboxState.videoPlaybackRate;
  if (textEl) textEl.textContent = `${lightboxState.videoPlaybackRate}x`;
}
window.cycleLightboxVideoSpeed = cycleLightboxVideoSpeed;

function closeImageLightbox() {
  const modal = document.getElementById("modal-image-lightbox");
  const vid = document.getElementById("lightbox-video");
  if (vid) {
    vid.pause();
    vid.src = "";
  }
  if (!modal) return;
  modal.classList.add("hidden");
  lightboxState.isOpen = false;
  document.body.style.overflow = "";
}
window.closeImageLightbox = closeImageLightbox;

function handleLightboxBackdropClick(e) {
  if (e.target.id === "modal-image-lightbox" || e.target.id === "lightbox-viewport") {
    closeImageLightbox();
  }
}
window.handleLightboxBackdropClick = handleLightboxBackdropClick;

function updateLightboxTransform() {
  const img = document.getElementById("lightbox-img");
  const vid = document.getElementById("lightbox-video");
  const badge = document.getElementById("lightbox-zoom-badge");
  const targetEl = lightboxState.mediaType === "video" ? vid : img;
  if (!targetEl) return;

  const currentW = Math.round(lightboxState.baseW * lightboxState.scale);
  const currentH = Math.round(lightboxState.baseH * lightboxState.scale);

  targetEl.style.width = currentW + "px";
  targetEl.style.height = currentH + "px";
  targetEl.style.maxWidth = "none";
  targetEl.style.maxHeight = "none";
  targetEl.style.transform = `translate(${lightboxState.translateX}px, ${lightboxState.translateY}px)`;

  if (badge) {
    const pct = Math.round(lightboxState.scale * 100);
    const mediaTag = lightboxState.mediaType === "video" ? "Cinema MP4" : "Native";
    const nat = lightboxState.naturalW ? ` • ${lightboxState.naturalW}×${lightboxState.naturalH} ${mediaTag}` : "";
    badge.textContent = `${pct}% (${currentW}×${currentH}px${nat})`;
  }
}

function toggleLightboxCrispMode() {
  const img = document.getElementById("lightbox-img");
  const btn = document.getElementById("btn-lightbox-crisp");
  const textEl = document.getElementById("lightbox-crisp-text");
  if (!img) return;

  lightboxState.isCrispMode = !lightboxState.isCrispMode;
  if (lightboxState.isCrispMode) {
    img.classList.add("crisp-pixel-mode");
    if (textEl) textEl.textContent = "Sharp Mode: ON";
    if (btn) btn.style.borderColor = "var(--color-primary-light, #60a5fa)";
  } else {
    img.classList.remove("crisp-pixel-mode");
    if (textEl) textEl.textContent = "Sharp Pixels";
    if (btn) btn.style.borderColor = "";
  }
}
window.toggleLightboxCrispMode = toggleLightboxCrispMode;

function zoomLightboxImage(delta) {
  const newScale = Math.min(lightboxState.maxScale, Math.max(lightboxState.minScale, lightboxState.scale + delta));
  lightboxState.scale = Number(newScale.toFixed(2));
  if (lightboxState.scale <= 1.0) {
    lightboxState.translateX = 0;
    lightboxState.translateY = 0;
  }
  updateLightboxTransform();
}
window.zoomLightboxImage = zoomLightboxImage;

function resetLightboxZoom() {
  lightboxState.scale = 1.0;
  lightboxState.translateX = 0;
  lightboxState.translateY = 0;
  calculateLightboxBaseDimensions();
  updateLightboxTransform();
}
window.resetLightboxZoom = resetLightboxZoom;

function handleLightboxWheel(e) {
  e.preventDefault();
  const delta = e.deltaY < 0 ? 0.2 : -0.2;
  zoomLightboxImage(delta);
}
window.handleLightboxWheel = handleLightboxWheel;

function handleLightboxDblClick(e) {
  e.preventDefault();
  if (lightboxState.scale > 1.2) {
    resetLightboxZoom();
  } else {
    lightboxState.scale = 2.5;
    updateLightboxTransform();
  }
}
window.handleLightboxDblClick = handleLightboxDblClick;

function handleLightboxMouseDown(e) {
  if (e.button !== 0) return; // only left click
  lightboxState.isDragging = true;
  lightboxState.dragStartX = e.clientX - lightboxState.translateX;
  lightboxState.dragStartY = e.clientY - lightboxState.translateY;
  const viewport = document.getElementById("lightbox-viewport");
  if (viewport) viewport.classList.add("panning");
}
window.handleLightboxMouseDown = handleLightboxMouseDown;

window.addEventListener("mousemove", (e) => {
  if (!lightboxState.isDragging || !lightboxState.isOpen) return;
  lightboxState.translateX = e.clientX - lightboxState.dragStartX;
  lightboxState.translateY = e.clientY - lightboxState.dragStartY;
  updateLightboxTransform();
});

window.addEventListener("mouseup", () => {
  if (lightboxState.isDragging) {
    lightboxState.isDragging = false;
    const viewport = document.getElementById("lightbox-viewport");
    if (viewport) viewport.classList.remove("panning");
  }
});

window.addEventListener("resize", () => {
  if (lightboxState.isOpen) {
    calculateLightboxBaseDimensions();
    updateLightboxTransform();
  }
});

window.addEventListener("keydown", (e) => {
  if (!lightboxState.isOpen) return;
  if (e.key === "Escape") {
    closeImageLightbox();
  } else if (e.key === " " || e.code === "Space") {
    if (lightboxState.mediaType === "video") {
      e.preventDefault();
      toggleLightboxPlayPause();
    }
  } else if (e.key === "+" || e.key === "=") {
    zoomLightboxImage(0.25);
  } else if (e.key === "-" || e.key === "_") {
    zoomLightboxImage(-0.25);
  } else if (e.key === "0") {
    resetLightboxZoom();
  }
});

async function copyLightboxImage() {
  if (!lightboxState.currentSrc) return;
  try {
    const res = await fetch(lightboxState.currentSrc);
    const blob = await res.blob();
    await navigator.clipboard.write([
      new ClipboardItem({ [blob.type]: blob })
    ]);
    const badge = document.getElementById("lightbox-zoom-badge");
    if (badge) {
      const prev = badge.textContent;
      badge.textContent = "✓ Copied!";
      setTimeout(() => { badge.textContent = prev; }, 1500);
    }
  } catch (err) {
    console.error("Failed to copy image", err);
  }
}
window.copyLightboxImage = copyLightboxImage;

// Global Delegated Click Listener for All Generated Images, Videos and Attachments
document.addEventListener("click", (e) => {
  const target = e.target;
  if (!target) return;

  // Ignore clicks on action buttons or links inside cards
  if (target.closest("button") || target.closest("a")) return;

  // 1. Image Click
  if (target.tagName === "IMG") {
    if (target.classList.contains("generated-real-photo") || 
        target.closest(".ai-raster-viewport") || 
        target.closest(".message-attachments")) {
      e.stopPropagation();
      openImageLightbox(target.src, target.alt || "Generated Artwork");
      return;
    } else if (target.classList.contains("real-ai-video-fallback") || target.closest(".ai-video-viewport")) {
      e.stopPropagation();
      const card = target.closest(".ai-video-card");
      const videoEl = card ? card.querySelector("video") : null;
      const sourceEl = videoEl ? videoEl.querySelector("source") : null;
      const mp4Url = card?.querySelector("a.btn-video-download")?.href || (sourceEl ? sourceEl.src : "") || (videoEl ? (videoEl.currentSrc || videoEl.src) : "");
      const title = card ? (card.getAttribute("data-title") || "Cinematic Video") : "Cinematic Video";
      openVideoLightbox(mp4Url || target.src, title, target.src, mp4Url);
      return;
    }
  }

  // 2. Video Element or Video Viewport Click in Chat
  const videoViewport = target.closest(".ai-video-viewport");
  if (videoViewport || target.tagName === "VIDEO") {
    // If the click is on native video control bar itself, let native controls handle it
    if (target.tagName === "VIDEO" && e.offsetY > target.clientHeight - 48) {
      return;
    }
    e.stopPropagation();
    const card = target.closest(".ai-video-card") || videoViewport?.closest(".ai-video-card");
    const title = card ? (card.getAttribute("data-title") || "Cinematic Video") : "Cinematic Video";
    const videoEl = card ? card.querySelector("video") : null;
    const sourceEl = videoEl ? videoEl.querySelector("source") : null;
    const webpImg = card ? card.querySelector("img.real-ai-video-fallback") : null;
    const mp4Url = card?.querySelector("a.btn-video-download")?.href || (sourceEl ? sourceEl.src : "") || (videoEl ? (videoEl.currentSrc || videoEl.src) : "");
    const playUrl = mp4Url || (videoEl ? (videoEl.currentSrc || videoEl.src) : (webpImg ? webpImg.src : ""));
    openVideoLightbox(playUrl, title, webpImg ? webpImg.src : "", mp4Url);
  }
});

async function enhanceCurrentLightboxImage(scale = 4) {
  if (!lightboxState.currentSrc) return;
  const btn = document.getElementById("btn-lightbox-enhance");
  const textEl = document.getElementById("lightbox-enhance-text");
  const titleEl = document.getElementById("lightbox-image-title");
  const imgEl = document.getElementById("lightbox-img");
  const dlLink = document.getElementById("lightbox-download-link");

  const originalSrc = lightboxState.currentSrc;
  const filename = originalSrc.split("/").pop().split("?")[0];

  if (btn) btn.disabled = true;
  if (textEl) textEl.textContent = "⏳ Enhancing to 8K...";

  try {
    const res = await fetch("/api/media/enhance-8k", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename: filename, scale: scale }),
    });

    const data = await res.json();
    if (res.ok && data.success) {
      const newUrl = data.url + `?t=${Date.now()}`;
      lightboxState.currentSrc = newUrl;
      if (imgEl) {
        imgEl.onload = () => {
          calculateLightboxBaseDimensions();
          updateLightboxTransform();
        };
        imgEl.src = newUrl;
      }
      if (dlLink) {
        dlLink.href = newUrl;
        dlLink.download = data.filename || "enhanced_8k.png";
      }
      if (titleEl) {
        titleEl.textContent = `${lightboxState.currentTitle || "Artwork"} ✨ 8K UHD (${data.width} × ${data.height})`;
      }
      if (textEl) textEl.textContent = "✓ 8K Enhanced";

      // Also update any matching image cards in chat view
      document.querySelectorAll(`img[src*="${filename}"]`).forEach((chatImg) => {
        chatImg.src = newUrl;
        const card = chatImg.closest(".ai-raster-image-card");
        if (card) {
          const pill = card.querySelector(".ai-image-res-pill");
          if (pill) pill.textContent = `✨ 8K UHD (${data.width} × ${data.height})`;
        }
      });
    } else {
      alert(`Enhance error: ${data.detail || data.error || "Failed to enhance image"}`);
      if (textEl) textEl.textContent = "✨ 8K Enhance";
    }
  } catch (err) {
    alert(`Enhancement request failed: ${err.message}`);
    if (textEl) textEl.textContent = "✨ 8K Enhance";
  } finally {
    if (btn) btn.disabled = false;
  }
}
window.enhanceCurrentLightboxImage = enhanceCurrentLightboxImage;

async function enhanceImageTo8K(btn, imgUrl) {
  if (!imgUrl) return;
  const filename = imgUrl.split("/").pop().split("?")[0];
  const origText = btn ? btn.innerHTML : "";
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span>⏳ Enhancing...</span>`;
  }
  try {
    const res = await fetch("/api/media/enhance-8k", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename: filename, scale: 4 }),
    });
    const data = await res.json();
    if (res.ok && data.success) {
      const newUrl = data.url + `?t=${Date.now()}`;
      const card = btn ? btn.closest(".ai-raster-image-card") : null;
      if (card) {
        const img = card.querySelector("img");
        if (img) img.src = newUrl;
        const dlBtn = card.querySelector(".btn-image-download");
        if (dlBtn) {
          dlBtn.href = newUrl;
          dlBtn.download = data.filename;
        }
        const pill = card.querySelector(".ai-image-res-pill");
        if (pill) pill.textContent = `✨ 8K UHD (${data.width} × ${data.height})`;
      }
      if (btn) btn.innerHTML = `<span>✓ 8K Done</span>`;
    } else {
      alert(`Enhancement failed: ${data.detail || data.error || "Unknown"}`);
      if (btn) btn.innerHTML = origText;
    }
  } catch (err) {
    alert(`Error: ${err.message}`);
    if (btn) btn.innerHTML = origText;
  } finally {
    if (btn) btn.disabled = false;
  }
}
window.enhanceImageTo8K = enhanceImageTo8K;
