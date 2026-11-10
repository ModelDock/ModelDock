with open('core/model_runner.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = "is_image_request = is_explicit_image or is_visual_keyword"
replacement = """is_image_model = any(k in model.lower() for k in ["image", "diffusion", "flux", "lumina"])
        is_visual_scene = any(k in prompt_lower for k in ["photography", "photograph", "wallpaper", "landscape", "portrait", "scenery", "realistic", "cinematic"])
        is_image_request = is_explicit_image or is_visual_keyword or is_image_model or is_visual_scene"""

assert target in text, "target not found"
text = text.replace(target, replacement, 1)

with open('core/model_runner.py', 'w', encoding='utf-8', newline='') as f:
    f.write(text)

print("Updated image model and visual scene detection in core/model_runner.py")
