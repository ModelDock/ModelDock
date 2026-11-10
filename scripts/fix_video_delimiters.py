with open("core/visual_synthesis.py", "r", encoding="utf-8") as f:
    code = f.read()

target = '''    return f\'\'\'<div class="ai-video-card" data-title="{title}">'''
repl = '''    card_html = f\'\'\'<div class="ai-video-card" data-title="{title}">'''

target_end = '''</div>\'\'\''''
repl_end = '''</div>\'\'\'
    return f"<!-- AI_VIDEO_CARD_START -->\\n{card_html}\\n<!-- AI_VIDEO_CARD_END -->"'''

assert target in code, "target not found in core/visual_synthesis.py"
code = code.replace(target, repl, 1)

idx_last_div = code.rfind(target_end)
assert idx_last_div != -1, "target_end not found in core/visual_synthesis.py"
code = code[:idx_last_div] + repl_end + code[idx_last_div + len(target_end):]

with open("core/visual_synthesis.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Updated core/visual_synthesis.py with clean comment delimiters!")
