/**
 * ModelDock Studio - Live Resource & Telemetry Monitor
 */

let monitorInterval = null;

function initMonitor() {
  refreshTelemetry();
  checkEngineStatus();
  refreshRunningContainers();
  // Poll every 3 seconds for zero background overhead
  monitorInterval = setInterval(() => {
    refreshTelemetry();
    checkEngineStatus();
    refreshRunningContainers();
  }, 3000);
}

async function refreshTelemetry() {
  try {
    const res = await fetch("/api/system/status");
    if (!res.ok) return;
    const data = await res.json();

    const sw = data.software || {};
    const host = data.host || {};
    const gpu = data.gpu || {};

    // Update Topbar Pills
    const pillAppRam = document.getElementById("pill-app-ram");
    if (pillAppRam) pillAppRam.textContent = `${sw.ram_mb || "--"} MB`;

    const pillGpu = document.getElementById("pill-gpu-vram");
    if (pillGpu) {
      if (gpu.available) {
        pillGpu.textContent = `${gpu.name ? gpu.name.replace("NVIDIA GeForce ", "") : "GPU"} (${Math.round(gpu.used_vram_mb)}MB)`;
      } else {
        pillGpu.textContent = "CPU Mode";
      }
    }

    // Update Telemetry Tab if visible
    const statProcRam = document.getElementById("stat-proc-ram");
    if (statProcRam) statProcRam.textContent = `${sw.ram_mb} MB`;

    const statProcCpu = document.getElementById("stat-proc-cpu");
    if (statProcCpu) statProcCpu.textContent = `${sw.cpu_percent}%`;

    const statHostRam = document.getElementById("stat-host-ram");
    if (statHostRam) statHostRam.textContent = `${host.used_ram_gb} / ${host.total_ram_gb} GB`;

    const statHostAvail = document.getElementById("stat-host-avail");
    if (statHostAvail) statHostAvail.textContent = `${host.free_ram_gb} GB`;

    const statHostCores = document.getElementById("stat-host-cores");
    if (statHostCores) statHostCores.textContent = `${host.cpu_count} Threads (${host.cpu_percent}% load)`;

    const statHostBar = document.getElementById("stat-host-bar");
    if (statHostBar) statHostBar.style.width = `${host.ram_percent}%`;

    // GPU Tab Metrics
    const statGpuVram = document.getElementById("stat-gpu-vram");
    const statGpuName = document.getElementById("stat-gpu-name");
    const statGpuBar = document.getElementById("stat-gpu-bar");
    const statGpuUtil = document.getElementById("stat-gpu-util");
    const statGpuTemp = document.getElementById("stat-gpu-temp");
    const statGpuBadge = document.getElementById("stat-gpu-badge");

    if (gpu.available) {
      if (statGpuVram) statGpuVram.textContent = `${gpu.used_vram_mb} / ${gpu.total_vram_mb} MB`;
      if (statGpuName) statGpuName.textContent = gpu.name;
      if (statGpuBar) statGpuBar.style.width = `${gpu.vram_percent}%`;
      if (statGpuUtil) statGpuUtil.textContent = `${gpu.gpu_util_percent}%`;
      if (statGpuTemp) statGpuTemp.textContent = `${gpu.temperature_c} °C`;
      if (statGpuBadge) statGpuBadge.textContent = "CUDA Active";
    } else {
      if (statGpuVram) statGpuVram.textContent = "N/A";
      if (statGpuName) statGpuName.textContent = "No Dedicated GPU Found (CPU Fallback)";
      if (statGpuBar) statGpuBar.style.width = "0%";
      if (statGpuBadge) statGpuBadge.textContent = "CPU";
    }
  } catch (err) {
    // Silent catch on transient network drop
  }
}

async function checkEngineStatus() {
  try {
    const res = await fetch("/api/engine/status");
    if (!res.ok) return;
    const data = await res.json();

    const pill = document.getElementById("engine-status-pill");
    const text = document.getElementById("engine-pill-text");
    const binPreview = document.getElementById("setting-binary-path");
    const hostInput = document.getElementById("setting-ollama-host");

    if (binPreview && data.binary_path) {
      binPreview.textContent = data.binary_path;
    }
    if (hostInput && data.host && document.activeElement !== hostInput) {
      hostInput.value = data.host;
    }

    if (data.running) {
      pill.className = "status-pill status-online";
      pill.title = data.active_model ? `Active Model: ${data.active_model}` : "Native Engine Active (Zero Ollama)";
      text.textContent = data.active_model ? "Running" : "Online";
    } else if (data.binary_ready) {
      pill.className = "status-pill status-online";
      pill.title = "Native Engine Ready (Zero Bloat, Zero Ollama)";
      text.textContent = "Engine";
    } else {
      pill.className = "status-pill status-offline";
      pill.title = "Native Engine binary missing";
      text.textContent = "Offline";
    }
  } catch (err) {
    const pill = document.getElementById("engine-status-pill");
    const text = document.getElementById("engine-pill-text");
    if (pill) pill.className = "status-pill status-offline";
    if (text) text.textContent = "Engine Unreachable";
  }
}

// --- Docker-Style Model Container Runtime Manager ---

