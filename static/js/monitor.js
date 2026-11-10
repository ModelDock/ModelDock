/**
 * ModelDock Studio - Live Resource & Telemetry Monitor
 */

let monitorInterval = null;

function initMonitor() {
  refreshTelemetry();
  checkEngineStatus();
  // Poll every 3 seconds for zero background overhead
  monitorInterval = setInterval(() => {
    refreshTelemetry();
    checkEngineStatus();
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
