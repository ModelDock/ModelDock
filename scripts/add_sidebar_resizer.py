import sys

with open('static/js/chat.js', 'r', encoding='utf-8') as f:
    content = f.read()

target = '  // Initialize Multi-Session History\n  initChatSessions();'

replacement = '''  // Initialize Draggable Sidebar Resizer
  initSidebarResizer();

  // Initialize Multi-Session History
  initChatSessions();'''

sidebar_resizer_code = '''
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
'''

target_before_toggle = '// --- Sidebar Toggle Logic ---'
if target not in content:
    print('Error: target not found')
    sys.exit(1)

if target_before_toggle not in content:
    print('Error: target_before_toggle not found')
    sys.exit(1)

content = content.replace(target, replacement, 1)
content = content.replace(target_before_toggle, sidebar_resizer_code + '\n' + target_before_toggle, 1)

with open('static/js/chat.js', 'w', encoding='utf-8') as f:
    f.write(content)

print('Successfully added initSidebarResizer to chat.js')
