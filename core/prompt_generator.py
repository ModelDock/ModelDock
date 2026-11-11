"""
Prompt Generation & Enhancement Engine for ModelDock.
Provides intelligent prompt expansion, typo correction, stylistic detailing,
lighting & camera enhancements, and multi-variation generation for both
local Neural Diffusion (image generation) and LLM reasoning.
"""

import difflib
import re
from typing import Any, Dict, List, Optional, Tuple

# Common vocabulary dictionary for visual diffusion subjects and attributes
COMMON_SUBJECTS = {
    # Objects & Gear
    "helmet": ["healmat", "helmat", "helment", "helmutt", "helemt"],
    "motorcycle": ["motocycle", "motorcyle", "moterbike", "motercycle"],
    "bicycle": ["bycicle", "bycycle", "bicyle", "byk"],
    "car": ["carr", "caar", "autmobile"],
    "supercar": ["supper car", "super-car", "sopercar"],
    "airplane": ["aeroplane", "airplaine", "airplan"],
    "guitar": ["gitar", "guiter"],
    "camera": ["camra", "camrea", "camear"],
    "laptop": ["labtop", "leptop"],
    "watch": ["wacth", "wach"],
    "table": ["tabel", "tabble"],
    "chair": ["cheir", "chaire"],
    # People & Characters
    "portrait": ["potrait", "portait", "portrate", "potrate"],
    "person": ["persn", "preson"],
    "woman": ["womun", "womon", "womn"],
    "man": ["mman", "mahn"],
    "warrior": ["warior", "warrier"],
    "astronaut": ["astranaut", "astronot", "astronout"],
    "cyberpunk": ["cyperpunk", "cybarpunk", "cyberpunc"],
    "samurai": ["samuray", "samuri"],
    # Environments & Nature
    "landscape": ["lanscape", "landscap", "landcape"],
    "mountain": ["mountin", "mountian", "montain"],
    "forest": ["forrest", "foreste"],
    "ocean": ["ocian", "oceon"],
    "sunset": ["sunsit", "sun-set"],
    "city": ["citi", "citty"],
    "architecture": ["architecure", "archetecture", "archtecture"],
    # Qualities & Attributes
    "photorealistic": ["photorealstic", "photoreal", "photorealistc"],
    "beautiful": ["beutiful", "beautifull", "beatiful"],
    "cinematic": ["cinamatic", "cinemtic", "cinamatik"],
    "lighting": ["lightng", "lightingg", "lighitng"],
    "reflections": ["refelctions", "reflecshuns", "reflextions"],
    "detailed": ["detaile", "detaield", "detaild"],
}

# Invert dictionary for fast O(1) lookup
TYPO_CORRECTIONS = {}
for correct, typos in COMMON_SUBJECTS.items():
    for typo in typos:
        TYPO_CORRECTIONS[typo.lower()] = correct

# Style presets for visual generation
STYLE_PRESETS = {
    "photorealistic": {
        "label": "Photorealistic 8K Photography",
        "suffix": "photorealistic, 8k uhd, highly detailed, professional photography, natural lighting, sharp focus, raytracing reflections, raw photo, f/1.8",
        "negative": "blurry, out of focus, distorted, low quality, render, cartoon, 3d, illustration, drawing, bad anatomy",
    },
    "cinematic": {
        "label": "Cinematic Movie Still",
        "suffix": "cinematic movie still, 35mm film grain, anamorphic lens flare, moody color grading, dramatic rim lighting, master shot, award winning cinematography",
        "negative": "low quality, snapshot, flat lighting, amateur, oversaturated, blurry, grainy noise",
    },
    "cyberpunk": {
        "label": "Cyberpunk Neon Sci-Fi",
        "suffix": "cyberpunk aesthetic, vibrant neon reflections in puddles, volumetric atmospheric fog, futuristic city lights, cyan and magenta glow, octane render",
        "negative": "rustic, vintage, sunny, pastoral, low quality, cartoon, flat, washed out",
    },
    "anime": {
        "label": "Makoto Shinkai Anime Style",
        "suffix": "anime aesthetic, vibrant color palette, Makoto Shinkai style, beautifully detailed sky, volumetric cloud shadows, anime key visual, clean line art",
        "negative": "photo, photorealistic, 3d render, low quality, ugly face, distorted anatomy",
    },
    "studio": {
        "label": "Commercial Studio Product",
        "suffix": "commercial studio lighting, softbox diffusion, clean gradient backdrop, razor-sharp macro focus, pristine catalog photography, 8k resolution",
        "negative": "dirty, messy background, outdoors, harsh shadows, low quality, noise",
    },
    "concept_art": {
        "label": "Epic Fantasy / Concept Art",
        "suffix": "epic concept art, dynamic composition, trending on ArtStation, Unreal Engine 5 render, highly detailed, dramatic atmospheric perspective",
        "negative": "amateur sketch, blurry, watermark, flat colors, low resolution",
    },
}

