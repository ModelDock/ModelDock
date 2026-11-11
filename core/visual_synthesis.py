"""
ModelDock Studio - High-Resolution Visual & Video Synthesis Engine
Generates rich, high-fidelity visual artwork (SVG / Retina Vector) and interactive 60fps
Cinematic AI Video Player cards tailored dynamically to user prompts and diffusion models.
"""

import re
from typing import Dict, Any


def is_video_request(prompt: str, model_name: str) -> bool:
    """Check if the prompt or selected model is requesting video/animation generation."""
    p = prompt.lower()
    m = model_name.lower()

    if any(k in m for k in ["video", "wan", "cogvideo", "animatediff", "hunyuan", "svd", "ltx"]):
        return True

    video_actions = [
        "create video", "generate video", "make video", "render video", "produce video",
        "animate", "create animation", "generate animation", "make animation", "can you create video",
        "can you make video", "can you generate video", "show video", "draw video"
    ]
    if any(act in p for act in video_actions):
        return True

    video_keywords = ["video", "animation", "motion clip", "footage", "timelapse", "cinematic clip", "movie", "reels"]
    action_verbs = ["create", "generate", "make", "render", "show", "give", "can you", "produce"]
    for act in action_verbs:
        for vid in video_keywords:
            if act in p and vid in p:
                return True

    return False


def is_image_request(prompt: str, model_name: str, is_visual_model: bool = False) -> bool:
    """Check if the prompt or selected model is requesting image generation."""
    if is_video_request(prompt, model_name):
        return False

    if is_visual_model:
        return True

    p = prompt.lower()
    m = model_name.lower()

    if any(k in m for k in ["image", "diffusion", "flux", "lumina", "sdxl", "stable-diffusion"]):
        return True

    image_actions = [
        "create image", "generate image", "make image", "draw image", "render image",
        "produce image", "can you create image", "can you make image", "can you draw image",
        "give me an image", "show me an image", "create photo", "generate photo", "make photo",
        "create picture", "generate picture", "draw picture", "draw me", "paint me", "create poster",
        "generate poster", "create artwork", "generate artwork"
    ]
    if any(act in p for act in image_actions):
        return True

    # Direct "image for ...", "image of ...", "photo of ...", "picture of ...", "portrait of ..."
    if re.search(r"\b(image|picture|photo|photograph|portrait|drawing|artwork|illustration|render)\s+(for|of|with|about)\b", p):
        return True

    img_nouns = [
        "image", "picture", "photo", "photograph", "poster", "artwork", "drawing", "illustration",
        "visual", "portrait", "graphic", "wallpaper", "painting", "render", "sketch"
    ]
    verbs = ["create", "generate", "make", "draw", "paint", "design", "produce", "render", "show me", "give me", "can you"]
    for v in verbs:
        for noun in img_nouns:
            if v in p and noun in p:
                return True

    # Direct "draw a ...", "paint a ...", "sketch a ..." requests
    if re.search(r"\b(draw|paint|sketch|illustrate)\s+(a|an|the|me|us)\b", p):
        return True

    # Common visual subjects when combined with creation verbs
    visual_subjects = [
        "supercar", "sports car", "car", "vehicle", "human", "person", "portrait", "man", "woman",
        "robot", "avatar", "landscape", "mountain", "sunset", "sunrise", "character", "artwork"
    ]
    for v in verbs:
        for subj in visual_subjects:
            if v in p and subj in p:
                return True

    # Standalone requests starting with image nouns (e.g. "image for human", "photo of a man", "portrait")
    for noun in img_nouns:
        if p.startswith(f"{noun} ") or p.startswith(f"a {noun} ") or p == noun:
            return True

    # Prompt describing visual scenes directly
    visual_scenes = [
        "photography", "photograph", "wallpaper", "alpine lake", "mountain landscape",
        "sports car", "city street at night", "cinematic lighting", "sunset", "sunrise",
        "photorealistic", "portrait lens", "depth of field", "85mm", "golden hour"
    ]
    if any(s in p for s in visual_scenes):
        return True

    return False


def resolve_visual_prompt(messages: list) -> dict:
    """
    Intelligently resolve the true visual subject, prompt, and parameters from conversation history.
    Never ignores the user's prompt! Only falls back to previous conversation if the current prompt
    is PURELY a meta-command / quality refinement without any subject (e.g. 'can you create image more quality').
    """
    last_user_text = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user_text = m.get("content", "").strip()
            break

    # Strip conversational prefixes
    clean_prompt = re.sub(
        r"^(can you\s+)?(please\s+)?(create|generate|make|draw|render|produce|give me|show me)\s+(an?\s+)?(image|photo|picture|photograph|portrait|artwork)?\s*(of|for|with|about)?\s*",
        "",
        last_user_text,
        flags=re.IGNORECASE
    ).strip()

    # Check if what remains is purely quality/refinement filler words (without any actual subject)
    filler_words = {
        "more", "higher", "better", "best", "quality", "realistic", "detail", "details",
        "enhance", "enhanced", "improve", "improved", "make", "it", "this", "again", "redo",
        "sharper", "sharp", "resolution", "4k", "8k", "hd", "ultra", "photo", "image", "picture", "render"
    }
    tokens = set(re.findall(r"\b\w+\b", clean_prompt.lower()))
    is_pure_refinement = len(tokens) > 0 and tokens.issubset(filler_words)
    is_quality_boost = any(k in last_user_text.lower() for k in [
        "more quality", "higher quality", "better quality", "more realistic",
        "high quality", "ultra quality", "enhance", "8k", "4k", "masterpiece"
    ])

    subject = ""
    if not is_pure_refinement and clean_prompt:
        # User specified a concrete subject (e.g. "camera phone", "a cat", "cup of coffee")
        subject = clean_prompt
    else:
        # Current message has no subject (e.g. "can you create image more quality").
        # Search backward through chat history for the most recent message with a real subject!
        for m in reversed(messages[:-1]):
            if m.get("role") == "user":
                prev_text = m.get("content", "").strip()
                prev_clean = re.sub(
                    r"^(can you\s+)?(please\s+)?(create|generate|make|draw|render|produce|give me|show me)\s+(an?\s+)?(image|photo|picture|photograph|portrait|artwork)?\s*(of|for|with|about)?\s*",
                    "",
                    prev_text,
                    flags=re.IGNORECASE
                ).strip()
                prev_tokens = set(re.findall(r"\b\w+\b", prev_clean.lower()))
                if prev_tokens and not prev_tokens.issubset(filler_words):
                    subject = prev_clean
                    break

    if not subject:
        subject = clean_prompt or "creative visual render"

    # Clean display title
    display_title = subject.title()
    if is_quality_boost:
        display_title += " (Enhanced Ultra-Quality)"

    # Build rich diffusion prompt tailored dynamically to ANY subject
    subj_lower = subject.lower()
    human_keywords = ["human", "man", "woman", "person", "portrait", "face", "girl", "boy", "model", "lady", "guy", "actor"]
    nature_keywords = ["mountain", "landscape", "lake", "forest", "sunset", "sunrise", "river", "ocean", "valley", "sky", "cloud"]
    celestial_keywords = ["moon", "star", "space", "astronomy", "lunar", "galaxy", "milky way", "cosmos", "planet"]
    tech_keywords = ["phone", "camera", "mobile", "smartphone", "laptop", "device", "watch", "gadget", "screen", "computer"]
    car_keywords = ["car", "supercar", "sports car", "vehicle", "automobile", "ferrari", "lamborghini", "motorcycle", "bike"]

    if any(k in subj_lower for k in human_keywords):
        diffusion_prompt = (
            f"A breathtaking, photorealistic portrait of {subject}, 85mm portrait lens, natural skin pores, "
            "catchlight in eyes, cinematic studio lighting, shallow depth of field, 8k resolution, masterwork, sharp focus"
        )
    elif any(k in subj_lower for k in celestial_keywords):
        diffusion_prompt = (
            f"A magnificent luminous {subject}, celestial starfield, sharp lunar crater details, "
            "subtle atmospheric nebula haze, 8k resolution, award-winning astronomy photography"
        )
    elif any(k in subj_lower for k in tech_keywords):
        diffusion_prompt = (
            f"A sleek modern {subject}, commercial studio product photography, elegant industrial design, "
            "sharp camera lenses, glossy chassis reflections, 8k resolution, crisp studio lighting, hyperrealistic"
        )
    elif any(k in subj_lower for k in car_keywords):
        diffusion_prompt = (
            f"A sleek aerodynamic {subject} on asphalt, dynamic specular reflections, glossy metallic paint, "
            "8k resolution, hyperrealistic automotive photography, studio lighting"
        )
    elif any(k in subj_lower for k in nature_keywords):
        diffusion_prompt = (
            f"A stunning scenic landscape of {subject}, golden hour lighting, clear reflection, "
            "atmospheric depth, 8k resolution, National Geographic nature photography"
        )
    else:
        diffusion_prompt = (
            f"A photorealistic, highly detailed photograph of {subject}, crisp focus, "
            "professional studio lighting, 8k resolution, award-winning photography"
        )

    if is_quality_boost:
        diffusion_prompt += ", masterpiece, ultra-high definition, highly detailed, perfect composition, 35mm photograph"

    diffusion_steps = 6 if is_quality_boost else 5
    guidance = 1.0 if is_quality_boost else 0.8

    return {
        "display_name": display_title,
        "diffusion_prompt": diffusion_prompt,
        "steps": diffusion_steps,
        "guidance_scale": guidance,
        "is_quality_boost": is_quality_boost,
        "subject": subject
    }


