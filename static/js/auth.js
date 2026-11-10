/**
 * ModelDock Studio - Hugging Face Authentication & Key Management
 */

function initAuth() {
  checkAuthStatus();

  // Save Token Button
  const btnSave = document.getElementById("btn-save-hf-token");
  if (btnSave) {
    btnSave.addEventListener("click", handleSaveToken);
  }

  // Logout Button
  const btnLogout = document.getElementById("btn-hf-logout");
  if (btnLogout) {
    btnLogout.addEventListener("click", handleLogout);
  }

  // Toggle Token Visibility
  const btnToggleVis = document.getElementById("btn-toggle-token-vis");
  const tokenInput = document.getElementById("hf-token-input");
  if (btnToggleVis && tokenInput) {
    btnToggleVis.addEventListener("click", () => {
      tokenInput.type = tokenInput.type === "password" ? "text" : "password";
    });
  }

  // Save Engine Host Button
  const btnSaveHost = document.getElementById("btn-save-engine-host");
  if (btnSaveHost) {
    btnSaveHost.addEventListener("click", handleSaveEngineHost);
  }
}

async function checkAuthStatus() {
  try {
    const res = await fetch("/api/auth/status");
    const data = await res.json();

    const banner = document.getElementById("auth-status-banner");
    const title = document.getElementById("auth-status-title");
    const desc = document.getElementById("auth-status-desc");
    const pill = document.getElementById("hf-auth-pill");
    const pillText = document.getElementById("hf-pill-text");
    const profileBox = document.getElementById("auth-profile-box");
    const formBox = document.getElementById("auth-input-form");

    if (data.authenticated && data.user) {
      AppState.isAuthenticated = true;
      AppState.hfUser = data.user;

      // Update Topbar Pill
      pill.className = "auth-pill authenticated";
      pillText.textContent = `@${data.user.username}`;

      // Update Auth Tab Banner
      banner.className = "status-banner banner-success";
      title.textContent = `Authenticated with Hugging Face (@${data.user.username})`;
      desc.textContent = `Access granted to Gated Models (Llama 3, Mistral, Gemma 2), private repositories, and high-rate downloads.`;

      // Fill Profile Card
      profileBox.classList.remove("hidden");
      formBox.classList.add("hidden");

      document.getElementById("auth-user-name").textContent = data.user.username;
      document.getElementById("auth-user-fullname").textContent = data.user.fullname || "Hugging Face User";
      document.getElementById("auth-token-role").textContent = `Role: ${data.user.token_role || "read"}`;
      document.getElementById("auth-user-orgs").textContent = `Organizations: ${data.user.orgs ? data.user.orgs.length : 0}`;

      const avatarImg = document.getElementById("auth-user-avatar");
      if (data.user.avatar_url) {
        avatarImg.src = data.user.avatar_url;
      } else {
        avatarImg.src = "https://huggingface.co/front/assets/huggingface_logo-noborder.svg";
      }

      // Sync Profile in Chat Sidebar
      if (typeof updateUserProfileInSidebar === "function") updateUserProfileInSidebar();
    } else {
      AppState.isAuthenticated = false;
      AppState.hfUser = null;

      // Update Topbar Pill
      pill.className = "auth-pill unauthenticated";
      pillText.textContent = "HF Token";

      // Update Auth Tab Banner
      banner.className = "status-banner banner-neutral";
      title.textContent = "Guest Mode (Unauthenticated)";
      desc.textContent = "You can download and run public models. To access Gated models like Meta-Llama-3, enter your token below.";

      profileBox.classList.add("hidden");
      formBox.classList.remove("hidden");

      // Sync Profile in Chat Sidebar
      if (typeof updateUserProfileInSidebar === "function") updateUserProfileInSidebar();
    }
  } catch (err) {
    console.error("Error checking auth status:", err);
  }
}

async function handleSaveToken() {
  const tokenInput = document.getElementById("hf-token-input");
  const token = tokenInput ? tokenInput.value.trim() : "";
  if (!token) {
    alert("Please enter a Hugging Face Access Token.");
    return;
  }

  const btnSave = document.getElementById("btn-save-hf-token");
  btnSave.disabled = true;
  btnSave.textContent = "Verifying...";

  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    });

    const data = await res.json();
    if (res.ok && data.success) {
      tokenInput.value = "";
      await checkAuthStatus();
      alert(`Successfully authenticated as @${data.user.username}! Gated models are now accessible.`);
    } else {
      alert(`Authentication failed: ${data.error || "Invalid token"}`);
    }
  } catch (err) {
    alert(`Network error connecting to verification endpoint: ${err.message}`);
  } finally {
    btnSave.disabled = false;
    btnSave.textContent = "Verify & Save";
  }
}

async function handleLogout() {
  if (!confirm("Are you sure you want to disconnect your Hugging Face token?")) return;

  try {
    await fetch("/api/auth/logout", { method: "POST" });
    await checkAuthStatus();
  } catch (err) {
    console.error("Logout error:", err);
  }
}

async function handleSaveEngineHost() {
  const hostInput = document.getElementById("setting-ollama-host");
  const newHost = hostInput ? hostInput.value.trim() : "";
  if (!newHost) return;

  try {
    const res = await fetch("/api/config/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ollama_host: newHost }),
    });
    if (res.ok) {
      alert("Local Engine Host updated.");
      checkEngineStatus();
      loadLocalModels();
    }
  } catch (err) {
    alert(`Failed to update host: ${err.message}`);
  }
}