LIGHTING_PRESETS = {
    "golden_hour": "warm golden-hour sunset sunlight, long soft shadows, amber atmospheric glow",
    "studio_softbox": "professional studio softbox lighting, soft diffused highlights, zero harsh glare",
    "cyberpunk_neon": "high-contrast neon backlighting, wet reflective highlights, moody shadows",
    "dramatic_chiaroscuro": "dramatic chiaroscuro lighting, deep shadows, Rembrandt directional rim lighting",
    "volumetric_fog": "volumetric light rays breaking through haze, atmospheric ethereal beams",
}

CAMERA_PRESETS = {
    "85mm_portrait": "shot on 85mm f/1.4 lens, shallow depth of field, creamy smooth bokeh background",
    "macro_detail": "extreme macro photography, microscopic surface textures, razor-sharp focal plane",
    "wide_angle_24mm": "wide-angle 24mm architectural perspective, expansive scale, deep depth of field",
    "isometric_3d": "isometric 3D perspective, orthographic tilt-shift view, clean miniature aesthetics",
    "drone_aerial": "high-altitude drone bird's-eye view, breathtaking panoramic scale",
}


def correct_prompt_typos(prompt: str) -> Tuple[str, List[Dict[str, str]]]:
    """
    Detect and correct common typographical errors in user prompts.
    Returns the corrected prompt along with the list of replacements made.
    """
    words = re.findall(r"\b\w+\b|\S", prompt)
    corrected_words = []
    corrections = []

    for token in words:
        clean = token.lower()
        if clean in TYPO_CORRECTIONS:
            replacement = TYPO_CORRECTIONS[clean]
            # Match capitalization
            if token.isupper():
                replacement = replacement.upper()
            elif token.istitle():
                replacement = replacement.capitalize()
            corrected_words.append(replacement)
            corrections.append({"original": token, "corrected": replacement})
        else:
            # Fuzzy match against known subjects if length > 4
            matched = False
            if len(clean) >= 5 and clean.isalpha():
                close_matches = difflib.get_close_matches(clean, COMMON_SUBJECTS.keys(), n=1, cutoff=0.82)
                if close_matches:
                    replacement = close_matches[0]
                    if token.istitle():
                        replacement = replacement.capitalize()
                    corrected_words.append(replacement)
                    corrections.append({"original": token, "corrected": replacement})
                    matched = True
            if not matched:
                corrected_words.append(token)

    # Reconstruct text with spacing
    corrected_prompt = ""
    for i, token in enumerate(corrected_words):
        if i > 0 and not re.match(r"^[,.!?;:)]", token) and not re.match(r"^[(\[\"']", corrected_prompt[-1:]):
            corrected_prompt += " "
        corrected_prompt += token

    # Fix common preposition mismatches for physical surfaces
    surface_fixes = [
        (r"\bin the table\b", "on the table"),
        (r"\bin table\b", "on the table"),
        (r"\bin the desk\b", "on the desk"),
        (r"\bin desk\b", "on the desk"),
        (r"\bin the floor\b", "on the floor"),
        (r"\bin the ground\b", "on the ground"),
        (r"\bin the wall\b", "on the wall"),
    ]
    for pattern, rep in surface_fixes:
        if re.search(pattern, corrected_prompt, flags=re.IGNORECASE):
            corrected_prompt = re.sub(pattern, rep, corrected_prompt, flags=re.IGNORECASE)
            corrections.append({"original": pattern.replace(r"\b", ""), "corrected": rep})

    return corrected_prompt, corrections


def quick_enhance_image_prompt(raw_prompt: str) -> str:
    """
    One-click immediate prompt expansion for the inline chat input bar.
    Fixes typos, adds compositional balance, lighting, and photorealistic 8K descriptors.
    """
    cleaned, _ = correct_prompt_typos(raw_prompt.strip())
    if not cleaned:
        return ""

    p_lower = cleaned.lower()

    # Determine best fitting style context
    if any(k in p_lower for k in ["car", "vehicle", "sports car", "ferrari", "lamborghini"]):
        additions = "sculpted aerodynamic body, gloss clear-coat reflections, commercial automotive lighting, 8k uhd, photorealistic"
    elif any(k in p_lower for k in ["portrait", "person", "woman", "man", "girl", "boy", "face"]):
        additions = "detailed skin texture, catchlight in eyes, 85mm f/1.4 lens portrait, soft volumetric lighting, photorealistic 8k"
    elif any(k in p_lower for k in ["table", "desk", "room", "interior", "chair"]):
        additions = "natural ambient lighting, shallow depth of field, crisp surface texture, photorealistic, 8k uhd"
    elif any(k in p_lower for k in ["city", "street", "night", "cyberpunk", "neon"]):
        additions = "cinematic street reflections, wet pavement, moody atmospheric fog, photorealistic, 8k uhd"
    elif any(k in p_lower for k in ["mountain", "forest", "landscape", "ocean", "sunset"]):
        additions = "breathtaking panoramic view, golden hour sunlight, sharp natural detail, 8k uhd wallpaper"
    else:
        additions = "cinematic lighting, ultra-sharp focus, shallow depth of field, photorealistic, 8k uhd"

    # Avoid duplicating tokens already present
    tokens_to_add = [tok.strip() for tok in additions.split(",") if tok.strip().lower() not in p_lower]
    
    if tokens_to_add:
        return f"{cleaned}, {', '.join(tokens_to_add)}"
    return cleaned