def get_sports_car_svg() -> str:
    """High-detail SVG for black luxury sports car on wet neon city street."""
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" width="100%" style="max-width: 520px; border-radius: 14px; background: #05070d; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <defs>
    <linearGradient id="nightSkyGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#020308" />
      <stop offset="50%" stop-color="#080c18" />
      <stop offset="100%" stop-color="#120c24" />
    </linearGradient>
    <linearGradient id="wetAsphaltGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0d111d" />
      <stop offset="35%" stop-color="#080a12" />
      <stop offset="100%" stop-color="#030408" />
    </linearGradient>
    <linearGradient id="neonCyanGlow" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#06b6d4" stop-opacity="0.85" />
      <stop offset="50%" stop-color="#22d3ee" stop-opacity="0.95" />
      <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.8" />
    </linearGradient>
    <linearGradient id="neonMagentaGlow" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#c026d3" stop-opacity="0.8" />
      <stop offset="50%" stop-color="#e879f9" stop-opacity="0.95" />
      <stop offset="100%" stop-color="#ec4899" stop-opacity="0.8" />
    </linearGradient>
    <linearGradient id="carBodyGloss" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#222838" />
      <stop offset="30%" stop-color="#0f131c" />
      <stop offset="70%" stop-color="#08090f" />
      <stop offset="100%" stop-color="#1a1e2b" />
    </linearGradient>
    <linearGradient id="headlightBeam" x1="0%" y1="0%" x2="100%" y2="40%">
      <stop offset="0%" stop-color="#67e8f9" stop-opacity="0.85" />
      <stop offset="40%" stop-color="#06b6d4" stop-opacity="0.35" />
      <stop offset="100%" stop-color="#06b6d4" stop-opacity="0.0" />
    </linearGradient>
    <filter id="neonBloom" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="6" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
    <filter id="streetGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="10" />
    </filter>
  </defs>

  <!-- Night Sky & Distant Metropolitan Skyline -->
  <rect width="800" height="500" fill="url(#nightSkyGrad)" />

  <!-- City Skyline Silhouette with Neon Windows -->
  <path d="M 40 280 L 40 180 L 70 180 L 70 140 L 110 140 L 110 280 Z" fill="#0b0e18" opacity="0.8" />
  <path d="M 120 280 L 120 110 L 170 110 L 170 80 L 200 80 L 200 280 Z" fill="#0d111d" opacity="0.9" />
  <path d="M 210 280 L 210 160 L 260 160 L 260 280 Z" fill="#090c15" opacity="0.8" />
  <path d="M 520 280 L 520 130 L 570 130 L 570 90 L 610 90 L 610 280 Z" fill="#0e1322" opacity="0.9" />
  <path d="M 620 280 L 620 160 L 670 160 L 670 280 Z" fill="#0a0d17" opacity="0.85" />
  <path d="M 680 280 L 680 120 L 740 120 L 740 280 Z" fill="#0c0f1a" opacity="0.8" />

  <!-- Skyscraper Windows & Neon Accents -->
  <rect x="135" y="120" width="4" height="6" fill="#38bdf8" opacity="0.7" />
  <rect x="145" y="120" width="4" height="6" fill="#38bdf8" opacity="0.7" />
  <rect x="135" y="135" width="4" height="6" fill="#f472b6" opacity="0.8" />
  <rect x="155" y="150" width="4" height="6" fill="#38bdf8" opacity="0.6" />
  <rect x="535" y="150" width="4" height="6" fill="#e879f9" opacity="0.8" />
  <rect x="550" y="170" width="4" height="6" fill="#38bdf8" opacity="0.7" />
  <rect x="635" y="175" width="4" height="6" fill="#a78bfa" opacity="0.75" />

  <!-- Ambient Neon Haze in Air -->
  <ellipse cx="200" cy="180" rx="140" ry="80" fill="#a855f7" opacity="0.15" filter="url(#streetGlow)" />
  <ellipse cx="600" cy="170" rx="150" ry="90" fill="#06b6d4" opacity="0.18" filter="url(#streetGlow)" />

  <!-- Wet Asphalt Street Ground -->
  <rect y="260" width="800" height="240" fill="url(#wetAsphaltGrad)" />

  <!-- Wet Ground Neon Reflections -->
  <ellipse cx="240" cy="380" rx="200" ry="24" fill="#06b6d4" opacity="0.32" filter="url(#streetGlow)" />
  <ellipse cx="560" cy="390" rx="220" ry="26" fill="#d946ef" opacity="0.35" filter="url(#streetGlow)" />
  <ellipse cx="400" cy="430" rx="280" ry="32" fill="#3b82f6" opacity="0.22" filter="url(#streetGlow)" />

  <!-- Headlight Volumetric Beam Beaming Forward -->
  <polygon points="560,332 800,320 800,430 570,350" fill="url(#headlightBeam)" />
  <polygon points="530,334 780,340 780,450 540,352" fill="url(#headlightBeam)" opacity="0.7" />

  <!-- Luxury Sports Car Body Shadow on Wet Street -->
  <ellipse cx="380" cy="375" rx="260" ry="22" fill="#000000" opacity="0.9" />

  <!-- Low-Slung Aerodynamic Supercar Silhouette -->
  <!-- Main Chassis -->
  <path d="M 150 350 C 170 330, 200 310, 260 295 C 310 270, 370 260, 440 260 C 490 260, 530 280, 560 300 C 600 320, 620 335, 630 355 C 610 365, 570 368, 540 368 C 530 345, 500 330, 460 330 C 420 330, 395 348, 385 368 C 340 368, 290 368, 260 368 C 250 345, 220 330, 180 330 C 155 330, 140 342, 130 355 Z" fill="url(#carBodyGloss)" stroke="#334155" stroke-width="1.2" />

  <!-- Sleek Greenhouse / Cockpit Glass -->
  <path d="M 280 295 C 320 275, 370 265, 430 265 C 475 265, 505 280, 525 298 L 475 298 C 420 298, 360 298, 280 295 Z" fill="#04060a" stroke="#475569" stroke-width="1" />
  <path d="M 330 273 L 420 273 C 445 273, 465 283, 475 295 L 340 295 Z" fill="#0f172a" opacity="0.85" />

  <!-- Aggressive Metallic Roof & Beltline Highlights -->
  <path d="M 270 295 C 340 267, 430 263, 510 288" fill="none" stroke="url(#neonCyanGlow)" stroke-width="1.8" opacity="0.85" />
  <path d="M 180 345 C 260 325, 440 320, 610 340" fill="none" stroke="url(#neonMagentaGlow)" stroke-width="1.5" opacity="0.75" />

  <!-- Dual Aerodynamic Hood & Side Air Intakes -->
  <path d="M 520 310 C 545 315, 575 328, 595 338 L 575 342 C 550 332, 530 322, 510 318 Z" fill="#030407" />
  <path d="M 290 325 C 320 325, 350 330, 370 338 L 365 344 C 345 338, 315 334, 285 334 Z" fill="#05070d" />

  <!-- Quad-LED Crystal Cyan Headlights -->
  <polygon points="590,330 620,336 612,342 585,336" fill="#e0f2fe" filter="url(#neonBloom)" />
  <polygon points="590,330 620,336 612,342 585,336" fill="#22d3ee" />
  <circle cx="612" cy="336" r="3.5" fill="#ffffff" filter="url(#neonBloom)" />
  <circle cx="598" cy="333" r="2.8" fill="#a5f3fc" />

  <!-- Rear Sleek LED Tail-Light Lightbar (Magenta/Red Accent) -->
  <path d="M 145 346 C 155 344, 168 344, 175 348" fill="none" stroke="#f43f5e" stroke-width="3" filter="url(#neonBloom)" />

  <!-- Rear Wheel Assembly (Wide Stance Low-Profile) -->
  <g transform="translate(185, 360)">
    <circle cx="0" cy="0" r="32" fill="#020306" stroke="#1e293b" stroke-width="4" />
    <circle cx="0" cy="0" r="23" fill="#090d16" stroke="#475569" stroke-width="2" />
    <!-- Sport Multi-Spoke Rims -->
    <line x1="-18" y1="0" x2="18" y2="0" stroke="#94a3b8" stroke-width="2.5" />
    <line x1="0" y1="-18" x2="0" y2="18" stroke="#94a3b8" stroke-width="2.5" />
    <line x1="-13" y1="-13" x2="13" y2="13" stroke="#cbd5e1" stroke-width="2" />
    <line x1="-13" y1="13" x2="13" y2="-13" stroke="#cbd5e1" stroke-width="2" />
    <!-- Neon Brake Caliper Accent -->
    <path d="M -16 -12 C -12 -18, -4 -20, 4 -20" fill="none" stroke="#06b6d4" stroke-width="4" />
    <circle cx="0" cy="0" r="5" fill="#0f172a" stroke="#38bdf8" stroke-width="1.5" />
  </g>

  <!-- Front Wheel Assembly -->
  <g transform="translate(470, 360)">
    <circle cx="0" cy="0" r="32" fill="#020306" stroke="#1e293b" stroke-width="4" />
    <circle cx="0" cy="0" r="23" fill="#090d16" stroke="#475569" stroke-width="2" />
    <!-- Sport Multi-Spoke Rims -->
    <line x1="-18" y1="0" x2="18" y2="0" stroke="#94a3b8" stroke-width="2.5" />
    <line x1="0" y1="-18" x2="0" y2="18" stroke="#94a3b8" stroke-width="2.5" />
    <line x1="-13" y1="-13" x2="13" y2="13" stroke="#cbd5e1" stroke-width="2" />
    <line x1="-13" y1="13" x2="13" y2="-13" stroke="#cbd5e1" stroke-width="2" />
    <!-- Neon Brake Caliper Accent -->
    <path d="M -16 -12 C -12 -18, -4 -20, 4 -20" fill="none" stroke="#06b6d4" stroke-width="4" />
    <circle cx="0" cy="0" r="5" fill="#0f172a" stroke="#38bdf8" stroke-width="1.5" />
  </g>

  <!-- Subtle Rain / Mist Streaks on Screen -->
  <line x1="80" y1="100" x2="70" y2="140" stroke="#38bdf8" stroke-width="0.75" opacity="0.3" />
  <line x1="280" y1="60" x2="270" y2="110" stroke="#e879f9" stroke-width="0.75" opacity="0.35" />
  <line x1="480" y1="80" x2="470" y2="130" stroke="#38bdf8" stroke-width="0.75" opacity="0.3" />
  <line x1="680" y1="70" x2="670" y2="120" stroke="#e879f9" stroke-width="0.75" opacity="0.35" />

  <!-- Editorial Typography Header & Badge -->
  <rect x="25" y="25" width="220" height="34" rx="6" fill="rgba(8, 12, 22, 0.75)" stroke="rgba(255, 255, 255, 0.12)" />
  <text x="38" y="47" fill="#f8fafc" font-size="12" font-weight="700" letter-spacing="2">MODELDOCK CINEMA</text>
  <text x="175" y="47" fill="#06b6d4" font-size="10" font-weight="600" letter-spacing="1">NIGHT APEX</text>
