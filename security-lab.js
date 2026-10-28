(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const STORAGE_KEY = "nila.security.lab.v1";
  const catalog = {
    surface: [
      ["Inventory assets in scope", "List approved hosts, subdomains, API base paths, app versions and owners. Mark excluded production systems explicitly.", "FOUNDATION"],
      ["Map entry points", "Document login, password reset, upload, search, import/export, admin and API routes from source/docs or normal app use.", "RECON"],
      ["Review public exposure", "In the owner-controlled deployment, check whether debug pages, directory indexes, backups or source maps are intentionally public.", "CONFIG"]
    ],
    auth: [
      ["Review account recovery", "Use test accounts to check reset-token expiry, single use, rate limiting and whether responses reveal account existence.", "AUTH"],
      ["Review session lifecycle", "Confirm cookies use Secure, HttpOnly and appropriate SameSite; verify logout and password changes invalidate sessions as designed.", "AUTH"],
      ["Review MFA and brute-force controls", "Verify MFA enforcement and rate limits with approved test accounts, staying within the written request budget.", "AUTH"]
    ],
    access: [
      ["Build a role-permission matrix", "For each role, record allowed actions and resources. Compare expected permissions with actual behavior in staging.", "ACCESS CONTROL"],
      ["Test object ownership with two test users", "Create synthetic records for user A and B. Verify A cannot read or modify B's records by changing identifiers in the normal UI/API workflow.", "IDOR"],
      ["Check tenant isolation", "If the app is multi-tenant, verify every data query is scoped server-side to the authenticated tenant, not just hidden in the UI.", "ACCESS CONTROL"]
    ],
    input: [
      ["Trace untrusted input to sensitive sinks", "Review where user input reaches SQL, shell commands, templates, file paths, URLs or HTML. Prefer parameterized APIs and allowlists.", "CODE REVIEW"],
      ["Review output encoding", "Check that untrusted text is rendered as text or contextually encoded; use harmless marker strings in a test environment.", "XSS PREVENTION"],
      ["Review file upload handling", "Check type/size limits, generated storage names, storage outside executable web roots, malware handling and authorization on download.", "INPUT HANDLING"]
    ],
    config: [
      ["Review transport and browser headers", "For the authorized deployment, verify HTTPS, HSTS where appropriate, CSP, frame protections, content-type sniffing protection and referrer policy.", "CONFIG"],
      ["Search repository history for secrets", "Use secret-scanning tools on the owned repository. Rotate any exposed credential; removing a line alone does not revoke it.", "SECRETS"],
      ["Check environment separation", "Verify debug mode is off in production, least-privilege service accounts are used, and staging data/credentials are not production copies.", "CONFIG"]
    ],
    api: [
      ["Validate API schemas and errors", "Confirm server-side types, lengths, enums and authorization are enforced. Errors should not expose stack traces or secrets.", "API"],
      ["Review rate limits and resource caps", "Check per-user limits, pagination caps, upload sizes and expensive operations using a documented, low-volume test plan.", "API"],
      ["Test business invariants", "Use test data to verify price, ownership, status transitions and quotas are enforced on the server, including repeated or out-of-order requests.", "BUSINESS LOGIC"]
    ],
    deps: [
      ["Run dependency and secret scanners", "For your repository, run Dependabot or OSV-Scanner and a secret scanner; triage findings against lockfiles and reachable code.", "SCA"],
      ["Review dangerous code patterns", "Search owned source for unsafe deserialization, dynamic evaluation, shell invocation, path concatenation and disabled TLS verification.", "SAST"],
      ["Add regression tests", "For each confirmed bug, add a test that fails before the fix and passes after it; document the fixed version and retest.", "REMEDIATION"]
    ],
    ai: [
      ["Threat-model prompt injection", "Use synthetic data to check whether untrusted documents can influence the model to ignore policy or mislabel data as trusted instructions.", "LLM SECURITY"],
      ["Audit tool permissions", "Confirm each AI tool has least privilege, strict argument validation, an allowlist, and human approval for consequential actions.", "AGENT SECURITY"],
      ["Test data boundaries", "Verify secrets, private memory and one user's data are not exposed to another user or sent to external providers without clear consent.", "PRIVACY"]
    ]
  };
  let state = load();
  function load() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{"target":"","scope":"","items":{}}'); }
    catch { return { target: "", scope: "", items: {} }; }
  }
  function save() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }
    catch { /* the report can still be exported */ }
  }
  function selectedTopics() {
    return [...document.querySelectorAll("#security-topics input:checked")].map(el => el.value);
  }
  function renderChecklist() {
    const box = $("security-checklist");
    if (!box) return;
    box.replaceChildren();
    const entries = selectedTopics().flatMap(topic => (catalog[topic] || []).map((item, index) => ({
      id: topic + "-" + index, topic, title: item[0], detail: item[1], tag: item[2]
    })));
    if (!state.target || !entries.length) {
      const empty = document.createElement("div"); empty.className = "empty";
      empty.textContent = "Enter an authorized target and select at least one review area.";
      box.append(empty); return;
    }
    const intro = document.createElement("p"); intro.className = "muted";
    intro.textContent = "Target: " + state.target + " · Local checklist only; no network traffic sent.";
    box.append(intro);
    const progress = document.createElement("p"); progress.className = "security-progress";
    const done = entries.filter(item => state.items[item.id]).length;
    progress.textContent = done + " of " + entries.length + " checks completed";
    box.append(progress);
    entries.forEach(item => {
      const row = document.createElement("label"); row.className = "security-check-item";
      const check = document.createElement("input"); check.type = "checkbox"; check.checked = !!state.items[item.id];
      check.addEventListener("change", () => { state.items[item.id] = check.checked; save(); renderChecklist(); });
      const copy = document.createElement("span");
      const title = document.createElement("strong"); title.textContent = item.title;
      const detail = document.createElement("p"); detail.textContent = item.detail;
      const tag = document.createElement("span"); tag.className = "security-tag"; tag.textContent = item.tag;
      copy.append(title, detail, tag); row.append(check, copy); box.append(row);
    });
  }
  $("security-scope-form")?.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!$("security-authorized").checked) {
      $("security-scope-status").textContent = "Confirm ownership or explicit authorization before creating a checklist.";
      return;
    }
    if (!$("security-safe-mode").checked) {
      $("security-scope-status").textContent = "This version supports checklist-only mode. Keep non-invasive mode enabled.";
      return;
    }
    const target = $("security-target").value.trim();
    if (!target) return;
    state.target = target;
    state.scope = $("security-scope").value.trim();
    save();
    $("security-scope-status").textContent = "Scope saved on this device. No request was sent to the target.";
    renderChecklist();
  });
  document.querySelectorAll("#security-topics input").forEach(input => input.addEventListener("change", renderChecklist));
  $("security-export")?.addEventListener("click", () => {
    if (!state.target) { window.alert("Create an authorized scope first."); return; }
    const selected = selectedTopics();
    const checks = selected.flatMap(topic => (catalog[topic] || []).map((item, index) => ({
      id: topic + "-" + index, topic, title: item[0], guidance: item[1],
      status: state.items[topic + "-" + index] ? "completed" : "not yet completed"
    })));
    const report = {
      product: "Nila Security Lab",
      generatedAt: new Date().toISOString(),
      target: state.target,
      authorizationScopeNotes: state.scope,
      mode: "non-invasive checklist; no target requests made",
      checks
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url; link.download = "nila-security-review.json"; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  if (state.target) {
    $("security-target").value = state.target;
    $("security-scope").value = state.scope || "";
    $("security-scope-status").textContent = "Previously saved local scope: " + state.target;
    $("security-authorized").checked = false;
  }
  renderChecklist();
})();