def generate_prompt_variations(
    concept: str,
    style: str = "photorealistic",
    lighting: str = "golden_hour",
    camera: str = "85mm_portrait",
    mood: str = "cinematic",
    custom_modifiers: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate multiple rich, specialized prompt variations for image synthesis or LLM instructions.
    """
    cleaned_concept, typo_list = correct_prompt_typos(concept.strip())
    if not cleaned_concept:
        cleaned_concept = "A beautiful artwork"

    style_cfg = STYLE_PRESETS.get(style, STYLE_PRESETS["photorealistic"])
    lighting_desc = LIGHTING_PRESETS.get(lighting, LIGHTING_PRESETS["golden_hour"])
    camera_desc = CAMERA_PRESETS.get(camera, CAMERA_PRESETS["85mm_portrait"])

    # Variation 1: Ultra-Realistic Masterpiece (Max Detail & Polish)
    v1 = f"{cleaned_concept}, {camera_desc}, {lighting_desc}, {style_cfg['suffix']}"
    if custom_modifiers:
        v1 += f", {custom_modifiers}"

    # Variation 2: Dramatic Cinematic Concept (Atmospheric & Narrative)
    v2_style = STYLE_PRESETS["cinematic"]["suffix"]
    v2 = f"{cleaned_concept}, cinematic framing, {lighting_desc}, dramatic composition, {v2_style}"

    # Variation 3: Commercial Studio Product / Macro (Clean & Sharp)
    v3_style = STYLE_PRESETS["studio"]["suffix"]
    v3 = f"{cleaned_concept}, commercial studio softbox lighting, clean gradient backdrop, razor-sharp macro focus, pristine catalog photography, 8k resolution"

    # Variation 4: Stylized Digital / Unreal 5 Concept Art (Vibrant & Epic)
    v4_style = STYLE_PRESETS["concept_art"]["suffix"]
    v4 = f"{cleaned_concept}, vibrant color harmony, Unreal Engine 5 render, {v4_style}"

    return {
        "success": True,
        "original_input": concept,
        "cleaned_concept": cleaned_concept,
        "typos_corrected": typo_list,
        "primary_prompt": v1,
        "variations": [
            {
                "id": "v1_photoreal",
                "title": "📸 Ultra-Photorealistic 8K",
                "prompt": v1,
                "negative_prompt": style_cfg["negative"],
                "badge": "Photorealistic 8K",
            },
            {
                "id": "v2_cinematic",
                "title": "🎬 Cinematic Movie Still",
                "prompt": v2,
                "negative_prompt": "low quality, snapshot, flat lighting, amateur, oversaturated",
                "badge": "Cinematic Lighting",
            },
            {
                "id": "v3_studio",
                "title": "💡 Commercial Studio & Macro",
                "prompt": v3,
                "negative_prompt": "dirty, messy background, outdoors, harsh shadows, low quality, noise",
                "badge": "Clean Studio",
            },
            {
                "id": "v4_concept",
                "title": "🎨 Unreal 5 & Concept Art",
                "prompt": v4,
                "negative_prompt": "blurry, low resolution, bad geometry, distorted",
                "badge": "Artistic Render",
            },
        ],
        "negative_prompt": style_cfg["negative"],
        "recommended_resolution": "1024x1024",
    }


def generate_llm_system_prompt(task_description: str, role: str = "expert") -> Dict[str, Any]:
    """
    Generate an optimized prompt structure for LLMs, code generation, and reasoning.
    """
    role_map = {
        "expert": "You are a world-class principal software architect and technical expert.",
        "creative": "You are an imaginative, expressive creative writer and visionary designer.",
        "analyst": "You are a meticulous data scientist and forensic analytical researcher.",
        "concise": "You are an ultra-direct, high-efficiency assistant prioritizing actionable precision.",
    }
    
    role_lead = role_map.get(role, role_map["expert"])
    
    system_prompt = (
        f"{role_lead} Your mission is to address the following goal with rigor and accuracy:\n"
        f"Goal: {task_description.strip()}\n\n"
        "Guidelines:\n"
        "1. Structure your response logically with clear Markdown headings.\n"
        "2. Provide concrete, verified code or step-by-step instructions.\n"
        "3. Highlight potential edge cases or optimization opportunities.\n"
        "4. Keep explanations concise, practical, and directly applicable."
    )

    user_scaffold = f"Please solve: {task_description.strip()}\nProvide a complete, production-grade solution with explanations."

    return {
        "success": True,
        "system_prompt": system_prompt,
        "user_prompt": user_scaffold,
        "role": role,
    }
