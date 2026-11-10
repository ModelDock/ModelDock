from pathlib import Path

p = Path(r"a:\AI_Project_work\ollama_2nd_copy\static\index.html")
content = p.read_text(encoding="utf-8")

old_modal = '''  <!-- Create / Edit Project Modal -->
  <div id="modal-project" class="modal-backdrop hidden" onclick="if(event.target === this) closeProjectModal()">
    <div class="modal-card">
      <div class="modal-header">
        <div class="modal-title-row">
          <span style="font-size: 1.3rem;">📁</span>
          <h3 id="modal-project-title">Create New Project</h3>
        </div>
        <button class="btn-close" onclick="closeProjectModal()" type="button">&times;</button>
      </div>
      <div class="modal-body">
        <input type="hidden" id="project-form-id" value="" />
        <div class="form-group">
          <label for="project-form-name">Project Name:</label>
          <input type="text" id="project-form-name" placeholder="e.g. Python Architect, Document Analysis, Medical QA" autocomplete="off" />
        </div>
        <div class="form-group">
          <label for="project-form-desc">Description (Optional):</label>
          <input type="text" id="project-form-desc" placeholder="Brief summary of what this project workspace handles" autocomplete="off" />
        </div>
        <div class="form-group">
          <label for="project-form-model">Assigned Model for this Project:</label>
          <select id="project-form-model" class="select-dropdown">
            <option value="">(Inherit Running Model)</option>
          </select>
          <div class="param-hint">ModelDock will automatically switch to this model when you chat in this project.</div>
        </div>
        <div class="form-group">
          <label for="project-form-instructions">Custom System Instructions (Optional):</label>
          <textarea id="project-form-instructions" rows="4" placeholder="e.g. You are an expert Python architect. Always provide clean, type-annotated code with docstrings and unit tests."></textarea>
          <div class="param-hint">These instructions will be automatically applied to all conversations inside this project.</div>
        </div>
      </div>
      <div class="modal-footer" style="display: flex; justify-content: space-between; align-items: center;">
        <button id="btn-delete-project" class="btn-danger hidden" onclick="deleteCurrentProject()" type="button">Delete Project</button>
        <div style="display: flex; gap: 0.5rem; margin-left: auto;">
          <button class="btn-secondary" onclick="closeProjectModal()" type="button">Cancel</button>
          <button id="btn-save-project" class="btn-primary" onclick="saveProjectFromModal()" type="button">Save &amp; Start Chat</button>
        </div>
      </div>
    </div>
  </div>'''

new_modal = '''  <!-- Create / Edit Project Modal -->
  <div id="modal-project" class="modal-backdrop hidden" onclick="if(event.target === this) closeProjectModal()">
    <div class="modal-card modal-card-project">
      <div class="modal-header">
        <div class="modal-title-row">
          <div class="modal-header-icon-box">
            <span style="font-size: 1.35rem;">📁</span>
          </div>
          <div class="modal-header-text">
            <h3 id="modal-project-title">Create New Project</h3>
            <p class="modal-header-subtitle">Group related chats with dedicated instructions and models.</p>
          </div>
        </div>
        <button class="btn-close" onclick="closeProjectModal()" type="button" title="Close modal">&times;</button>
      </div>
      <div class="modal-body">
        <input type="hidden" id="project-form-id" value="" />
        <div class="form-group">
          <label for="project-form-name">
            <span>Project Name</span>
            <span class="label-required">*Required</span>
          </label>
          <input type="text" id="project-form-name" class="input-text" placeholder="e.g. Python Architect, Document Analysis, Web Scraper" autocomplete="off" />
        </div>
        <div class="form-group">
          <label for="project-form-desc">
            <span>Description</span>
            <span class="label-optional">(Optional)</span>
          </label>
          <input type="text" id="project-form-desc" class="input-text" placeholder="Brief summary of what this project workspace handles" autocomplete="off" />
        </div>
        <div class="form-group">
          <label for="project-form-model">
            <span>Assigned Model</span>
            <span class="label-optional">(Optional)</span>
          </label>
          <div class="select-wrapper">
            <select id="project-form-model" class="select-dropdown">
              <option value="">(Inherit Running Model)</option>
            </select>
          </div>
          <div class="param-hint">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
            <span>ModelDock automatically switches to this model when chatting in this project.</span>
          </div>
        </div>
        <div class="form-group">
          <label for="project-form-instructions">
            <span>Custom System Instructions</span>
            <span class="label-optional">(Optional)</span>
          </label>
          <textarea id="project-form-instructions" class="input-textarea" rows="4" placeholder="e.g. You are an expert software architect. Always provide clean, production-grade code with docstrings, type annotations, and unit tests."></textarea>
          <div class="param-hint">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
            <span>Automatically applied as system prompt to all conversations in this project.</span>
          </div>
        </div>
      </div>
      <div class="modal-footer" style="display: flex; justify-content: space-between; align-items: center;">
        <button id="btn-delete-project" class="btn-danger hidden" onclick="deleteCurrentProject()" type="button" style="display: inline-flex; align-items: center; gap: 0.35rem;">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
          <span>Delete Project</span>
        </button>
        <div class="modal-footer-actions" style="display: flex; gap: 0.6rem; margin-left: auto;">
          <button class="btn-secondary" onclick="closeProjectModal()" type="button">Cancel</button>
          <button id="btn-save-project" class="btn-primary" onclick="saveProjectFromModal()" type="button" style="display: inline-flex; align-items: center; gap: 0.4rem;">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
            <span>Save &amp; Start Chat</span>
          </button>
        </div>
      </div>
    </div>
  </div>'''

assert old_modal in content, "old_modal not found in index.html"
content = content.replace(old_modal, new_modal, 1)
p.write_text(content, encoding="utf-8")
print("Updated modal-project markup in static/index.html!")
