from pathlib import Path

p = Path(r"a:\AI_Project_work\ollama_2nd_copy\static\index.html")
content = p.read_text(encoding="utf-8")

# 1. Early width restore in <head>
old_head_script = '''  <script>
    // Bulletproof Early-Loaded Sidebar Controller (Immune to cache / network latency)
    function toggleSidebar(forcedState) {'''

new_head_script = '''  <script>
    // Restore user-customized sidebar width immediately before paint
    (function() {
      try {
        const savedWidth = localStorage.getItem("modeldock_sidebar_width");
        if (savedWidth) {
          const w = parseInt(savedWidth, 10);
          if (w >= 190 && w <= 550) {
            document.documentElement.style.setProperty("--sidebar-width", `${w}px`);
          }
        }
      } catch(e) {}
    })();

    // Bulletproof Early-Loaded Sidebar Controller (Immune to cache / network latency)
    function toggleSidebar(forcedState) {'''

assert old_head_script in content, "old_head_script not found"
content = content.replace(old_head_script, new_head_script, 1)

# 2. Insert sidebar-resizer handle after </aside>
old_aside_close = '''        </aside>

        <!-- Right Main Chat Canvas -->
        <div class="chat-main">'''

new_aside_close = '''        </aside>

        <!-- Draggable Resizer Handle for Sidebar -->
        <div id="sidebar-resizer" class="sidebar-resizer" title="Drag to resize sidebar width (Double-click to reset)"></div>

        <!-- Right Main Chat Canvas -->
        <div class="chat-main">'''

assert old_aside_close in content, "old_aside_close not found"
content = content.replace(old_aside_close, new_aside_close, 1)

p.write_text(content, encoding="utf-8")
print("Updated static/index.html with early width restore and sidebar-resizer handle!")