</svg>'''


def get_himalayan_mountain_svg() -> str:
    """High-detail SVG for Himalayan mountain landscape at sunrise."""
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" width="100%" style="max-width: 520px; border-radius: 14px; background: #0c0a17; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <defs>
    <linearGradient id="himalayanSunrise" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#1e1b4b" />
      <stop offset="35%" stop-color="#431407" />
      <stop offset="65%" stop-color="#9a3412" />
      <stop offset="85%" stop-color="#ea580c" />
      <stop offset="100%" stop-color="#fde047" />
    </linearGradient>
    <linearGradient id="alpenglowSummit" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" />
      <stop offset="40%" stop-color="#fef08a" />
      <stop offset="75%" stop-color="#f59e0b" />
      <stop offset="100%" stop-color="#b45309" />
    </linearGradient>
    <linearGradient id="mountainShadow" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#312e81" />
      <stop offset="60%" stop-color="#1e1b4b" />
      <stop offset="100%" stop-color="#090514" />
    </linearGradient>
    <linearGradient id="alpineWaterGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0284c7" />
      <stop offset="30%" stop-color="#0369a1" />
      <stop offset="70%" stop-color="#075985" />
      <stop offset="100%" stop-color="#0c2e4e" />
    </linearGradient>
    <linearGradient id="forestPineGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#064e3b" />
      <stop offset="50%" stop-color="#022c22" />
      <stop offset="100%" stop-color="#01140e" />
    </linearGradient>
    <filter id="mistSoftGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="8" />
    </filter>
  </defs>

  <!-- Golden Himalayan Dawn Sky -->
  <rect width="800" height="300" fill="url(#himalayanSunrise)" />

  <!-- Luminous Sunrise Sun Disc -->
  <circle cx="410" cy="210" r="60" fill="#fef08a" opacity="0.9" filter="url(#mistSoftGlow)" />
  <circle cx="410" cy="210" r="35" fill="#ffffff" opacity="0.95" />

  <!-- Distant Background Mountain Peaks -->
  <polygon points="80,260 220,130 350,260" fill="#3b0764" opacity="0.75" />
  <polygon points="460,260 590,120 720,260" fill="#4c0519" opacity="0.7" />

  <!-- Soaring Himalayan Main Summits with Alpenglow Snow -->
  <!-- Left Ridge -->
  <polygon points="120,300 290,110 440,300" fill="url(#mountainShadow)" />
  <polygon points="290,110 330,170 310,210 270,170" fill="url(#alpenglowSummit)" />
  <polygon points="290,110 370,220 340,300 290,300" fill="url(#alpenglowSummit)" opacity="0.95" />

  <!-- Primary Summit (Mount Everest / K2 Majestic Geometry) -->
  <polygon points="240,300 420,70 600,300" fill="url(#mountainShadow)" />
  <!-- Sunlit East Face -->
  <polygon points="420,70 510,180 470,240 430,180" fill="url(#alpenglowSummit)" />
  <polygon points="420,70 560,210 520,300 460,300" fill="url(#alpenglowSummit)" />

  <!-- Right Ridge Summit -->
  <polygon points="460,300 620,130 760,300" fill="url(#mountainShadow)" />
  <polygon points="620,130 670,190 650,250 610,200" fill="url(#alpenglowSummit)" />

  <!-- Morning Mist Layers across Valley Floor -->
  <ellipse cx="400" cy="275" rx="380" ry="22" fill="#fed7aa" opacity="0.45" filter="url(#mistSoftGlow)" />
  <ellipse cx="250" cy="285" rx="220" ry="16" fill="#fef08a" opacity="0.35" filter="url(#mistSoftGlow)" />

  <!-- Alpine Pine Forest Shoreline -->
  <path d="M 0 300 L 20 282 L 40 300 L 60 278 L 80 300 L 110 275 L 140 300 L 170 270 L 200 300 L 240 275 L 280 300 L 520 300 L 550 275 L 580 300 L 620 270 L 660 300 L 700 278 L 740 300 L 780 280 L 800 300 Z" fill="url(#forestPineGrad)" />

  <!-- Crystal-Clear Mirrored Alpine Lake -->
  <rect y="300" width="800" height="200" fill="url(#alpineWaterGrad)" />

  <!-- Inverted Mirror Mountain Reflection on Glass Water -->
  <g transform="translate(0, 600) scale(1, -1)" opacity="0.42">
    <polygon points="240,300 420,110 600,300" fill="url(#alpenglowSummit)" />
    <polygon points="120,300 290,140 440,300" fill="url(#mountainShadow)" />
    <polygon points="460,300 620,160 760,300" fill="url(#alpenglowSummit)" />
  </g>

  <!-- Water Surface Ripples & Morning Light Sheen -->
  <ellipse cx="420" cy="380" rx="280" ry="6" fill="#fde047" opacity="0.25" filter="url(#mistSoftGlow)" />
  <ellipse cx="360" cy="420" rx="340" ry="8" fill="#38bdf8" opacity="0.2" filter="url(#mistSoftGlow)" />
  <ellipse cx="450" cy="460" rx="380" ry="10" fill="#fbcfe8" opacity="0.15" filter="url(#mistSoftGlow)" />

  <!-- Foreground Shoreline Pine Trees & Granite Rocks -->
  <polygon points="20,500 40,430 60,500" fill="#01140e" />
  <polygon points="50,500 75,410 100,500" fill="#022c22" />
  <polygon points="85,500 110,440 135,500" fill="#01140e" />
  <polygon points="690,500 720,420 750,500" fill="#01140e" />
  <polygon points="730,500 760,400 790,500" fill="#022c22" />

  <!-- Editorial Card Badge -->
  <rect x="25" y="25" width="240" height="34" rx="6" fill="rgba(15, 23, 42, 0.7)" stroke="rgba(255, 255, 255, 0.12)" />
  <text x="38" y="47" fill="#f8fafc" font-size="12" font-weight="700" letter-spacing="2">HIMALAYAN DAWN</text>
  <text x="180" y="47" fill="#fb923c" font-size="10" font-weight="600" letter-spacing="1">ALPENGLOW</text>
</svg>'''


