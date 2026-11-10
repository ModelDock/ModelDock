video_css = '''
/* ==========================================================================
   AI Generated High-Quality Video Card & Interactive Player
   ========================================================================== */
.ai-video-card {
  margin: 0.95rem 0;
  background: #0b0e17;
  border: 1px solid rgba(139, 92, 246, 0.45);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: 0 14px 40px rgba(0, 0, 0, 0.6), 0 0 20px rgba(139, 92, 246, 0.15);
  display: flex;
  flex-direction: column;
  max-width: 520px;
  width: 100%;
  box-sizing: border-box;
}

.ai-video-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.6rem 0.9rem;
  background: #121624;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  gap: 0.5rem;
  flex-wrap: wrap;
}

.ai-video-badge-label {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: #ddd6fe;
}

.ai-video-res-pill {
  font-size: 0.66rem;
  padding: 0.15rem 0.45rem;
  border-radius: var(--radius-full);
  background: rgba(139, 92, 246, 0.2);
  border: 1px solid rgba(139, 92, 246, 0.4);
  color: #c4b5fd;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.ai-video-actions {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.btn-video-action {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.28rem 0.68rem;
  font-size: 0.72rem;
  font-weight: 500;
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #f1f5f9;
  cursor: pointer;
  transition: all 0.18s ease;
}

.btn-video-action:hover {
  background: rgba(139, 92, 246, 0.3);
  border-color: rgba(139, 92, 246, 0.6);
  color: #fff;
  transform: translateY(-1px);
}

.ai-video-viewport {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #06070b;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.ai-video-viewport svg,
.ai-video-viewport video,
.ai-video-viewport canvas {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.ai-video-footer {
  padding: 0.55rem 0.9rem;
  background: #0f121d;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.ai-video-timeline {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.ai-video-progress-bar {
  flex: 1;
  height: 4px;
  background: rgba(255, 255, 255, 0.12);
  border-radius: var(--radius-full);
  overflow: hidden;
  position: relative;
}

.ai-video-progress-fill {
  height: 100%;
  width: 100%;
  background: linear-gradient(90deg, #8b5cf6, #ec4899, #6366f1);
  border-radius: var(--radius-full);
  animation: videoProgressScan 6s linear infinite;
}

@keyframes videoProgressScan {
  0% { transform: scaleX(0); transform-origin: left; }
  100% { transform: scaleX(1); transform-origin: left; }
}

.ai-video-card.is-paused .ai-video-progress-fill {
  animation-play-state: paused !important;
}

.ai-video-card.is-paused svg * {
  animation-play-state: paused !important;
}

.ai-video-timecode {
  font-size: 0.7rem;
  font-family: var(--font-mono);
  color: #94a3b8;
  white-space: nowrap;
}
'''

with open("static/css/style.css", "a", encoding="utf-8") as f:
    f.write(video_css)

print("Appended video card styles to static/css/style.css successfully!")