async function refreshRunningContainers() {
  const containerListEl = document.getElementById("containers-list-container");
  if (!containerListEl) return;

  try {
    const res = await fetch("/api/engine/containers");
    if (!res.ok) return;
    const containers = await res.json();

    // Update Telemetry Containers Section
    if (!containers || containers.length === 0) {
      containerListEl.innerHTML = `
        <div class="empty-state" style="padding: 1.5rem; border: 1px dashed var(--border-subtle); border-radius: var(--radius-md); text-align: center; background: rgba(0, 0, 0, 0.15);">
          <div style="font-size: 1.8rem; margin-bottom: 0.35rem;">💤</div>
          <h4 style="margin: 0 0 0.3rem 0; font-size: 0.95rem; color: #f1f5f9;">No Active Model Containers in Memory</h4>
          <p style="margin: 0; font-size: 0.8rem; color: var(--text-secondary);">
            Hardware is running at 100% idle with zero model VRAM overhead. Launching any model in Chat will create and spin up an active container instance here.
          </p>
        </div>
      `;
      return;
    }

    containerListEl.innerHTML = containers
      .map((c) => {
        const isPaused = Boolean(c.is_paused);
        const cardClass = isPaused ? "container-card is-paused" : "container-card";
        const statusBadge = isPaused
          ? '<span class="container-status-badge paused"><span class="status-dot" style="background:#facc15;"></span> Paused</span>'
          : '<span class="container-status-badge running"><span class="status-dot" style="background:#10b981;"></span> Running</span>';

        const pauseActionBtn = isPaused
          ? `<button class="btn-primary btn-sm" onclick="resumeModelContainer()" title="Resume active container computation" style="background: linear-gradient(135deg, #059669 0%, #10b981 100%);">
               ▶️ Resume
             </button>`
          : `<button class="btn-secondary btn-sm" onclick="pauseModelContainer()" title="Suspend compute to cool down CPU/GPU without unloading weights">
               ⏸️ Pause
             </button>`;

        const tempStr = c.temperature_c ? `${c.temperature_c} °C` : "--";

        return `
          <div class="${cardClass}">
            <div class="container-top">
              <div class="container-meta">
                <span class="container-id-badge">${escapeMonitorHtml(c.id)}</span>
                <span class="container-name">${escapeMonitorHtml(c.display_name || c.model_name)}</span>
                <span class="badge" style="background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.35); font-size: 0.72rem;">
                  ${escapeMonitorHtml(c.family)} • ${escapeMonitorHtml(c.type)}
                </span>
                ${statusBadge}
              </div>
              <div style="font-size: 0.76rem; color: var(--text-secondary); font-family: var(--font-mono);">
                PID: <strong>${c.pid || "Active"}</strong> ${c.port ? `• Port: <strong>${c.port}</strong>` : ""}
              </div>
            </div>

            <div class="container-metrics-grid">
              <div class="container-metric-item">
                <span class="container-metric-label">GPU VRAM Allocated</span>
                <span class="container-metric-value" style="color: #38bdf8;">${c.vram_formatted}</span>
              </div>
              <div class="container-metric-item">
                <span class="container-metric-label">Host RAM (RSS)</span>
                <span class="container-metric-value">${c.ram_mb} MB</span>
              </div>
              <div class="container-metric-item">
                <span class="container-metric-label">Process CPU %</span>
                <span class="container-metric-value">${c.cpu_percent}%</span>
              </div>
              <div class="container-metric-item">
                <span class="container-metric-label">Hardware Temp</span>
                <span class="container-metric-value" style="color: #facc15;">${tempStr}</span>
              </div>
              <div class="container-metric-item">
                <span class="container-metric-label">Container Uptime</span>
                <span class="container-metric-value">${c.uptime_formatted}</span>
              </div>
            </div>

            <div class="container-actions-row">
              ${pauseActionBtn}
              <button class="btn-secondary btn-sm" onclick="purgeModelVram()" title="Free cached PyTorch/CUDA VRAM buffers without terminating the model">
                ⚡ Purge VRAM
              </button>
              <button class="btn-danger btn-sm" onclick="stopActiveModelContainer()" title="Emergency stop: Terminate container process and free all GPU/CPU memory">
                ⏹️ Stop & Free VRAM
              </button>
            </div>
          </div>
        `;
      })
      .join("");
  } catch (err) {
    // Silent catch on poll
  }
}

async function pauseModelContainer() {
  try {
    const res = await fetch("/api/engine/pause", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      await refreshRunningContainers();
    } else {
      alert(`Pause failed: ${data.error || "Unknown error"}`);
    }
  } catch (e) {
    alert(`Request error: ${e.message}`);
  }
}
window.pauseModelContainer = pauseModelContainer;

async function resumeModelContainer() {
  try {
    const res = await fetch("/api/engine/resume", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      await refreshRunningContainers();
    } else {
      alert(`Resume failed: ${data.error || "Unknown error"}`);
    }
  } catch (e) {
    alert(`Request error: ${e.message}`);
  }
}
window.resumeModelContainer = resumeModelContainer;

async function stopActiveModelContainer(event) {
  if (event) event.stopPropagation();
  if (!confirm("Are you sure you want to stop the active model container and free all GPU/CPU memory?")) return;

  try {
    const res = await fetch("/api/engine/stop", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      await refreshRunningContainers();
      await refreshTelemetry();
    } else {
      alert(`Stop failed: ${data.error || "Unknown error"}`);
    }
  } catch (e) {
    alert(`Request error: ${e.message}`);
  }
}
window.stopActiveModelContainer = stopActiveModelContainer;

async function purgeModelVram() {
  try {
    const res = await fetch("/api/engine/free-memory", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      await refreshRunningContainers();
      await refreshTelemetry();
      alert("✓ GPU VRAM and cached memory buffers purged successfully.");
    }
  } catch (e) {
    alert(`Purge error: ${e.message}`);
  }
}
window.purgeModelVram = purgeModelVram;

function escapeMonitorHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