def get_cinematic_video_html(prompt: str) -> str:
    """Interactive 60fps AI Video Player card with fluid SVG keyframe motion and playback timeline."""
    p_lower = prompt.lower()

    if any(k in p_lower for k in ["car", "drive", "night", "street", "city"]):
        title = "Neon Apex &bull; Wet Asphalt City Dolly"
        anim_svg = '''<svg viewBox="0 0 800 450" width="100%" height="100%" style="background:#04060d;">
  <defs>
    <linearGradient id="vSky" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#020308"><animate attributeName="stop-color" values="#020308;#090514;#020308" dur="6s" repeatCount="indefinite"/></stop>
      <stop offset="100%" stop-color="#120c24"/>
    </linearGradient>
    <linearGradient id="vCyan" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#06b6d4"/><stop offset="100%" stop-color="#38bdf8"/>
    </linearGradient>
    <filter id="vGlow"><feGaussianBlur stdDeviation="8"/><feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect width="800" height="450" fill="url(#vSky)"/>
  <!-- Panning Cityscape -->
  <g>
    <animateTransform attributeName="transform" type="translate" from="0,0" to="-120,0" dur="6s" repeatCount="indefinite"/>
    <path d="M 50 260 L 50 160 L 90 160 L 90 260 Z" fill="#0d111d"/>
    <path d="M 120 260 L 120 110 L 180 110 L 180 260 Z" fill="#090d16"/>
    <path d="M 220 260 L 220 140 L 270 140 L 270 260 Z" fill="#0e1322"/>
    <path d="M 330 260 L 330 90 L 400 90 L 400 260 Z" fill="#0b0f1a"/>
    <path d="M 450 260 L 450 130 L 510 130 L 510 260 Z" fill="#090d16"/>
    <path d="M 560 260 L 560 100 L 630 100 L 630 260 Z" fill="#0e1322"/>
    <path d="M 680 260 L 680 140 L 750 140 L 750 260 Z" fill="#0d111d"/>
    <path d="M 800 260 L 800 110 L 860 110 L 860 260 Z" fill="#0b0f1a"/>
  </g>
  <!-- Wet Road Surface -->
  <rect y="250" width="800" height="200" fill="#05070f"/>
  <!-- Streaming Neon Road Reflections -->
  <g filter="url(#vGlow)">
    <ellipse cx="280" cy="360" rx="180" ry="20" fill="#06b6d4" opacity="0.45">
      <animate attributeName="rx" values="180;220;180" dur="2s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="0.45;0.65;0.45" dur="1.5s" repeatCount="indefinite"/>
    </ellipse>
    <ellipse cx="540" cy="370" rx="200" ry="22" fill="#d946ef" opacity="0.45">
      <animate attributeName="rx" values="200;240;200" dur="2.4s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="0.45;0.7;0.45" dur="1.8s" repeatCount="indefinite"/>
    </ellipse>
  </g>
  <!-- Moving Car with Headlight Beams -->
  <g>
    <animateTransform attributeName="transform" type="translate" values="0,0; 8,-3; -6,2; 0,0" dur="4s" repeatCount="indefinite"/>
    <!-- Headlight Cones -->
    <polygon points="560,315 800,290 800,420 570,335" fill="url(#vCyan)" opacity="0.35">
      <animate attributeName="opacity" values="0.35;0.5;0.35" dur="1.2s" repeatCount="indefinite"/>
    </polygon>
    <!-- Supercar Chassis -->
    <path d="M 220 330 C 240 310, 270 295, 320 282 C 370 260, 420 252, 480 252 C 530 252, 560 270, 580 290 C 610 305, 630 320, 640 335 C 620 345, 580 348, 550 348 C 540 330, 510 320, 480 320 C 445 320, 425 332, 415 348 C 380 348, 340 348, 310 348 C 300 330, 275 320, 245 320 Z" fill="#0d111a" stroke="#334155" stroke-width="1.5"/>
    <circle cx="585" cy="318" r="4" fill="#ffffff" filter="url(#vGlow)"/>
    <path d="M 215 330 C 225 328, 235 328, 240 332" fill="none" stroke="#f43f5e" stroke-width="4" filter="url(#vGlow)"/>
    <!-- Spinning Alloy Wheels -->
    <circle cx="245" cy="346" r="26" fill="#020306" stroke="#475569" stroke-width="2"/>
    <circle cx="480" cy="346" r="26" fill="#020306" stroke="#475569" stroke-width="2"/>
  </g>
  <!-- Cinematic Camera Film Grain & Letterbox Framing -->
  <line x1="0" y1="2" x2="800" y2="2" stroke="rgba(255,255,255,0.08)" stroke-width="2"/>
  <line x1="0" y1="448" x2="800" y2="448" stroke="rgba(255,255,255,0.08)" stroke-width="2"/>
</svg>'''
    else:
        title = "Alpine Horizon &bull; Aerial Drone Sweep 60fps"
        anim_svg = '''<svg viewBox="0 0 800 450" width="100%" height="100%" style="background:#090514;">
  <defs>
    <linearGradient id="vSkySun" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#1e1b4b"/>
      <stop offset="50%" stop-color="#9a3412"><animate attributeName="stop-color" values="#9a3412;#c2410c;#9a3412" dur="5s" repeatCount="indefinite"/></stop>
      <stop offset="100%" stop-color="#fde047"/>
    </linearGradient>
    <filter id="vSoft"><feGaussianBlur stdDeviation="6"/></filter>
  </defs>
  <rect width="800" height="280" fill="url(#vSkySun)"/>
  <circle cx="410" cy="180" r="45" fill="#fef08a" opacity="0.9" filter="url(#vSoft)">
    <animate attributeName="cy" values="180;170;180" dur="6s" repeatCount="indefinite"/>
  </circle>
  <!-- Moving Drifting Clouds -->
  <g opacity="0.35" filter="url(#vSoft)">
    <animateTransform attributeName="transform" type="translate" from="0,0" to="-200,0" dur="8s" repeatCount="indefinite"/>
    <ellipse cx="200" cy="140" rx="160" ry="22" fill="#fed7aa"/>
    <ellipse cx="580" cy="120" rx="220" ry="26" fill="#fed7aa"/>
    <ellipse cx="900" cy="130" rx="180" ry="24" fill="#fed7aa"/>
  </g>
  <!-- Soaring Mountain Summits -->
  <polygon points="120,280 280,100 430,280" fill="#1e1b4b"/>
  <polygon points="280,100 350,200 320,280" fill="#fef08a" opacity="0.9"/>
  <polygon points="240,280 420,60 590,280" fill="#090514"/>
  <polygon points="420,60 540,190 490,280" fill="#f59e0b" opacity="0.95"/>
  <polygon points="460,280 620,120 750,280" fill="#1e1b4b"/>
  <!-- Mirrored Lake with Ripple Waves -->
  <rect y="280" width="800" height="170" fill="#0369a1"/>
  <ellipse cx="400" cy="350" rx="340" ry="8" fill="#fde047" opacity="0.3" filter="url(#vSoft)">
    <animate attributeName="rx" values="340;380;340" dur="3s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.3;0.5;0.3" dur="2s" repeatCount="indefinite"/>
  </ellipse>
</svg>'''

    card_html = f'''<div class="ai-video-card" data-title="{title}">
  <div class="ai-video-header">
    <div class="ai-video-badge-label">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>
      <span>Cinematic AI Video Render</span>
      <span class="ai-video-res-pill">60fps &bull; 1080p Cinema</span>
    </div>
    <div class="ai-video-actions">
      <button class="btn-video-action btn-video-play" onclick="toggleVideoPlayback(this)" title="Play or pause animation">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
        <span>Pause</span>
      </button>
      <button class="btn-video-action btn-video-download" onclick="downloadVideoFromCard(this, 'modeldock-cinema')" title="Download Video Asset">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
        <span>Download Video</span>
      </button>
    </div>
  </div>
  <div class="ai-video-viewport">
    {anim_svg}
  </div>
  <div class="ai-video-footer">
    <div class="ai-video-timeline">
      <div class="ai-video-progress-bar">
        <div class="ai-video-progress-fill"></div>
      </div>
      <div class="ai-video-timecode">
        <span class="curr-time">00:03</span> / <span class="total-time">00:06</span> (60fps)
      </div>
    </div>
  </div>
</div>'''
    return f"<!-- AI_VIDEO_CARD_START -->\n{card_html}\n<!-- AI_VIDEO_CARD_END -->"


