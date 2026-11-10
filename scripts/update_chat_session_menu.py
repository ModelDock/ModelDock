from pathlib import Path

p = Path(r"a:\AI_Project_work\ollama_2nd_copy\static\js\chat.js")
content = p.read_text(encoding="utf-8")

# 1. Add renameSession and moveSessionToProject right after togglePinSession
old_pin_func = '''function togglePinSession(sessionId, e) {
  if (e) e.stopPropagation();
  const s = chatSessions.find((item) => item.id === sessionId);
  if (s) {
    s.pinned = !s.pinned;
    saveSessionsToStorage();
    renderSidebarSessions();
  }
}'''

new_pin_and_actions = '''function togglePinSession(sessionId, e) {
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
});'''

assert old_pin_func in content, "old_pin_func not found in chat.js"
content = content.replace(old_pin_func, new_pin_and_actions, 1)

# 2. Update createSessionItemElement to output Pin icon + 3-dots icon
old_create_item = '''function createSessionItemElement(session, isNested = false) {
  const item = document.createElement("div");
  item.className = "session-item" + (session.id === activeSessionId ? " active" : "") + (isNested ? " nested-session" : "");
  item.onclick = () => selectSession(session.id);
  item.title = session.title || "Chat Session";

  const titleSpan = document.createElement("span");
  titleSpan.className = "session-title";
  titleSpan.textContent = session.title || "Chat Session";

  const actions = document.createElement("div");
  actions.className = "session-actions";

  // Pin button
  const pinBtn = document.createElement("button");
  pinBtn.className = "session-action-btn";
  pinBtn.title = session.pinned ? "Unpin chat" : "Pin chat";
  pinBtn.innerHTML = session.pinned ? "📌" : "📍";
  pinBtn.onclick = (e) => togglePinSession(session.id, e);

  // Delete button
  const delBtn = document.createElement("button");
  delBtn.className = "session-action-btn";
  delBtn.title = "Delete conversation";
  delBtn.innerHTML = "🗑️";
  delBtn.onclick = (e) => deleteSession(session.id, e);

  actions.appendChild(pinBtn);
  actions.appendChild(delBtn);

  item.appendChild(titleSpan);
  item.appendChild(actions);
  return item;
}'''

new_create_item = '''function createSessionItemElement(session, isNested = false) {
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
}'''

assert old_create_item in content, "old_create_item not found in chat.js"
content = content.replace(old_create_item, new_create_item, 1)

p.write_text(content, encoding="utf-8")
print("Updated chat.js with Pin + 3-dots icon menu and actions!")
