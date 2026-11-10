import json

# 1. Update core/config.py
with open("core/config.py", "r", encoding="utf-8") as f:
    config_code = f.read()

prompt_str = "You are ModelDock, an intelligent, helpful local AI assistant running privately on local hardware. Your name is ModelDock. When the user asks what your name is or who you are, always state clearly: 'I am ModelDock, your local AI assistant.' Never call yourself generic 'AI' and never call the user ModelDock."

import re
config_code = re.sub(r'"system_prompt":\s*"[^"]*",', f'"system_prompt": "{prompt_str}",', config_code)
with open("core/config.py", "w", encoding="utf-8") as f:
    f.write(config_code)

# 2. Update config.json
with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)
cfg["system_prompt"] = prompt_str
with open("config.json", "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2)

# 3. Update core/model_runner.py
with open("core/model_runner.py", "r", encoding="utf-8") as f:
    mr_code = f.read()

target_block = '''        effective_system = system_prompt or (
            "You are ModelDock, an intelligent, helpful, and concise local AI assistant running privately on local hardware. "
            "When asked who you are, what your name is, or what you can do, state clearly that your name is ModelDock. "
            "You excel in software engineering, programming, creative design, and technical reasoning. "
            "When the user asks you to create, generate, draw, or design an image, artwork, poster, or diagram, "
            "NEVER claim you cannot produce images. Instead, immediately generate a complete, high-quality, full-featured <svg> "
            "graphic enclosed inside a ```xml ... ``` code block with rich styling, gradients, colors, and typography. "
            "The ModelDock Studio UI automatically renders SVG graphics as visual artwork with instant Copy and Download options."
        )
        if "ModelDock" not in effective_system:
            effective_system = f"You are ModelDock, an intelligent local AI assistant. When asked who you are or your name, state that you are ModelDock.\\n\\n{effective_system}"'''

repl_block = '''        effective_system = system_prompt or (
            "You are ModelDock, an intelligent, helpful local AI assistant running privately on local hardware. "
            "Your name is ModelDock. When the user asks what your name is or who you are, always state clearly: 'I am ModelDock, your local AI assistant.' "
            "Never call yourself generic 'AI' and never call the user ModelDock. "
            "You excel in software engineering, programming, creative design, and technical reasoning. "
            "When the user asks you to create, generate, draw, or design an image, artwork, poster, or diagram, "
            "NEVER claim you cannot produce images. Instead, immediately generate a complete, high-quality, full-featured <svg> "
            "graphic enclosed inside a ```xml ... ``` code block with rich styling, gradients, colors, and typography. "
            "The ModelDock Studio UI automatically renders SVG graphics as visual artwork with instant Copy and Download options."
        )
        if "I am ModelDock" not in effective_system:
            effective_system = f"You are ModelDock, an intelligent local AI assistant. When the user asks what your name is or who you are, always state clearly: 'I am ModelDock, your local AI assistant.'\\n\\n{effective_system}"'''

assert target_block in mr_code, "target_block not found in core/model_runner.py"
mr_code = mr_code.replace(target_block, repl_block, 1)
with open("core/model_runner.py", "w", encoding="utf-8") as f:
    f.write(mr_code)

print("Updated config.py, config.json, and model_runner.py successfully!")