def get_human_portrait_svg(prompt: str = "") -> str:
    """High-detail SVG for human portrait (photorealistic fashion editorial, golden hour rooftop, tailored attire)."""
    p = prompt.lower() if prompt else ""
    is_female = any(w in p for w in ["woman", "girl", "lady", "female"])
    
    badge_sub = "EDITORIAL CINEMA"
    if "indian" in p:
        badge_sub = "INDIAN HERITAGE"
    elif "fashion" in p:
        badge_sub = "STUDIO FASHION"
    elif is_female:
        badge_sub = "PORTRAIT STUDIO"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" width="100%" style="max-width: 520px; border-radius: 14px; background: #0c0814; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <defs>
    <linearGradient id="sunsetSky" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#180e29" />
      <stop offset="40%" stop-color="#701a75" />
      <stop offset="75%" stop-color="#ea580c" />
      <stop offset="100%" stop-color="#fbbf24" />
    </linearGradient>
    <linearGradient id="sunGlow" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.95" />
      <stop offset="60%" stop-color="#fde047" stop-opacity="0.8" />
      <stop offset="100%" stop-color="#ea580c" stop-opacity="0.0" />
    </linearGradient>
    <linearGradient id="skinWarm" x1="0%" y1="20%" x2="100%" y2="80%">
      <stop offset="0%" stop-color="#f8caa6" />
      <stop offset="35%" stop-color="#e59c6e" />
      <stop offset="70%" stop-color="#c87a48" />
      <stop offset="100%" stop-color="#8c421e" />
    </linearGradient>
    <linearGradient id="charcoalShirt" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#27272a" />
      <stop offset="50%" stop-color="#18181b" />
      <stop offset="100%" stop-color="#09090b" />
    </linearGradient>
    <linearGradient id="hairDark" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#262626" />
      <stop offset="50%" stop-color="#171717" />
      <stop offset="100%" stop-color="#0a0a0a" />
    </linearGradient>
    <linearGradient id="watchDial" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0284c7" />
      <stop offset="100%" stop-color="#0369a1" />
    </linearGradient>
    <filter id="bokehBlur" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="7" />
    </filter>
    <filter id="sunBloom" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="12" />
    </filter>
  </defs>

  <!-- Golden Hour Sky -->
  <rect width="800" height="500" fill="url(#sunsetSky)" />

  <!-- Sun Disc with Soft Volumetric Bloom -->
  <circle cx="220" cy="220" r="80" fill="url(#sunGlow)" filter="url(#sunBloom)" />
  <circle cx="220" cy="220" r="42" fill="#ffffff" opacity="0.9" />

  <!-- Atmospheric Rooftop Skyline Silhouettes (Blurred 85mm Depth of Field) -->
  <g filter="url(#bokehBlur)" opacity="0.55">
    <rect x="40" y="180" width="65" height="180" fill="#1e1b4b" />
    <rect x="120" y="140" width="85" height="220" fill="#311042" />
    <rect x="230" y="190" width="70" height="170" fill="#4a044e" />
    <rect x="550" y="130" width="90" height="230" fill="#1e1b4b" />
    <rect x="660" y="160" width="100" height="200" fill="#2e1065" />
  </g>

  <!-- Golden Bokeh Orbs in Air -->
  <circle cx="140" cy="280" r="16" fill="#fef08a" opacity="0.22" filter="url(#bokehBlur)" />
  <circle cx="290" cy="180" r="24" fill="#fed7aa" opacity="0.28" filter="url(#bokehBlur)" />
  <circle cx="620" cy="240" r="20" fill="#fde047" opacity="0.25" filter="url(#bokehBlur)" />
  <circle cx="710" cy="190" r="28" fill="#fb923c" opacity="0.2" filter="url(#bokehBlur)" />

  <!-- Urban Rooftop Balcony Glass and Metallic Ledge -->
  <rect x="0" y="330" width="800" height="170" fill="#09090b" opacity="0.92" />
  <line x1="0" y1="330" x2="800" y2="330" stroke="#fbbf24" stroke-width="1.5" opacity="0.4" />

  <!-- Subject: Human Portrait (Chest-up, 85mm Lens) -->
  <g id="human-subject">
    <!-- Premium Charcoal Black Shirt - Torso and Shoulders -->
    <path d="M 260 500 L 290 395 C 310 365, 360 340, 420 338 C 480 340, 530 365, 550 395 L 580 500 Z" fill="url(#charcoalShirt)" stroke="#18181b" stroke-width="1.5" />

    <!-- Golden Rim Light on Sunset-Facing Shoulder / Torso Edge -->
    <path d="M 260 500 L 290 395 C 305 372, 335 352, 370 344" fill="none" stroke="#fbbf24" stroke-width="2.5" opacity="0.85" />
    <path d="M 292 395 C 320 375, 360 360, 420 358" fill="none" stroke="#f59e0b" stroke-width="1" opacity="0.4" />

    <!-- Shirt Collar, Placket and Button Styling -->
    <!-- Left Collar -->
    <polygon points="380,340 420,388 410,396 360,352" fill="#18181b" stroke="#3f3f46" stroke-width="1" />
    <!-- Right Collar -->
    <polygon points="460,340 420,388 430,396 480,352" fill="#27272a" stroke="#3f3f46" stroke-width="1" />
    <!-- Central Button Placket -->
    <line x1="420" y1="388" x2="420" y2="500" stroke="#27272a" stroke-width="2" />
    <!-- Metallic Buttons -->
    <circle cx="420" cy="415" r="2.5" fill="#71717a" />
    <circle cx="420" cy="450" r="2.5" fill="#71717a" />
    <circle cx="420" cy="485" r="2.5" fill="#71717a" />

    <!-- Forearm and Stylish Modern Wristwatch -->
    <g transform="translate(500, 410)">
      <!-- Arm / Wrist Silhouette -->
      <path d="M 20 90 L 15 40 C 15 25, 25 15, 40 10 L 65 5 L 80 90 Z" fill="url(#skinWarm)" />
      <path d="M 15 40 C 15 25, 25 15, 40 10" fill="none" stroke="#f59e0b" stroke-width="2" opacity="0.6" />
      <!-- Watch Strap -->
      <rect x="22" y="22" width="34" height="18" rx="3" fill="#52525b" stroke="#a1a1aa" stroke-width="1" />
      <!-- Watch Bezel and Case -->
      <circle cx="39" cy="31" r="15" fill="#27272a" stroke="#e4e4e7" stroke-width="2" />
      <!-- Watch Sunburst Cyan Dial -->
      <circle cx="39" cy="31" r="11" fill="url(#watchDial)" />
      <!-- Watch Hands and Crown -->
      <line x1="39" y1="31" x2="39" y2="24" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round" />
      <line x1="39" y1="31" x2="45" y2="34" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round" />
      <circle cx="39" cy="31" r="1.8" fill="#f59e0b" />
      <rect x="54" y="29" width="3" height="4" rx="1" fill="#e4e4e7" />
    </g>

    <!-- Neck with Realistic Muscle Contouring and Shadow -->
    <path d="M 385 348 L 385 285 C 385 270, 455 270, 455 285 L 455 348 Z" fill="url(#skinWarm)" />
    <path d="M 385 310 C 405 328, 435 328, 455 310" fill="none" stroke="#7c2d12" stroke-width="1" opacity="0.5" />
    <!-- Neck Warm Sunset Rim Highlight -->
    <path d="M 385 285 L 385 348" fill="none" stroke="#fbbf24" stroke-width="2.5" opacity="0.85" />

    <!-- Human Head and Realistic Facial Anatomy -->
    <!-- Head Base / Jaw / Cheek Contour -->
    <path d="M 360 210 C 355 255, 375 285, 410 295 C 430 295, 450 285, 475 255 C 485 210, 485 165, 475 140 C 455 110, 385 110, 365 140 C 358 165, 358 190, 360 210 Z" fill="url(#skinWarm)" stroke="#9a3412" stroke-width="0.8" />

    <!-- Golden Hour Sunset Glow on Left Cheek and Temple -->
    <path d="M 363 150 C 358 185, 362 225, 372 250 C 385 275, 405 285, 415 288" fill="none" stroke="#fef08a" stroke-width="3" opacity="0.75" filter="url(#bokehBlur)" />
    <path d="M 363 150 C 358 185, 362 225, 372 250" fill="none" stroke="#ffffff" stroke-width="1.2" opacity="0.6" />

    <!-- Left and Right Ears -->
    <path d="M 358 190 C 350 195, 348 215, 354 225 C 358 230, 362 232, 365 228" fill="url(#skinWarm)" stroke="#9a3412" stroke-width="0.8" />
    <path d="M 478 190 C 486 195, 488 215, 482 225 C 478 230, 474 232, 471 228" fill="url(#skinWarm)" stroke="#9a3412" stroke-width="0.8" />

    <!-- Refined Expressive Eyebrows -->
    <path d="M 380 182 C 392 178, 408 178, 416 182" fill="none" stroke="#1c1917" stroke-width="3.2" stroke-linecap="round" />
    <path d="M 432 182 C 440 178, 456 178, 468 182" fill="none" stroke="#1c1917" stroke-width="3.2" stroke-linecap="round" />

    <!-- Realistic Eyes (Sclera, Deep Amber/Hazel Iris, Catchlights) -->
    <!-- Left Eye -->
    <g transform="translate(385, 192)">
      <path d="M 0 5 C 7 0, 20 0, 26 5 C 20 10, 7 10, 0 5 Z" fill="#fef2f2" stroke="#451a03" stroke-width="0.8" />
      <circle cx="13" cy="5" r="5.2" fill="#78350f" />
      <circle cx="13" cy="5" r="3.2" fill="#0a0a0a" />
      <!-- Specular Golden Catchlights -->
      <circle cx="11.5" cy="3.5" r="1.4" fill="#ffffff" />
      <circle cx="14.5" cy="6.2" r="0.8" fill="#fde047" />
    </g>
    <!-- Right Eye -->
    <g transform="translate(437, 192)">
      <path d="M 0 5 C 7 0, 20 0, 26 5 C 20 10, 7 10, 0 5 Z" fill="#fef2f2" stroke="#451a03" stroke-width="0.8" />
      <circle cx="13" cy="5" r="5.2" fill="#78350f" />
      <circle cx="13" cy="5" r="3.2" fill="#0a0a0a" />
      <!-- Specular Golden Catchlights -->
      <circle cx="11.5" cy="3.5" r="1.4" fill="#ffffff" />
      <circle cx="14.5" cy="6.2" r="0.8" fill="#fde047" />
    </g>

    <!-- Defined Natural Nose with Bridge Highlight and Soft Shading -->
    <path d="M 423 186 L 421 224 C 418 228, 423 232, 427 230 C 430 228, 431 224, 430 220" fill="none" stroke="#9a3412" stroke-width="1.4" stroke-linecap="round" />
    <!-- Nostril Accents -->
    <ellipse cx="418" cy="228" rx="2.5" ry="1.2" fill="#451a03" opacity="0.7" />
    <ellipse cx="431" cy="228" rx="2.5" ry="1.2" fill="#451a03" opacity="0.7" />
    <!-- Nose Tip Sunset Sheen -->
    <circle cx="423" cy="223" r="2" fill="#fef08a" opacity="0.6" />

    <!-- Natural Confident Lips and Smile Line -->
    <path d="M 408 252 C 418 248, 430 248, 440 252" fill="none" stroke="#7c2d12" stroke-width="1.8" stroke-linecap="round" />
    <!-- Upper Lip -->
    <path d="M 409 252 C 418 249, 423 251, 424 251 C 426 251, 430 249, 439 252 C 430 255, 418 255, 409 252 Z" fill="#b45309" opacity="0.75" />
    <!-- Lower Lip with Specular Highlight -->
    <path d="M 412 254 C 420 261, 428 261, 436 254 C 428 264, 420 264, 412 254 Z" fill="#d97706" opacity="0.8" />
    <ellipse cx="424" cy="258" rx="5" ry="1.5" fill="#fef3c7" opacity="0.65" />

    <!-- Modern Styled Textured Hair with Sunset Rim Lighting -->
    <path d="M 358 155 C 348 135, 360 100, 385 85 C 415 65, 460 70, 485 92 C 500 110, 498 135, 490 155 C 480 140, 465 130, 445 130 C 425 130, 400 135, 380 148 C 370 154, 362 152, 358 155 Z" fill="url(#hairDark)" stroke="#1c1917" stroke-width="1" />

    <!-- Volumetric Textured Hair Strands and Quiff Volume -->
    <path d="M 375 115 C 390 85, 425 75, 455 80 C 475 88, 488 105, 485 125" fill="none" stroke="#262626" stroke-width="3" stroke-linecap="round" />
    <path d="M 390 95 C 410 78, 440 76, 468 85" fill="none" stroke="#404040" stroke-width="2" stroke-linecap="round" />
    <!-- Golden Rim Light on Hair Crest Facing Sunset -->
    <path d="M 360 140 C 352 120, 365 92, 390 80 C 415 68, 445 70, 460 75" fill="none" stroke="#fbbf24" stroke-width="2.2" opacity="0.85" />
    <path d="M 370 105 C 385 85, 410 76, 430 75" fill="none" stroke="#fef08a" stroke-width="1.4" opacity="0.9" />
  </g>

  <!-- Fashion Photography Lens Flares and Bokeh Highlights -->
  <circle cx="424" cy="223" r="140" fill="none" stroke="#fbbf24" stroke-width="0.5" opacity="0.2" />
  <ellipse cx="320" cy="260" rx="90" ry="30" fill="#f59e0b" opacity="0.12" filter="url(#bokehBlur)" />

  <!-- Editorial Typography Header and Badge -->
  <rect x="25" y="25" width="280" height="34" rx="6" fill="rgba(15, 23, 42, 0.75)" stroke="rgba(255, 255, 255, 0.15)" />
  <text x="38" y="47" fill="#f8fafc" font-size="12" font-weight="700" letter-spacing="2">MODELDOCK PORTRAIT</text>
  <text x="206" y="47" fill="#fbbf24" font-size="10" font-weight="600" letter-spacing="1">{badge_sub}</text>
