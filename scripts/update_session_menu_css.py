from pathlib import Path

p = Path(r"a:\AI_Project_work\ollama_2nd_copy\static\css\style.css")
content = p.read_text(encoding="utf-8")

old_css = '''.session-actions {
  display: none;
  align-items: center;
  gap: 0.25rem;
  margin-left: 0.35rem;
}

.session-item:hover .session-actions {
  display: flex;
}

.session-action-btn {
  background: none;
  border: none;
  color: #a1a1aa;
  padding: 0.2rem;
  cursor: pointer;
  border-radius: 4px;
  font-size: 0.75rem;
  line-height: 1;
}

.session-action-btn:hover {
  color: #ef4444;
}'''

new_css = '''.session-actions {
  display: none;
  align-items: center;
  gap: 0.15rem;
  margin-left: auto;
  flex-shrink: 0;
}

.session-item:hover .session-actions,
.session-item.active .session-actions,
.session-item.is-pinned .session-actions {
  display: flex;
}

.session-item.is-pinned:not(:hover) .session-dots-btn {
  display: none;
}

.session-item.is-pinned .session-pin-btn {
  color: #818cf8;
  opacity: 0.95;
}

.session-action-btn {
  background: transparent;
  border: none;
  color: #71717a;
  padding: 0.25rem 0.35rem;
  cursor: pointer;
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
  line-height: 1;
}

.session-action-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #f8fafc;
}

.session-pin-btn:hover {
  color: #818cf8;
}

.session-pin-btn.pinned-active {
  color: #818cf8;
}

.session-dots-btn:hover {
  color: #ffffff;
}

.session-rename-input {
  background: #141824;
  border: 1px solid #6366f1;
  border-radius: 4px;
  color: #f8fafc;
  font-family: inherit;
  font-size: 0.82rem;
  padding: 0.15rem 0.4rem;
  width: 100%;
  outline: none;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.25);
  box-sizing: border-box;
}

/* 3-Dot Floating Context Menu */
.session-context-menu {
  position: fixed;
  z-index: 10000;
  background: #161a26;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.7), 0 0 20px rgba(99, 102, 241, 0.12);
  min-width: 190px;
  padding: 0.35rem;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  animation: menuFadeIn 0.14s ease-out;
  backdrop-filter: blur(12px);
}

@keyframes menuFadeIn {
  from {
    opacity: 0;
    transform: scale(0.96);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.chat-menu-item {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.5rem 0.75rem;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: #cbd5e1;
  font-size: 0.82rem;
  font-family: var(--font-sans);
  text-align: left;
  cursor: pointer;
  transition: all 0.12s ease;
  width: 100%;
  box-sizing: border-box;
  text-decoration: none;
}

.chat-menu-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

.chat-menu-item-inner {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  flex: 1;
}

.chat-menu-danger {
  color: #f87171 !important;
}

.chat-menu-danger:hover {
  background: rgba(239, 68, 68, 0.15) !important;
  color: #fca5a5 !important;
}

.chat-menu-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.08);
  margin: 0.25rem 0.4rem;
}

/* Submenu for Move to Project */
.chat-menu-has-sub {
  position: relative;
  justify-content: space-between;
}

.chevron-sub {
  color: #64748b;
  margin-left: auto;
}

.chat-menu-sub {
  position: absolute;
  left: 100%;
  top: 0;
  margin-left: 6px;
  background: #161a26;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.7);
  min-width: 195px;
  max-width: 250px;
  max-height: 280px;
  overflow-y: auto;
  padding: 0.35rem;
  display: none;
  flex-direction: column;
  gap: 0.15rem;
  z-index: 10001;
  backdrop-filter: blur(12px);
}

.chat-menu-has-sub:hover .chat-menu-sub,
.chat-menu-has-sub:focus-within .chat-menu-sub {
  display: flex;
}

.chat-menu-subitem {
  font-size: 0.8rem;
  padding: 0.45rem 0.65rem;
}

.chat-menu-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.proj-check {
  color: #818cf8;
  font-weight: 700;
  margin-left: auto;
}

.active-proj-item {
  background: rgba(99, 102, 241, 0.12);
  color: #818cf8;
}

.chat-submenu-empty {
  font-size: 0.76rem;
  color: #64748b;
  padding: 0.45rem 0.65rem;
  text-align: center;
}'''

assert old_css in content, "old_css not found in style.css"
content = content.replace(old_css, new_css, 1)

p.write_text(content, encoding="utf-8")
print("Updated session-actions and added 3-dot context menu styles in static/css/style.css!")
