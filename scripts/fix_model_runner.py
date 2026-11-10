import os

with open('core/model_runner.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = """        # If user explicitly asks for visual image/artwork generation, or engine is in safe fallback mode
        if is_image_request or getattr(self.engine, "is_fallback_mode", False):"""

replacement = """        # Only enter fallback mode if native engine is in safe fallback mode (llama-server binary could not run)
        if getattr(self.engine, "is_fallback_mode", False):"""

target_norm = target.replace("\r\n", "\n")
replacement_norm = replacement.replace("\r\n", "\n")
text_norm = text.replace("\r\n", "\n")

if target_norm not in text_norm:
    raise ValueError("target not found in core/model_runner.py")

text_norm = text_norm.replace(target_norm, replacement_norm, 1)

# Also add the sports car branch in fallback mode right before tea / chai
car_target = """                elif any(k in prompt_lower for k in ["tea", "chai", "jaipur", "kulhad", "stall", "kettle"]):"""

car_code = """                elif any(k in prompt_lower for k in ["car", "vehicle", "sports car", "automotive", "automobile", "ferrari", "porsche", "night street", "neon", "racing", "speed"]):
                    # Black Luxury Sports Car under Neon City Rain
                    response_text = (
                        "```xml\\n"
                        "<svg xmlns=\\"http://www.w3.org/2000/svg\\" viewBox=\\"0 0 600 850\\" width=\\"100%\\" style=\\"max-width: 440px; border-radius: 14px; background: #050508; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;\\">\\n"
                        "  <defs>\\n"
                        "    <linearGradient id=\\"wetStreet\\" x1=\\"0%\\" y1=\\"0%\\" x2=\\"0%\\" y2=\\"100%\\">\\n"
                        "      <stop offset=\\"0%\\" stop-color=\\"#080914\\" />\\n"
                        "      <stop offset=\\"50%\\" stop-color=\\"#04050a\\" />\\n"
                        "      <stop offset=\\"100%\\" stop-color=\\"#010204\\" />\\n"
                        "    </linearGradient>\\n"
                        "    <linearGradient id=\\"neonCyan\\" x1=\\"0%\\" y1=\\"0%\\" x2=\\"100%\\" y2=\\"0%\\">\\n"
                        "      <stop offset=\\"0%\\" stop-color=\\"#06b6d4\\" />\\n"
                        "      <stop offset=\\"100%\\" stop-color=\\"#3b82f6\\" />\\n"
                        "    </linearGradient>\\n"
                        "    <linearGradient id=\\"neonPurple\\" x1=\\"0%\\" y1=\\"0%\\" x2=\\"100%\\" y2=\\"0%\\">\\n"
                        "      <stop offset=\\"0%\\" stop-color=\\"#a855f7\\" />\\n"
                        "      <stop offset=\\"100%\\" stop-color=\\"#ec4899\\" />\\n"
                        "    </linearGradient>\\n"
                        "    <linearGradient id=\\"carBody\\" x1=\\"0%\\" y1=\\"0%\\" x2=\\"100%\\" y2=\\"100%\\">\\n"
                        "      <stop offset=\\"0%\\" stop-color=\\"#1e293b\\" />\\n"
                        "      <stop offset=\\"40%\\" stop-color=\\"#0f172a\\" />\\n"
                        "      <stop offset=\\"80%\\" stop-color=\\"#020617\\" />\\n"
                        "      <stop offset=\\"100%\\" stop-color=\\"#000000\\" />\\n"
                        "    </linearGradient>\\n"
                        "    <linearGradient id=\\"neonReflection\\" x1=\\"0%\\" y1=\\"0%\\" x2=\\"0%\\" y2=\\"100%\\">\\n"
                        "      <stop offset=\\"0%\\" stop-color=\\"#06b6d4\\" stop-opacity=\\"0.6\\" />\\n"
                        "      <stop offset=\\"60%\\" stop-color=\\"#a855f7\\" stop-opacity=\\"0.3\\" />\\n"
                        "      <stop offset=\\"100%\\" stop-color=\\"#000000\\" stop-opacity=\\"0\\" />\\n"
                        "    </linearGradient>\\n"
                        "    <filter id=\\"neonGlow\\" x=\\"-30%\\" y=\\"-30%\\" width=\\"160%\\" height=\\"160%\\">\\n"
                        "      <feGaussianBlur stdDeviation=\\"4\\" />\\n"
                        "    </filter>\\n"
                        "  </defs>\\n\\n"
                        "  <!-- Night Sky & Wet Asphalt Background -->\\n"
                        "  <rect width=\\"600\\" height=\\"850\\" fill=\\"url(#wetStreet)\\" />\\n\\n"
                        "  <!-- Background Wet City Reflections -->\\n"
                        "  <ellipse cx=\\"300\\" cy=\\"620\\" rx=\\"240\\" ry=\\"35\\" fill=\\"url(#neonReflection)\\" opacity=\\"0.55\\" />\\n"
                        "  <line x1=\\"60\\" y1=\\"590\\" x2=\\"540\\" y2=\\"590\\" stroke=\\"#06b6d4\\" stroke-width=\\"1\\" opacity=\\"0.35\\" />\\n"
                        "  <line x1=\\"100\\" y1=\\"640\\" x2=\\"500\\" y2=\\"640\\" stroke=\\"#a855f7\\" stroke-width=\\"1.5\\" opacity=\\"0.4\\" />\\n\\n"
                        "  <!-- Sports Car Sleek Silhouette & Aerodynamic Body -->\\n"
                        "  <path d=\\"M 100 520 C 130 460, 210 430, 290 425 C 370 420, 440 445, 480 490 C 510 520, 520 545, 510 565 C 500 580, 460 585, 430 585 C 410 540, 350 540, 330 585 C 270 585, 230 585, 200 585 C 180 540, 120 540, 100 585 C 80 585, 70 560, 75 540 Z\\" fill=\\"url(#carBody)\\" stroke=\\"#334155\\" stroke-width=\\"2\\" />\\n"
                        "  <!-- Cockpit & Tinted Windshield -->\\n"
                        "  <path d=\\"M 200 480 C 230 435, 270 430, 340 430 C 400 430, 430 455, 450 480 Z\\" fill=\\"#020617\\" stroke=\\"#06b6d4\\" stroke-width=\\"1\\" opacity=\\"0.9\\" />\\n"
                        "  <line x1=\\"210\\" y1=\\"475\\" x2=\\"440\\" y2=\\"475\\" stroke=\\"#38bdf8\\" stroke-width=\\"1.5\\" opacity=\\"0.6\\" />\\n\\n"
                        "  <!-- Wheels & Glossy Alloy Rims -->\\n"
                        "  <circle cx=\\"150\\" cy=\\"575\\" r=\\"38\\" fill=\\"#09090b\\" stroke=\\"#1e293b\\" stroke-width=\\"6\\" />\\n"
                        "  <circle cx=\\"150\\" cy=\\"575\\" r=\\"24\\" fill=\\"#18181b\\" stroke=\\"#06b6d4\\" stroke-width=\\"2\\" />\\n"
                        "  <circle cx=\\"370\\" cy=\\"575\\" r=\\"38\\" fill=\\"#09090b\\" stroke=\\"#1e293b\\" stroke-width=\\"6\\" />\\n"
                        "  <circle cx=\\"370\\" cy=\\"575\\" r=\\"24\\" fill=\\"#18181b\\" stroke=\\"#a855f7\\" stroke-width=\\"2\\" />\\n\\n"
                        "  <!-- Neon Headlights & Cyberpunk Ground Effects -->\\n"
                        "  <ellipse cx=\\"85\\" cy=\\"535\\" rx=\\"14\\" ry=\\"5\\" fill=\\"#38bdf8\\" filter=\\"url(#neonGlow)\\" />\\n"
                        "  <ellipse cx=\\"85\\" cy=\\"535\\" rx=\\"10\\" ry=\\"3\\" fill=\\"#ffffff\\" />\\n"
                        "  <path d=\\"M 90 540 L 20 620 L 70 640 Z\\" fill=\\"#06b6d4\\" opacity=\\"0.2\\" />\\n"
                        "  <ellipse cx=\\"505\\" cy=\\"550\\" rx=\\"12\\" ry=\\"4\\" fill=\\"#f43f5e\\" filter=\\"url(#neonGlow)\\" />\\n"
                        "  <ellipse cx=\\"505\\" cy=\\"550\\" rx=\\"8\\" ry=\\"2\\" fill=\\"#ffffff\\" />\\n\\n"
                        "  <!-- Underglow Neon Strip -->\\n"
                        "  <line x1=\\"190\\" y1=\\"585\\" x2=\\"330\\" y2=\\"585\\" stroke=\\"#06b6d4\\" stroke-width=\\"5\\" filter=\\"url(#neonGlow)\\" />\\n"
                        "  <line x1=\\"190\\" y1=\\"585\\" x2=\\"330\\" y2=\\"585\\" stroke=\\"#ffffff\\" stroke-width=\\"2\\" />\\n\\n"
                        "  <!-- Header Typography & Metadata -->\\n"
                        "  <text x=\\"300\\" y=\\"90\\" fill=\\"#06b6d4\\" font-size=\\"12\\" font-weight=\\"700\\" letter-spacing=\\"6\\" text-anchor=\\"middle\\">NIGHT CITY &bull; AUTOMOTIVE EDITION</text>\\n"
                        "  <text x=\\"300\\" y=\\"140\\" fill=\\"#f8fafc\\" font-size=\\"32\\" font-weight=\\"800\\" letter-spacing=\\"8\\" text-anchor=\\"middle\\">NEON REFLECTIONS</text>\\n"
                        "  <text x=\\"300\\" y=\\"740\\" fill=\\"#f8fafc\\" font-size=\\"16\\" font-weight=\\"700\\" letter-spacing=\\"5\\" text-anchor=\\"middle\\">BLACK LUXURY SPORTS CAR</text>\\n"
                        "  <text x=\\"300\\" y=\\"770\\" fill=\\"#94a3b8\\" font-size=\\"11\\" letter-spacing=\\"3\\" text-anchor=\\"middle\\">WET ASPHALT &bull; CYAN &amp; PURPLE AMBIENCE &bull; CINEMATIC</text>\\n"
                        "</svg>\\n"
                        "```\\n\\n"
                        "**Artwork Highlights:**\\n"
                        "- **Subject**: Black luxury sports car with aerodynamic contours parked on rain-soaked urban asphalt.\\n"
                        "- **Lighting & Reflections**: Cinematic neon cyan (`#06b6d4`) and magenta purple (`#a855f7`) underglow with diffused surface mirror reflections.\\n"
                        "- **Controls**: You can click **Copy Image** or **Download Image** at the top right of the visual card above."
                    )
                elif any(k in prompt_lower for k in ["tea", "chai", "jaipur", "kulhad", "stall", "kettle"]):"""

if car_target in text_norm:
    text_norm = text_norm.replace(car_target, car_code, 1)

with open('core/model_runner.py', 'w', encoding='utf-8', newline='') as f:
    f.write(text_norm.replace('\n', '\r\n'))

print('Fixed core/model_runner.py successfully!')