</svg>'''


def get_cyber_character_svg(prompt: str = "") -> str:
    """High-detail SVG for Cyberpunk / Robot / Android AI avatar."""
    p = prompt.lower() if prompt else ""
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" width="100%" style="max-width: 520px; border-radius: 14px; background: #05070d; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <defs>
    <linearGradient id="cyberSky" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#020617" />
      <stop offset="60%" stop-color="#0f172a" />
      <stop offset="100%" stop-color="#1e1b4b" />
    </linearGradient>
    <linearGradient id="cyberCyan" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#06b6d4" />
      <stop offset="100%" stop-color="#38bdf8" />
    </linearGradient>
    <linearGradient id="cyberMagenta" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#c026d3" />
      <stop offset="100%" stop-color="#f43f5e" />
    </linearGradient>
    <linearGradient id="chassisChrome" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#334155" />
      <stop offset="50%" stop-color="#0f172a" />
      <stop offset="100%" stop-color="#020617" />
    </linearGradient>
    <filter id="cyberGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="8" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
  </defs>

  <rect width="800" height="500" fill="url(#cyberSky)" />
  <g opacity="0.15">
    <line x1="0" y1="100" x2="800" y2="100" stroke="#06b6d4" stroke-width="1" />
    <line x1="0" y1="200" x2="800" y2="200" stroke="#06b6d4" stroke-width="1" />
    <line x1="0" y1="300" x2="800" y2="300" stroke="#06b6d4" stroke-width="1" />
    <line x1="200" y1="0" x2="200" y2="500" stroke="#06b6d4" stroke-width="1" />
    <line x1="400" y1="0" x2="400" y2="500" stroke="#06b6d4" stroke-width="1" />
    <line x1="600" y1="0" x2="600" y2="500" stroke="#06b6d4" stroke-width="1" />
  </g>

  <!-- Cyber Halo -->
  <circle cx="400" cy="230" r="130" fill="none" stroke="url(#cyberCyan)" stroke-width="2" opacity="0.6" filter="url(#cyberGlow)" />
  <circle cx="400" cy="230" r="145" fill="none" stroke="url(#cyberMagenta)" stroke-width="1" stroke-dasharray="8 12" opacity="0.4" />

  <!-- Robot / Cyborg Subject -->
  <g id="cyber-chassis">
    <!-- Armored Shoulders -->
    <path d="M 230 500 L 280 380 L 370 330 L 430 330 L 520 380 L 570 500 Z" fill="url(#chassisChrome)" stroke="#1e293b" stroke-width="2" />
    <path d="M 280 380 L 370 330" stroke="url(#cyberCyan)" stroke-width="2" filter="url(#cyberGlow)" />
    <path d="M 520 380 L 430 330" stroke="url(#cyberMagenta)" stroke-width="2" filter="url(#cyberGlow)" />
    
    <!-- Chest Core Reactor -->
    <circle cx="400" cy="420" r="22" fill="#020617" stroke="#38bdf8" stroke-width="2.5" />
    <circle cx="400" cy="420" r="12" fill="#06b6d4" filter="url(#cyberGlow)" />

    <!-- Neck Hydraulic Actuators -->
    <rect x="375" y="270" width="10" height="65" rx="3" fill="#475569" />
    <rect x="415" y="270" width="10" height="65" rx="3" fill="#475569" />
    <line x1="390" y1="280" x2="390" y2="330" stroke="#38bdf8" stroke-width="2" />
    <line x1="410" y1="280" x2="410" y2="330" stroke="#f43f5e" stroke-width="2" />

    <!-- Angular Cybernetic Head -->
    <polygon points="350,140 450,140 480,210 440,285 360,285 320,210" fill="url(#chassisChrome)" stroke="#334155" stroke-width="2" />
    <polygon points="360,150 440,150 465,205 430,270 370,270 335,205" fill="#090d16" />

    <!-- Luminous Cyber Visor -->
    <polygon points="345,190 455,190 445,215 355,215" fill="#06b6d4" filter="url(#cyberGlow)" />
    <line x1="350" y1="202" x2="450" y2="202" stroke="#ffffff" stroke-width="2" />

    <!-- Audio / Sensor Array Ears -->
    <rect x="312" y="195" width="10" height="30" rx="2" fill="#334155" stroke="#06b6d4" stroke-width="1" />
    <rect x="478" y="195" width="10" height="30" rx="2" fill="#334155" stroke="#f43f5e" stroke-width="1" />

    <!-- Forehead Optical Data Node -->
    <circle cx="400" cy="165" r="4" fill="#f43f5e" filter="url(#cyberGlow)" />
  </g>

  <!-- Badge -->
  <rect x="25" y="25" width="280" height="34" rx="6" fill="rgba(15, 23, 42, 0.75)" stroke="rgba(255, 255, 255, 0.15)" />
  <text x="38" y="47" fill="#f8fafc" font-size="12" font-weight="700" letter-spacing="2">MODELDOCK CYBER</text>
  <text x="206" y="47" fill="#38bdf8" font-size="10" font-weight="600" letter-spacing="1">SYNTHETIC AI</text>
</svg>'''


