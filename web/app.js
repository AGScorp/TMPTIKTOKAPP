// holoApp frontend logic — stateless tokens (no cookies). Uses localStorage for access/refresh tokens.

const $ = (id) => document.getElementById(id);

const TOKENS = {
  access: "tk_access",
  refresh: "tk_refresh",
  openid: "tk_open_id",
};

const state = {
  config: null,
  loggedIn: false,
  nextCursor: null,
  loading: false,
};

function getAccessToken() {
  try {
    return localStorage.getItem(TOKENS.access) || "";
  } catch {
    return "";
  }
}
function getRefreshToken() {
  try {
    return localStorage.getItem(TOKENS.refresh) || "";
  } catch {
    return "";
  }
}
function setTokens(payload = {}) {
  try {
    if (payload.access_token) localStorage.setItem(TOKENS.access, payload.access_token);
    if (payload.refresh_token) localStorage.setItem(TOKENS.refresh, payload.refresh_token);
    if (payload.open_id) localStorage.setItem(TOKENS.openid, payload.open_id);
  } catch {}
  renderDebug();
}
function clearTokens() {
  try {
    localStorage.removeItem(TOKENS.access);
    localStorage.removeItem(TOKENS.refresh);
    localStorage.removeItem(TOKENS.openid);
  } catch {}
  renderDebug();
}

function syncDevTokenInputs() {
  try {
    const ai = document.getElementById("accessInput");
    const ri = document.getElementById("refreshInput");
    if (ai) ai.value = getAccessToken();
    if (ri) ri.value = getRefreshToken();
  } catch {}
}
function saveTokensFromInputs() {
  const ai = document.getElementById("accessInput");
  const ri = document.getElementById("refreshInput");
  const access = ((ai && ai.value) || "").trim();
  const refresh = ((ri && ri.value) || "").trim();
  setTokens({ access_token: access, refresh_token: refresh });
  syncDevTokenInputs();
  state.loggedIn = !!getAccessToken();
  updateAuthUI();
  setStatus("บันทึก Token แล้ว");
  if (state.loggedIn) {
    checkLoginAndLoadMe().catch(() => {});
  }
}

function clearTokensAndUI() {
  clearTokens();
  syncDevTokenInputs();
  state.loggedIn = false;
  updateAuthUI();
  setStatus("ลบ Token แล้ว");
}

async function logoutClick() {
  try {
    clearTokens();
    await fetch(toUrl("/auth/logout"), { method: "POST" });
  } finally {
    location.reload();
  }
}

function loadFirstPage() { loadVideos(true); }
function loadNextPage() { loadVideos(false); }
function runQuery() { queryVideos(); }

// expose helpers globally as a fallback for inline handlers
if (typeof window !== "undefined") {
  window.holo = {
    ...(window.holo || {}),
    setTokens,
    clearTokens,
    getAccessToken,
    getRefreshToken,
    loadVideos,
    checkLoginAndLoadMe,
    state,
    saveTokensFromInputs,
    clearTokensAndUI,
    loadFirstPage,
    loadNextPage,
    runQuery,
    logoutClick,
  };
  console.info("[UI] holo debug object available on window.holo");
}

function setStatus(msg) {
  console.info("[UI] status:", msg);
  const el = $("statusText");
  if (el) el.textContent = msg;
  renderDebug();
}

function fmtInt(n) {
  if (n === null || n === undefined) return "-";
  try {
    return new Intl.NumberFormat().format(n);
  } catch {
    return String(n);
  }
}

/**
 * Build absolute URL for API/static calls.
 */
function toUrl(path) {
  try {
    if (!path) return "/";
    if (/^https?:\/\//i.test(path)) return path;
    const base = (state && state.config && state.config.api_base_url) || (window.location.origin + "/");
    return new URL(path, base).toString();
  } catch {
    return path;
  }
}

function getAuthHeaders() {
  const token = getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// Unified fetch that auto-attempts token refresh on 401 once
async function fetchWithRefresh(url, options = {}, retried = false) {
  const absoluteUrl = url.includes("http") ? url : toUrl(url);
  const headers = { ...(options.headers || {}) };

  if (!options.skipAuth) {
    Object.assign(headers, getAuthHeaders());
  }

  const opts = { ...options, headers };

  const res = await fetch(absoluteUrl, opts);
  if (res.ok) {
    // try to parse JSON; fall back to text
    const ct = res.headers.get("content-type") || "";
    if (ct.includes("application/json")) return res.json();
    try { return await res.json(); } catch { return await res.text(); }
  }

  // Attempt refresh once on 401, if we have refresh_token
  if (res.status === 401 && !retried) {
    const rt = getRefreshToken();
    if (rt) {
      try {
        const r = await fetch(toUrl("/auth/refresh"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: rt }),
        });
        if (r.ok) {
          const data = await r.json();
          setTokens({
            access_token: data.access_token || (data.data && data.data.access_token),
            refresh_token: data.refresh_token || (data.data && data.data.refresh_token) || rt,
            open_id: data.open_id || (data.data && (data.data.open_id || (data.data.user || {}).open_id)),
          });
          // retry original request once
          return fetchWithRefresh(url, options, true);
        }
      } catch {}
    }
    // refresh failed: clear tokens
    clearTokens();
    throw new Error("unauthorized");
  }

  const text = await res.text();
  const method = opts.method || "GET";
  throw new Error(text || `${method} ${absoluteUrl} failed with ${res.status}`);
}

