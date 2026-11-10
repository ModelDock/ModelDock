from pathlib import Path

p = Path(r"a:\AI_Project_work\ollama_2nd_copy\static\css\style.css")
content = p.read_text(encoding="utf-8")

css_additions = '''
/* ==========================================================================
   Modern Polished Form Controls & Modal Cards (Projects, Imports, Settings)
   ========================================================================== */

.modal-card-project {
  max-width: 560px !important;
  width: 95% !important;
  background: linear-gradient(180deg, #131726 0%, #0c0f1a 100%) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  border-radius: 16px !important;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.75), 0 0 40px rgba(99, 102, 241, 0.16) !important;
  overflow: hidden;
  animation: modalSlideIn 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: scale(0.96) translateY(8px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.modal-header-icon-box {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.modal-header-text {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.modal-header-subtitle {
  font-size: 0.78rem;
  color: #94a3b8;
  margin: 0;
  line-height: 1.35;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  margin-bottom: 1.15rem;
  width: 100%;
  box-sizing: border-box;
}

.form-group:last-child {
  margin-bottom: 0.35rem;
}

.form-group label,
.modal-body label {
  display: flex !important;
  align-items: center;
  justify-content: space-between;
  font-size: 0.76rem !important;
  font-weight: 600 !important;
  color: #cbd5e1 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  margin-bottom: 0.2rem !important;
  user-select: none;
}

.label-required {
  font-size: 0.7rem;
  color: #818cf8;
  font-weight: 500;
  text-transform: none;
  letter-spacing: normal;
}

.label-optional {
  font-size: 0.7rem;
  color: #64748b;
  font-weight: 400;
  text-transform: none;
  letter-spacing: normal;
}

.form-group input[type="text"],
.form-group input[type="password"],
.form-group input[type="email"],
.form-group textarea,
.modal-body input[type="text"],
.modal-body textarea,
.input-text,
.input-textarea {
  display: block !important;
  width: 100% !important;
  box-sizing: border-box !important;
  background: #161a29 !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  border-radius: 9px !important;
  color: #f8fafc !important;
  font-family: var(--font-sans) !important;
  font-size: 0.88rem !important;
  line-height: 1.45 !important;
  padding: 0.65rem 0.85rem !important;
  outline: none !important;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease !important;
}

.form-group input[type="text"]::placeholder,
.form-group textarea::placeholder,
.modal-body input::placeholder,
.modal-body textarea::placeholder,
.input-text::placeholder,
.input-textarea::placeholder {
  color: #525a70 !important;
}

.form-group input[type="text"]:focus,
.form-group textarea:focus,
.modal-body input[type="text"]:focus,
.modal-body textarea:focus,
.input-text:focus,
.input-textarea:focus {
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25) !important;
  background: #1b2033 !important;
}

.form-group textarea,
.modal-body textarea,
.input-textarea {
  min-height: 105px !important;
  resize: vertical !important;
  line-height: 1.5 !important;
}

.select-wrapper {
  position: relative;
  width: 100%;
}

.form-group select,
.modal-body select.select-dropdown,
.select-dropdown {
  display: block !important;
  width: 100% !important;
  box-sizing: border-box !important;
  background: #161a29 !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  border-radius: 9px !important;
  color: #f8fafc !important;
  font-family: var(--font-sans) !important;
  font-size: 0.88rem !important;
  padding: 0.65rem 0.85rem !important;
  outline: none !important;
  cursor: pointer !important;
  appearance: none !important;
  -webkit-appearance: none !important;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2.2'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E") !important;
  background-repeat: no-repeat !important;
  background-position: right 0.85rem center !important;
  background-size: 14px !important;
  padding-right: 2.3rem !important;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease !important;
}

.form-group select:focus,
.modal-body select.select-dropdown:focus,
.select-dropdown:focus {
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25) !important;
  background-color: #1b2033 !important;
}

.param-hint {
  font-size: 0.74rem;
  color: #64748b;
  margin-top: 0.35rem;
  line-height: 1.35;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.param-hint svg {
  flex-shrink: 0;
  opacity: 0.75;
}

.modal-footer-actions {
  display: flex;
  gap: 0.6rem;
  align-items: center;
  margin-left: auto;
}
'''

content += css_additions
p.write_text(content, encoding="utf-8")
print("Appended polished form and modal CSS to static/css/style.css!")
