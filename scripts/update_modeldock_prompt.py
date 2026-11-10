with open('core/model_runner.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = '''        effective_system = system_prompt or (
            "You are ModelDock Studio Assistant, a world-class coding and AI assistant running privately on local hardware. "
            "You excel in software engineering, programming, creative design, and technical reasoning. "
            "When the user asks you to create, generate, draw, or design an image, artwork, poster, or diagram, "
            "NEVER claim you cannot produce images. Instead, immediately generate a complete, high-quality, full-featured <svg> "
            "graphic enclosed inside a ```xml ... ``` code block with rich styling, gradients, colors, and typography. "
            "The ModelDock Studio UI automatically renders SVG graphics as visual artwork with instant Copy and Download options."
        )'''

repl = '''        effective_system = system_prompt or (
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

assert target in text, 'target not in text'
text = text.replace(target, repl, 1)

with open('core/model_runner.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated core/model_runner.py successfully')
