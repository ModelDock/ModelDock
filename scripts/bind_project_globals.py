from pathlib import Path

p = Path(r"a:\AI_Project_work\ollama_2nd_copy\static\js\chat.js")
content = p.read_text(encoding="utf-8")

old = '''  // If newly created, immediately start a chat inside this project!
  if (isNew) {
    createNewSession(projId);
  } else {
    renderSidebarSessions();
    loadActiveSession();
  }
}'''

new = '''  // If newly created, immediately start a chat inside this project!
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
window.deleteCurrentProject = deleteCurrentProject;'''

assert old in content, "old block not found in chat.js"
content = content.replace(old, new, 1)
p.write_text(content, encoding="utf-8")
print("Added global window bindings for project modal in chat.js!")
