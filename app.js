(() => {
  const $ = (id) => document.getElementById(id);
  const KEY = "nila.mobile.v1";
  const starter = { messages: [], knowledge: [] };
  let data = loadData();
  let installPrompt = null;
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
      return "Naan Nila-oda first mobile prototype, chellam. Ippo indha phone browser-la chat history save pannalaam, Learning tab-la notes teach pannalaam, and un question-ku match aagura saved notes retrieve pannalaam. Idhu innum full language-model AI illa; OpenAI/Gemini/Claude API-um Python SQLite engine-um connect pannala.";
    }
    if (/teach|learn|note|knowledge|eppadi.*save/.test(lower)) {
      return "Learning tab open panni Note title + content enter panni “Save to Nila's knowledge” press pannu, chellam. Apram Chat-la andha topic pathi kelvi kelu. Naan saved notes-la irundhu matching content theduven.";
    }
    if (scored.length) {
      return "Un saved notes-la idhoda related information kidaichirukku, chellam:\n\n" + scored.map((x,i) => (i+1) + ". " + x.note.title + "\n" + x.note.content).join("\n\n") + "\n\nIdhu saved-note retrieval mattum; exact answer note-la illa na sollu, note-ai improve pannalaam.";
    }
    return "Chellam, indha kelvikku match aagura note innum en knowledge-la illa. Learning tab-la indha topic-ai note-aa save pannu; appuram naan adha search panni eduththu tharen. Ippo external AI model connect aagala, so saved notes-ku veliya irukkura kelvigalukku reliable answer generate panna mudiyadhu.";
  }
  function send(text) {
    const clean = text.trim(); if (!clean) return;
    addMessage("user", clean); addMessage("assistant", answerFor(clean)); saveData();
    $("chat-input").value = ""; $("chat-input").style.height = "auto";
    $("suggestions").hidden = true;
  }
  $("chat-form").addEventListener("submit", e => { e.preventDefault(); send($("chat-input").value); });
  $("chat-input").addEventListener("input", e => { e.target.style.height = "auto"; e.target.style.height = Math.min(e.target.scrollHeight,140) + "px"; });
  document.querySelectorAll("[data-prompt]").forEach(btn => btn.addEventListener("click", () => send(btn.dataset.prompt)));
  document.querySelectorAll("[data-view]").forEach(btn => btn.addEventListener("click", () => {
    document.querySelectorAll(".view").forEach(v => v.classList.toggle("active", v.id === btn.dataset.view));
    document.querySelectorAll(".nav-item").forEach(b => b.classList.toggle("selected", b === btn));
    window.scrollTo({top:0,behavior:"smooth"});
  }));
  $("knowledge-form").addEventListener("submit", e => {
    e.preventDefault(); const title = $("note-title").value.trim(), content = $("note-content").value.trim();
    if (!title || !content) return;
    data.knowledge.push({ id: Date.now().toString(36) + Math.random().toString(36).slice(2,7), title, content, at: new Date().toISOString() });
    $("note-title").value = ""; $("note-content").value = ""; saveData(); toast("Saved to Nila's knowledge.");
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
  if (!data.messages.length) {
    addMessage("assistant", "Vanakkam, chellam 💙 Naan Nila. Learning tab-la un notes add pannina, indha prototype andha notes-ai search panni chat-la kaattum. Idhu local demo; full AI model innum connect pannala.");
  }
  saveData();
})();