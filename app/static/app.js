(function () {
  "use strict";

  // Utilities
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  const alerts = $("#alerts");
  const tokenInput = $("#token-input");
  const saveTokenBtn = $("#save-token-btn");
  const clearTokenBtn = $("#clear-token-btn");
  const tokenStatus = $("#token-status");

  const displayDebugBtn = $("#display-debug-btn");
  const contentDebugBtn = $("#content-debug-btn");
  const debugOutput = $("#debug-output");

  const clientTokenBtn = $("#client-token-btn");
  const clientTokenOutput = $("#client-token-output");

  const fetchProfileBtn = $("#fetch-profile-btn");
  const creatorInfoBtn = $("#creator-info-btn");
  const profileImage = $("#profile-image");
  const profileDisplayName = $("#profile-display-name");
  const profileOpenId = $("#profile-open-id");
  const statFollowers = $("#stat-followers");
  const statFollowing = $("#stat-following");
  const statLikes = $("#stat-likes");
  const statVideos = $("#stat-videos");
  const creatorInfoOutput = $("#creator-info-output");

  const uploadFileForm = $("#upload-file-form");
  const uploadFileInput = $("#upload-file-input");
  const uploadFilePrivacy = $("#upload-file-privacy");
  const uploadFileOutput = $("#upload-file-output");

  const uploadUrlForm = $("#upload-url-form");
  const uploadUrlInput = $("#upload-url-input");
  const uploadUrlPrivacy = $("#upload-url-privacy");
  const uploadUrlOutput = $("#upload-url-output");

  const statusForm = $("#status-form");
  const statusJobId = $("#status-job-id");
  const statusOutput = $("#status-output");

  const publishForm = $("#publish-form");
  const publishJobId = $("#publish-job-id");
  const publishPrivacy = $("#publish-privacy");
  const publishCaption = $("#publish-caption");
  const publishOutput = $("#publish-output");

  // Alerts
  function addAlert(type, text) {
    const el = document.createElement("div");
    el.className = `alert ${type}`;
    el.textContent = text;
    alerts.appendChild(el);
    setTimeout(() => {
      el.remove();
    }, 6000);
  }

  // Token storage
  function getToken() {
    return localStorage.getItem("access_token") || "";
  }

  function setToken(token) {
    if (token) {
      localStorage.setItem("access_token", token);
    }
    updateTokenStatus();
  }

  function clearToken() {
    localStorage.removeItem("access_token");
    updateTokenStatus();
  }

  function updateTokenStatus() {
    const t = getToken();
    if (t) {
      tokenStatus.textContent = `สถานะ: มีโทเค็นที่บันทึกไว้ (prefix=${t.slice(0, 6)}...)`;
    } else {
      tokenStatus.textContent = "สถานะ: ยังไม่มีโทเค็นที่บันทึกไว้";
    }
  }

  // Tabs
  function initTabs() {
    const tabs = $$(".tab");
    const panels = {
      dashboard: $("#tab-dashboard"),
      profile: $("#tab-profile"),
      content: $("#tab-content"),
    };

    function activate(name) {
      tabs.forEach((btn) => {
        const isActive = btn.dataset.tab === name;
        btn.classList.toggle("active", isActive);
        btn.setAttribute("aria-selected", String(isActive));
      });
      Object.entries(panels).forEach(([n, el]) => {
        el.classList.toggle("active", n === name);
      });
      history.replaceState(null, "", name === "dashboard" ? "/" : `/${name}`);
    }

    tabs.forEach((btn) => {
      btn.addEventListener("click", () => activate(btn.dataset.tab));
    });

    // Deep-link support
    const path = location.pathname.replace(/^\/+/, "");
    if (path === "profile") activate("profile");
    else if (path === "content") activate("content");
    else activate("dashboard");
  }

  // Fetch helpers
  async function jsonGet(url, { bearer, headers } = {}) {
    const h = { ...(headers || {}) };
    if (bearer) h.Authorization = `Bearer ${bearer}`;
    const res = await fetch(url, { headers: h });
    return await res.json();
  }

  async function jsonPost(url, body, { bearer, headers } = {}) {
    const h = { "Content-Type": "application/json", ...(headers || {}) };
    if (bearer) h.Authorization = `Bearer ${bearer}`;
    const res = await fetch(url, { method: "POST", headers: h, body: JSON.stringify(body) });
    return await res.json();
  }

  async function formPost(url, formData, { bearer } = {}) {
    const h = {};
    if (bearer) h.Authorization = `Bearer ${bearer}`;
    const res = await fetch(url, { method: "POST", headers: h, body: formData });
    return await res.json();
  }

  // Wire up controls
  function initControls() {
    // Token
    saveTokenBtn?.addEventListener("click", () => {
      const val = tokenInput.value.trim();
      if (!val) {
        addAlert("danger", "กรุณาใส่โทเค็นก่อนบันทึก");
        return;
      }
      setToken(val);
      addAlert("success", "บันทึกโทเค็นเรียบร้อย");
    });

    clearTokenBtn?.addEventListener("click", () => {
      clearToken();
      addAlert("info", "ลบโทเค็นเรียบร้อย");
    });

    // Debug
    displayDebugBtn?.addEventListener("click", async () => {
      try {
        const tk = getToken();
        const data = await jsonGet(`/display/debug?token=${encodeURIComponent(tk || "")}`);
        debugOutput.textContent = JSON.stringify(data, null, 2);
        addAlert("info", "เรียก /display/debug สำเร็จ");
      } catch (e) {
        addAlert("danger", "เรียก /display/debug ล้มเหลว");
      }
    });

    contentDebugBtn?.addEventListener("click", async () => {
      try {
        const data = await jsonGet("/content/debug");
        debugOutput.textContent = JSON.stringify(data, null, 2);
        addAlert("info", "เรียก /content/debug สำเร็จ");
      } catch (e) {
        addAlert("danger", "เรียก /content/debug ล้มเหลว");
      }
    });

    // Client token
    clientTokenBtn?.addEventListener("click", async () => {
      try {
        const data = await jsonPost("/auth/client-token", {});
        clientTokenOutput.textContent = JSON.stringify(data, null, 2);
        addAlert("success", "ขอโทเค็นระดับไคลเอ็นต์สำเร็จ");
      } catch (e) {
        addAlert("danger", "ขอโทเค็นระดับไคลเอ็นต์ล้มเหลว");
      }
    });

    // Profile fetch
    fetchProfileBtn?.addEventListener("click", async () => {
      const tk = getToken();
      if (!tk) {
        addAlert("danger", "ยังไม่มีโทเค็น - กรุณาบันทึกโทเค็นก่อน");
        return;
      }
      try {
        const data = await jsonGet("/display/profile", { bearer: tk });
        const user = data?.data?.user || {};
        profileDisplayName.textContent = user.display_name || "-";
        profileOpenId.textContent = user.open_id || "-";
        const img = user.profile_image_url || "";
        if (img) {
          profileImage.src = img;
          profileImage.hidden = false;
        } else {
          profileImage.hidden = true;
        }
        const s = user.stats || {};
        statFollowers.textContent = s.follower_count ?? 0;
        statFollowing.textContent = s.following_count ?? 0;
        statLikes.textContent = s.likes_count ?? 0;
        statVideos.textContent = s.video_count ?? 0;

        addAlert("success", "ดึงข้อมูลโปรไฟล์สำเร็จ");
      } catch (e) {
        addAlert("danger", "ดึงข้อมูลโปรไฟล์ล้มเหลว");
      }
    });

    // Creator info
    creatorInfoBtn?.addEventListener("click", async () => {
      const tk = getToken();
      try {
        const q = tk ? `?access_token=${encodeURIComponent(tk)}` : "";
        const data = await jsonGet(`/content/creator-info${q}`);
        creatorInfoOutput.textContent = JSON.stringify(data, null, 2);
        addAlert("info", "ดึงข้อมูลผู้สร้างสำเร็จ");
      } catch (e) {
        addAlert("danger", "ดึงข้อมูลผู้สร้างล้มเหลว");
      }
    });

    // Upload file
    uploadFileForm?.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const file = uploadFileInput.files?.[0];
      if (!file) {
        addAlert("danger", "กรุณาเลือกไฟล์วิดีโอ");
        return;
      }
      try {
        const fd = new FormData();
        fd.append("file", file);
        fd.append("publish_mode", uploadFilePrivacy.value || "draft");
        const data = await formPost("/content/upload/file", fd);
        uploadFileOutput.textContent = JSON.stringify(data, null, 2);
        if (data?.job?.id) {
          addAlert("success", `อัปโหลดไฟล์สำเร็จ: job_id=${data.job.id}`);
          // Autofill status/publish forms with job id
          statusJobId.value = data.job.id;
          publishJobId.value = data.job.id;
        } else {
          addAlert("info", "อัปโหลดไฟล์เสร็จ แต่ไม่พบ job_id ในผลลัพธ์");
        }
      } catch (e) {
        addAlert("danger", "อัปโหลดไฟล์ล้มเหลว");
      }
    });

    // Upload by URL
    uploadUrlForm?.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const src = uploadUrlInput.value.trim();
      if (!src) {
        addAlert("danger", "กรุณาใส่ URL ของไฟล์");
        return;
      }
      try {
        const fd = new FormData();
        fd.append("source_url", src);
        fd.append("publish_mode", uploadUrlPrivacy.value || "draft");
        const data = await formPost("/content/upload/url", fd);
        uploadUrlOutput.textContent = JSON.stringify(data, null, 2);
        if (data?.job?.id) {
          addAlert("success", `สร้างงานดึงไฟล์สำเร็จ: job_id=${data.job.id}`);
          statusJobId.value = data.job.id;
          publishJobId.value = data.job.id;
        } else {
          addAlert("info", "สร้างงานเสร็จ แต่ไม่พบ job_id ในผลลัพธ์");
        }
      } catch (e) {
        addAlert("danger", "สร้างงานดึงไฟล์ล้มเหลว (URL อาจไม่อยู่ในโดเมนที่อนุญาต)");
      }
    });

    // Check status
    statusForm?.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const id = statusJobId.value.trim();
      if (!id) {
        addAlert("danger", "กรุณาใส่ job_id");
        return;
      }
      try {
        const data = await jsonGet(`/content/status/${encodeURIComponent(id)}`);
        statusOutput.textContent = JSON.stringify(data, null, 2);
        addAlert("info", `สถานะงาน: ${data?.status?.state || data?.status || data?.state || "unknown"}`);
      } catch (e) {
        addAlert("danger", "ตรวจสอบสถานะล้มเหลว");
      }
    });

    // Publish
    publishForm?.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const id = publishJobId.value.trim();
      if (!id) {
        addAlert("danger", "กรุณาใส่ job_id");
        return;
      }
      try {
        const fd = new FormData();
        fd.append("job_id", id);
        fd.append("privacy", publishPrivacy.value || "draft");
        const cap = publishCaption.value.trim();
        if (cap) fd.append("caption", cap);
        const data = await formPost("/content/publish", fd);
        publishOutput.textContent = JSON.stringify(data, null, 2);
        if (data?.result?.ok) {
          addAlert("success", "เผยแพร่สำเร็จ");
        } else {
          addAlert("info", `ผลลัพธ์เผยแพร่: ${JSON.stringify(data)}`);
        }
      } catch (e) {
        addAlert("danger", "เผยแพร่ล้มเหลว");
      }
    });
  }

  // Init
  function boot() {
    updateTokenStatus();
    initTabs();
    initControls();
  }

  document.addEventListener("DOMContentLoaded", boot);
})();