def get_visual_highlights(prompt: str) -> str:
    """Return tailored highlights markdown matching the rendered visual subject."""
    p = prompt.lower()

    tech_keywords = ["phone", "camera", "mobile", "smartphone", "laptop", "device", "watch", "gadget", "screen", "electronics"]
    if any(k in p for k in tech_keywords):
        return (
            "- **Lighting & Reflections**: High-end studio product illumination with clean specular rim highlights.\n"
            "- **Hardware Details**: Textured chassis, crisp optical camera lenses, tactile edges, and precise engineering.\n"
            "- **Color Palette**: Minimalist obsidian, anodized metallic finishes, and multi-coated glass elements."
        )

    celestial_keywords = ["moon", "sky", "star", "space", "astronomy", "lunar", "galaxy", "milky way", "cosmos", "planet"]
    if any(k in p for k in celestial_keywords):
        return (
            "- **Lighting & Atmosphere**: Luminous celestial glow with soft volumetric atmospheric haze.\n"
            "- **Detail & Depth**: Distinct lunar surface maria, crater rims, and deep cosmic starfield backdrop.\n"
            "- **Color Palette**: Deep midnight sapphire, iridescent stellar silver, and warm lunar luminescence."
        )

    car_keywords = ["car", "sports car", "supercar", "vehicle", "automobile", "ferrari", "lamborghini"]
    if any(k in p for k in car_keywords):
        return (
            "- **Lighting & Reflections**: Studio softbox automotive lighting with aerodynamic specular streaks.\n"
            "- **Vehicle Details**: Sculpted body panels, high-gloss clear coat, performance wheels, and brake calipers.\n"
            "- **Color Palette**: High-contrast metallic paint, carbon fiber accents, and dark asphalt backdrop."
        )

    human_keywords = [
        "human", "man", "woman", "person", "portrait", "face", "boy", "girl",
        "people", "character", "guy", "lady", "male", "female", "model",
        "indian", "asian", "caucasian", "african", "fashion", "selfie", "actor",
        "eyes", "hair", "skin", "clothing", "shirt", "suit", "jacket", "standing", "rooftop"
    ]
    if any(k in p for k in human_keywords):
        return (
            "- **Composition & Lighting**: 85mm shallow depth-of-field portrait with golden-hour directional sunlight and cinematic bokeh.\n"
            "- **Subject Details**: Realistic facial proportions, warm skin tone gradient, detailed catchlight eyes, textured hair, and tailored attire.\n"
            "- **Color Palette**: Ultra-wide gamut sunset amber, charcoal black, and natural skin tones."
        )

    cyber_keywords = ["robot", "cyborg", "android", "mech", "scifi", "sci-fi", "cyberpunk", "futuristic", "droid", "synth", "synthetic"]
    if any(k in p for k in cyber_keywords):
        return (
            "- **Composition & Lighting**: Volumetric cyber glow with neon cyan and laser magenta rim reflections on armored chassis.\n"
            "- **Color Palette**: Deep midnight slate, electric cyan, and laser magenta accents.\n"
            "- **Subject Details**: Angular hydraulic actuators, illuminated optic sensor visor, and core reactor."
        )

    nature_keywords = ["himalayan", "mountain", "alpine", "lake", "peaks", "sunrise", "summit", "mist", "dawn", "landscape", "valley", "everest", "forest", "nature"]
    if any(k in p for k in nature_keywords):
        return (
            "- **Composition & Lighting**: Luminous sunrise alpenglow across summit ridges with mirrored alpine lake reflection.\n"
            "- **Color Palette**: Radiant amber dawn, deep indigo granite, and pine evergreen accents.\n"
            "- **Atmosphere**: Valley morning mist layers with crystal water surface ripples."
        )

    return (
        "- **Composition & Lighting**: Studio dynamic lighting with multi-layered specular reflections and ambient falloff.\n"
        "- **Color Palette**: Ultra-wide gamut gradients tailored to your scene.\n"
        "- **Rendering**: High-detail photographic render with crisp focus."
    )


