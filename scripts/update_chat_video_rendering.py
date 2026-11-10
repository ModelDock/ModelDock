with open("static/js/chat.js", "r", encoding="utf-8") as f:
    js = f.read()

# 1. Update renderMarkdown to extract video cards before escaping
target_extract = '''  // 1. Extract SVG Image Blocks before HTML escaping
  const imageCards = [];'''

repl_extract = '''  // 0. Extract AI Video Cards before HTML escaping
  const videoCards = [];
  const videoCardRegex = /<div class="ai-video-card"[\\s\\S]*?<\\/div>\\s*<\\/div>\\s*<\\/div>/gi;
  text = text.replace(videoCardRegex, (match) => {
    const token = `__AI_VIDEO_CARD_TOKEN_${videoCards.length}__`;
    videoCards.push(match);
    return token;
  });

  // 1. Extract SVG Image Blocks before HTML escaping
  const imageCards = [];'''

# 2. Update renderMarkdown to restore video cards
target_restore = '''  // 12. Restore AI Image Cards
  imageCards.forEach((card, idx) => {
    processed = processed.replace(`__AI_IMAGE_CARD_TOKEN_${idx}__`, card);
  });'''

repl_restore = '''  // 12. Restore AI Image Cards
  imageCards.forEach((card, idx) => {
    processed = processed.replace(`__AI_IMAGE_CARD_TOKEN_${idx}__`, card);
  });

  // 13. Restore AI Video Cards
  videoCards.forEach((card, idx) => {
    processed = processed.replace(`__AI_VIDEO_CARD_TOKEN_${idx}__`, card);
  });'''

video_helper_functions = '''
/**
 * AI Video Player Interactive Controls (Play / Pause & Download)
 */
function toggleVideoPlayback(btn) {
  const card = btn.closest(".ai-video-card");
  if (!card) return;
  const isPaused = card.classList.toggle("is-paused");
  const label = btn.querySelector("span");
  if (label) {
    label.textContent = isPaused ? "Play" : "Pause";
  }
}
window.toggleVideoPlayback = toggleVideoPlayback;

function downloadVideoFromCard(btn, filename = "modeldock-cinema") {
  const card = btn.closest(".ai-video-card");
  if (!card) return;
  const svg = card.querySelector(".ai-video-viewport svg");
  if (!svg) return;

  const originalHtml = btn.innerHTML;
  btn.innerHTML = `<span style="color:#a78bfa;">✓ Downloading...</span>`;
  try {
    const svgData = new XMLSerializer().serializeToString(svg);
    const blob = new Blob([svgData], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${filename}.svg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 2000);
    setTimeout(() => { btn.innerHTML = originalHtml; }, 1500);
  } catch (e) {
    btn.innerHTML = originalHtml;
  }
}
window.downloadVideoFromCard = downloadVideoFromCard;
'''

assert target_extract in js, "target_extract not found in static/js/chat.js"
assert target_restore in js, "target_restore not found in static/js/chat.js"

js = js.replace(target_extract, repl_extract, 1)
js = js.replace(target_restore, repl_restore, 1)
js += "\n" + video_helper_functions

with open("static/js/chat.js", "w", encoding="utf-8") as f:
    f.write(js)

print("Updated static/js/chat.js with video card rendering and controls successfully!")
