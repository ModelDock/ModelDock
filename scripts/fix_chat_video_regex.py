with open("static/js/chat.js", "r", encoding="utf-8") as f:
    js = f.read()

target = '''  const videoCardRegex = /<div class="ai-video-card"[\\s\\S]*?<\\/div>\\s*<\\/div>\\s*<\\/div>/gi;
  text = text.replace(videoCardRegex, (match) => {
    const token = `__AI_VIDEO_CARD_TOKEN_${videoCards.length}__`;
    videoCards.push(match);
    return token;
  });'''

repl = '''  const videoCardRegex = /<!-- AI_VIDEO_CARD_START -->\\s*([\\s\\S]*?)\\s*<!-- AI_VIDEO_CARD_END -->/gi;
  text = text.replace(videoCardRegex, (match, cardHtml) => {
    const token = `__AI_VIDEO_CARD_TOKEN_${videoCards.length}__`;
    videoCards.push(cardHtml.trim());
    return token;
  });'''

assert target in js, "target not found in static/js/chat.js"
js = js.replace(target, repl, 1)

with open("static/js/chat.js", "w", encoding="utf-8") as f:
    f.write(js)

print("Updated static/js/chat.js with clean video delimiter parsing!")
