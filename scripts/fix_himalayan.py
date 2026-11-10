import re

with open('core/model_runner.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Replace the greeting check with word boundaries \b
old_greeting = 'elif any(k in prompt_lower for k in ["hello", "hi", "hey"]):'
new_greeting = 'elif any(re.search(rf"\\b{k}\\b", prompt_lower) for k in ["hello", "hi", "hey", "greetings"]):'

assert old_greeting in text, "old_greeting not found"
text = text.replace(old_greeting, new_greeting, 1)

# 2. Add Himalayan landscape artwork branch right before tea / chai
car_anchor = """                elif any(k in prompt_lower for k in ["tea", "chai", "jaipur", "kulhad", "stall", "kettle"]):"""

landscape_code = """                elif any(k in prompt_lower for k in ["himalayan", "mountain", "landscape", "lake", "alpine", "nature", "scenery", "mist", "forest", "sunrise", "snow", "peaks"]):
                    # Himalayan Sunrise & Alpine Lake Artwork
                    response_text = (
                        "```xml\\n"
                        "<svg xmlns=\\"http://www.w3.org/2000/svg\\" viewBox=\\"0 0 600 850\\" width=\\"100%\\" style=\\"max-width: 440px; border-radius: 14px; background: #070d18; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;\\">\\n"
                        "  <defs>\\n"
                        "    <linearGradient id=\\"skySunrise\\" x1=\\"0%\\" y1=\\"0%\\" x2=\\"0%\\" y2=\\"100%\\">\\n"
                        "      <stop offset=\\"0%\\" stop-color=\\"#1e1b4b\\" />\\n"
                        "      <stop offset=\\"25%\\" stop-color=\\"#312e81\\" />\\n"
                        "      <stop offset=\\"50%\\" stop-color=\\"#701a75\\" />\\n"
                        "      <stop offset=\\"75%\\" stop-color=\\"#c2410c\\" />\\n"
                        "      <stop offset=\\"92%\\" stop-color=\\"#f59e0b\\" />\\n"
                        "      <stop offset=\\"100%\\" stop-color=\\"#fef08a\\" />\\n"
                        "    </linearGradient>\\n"
                        "    <linearGradient id=\\"sunGlow\\" x1=\\"0%\\" y1=\\"0%\\" x2=\\"100%\\" y2=\\"100%\\">\\n"
                        "      <stop offset=\\"0%\\" stop-color=\\"#fde047\\" />\\n"
                        "      <stop offset=\\"100%\\" stop-color=\\"#fb923c\\" />\\n"
                        "    </linearGradient>\\n"
                        "    <linearGradient id=\\"snowPeaks\\" x1=\\"0%\\" y1=\\"0%\\" x2=\\"100%\\" y2=\\"100%\\">\\n"
                        "      <stop offset=\\"0%\\" stop-color=\\"#ffffff\\" />\\n"
                        "      <stop offset=\\"40%\\" stop-color=\\"#f8fafc\\" />\\n"
                        "      <stop offset=\\"70%\\" stop-color=\\"#cbd5e1\\" />\\n"
                        "      <stop offset=\\"100%\\" stop-color=\\"#64748b\\" />\\n"
                        "    </linearGradient>\\n"
                        "    <linearGradient id=\\"mountainRock\\" x1=\\"0%\\" y1=\\"0%\\" x2=\\"0%\\" y2=\\"100%\\">\\n"
                        "      <stop offset=\\"0%\\" stop-color=\\"#334155\\" />\\n"
                        "      <stop offset=\\"60%\\" stop-color=\\"#1e293b\\" />\\n"
                        "      <stop offset=\\"100%\\" stop-color=\\"#0f172a\\" />\\n"
                        "    </linearGradient>\\n"
                        "    <linearGradient id=\\"alpineLake\\" x1=\\"0%\\" y1=\\"0%\\" x2=\\"0%\\" y2=\\"100%\\">\\n"
                        "      <stop offset=\\"0%\\" stop-color=\\"#0f766e\\" />\\n"
                        "      <stop offset=\\"30%\\" stop-color=\\"#0e7490\\" />\\n"
                        "      <stop offset=\\"65%\\" stop-color=\\"#0369a1\\" />\\n"
                        "      <stop offset=\\"100%\\" stop-color=\\"#022c22\\" />\\n"
                        "    </linearGradient>\\n"
                        "    <linearGradient id=\\"pineForest\\" x1=\\"0%\\" y1=\\"0%\\" x2=\\"0%\\" y2=\\"100%\\">\\n"
                        "      <stop offset=\\"0%\\" stop-color=\\"#065f46\\" />\\n"
                        "      <stop offset=\\"100%\\" stop-color=\\"#022c22\\" />\\n"
                        "    </linearGradient>\\n"
                        "    <filter id=\\"mistBlur\\" x=\\"-20%\\" y=\\"-20%\\" width=\\"140%\\" height=\\"140%\\">\\n"
                        "      <feGaussianBlur stdDeviation=\\"4\\" />\\n"
                        "    </filter>\\n"
                        "  </defs>\\n\\n"
                        "  <!-- Himalayan Sunrise Sky -->\\n"
                        "  <rect width=\\"600\\" height=\\"850\\" fill=\\"url(#skySunrise)\\" />\\n\\n"
                        "  <!-- Golden Rising Sun Orb -->\\n"
                        "  <circle cx=\\"300\\" cy=\\"280\\" r=\\"75\\" fill=\\"url(#sunGlow)\\" opacity=\\"0.95\\" />\\n"
                        "  <circle cx=\\"300\\" cy=\\"280\\" r=\\"110\\" fill=\\"#fef08a\\" opacity=\\"0.2\\" />\\n\\n"
                        "  <!-- Background Distant Mountain Ridges -->\\n"
                        "  <polygon points=\\"0,420 140,240 280,380 430,220 600,430 600,600 0,600\\" fill=\\"#1e1b4b\\" opacity=\\"0.6\\" />\\n\\n"
                        "  <!-- Grand Himalayan Snow-Capped Mountain Peak (Center) -->\\n"
                        "  <polygon points=\\"120,530 300,190 480,530\\" fill=\\"url(#mountainRock)\\" />\\n"
                        "  <!-- Snow Cap Glaciers on Summit -->\\n"
                        "  <polygon points=\\"300,190 240,290 280,310 300,280 320,310 360,290\\" fill=\\"url(#snowPeaks)\\" />\\n"
                        "  <polygon points=\\"300,190 270,250 300,270 330,250\\" fill=\\"#ffffff\\" opacity=\\"0.95\\" />\\n\\n"
                        "  <!-- Flanking Jagged Ridges -->\\n"
                        "  <polygon points=\\"0,530 110,310 240,510\\" fill=\\"#1e293b\\" />\\n"
                        "  <polygon points=\\"110,310 80,380 110,390 140,380\\" fill=\\"url(#snowPeaks)\\" />\\n"
                        "  <polygon points=\\"360,510 490,290 600,530\\" fill=\\"#1e293b\\" />\\n"
                        "  <polygon points=\\"490,290 460,360 490,370 520,360\\" fill=\\"url(#snowPeaks)\\" />\\n\\n"
                        "  <!-- Soft Morning Mountain Mist -->\\n"
                        "  <ellipse cx=\\"300\\" cy=\\"520\\" rx=\\"280\\" ry=\\"35\\" fill=\\"#f1f5f9\\" opacity=\\"0.35\\" filter=\\"url(#mistBlur)\\" />\\n"
                        "  <ellipse cx=\\"200\\" cy=\\"500\\" rx=\\"160\\" ry=\\"25\\" fill=\\"#fed7aa\\" opacity=\\"0.25\\" filter=\\"url(#mistBlur)\\" />\\n\\n"
                        "  <!-- Lush Alpine Pine Forest Shoreline -->\\n"
                        "  <polygon points=\\"0,560 600,560 600,610 0,610\\" fill=\\"url(#pineForest)\\" />\\n"
                        "  <!-- Pine Tree Silhouettes -->\\n"
                        "  <polygon points=\\"40,560 55,510 70,560\\" fill=\\"#022c22\\" />\\n"
                        "  <polygon points=\\"60,560 75,500 90,560\\" fill=\\"#064e3b\\" />\\n"
                        "  <polygon points=\\"80,560 95,515 110,560\\" fill=\\"#022c22\\" />\\n"
                        "  <polygon points=\\"180,560 195,505 210,560\\" fill=\\"#064e3b\\" />\\n"
                        "  <polygon points=\\"200,560 215,495 230,560\\" fill=\\"#022c22\\" />\\n"
                        "  <polygon points=\\"380,560 395,500 410,560\\" fill=\\"#022c22\\" />\\n"
                        "  <polygon points=\\"400,560 415,490 430,560\\" fill=\\"#064e3b\\" />\\n"
                        "  <polygon points=\\"500,560 515,510 530,560\\" fill=\\"#022c22\\" />\\n"
                        "  <polygon points=\\"520,560 535,495 550,560\\" fill=\\"#064e3b\\" />\\n\\n"
                        "  <!-- Crystal-Clear Alpine Lake with Inverted Peak Reflection -->\\n"
                        "  <rect x=\\"0\\" y=\\"590\\" width=\\"600\\" height=\\"260\\" fill=\\"url(#alpineLake)\\" />\\n"
                        "  <!-- Mirror Reflection of Himalayan Peaks in Water -->\\n"
                        "  <polygon points=\\"160,590 300,750 440,590\\" fill=\\"#0f172a\\" opacity=\\"0.45\\" />\\n"
                        "  <polygon points=\\"260,710 300,750 340,710\\" fill=\\"#e2e8f0\\" opacity=\\"0.35\\" />\\n"
                        "  <!-- Golden Sunrise Water Shimmer Lines -->\\n"
                        "  <line x1=\\"220\\" y1=\\"620\\" x2=\\"380\\" y2=\\"620\\" stroke=\\"#fde047\\" stroke-width=\\"1.5\\" opacity=\\"0.6\\" />\\n"
                        "  <line x1=\\"180\\" y1=\\"650\\" x2=\\"420\\" y2=\\"650\\" stroke=\\"#fb923c\\" stroke-width=\\"1.2\\" opacity=\\"0.5\\" />\\n"
                        "  <line x1=\\"140\\" y1=\\"690\\" x2=\\"460\\" y2=\\"690\\" stroke=\\"#38bdf8\\" stroke-width=\\"1\\" opacity=\\"0.4\\" />\\n"
                        "  <line x1=\\"80\\" y1=\\"730\\" x2=\\"520\\" y2=\\"730\\" stroke=\\"#2dd4bf\\" stroke-width=\\"0.8\\" opacity=\\"0.35\\" />\\n\\n"
                        "  <!-- Editorial Typography Header -->\\n"
                        "  <text x=\\"300\\" y=\\"78\\" fill=\\"#fde047\\" font-size=\\"11\\" font-weight=\\"700\\" letter-spacing=\\"6\\" text-anchor=\\"middle\\">EXPEDITION &bull; ALPINE SERIES</text>\\n"
                        "  <text x=\\"300\\" y=\\"128\\" fill=\\"#ffffff\\" font-size=\\"32\\" font-weight=\\"800\\" letter-spacing=\\"7\\" text-anchor=\\"middle\\">HIMALAYAN SUNRISE</text>\\n"
                        "  <text x=\\"300\\" y=\\"790\\" fill=\\"#f8fafc\\" font-size=\\"14\\" font-weight=\\"700\\" letter-spacing=\\"5\\" text-anchor=\\"middle\\">CRYSTAL ALPINE LAKE REFLECTION</text>\\n"
                        "  <text x=\\"300\\" y=\\"815\\" fill=\\"#94a3b8\\" font-size=\\"10\\" letter-spacing=\\"3\\" text-anchor=\\"middle\\">SNOW PEAKS &bull; MORNING MIST &bull; GOLDEN DAWN</text>\\n"
                        "</svg>\\n"
                        "```\\n\\n"
                        "**Artwork Highlights:**\\n"
                        "- **Subject**: Towering snow-capped Himalayan summits illuminated by the first rays of golden dawn.\\n"
                        "- **Atmosphere & Water**: Crystal-clear alpine lake mirroring the peaks, framed by deep emerald pine forests and soft morning mist.\\n"
                        "- **Controls**: You can click **Copy Image** or **Download Image** at the top right of the visual card above."
                    )
                elif any(k in prompt_lower for k in ["tea", "chai", "jaipur", "kulhad", "stall", "kettle"]):"""

assert car_anchor in text, "car_anchor not found"
text = text.replace(car_anchor, landscape_code, 1)

with open('core/model_runner.py', 'w', encoding='utf-8', newline='') as f:
    f.write(text.replace('\n', '\r\n'))

print("Updated core/model_runner.py with landscape artwork and word-boundary greeting check!")