async function apiGet(url) {
  return fetchWithRefresh(url, { method: "GET" });
}

async function apiPost(url, body) {
  return fetchWithRefresh(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
}

function applyUserInfo(data) {
  const d = (data && data.data) || data || {};
  const user = d.user || d;
  $("meDisplayName").textContent = user.display_name || "-";
  $("meOpenId").textContent = user.open_id || "-";
  const deep = user.profile_deep_link || "#";
  const a = $("meDeepLink");
  a.href = deep || "#";
  a.textContent = deep ? "เปิดดู" : "-";
  const avatar = user.avatar_url || user.avatar_large_url || "";
  const img = $("meAvatar");
  if (img) img.src = avatar || "data:image/gif;base64,R0lGODlhAQABAAAAACw=";
  $("meFollower").textContent = fmtInt(user.follower_count);
  $("meFollowing").textContent = fmtInt(user.following_count);
  $("meLikes").textContent = fmtInt(user.likes_count);
  $("meVideos").textContent = fmtInt(user.video_count);
  renderDebug();
}

function escapeHtml(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function videoCard(v) {
  const cover = v.cover_image_url || "";
  const title = v.title || v.video_description || "(ไม่มีชื่อ)";
  const share = v.share_url || v.embed_link || "#";
  const like = fmtInt(v.like_count);
  const com = fmtInt(v.comment_count);
  const shareCount = fmtInt(v.share_count);
  const view = fmtInt(v.view_count);
  const id = v.id || "-";
  return `
    <div class="video">
      <img class="video-cover" src="${escapeHtml(cover)}" alt="cover"/>
      <div style="margin-top:8px"><b>${escapeHtml(title)}</b></div>
      <div class="muted" style="margin:6px 0">ID: <code>${escapeHtml(id)}</code></div>
      <div class="muted">❤️ ${like} · 💬 ${com} · 🔁 ${shareCount} · 👁️ ${view}</div>
      <div style="margin-top:8px">
        <a href="${escapeHtml(share)}" target="_blank" rel="noreferrer">เปิดบน TikTok</a>
      </div>
    </div>
  `;
}

function renderVideos(list) {
  const grid = $("videosGrid");
  if (!Array.isArray(list) || list.length === 0) {
    grid.innerHTML = `<div class="muted">ไม่มีข้อมูลวิดีโอ</div>`;
  } else {
    grid.innerHTML = list.map(videoCard).join("");
  }
  renderDebug();
}

function setCursorInfo(cursor) {
  $("videoCursorInfo").textContent = `cursor: ${cursor || "-"}`;
  renderDebug();
}

function setLoading(loading) {
  state.loading = !!loading;
  const loadBtn = $("loadVideosBtn");
  const nextBtn = $("nextPageBtn");
  if (loadBtn) loadBtn.disabled = state.loading || !state.loggedIn;
  if (nextBtn) nextBtn.disabled = state.loading || !state.loggedIn || !state.nextCursor;
  renderDebug();
}

function updateAuthUI() {
  const logged = !!state.loggedIn;
  const loginBtn = $("loginBtn");
  const logoutBtn = $("logoutBtn");
  const loadBtn = $("loadVideosBtn");
  const nextBtn = $("nextPageBtn");
  const queryBtn = $("queryBtn");

  // Keep controls clickable so the page always responds to user actions
  if (loginBtn) loginBtn.disabled = false;
  if (logoutBtn) logoutBtn.disabled = !logged;
  if (loadBtn) loadBtn.disabled = !!state.loading;
  if (nextBtn) nextBtn.disabled = !!state.loading || !state.nextCursor;
  if (queryBtn) queryBtn.disabled = !!state.loading;

  // Show all sections so user can interact, but hide user info when logged out
  const me = $("meCard");
  if (me) me.classList.toggle("hide", !logged);
  ["videoControls", "videosCard", "queryCard"].forEach((id) => {
    const el = $(id);
    if (el) el.classList.remove("hide");
  });

  renderDebug();
}

function renderDebug() {
  const el = document.getElementById("debugInfo");
  if (!el) return;
  try {
    const access = getAccessToken() ? "yes" : "no";
    const refresh = getRefreshToken() ? "yes" : "no";
    el.textContent = `loggedIn=${state.loggedIn} access=${access} refresh=${refresh} loading=${state.loading} cursor=${state.nextCursor || "-"}`;
  } catch {}
}

async function checkLoginAndLoadMe() {
  // Initial guess: logged in if we have an access token
  state.loggedIn = !!getAccessToken();
  updateAuthUI();

  if (!state.loggedIn) {
    setStatus("ยังไม่ได้เข้าสู่ระบบ โปรดคลิกปุ่ม 'เข้าสู่ระบบด้วย TikTok'");
    return;
  }

  setStatus("กำลังตรวจสอบสถานะการเข้าสู่ระบบ...");
  try {
    const me = await apiGet("/api/me");
    state.loggedIn = true;
    setStatus("เข้าสู่ระบบแล้ว");
    applyUserInfo(me);
  } catch (e) {
    state.loggedIn = false;
    setStatus("เข้าสู่ระบบหมดอายุ โปรดเข้าสู่ระบบใหม่");
  }
  updateAuthUI();
}

async function loadVideos(firstPage = true) {
  if (!state.loggedIn) {
    setStatus("กรุณาเข้าสู่ระบบก่อน");
    return;
  }
  if (state.loading) return;
  setLoading(true);
  try {
    if (firstPage) state.nextCursor = null;
    const maxCount = parseInt(($("maxCount").value || "20"), 10) || 20;
    const payload = { max_count: maxCount };
    if (!firstPage && state.nextCursor) payload.cursor = state.nextCursor;

    const res = await apiPost("/api/videos", payload);
    const data = (res && res.data) || res || {};
    const list = data.videos || data.list || [];
    const hasMore = !!data.has_more;
    const cursorNext = data.cursor || data.cursor_next || res.cursor_next || null;

    renderVideos(list);
    state.nextCursor = hasMore ? cursorNext : null;
    setCursorInfo(state.nextCursor);
  } catch (e) {
    console.error(e);
    setStatus(`โหลดวิดีโอล้มเหลว: ${e.message || e}`);
  } finally {
    setLoading(false);
    updateAuthUI();
  }
}

async function queryVideos() {
  if (!state.loggedIn) {
    setStatus("กรุณาเข้าสู่ระบบก่อน");
    return;
  }
  const raw = $("videoIds").value || "";
  const ids = raw
    .split(/\r?\n/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
  if (ids.length === 0) {
    $("queryResult").textContent = "กรุณาใส่ video_ids อย่างน้อย 1 ค่า";
    return;
  }
  try {
    const res = await apiPost("/api/videos/query", { video_ids: ids });
    $("queryResult").textContent = JSON.stringify(res, null, 2);
  } catch (e) {
    $("queryResult").textContent = `เกิดข้อผิดพลาด: ${e.message || e}`;
  }
}

function bindUI() {
  const loginBtn = $("loginBtn");
  if (loginBtn) {
    loginBtn.addEventListener("click", () => {
      // Stateless: redirect to backend which will redirect to TikTok
      window.location.href = toUrl("/auth/login");
    });
  }

  const logoutBtn = $("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      try {
        clearTokens();
        // optional notify backend (no cookies kept)
        await fetch(toUrl("/auth/logout"), { method: "POST" });
      } finally {
        window.location.reload();
      }
    });
  }

  const loadBtn = $("loadVideosBtn");
  if (loadBtn) loadBtn.addEventListener("click", () => loadVideos(true));

  const nextBtn = $("nextPageBtn");
  if (nextBtn) nextBtn.addEventListener("click", () => loadVideos(false));

  const queryBtn = $("queryBtn");
  if (queryBtn) queryBtn.addEventListener("click", queryVideos);

  // Dev token helpers
  const accessInput = $("accessInput");
  const refreshInput = $("refreshInput");
  const saveTokensBtn = $("saveTokensBtn");
  const clearTokensBtn = $("clearTokensBtn");

  if (saveTokensBtn) {
    saveTokensBtn.addEventListener("click", async () => {
      const access = (accessInput && accessInput.value || "").trim();
      const refresh = (refreshInput && refreshInput.value || "").trim();
      setTokens({ access_token: access, refresh_token: refresh });
      syncDevTokenInputs();
      state.loggedIn = !!getAccessToken();
      updateAuthUI();
      setStatus("บันทึก Token แล้ว");
      if (state.loggedIn) {
        try { await checkLoginAndLoadMe(); } catch {}
      }
    });
  }
  if (clearTokensBtn) {
    clearTokensBtn.addEventListener("click", () => {
      clearTokens();
      syncDevTokenInputs();
      state.loggedIn = false;
      updateAuthUI();
      setStatus("ลบ Token แล้ว");
    });
  }

  document.addEventListener("click", (e) => {
    const t = e.target;
    const id = t && t.id;
    if (id) console.info("[UI] click:", id);
  });
  document.addEventListener("keydown", (e) => {
    if (e.altKey && (e.key === "n" || e.key === "N")) {
      e.preventDefault();
      console.info("[UI] hotkey Alt+N");
      loadVideos(false);
    }
  });
}

(async function init() {
  try {
    const res = await fetch(toUrl("/config"));
    if (res.ok) {
      state.config = await res.json();
      console.info("Config:", state.config);
    }
  } catch (e) {
    console.warn("โหลดคอนฟิกไม่สำเร็จ", e);
  }

  bindUI();
  syncDevTokenInputs();
  updateAuthUI();
  await checkLoginAndLoadMe();
  if (state.loggedIn) {
    await loadVideos(true);
  }

  // keep debug info live
  setInterval(renderDebug, 1000);
})();