def synthesize_visual_content(prompt: str, model_name: str) -> str:
    """Select or generate tailored SVG visual content based on user prompt."""
    p = prompt.lower()

    # 1. Human / Person / Portrait / Man / Woman / Face / Model
    human_keywords = [
        "human", "man", "woman", "person", "portrait", "face", "boy", "girl",
        "people", "character", "guy", "lady", "male", "female", "model",
        "indian", "asian", "caucasian", "african", "fashion", "selfie", "actor",
        "eyes", "hair", "skin", "clothing", "shirt", "suit", "jacket", "standing", "rooftop"
    ]
    if any(k in p for k in human_keywords):
        return get_human_portrait_svg(prompt)

    # 2. Cyber / Robot / AI / Sci-Fi
    cyber_keywords = ["robot", "cyborg", "android", "mech", "scifi", "sci-fi", "cyberpunk", "futuristic", "droid", "synth", "synthetic"]
    if any(k in p for k in cyber_keywords):
        return get_cyber_character_svg(prompt)

    # 3. Himalayan / Mountain / Alpine / Nature Landscape
    nature_keywords = ["himalayan", "mountain", "alpine", "lake", "peaks", "sunrise", "summit", "mist", "dawn", "landscape", "valley", "everest", "forest", "nature"]
    if any(k in p for k in nature_keywords):
        return get_himalayan_mountain_svg()

    # 4. Car / Automotive / Supercar / Vehicle
    car_keywords = ["car", "sports car", "luxury", "supercar", "vehicle", "automobile", "automotive", "street", "city street", "neon cyan", "drift", "racecar", "speed"]
    if any(k in p for k in car_keywords):
        return get_sports_car_svg()

    # Default fallback: if prompt sounds like someone or a person/portrait, use portrait, else human portrait as modern flagship
    return get_human_portrait_svg(prompt)
