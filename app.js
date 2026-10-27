(() => {
  const $ = (id) => document.getElementById(id);
  const KEY = "nila.mobile.v1";
  const starter = { messages: [], knowledge: [] };
  let data = loadData();
  let installPrompt = null;
  const API_KEY = "nila.api.config.v1";
  function apiConfig() { try { return JSON.parse(localStorage.getItem(API_KEY) || "{}"); } catch { return {}; } }
  function setApiStatus(message) { const el = $("api-status"); if (el) el.textContent = message; const hint = $("connection-hint"); if (hint) hint.textContent = apiConfig().url ? "Python backend configured · Replies use Nila agent + SQLite when online" : "Local notes mode · Configure Python backend in Settings to sync with SQLite"; }
  async function apiRequest(path, options = {}) {
    const cfg = apiConfig();
    if (!cfg.url || !cfg.token) throw new Error("Backend URL/token not configured");
    const response = await fetch(cfg.url.replace(/\/$/, "") + path, { ...options, headers: { "Content-Type": "application/json", "Authorization": "Bearer " + cfg.token, ...(options.headers || {}) } });
    if (!response.ok) throw new Error("Backend returned HTTP " + response.status);
    return response.json();
  }
  function loadData() {
    try { return Object.assign({}, starter, JSON.parse(localStorage.getItem(KEY) || "{}")); }
    catch { return structuredClone(starter); }
  }
  function saveData() {
    try { localStorage.setItem(KEY, JSON.stringify(data)); }
    catch { toast("Storage is full. Export a backup or remove some data."); }
    renderMessages(); renderKnowledge(); renderStats();
  }
  function toast(msg) {
    const el = $("toast"); el.textContent = msg; el.classList.add("show");
    clearTimeout(toast.timer); toast.timer = setTimeout(() => el.classList.remove("show"), 2600);
  }
  function safeText(value) { return String(value ?? ""); }
  function renderMessages() {
    const box = $("messages"); box.replaceChildren();
    data.messages.slice(-80).forEach(m => {
      const article = document.createElement("div"); article.className = "message " + (m.role === "user" ? "user" : "assistant");
      const who = document.createElement("span"); who.className = "who"; who.textContent = m.role === "user" ? "YOU" : "NILA";
      const body = document.createElement("div"); body.textContent = safeText(m.text);
      article.append(who, body); box.append(article);
    });
    box.scrollTop = box.scrollHeight;
  }
  function renderKnowledge() {
    const box = $("knowledge-list"); box.replaceChildren();
    $("knowledge-count").textContent = data.knowledge.length;
    if (!data.knowledge.length) { const e = document.createElement("div"); e.className = "empty"; e.textContent = "No notes yet. Add a note above to start teaching Nila."; box.append(e); return; }
    [...data.knowledge].reverse().forEach(note => {
      const card = document.createElement("article"); card.className = "knowledge-card";
      const title = document.createElement("h4"); title.textContent = note.title;
      const content = document.createElement("p"); content.textContent = note.content;
      const del = document.createElement("button"); del.type = "button"; del.textContent = "Delete note";
      del.addEventListener("click", () => { data.knowledge = data.knowledge.filter(n => n.id !== note.id); saveData(); toast("Note deleted."); });
      card.append(title, content, del); box.append(card);
    });
  }
  function renderStats() { $("message-count").textContent = data.messages.length; }
  function addMessage(role, text) { data.messages.push({ role, text, at: new Date().toISOString() }); }
  function words(text) { return String(text).toLowerCase().match(/[a-z0-9]+|[\u0B80-\u0BFF]+/g) || []; }
  function answerFor(question) {
    const q = words(question);
    if (!q.length) return "Chellam, konjam clear-aa type pannu. Un notes-la irundhu thedi help panren.";
    const scored = data.knowledge.map(note => {
      const noteWords = new Set(words(note.title + " " + note.content));
      const score = q.reduce((n, w) => n + (noteWords.has(w) ? 1 : 0), 0);
      return { note, score };
    }).filter(x => x.score > 0).sort((a,b) => b.score-a.score).slice(0,3);
    const lower = question.toLowerCase();
    if (/what can you do|help|enna pann|what are you/.test(lower)) {
      return "Naan Nila mobile app, chellam. Chat + Learning notes + optional Python backend (agent retrieval). Full AGI model illa — saved knowledge + SQLite engine.";
    }
    if (/teach|learn|note|knowledge|eppadi.*save/.test(lower)) {
      return "Learning tab open panni Note title + content save pannu. Backend connect pannina SQLite-kum sync aagum.";
    }
    if (scored.length) {
      return "Un saved notes-la related info:\n\n" + scored.map((x,i) => (i+1) + ". " + x.note.title + "\n" + x.note.content).join("\n\n");
    }
    return "Match aagura note illa. Learning tab-la topic save pannu, or backend connect panni learn sessions run pannu.";
  }
  async function send(text) {
    const clean = text.trim(); if (!clean) return;
    addMessage("user", clean);
    const answerIndex = data.messages.length;
    addMessage("assistant", "Nila is thinking…"); saveData();
    $("chat-input").value = ""; $("chat-input").style.height = "auto";
    $("suggestions").hidden = true;
    try {
      const result = await apiRequest("/api/chat", { method: "POST", body: JSON.stringify({ message: clean, mode: "agent" }) });
      let reply = result.answer || "Backend returned an empty answer.";
      if (Array.isArray(result.suggestions) && result.suggestions.length) {
        reply += "\n\nSuggestions:\n- " + result.suggestions.join("\n- ");
      }
      data.messages[answerIndex].text = reply;
      setApiStatus("Connected · " + (result.engine || "Nila Python engine"));
    } catch (err) {
      data.messages[answerIndex].text = answerFor(clean);
      if (apiConfig().url) setApiStatus("Backend unavailable; using phone-local notes. Check URL, token, or server status.");
    }
    saveData();
  }
  $("chat-form").addEventListener("submit", e => { e.preventDefault(); send($("chat-input").value); });
  $("chat-input").addEventListener("input", e => { e.target.style.height = "auto"; e.target.style.height = Math.min(e.target.scrollHeight,140) + "px"; });
  document.querySelectorAll("[data-prompt]").forEach(btn => btn.addEventListener("click", () => send(btn.dataset.prompt)));
  document.querySelectorAll("[data-view]").forEach(btn => btn.addEventListener("click", () => {
    document.querySelectorAll(".view").forEach(v => v.classList.toggle("active", v.id === btn.dataset.view));
    document.querySelectorAll(".nav-item").forEach(b => b.classList.toggle("selected", b === btn));
    window.scrollTo({top:0,behavior:"smooth"});
  }));
  $("knowledge-form").addEventListener("submit", async e => {
    e.preventDefault(); const title = $("note-title").value.trim(), content = $("note-content").value.trim();
    if (!title || !content) return;
    data.knowledge.push({ id: Date.now().toString(36) + Math.random().toString(36).slice(2,7), title, content, at: new Date().toISOString() });
    $("note-title").value = ""; $("note-content").value = ""; saveData();
    try {
      const result = await apiRequest("/api/knowledge", { method: "POST", body: JSON.stringify({ title, content, source: "Nila phone app", verified: false, topic: "" }) });
      toast("Saved on phone + Python SQLite (ID " + result.id + ").");
    } catch (err) {
      toast(apiConfig().url ? "Saved on phone only; backend sync failed." : "Saved on this phone. Connect backend in Settings to sync.");
    }
  });

  $("api-form").addEventListener("submit", async e => {
    e.preventDefault();
    const url = $("api-url").value.trim().replace(/\/$/, "");
    const token = $("api-token").value.trim();
    if (!url || !token) { setApiStatus("Enter both backend URL and access token."); return; }
    if (!url.startsWith("https://") && !url.startsWith("http://localhost") && !url.startsWith("http://127.0.0.1")) {
      setApiStatus("Use HTTPS (or localhost for testing)."); return;
    }
    localStorage.setItem(API_KEY, JSON.stringify({ url, token }));
    setApiStatus("Testing secure connection…");
    try {
      const health = await fetch(url + "/api/health");
      if (!health.ok) throw new Error("Health check failed: HTTP " + health.status);
      const test = await apiRequest("/api/chat", { method: "POST", body: JSON.stringify({ message: "connection test", mode: "agent" }) });
      setApiStatus("Connected successfully · " + (test.engine || "Nila Python engine"));
      toast("Nila Python backend connected, chellam!");
    } catch (err) {
      setApiStatus("Could not connect. Check the URL, token, CORS settings, and whether the server is awake.");
    }
  });
  $("clear-notes").addEventListener("click", () => {
    if (!data.knowledge.length) return toast("There are no notes to clear.");
    if (confirm("Delete all saved knowledge notes? This cannot be undone unless you exported a backup.")) { data.knowledge = []; saveData(); toast("Knowledge notes cleared."); }
  });
  $("export-btn").addEventListener("click", () => {
    const blob = new Blob([JSON.stringify(data,null,2)], {type:"application/json"});
    const url = URL.createObjectURL(blob); const a = document.createElement("a");
    a.href = url; a.download = "nila-backup.json"; a.click(); URL.revokeObjectURL(url); toast("Backup export started.");
  });
  $("import-file").addEventListener("change", async e => {
    const file = e.target.files && e.target.files[0]; if (!file) return;
    try {
      const imported = JSON.parse(await file.text());
      if (!Array.isArray(imported.messages) || !Array.isArray(imported.knowledge)) throw new Error("Invalid backup");
      if (!confirm("Replace this device's Nila data with the selected backup?")) return;
      data = { messages: imported.messages, knowledge: imported.knowledge }; saveData(); toast("Nila backup restored.");
    } catch { toast("Could not import that file. Choose a valid Nila JSON backup."); }
    finally { e.target.value = ""; }
  });
  window.addEventListener("beforeinstallprompt", e => { e.preventDefault(); installPrompt = e; });
  $("install-btn").addEventListener("click", async () => {
    if (installPrompt) { installPrompt.prompt(); await installPrompt.userChoice; installPrompt = null; }
    else toast("Chrome menu ⋮ → Add to Home screen / Install app use pannu.");
  });
  if ("serviceWorker" in navigator && (location.protocol === "https:" || location.hostname === "localhost")) {
    window.addEventListener("load", () => navigator.serviceWorker.register("./sw.js").catch(() => {}));
  }
  const REPO_RELEASES_API = "https://api.github.com/repos/kirushnakanthan2021-crypto/Nila/releases/latest";
  let availableApkUrl = "";
  async function checkForUpdates() {
    try {
      const [versionResponse, releaseResponse] = await Promise.all([
        fetch("./app-version.json?ts=" + Date.now(), { cache: "no-store" }),
        fetch(REPO_RELEASES_API, { headers: { Accept: "application/vnd.github+json" }, cache: "no-store" })
      ]);
      if (!versionResponse.ok || !releaseResponse.ok) return;
      const localVersion = await versionResponse.json();
      const release = await releaseResponse.json();
      if (!release || release.draft || release.prerelease || !release.tag_name) return;
      const localTag = String(localVersion.version || "v0.0.0");
      if (release.tag_name === localTag) return;
      const apk = (release.assets || []).find(asset => asset.name && asset.name.endsWith(".apk"));
      if (!apk) return;
      availableApkUrl = apk.browser_download_url || release.html_url;
      const banner = $("update-banner");
      if (!banner) return;
      $("update-copy").textContent = "Installed " + localTag + " · Available " + release.tag_name + ". Download the APK, then open it from Downloads to install.";
      banner.hidden = false;
      $("update-btn").onclick = () => {
        if (availableApkUrl) window.open(availableApkUrl, "_blank", "noopener");
        else window.open(release.html_url, "_blank", "noopener");
      };
      $("dismiss-update").onclick = () => { banner.hidden = true; };
    } catch { /* offline */ }
  }
  const savedConfig = apiConfig();
  if ($("api-url")) $("api-url").value = savedConfig.url || "";
  if ($("api-token")) $("api-token").value = savedConfig.token || "";
  if (savedConfig.url) setApiStatus("Backend configured. Press Save & test connection to verify.");
  if (!data.messages.length) {
    addMessage("assistant", "Vanakkam, chellam 💙 Naan Nila v0.3. Backend connect pannina agent + SQLite use aagum. Local notes mode-um work aagum.");
  }
  saveData();
  checkForUpdates();
})();
