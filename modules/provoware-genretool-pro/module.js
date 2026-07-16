(() => {
  const STORAGE_KEY = "multimodultool2026.provoware-genretool-pro.v1";
  const SEED_URL = "genres_db.json";
  const MAX_ITEMS = 1800;
  const CATEGORIES = {
    genre: "Genre",
    mood: "Stimmung",
    style: "Stil",
    effect: "Effekt",
    theme: "Thema",
    special: "Besonderheit"
  };
  const state = loadState();
  let undoStack = [];
  let redoStack = [];
  let currentResults = [];

  const $ = (id) => document.getElementById(id);
  const els = {
    form: $("genretool-entry-form"), category: $("genretool-category"), term: $("genretool-term"),
    search: $("genretool-search"), filter: $("genretool-filter"), count: $("genretool-count"), list: $("genretool-list"),
    status: $("genretool-status"), resultCount: $("genretool-result-count"), generate: $("genretool-generate"),
    results: $("genretool-results"), history: $("genretool-history"), undo: $("genretool-undo"), redo: $("genretool-redo"),
    export: $("genretool-export"), import: $("genretool-import"), backup: $("genretool-backup"), reset: $("genretool-reset")
  };

  function emptyState() { return { items: [], history: [], updatedAt: new Date().toISOString() }; }
  function loadState() {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return emptyState();
    try {
      const data = JSON.parse(raw);
      return Array.isArray(data.items) && Array.isArray(data.history) ? data : emptyState();
    } catch {
      return emptyState();
    }
  }
  function save(message) {
    state.updatedAt = new Date().toISOString();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    setStatus(message);
    render();
  }
  function snapshot() { undoStack.push(JSON.stringify(state)); redoStack = []; }
  function restore(raw) {
    const data = JSON.parse(raw);
    state.items = data.items || [];
    state.history = data.history || [];
    save("Änderung wiederhergestellt. Daten wurden lokal gespeichert.");
  }
  function setStatus(message) { els.status.textContent = message; }
  function cleanTerm(value) { return value.trim().replace(/\s+/g, " ").slice(0, 80); }
  function exists(term, ignoreId = "") {
    const normalized = term.toLowerCase();
    return state.items.some((item) => item.id !== ignoreId && item.term.toLowerCase() === normalized);
  }
  function createId() { return `gt-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`; }
  function download(name, text) {
    const blob = new Blob([text], { type: "application/json;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = name;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  function addItem(category, term, favorite = false) {
    if (!CATEGORIES[category]) return "Kategorie ist ungültig. Nichts wurde gespeichert.";
    const cleaned = cleanTerm(term);
    if (!cleaned) return "Der Begriff ist leer. Nichts wurde gespeichert.";
    if (state.items.length >= MAX_ITEMS) return "Das Archiv ist voll. Nichts wurde gespeichert.";
    if (exists(cleaned)) return "Doppelter Begriff in der Datenbank. Nichts wurde gespeichert.";
    state.items.push({ id: createId(), category, term: cleaned, favorite, createdAt: new Date().toISOString() });
    return "";
  }

  function visibleItems() {
    const needle = els.search.value.trim().toLowerCase();
    const category = els.filter.value;
    return state.items.filter((item) => (category === "all" || item.category === category) && item.term.toLowerCase().includes(needle));
  }

  function renderList() {
    els.count.textContent = `${state.items.length} von ${MAX_ITEMS} Einträgen.`;
    const items = visibleItems();
    els.list.innerHTML = items.length ? "" : '<p class="genretool__meta">Keine passenden Einträge.</p>';
    items.forEach((item) => {
      const row = document.createElement("div");
      row.className = "genretool__item";
      row.innerHTML = `<div class="genretool__row"><strong>${escapeHtml(item.term)}</strong><span class="genretool__chip">${CATEGORIES[item.category]}</span></div>
        <div class="genretool__row"><button data-action="fav" data-id="${item.id}">${item.favorite ? "★ Favorit" : "☆ Favorit"}</button><button data-action="edit" data-id="${item.id}">Bearbeiten</button><button data-action="copy" data-id="${item.id}">Kopieren</button><button data-action="delete" data-id="${item.id}">Löschen</button></div>`;
      els.list.append(row);
    });
  }

  function renderResults() {
    els.results.innerHTML = currentResults.length ? "" : '<p class="genretool__meta">Noch keine Zufallsergebnisse.</p>';
    currentResults.forEach((result, index) => {
      const box = document.createElement("div");
      box.className = "genretool__result";
      const text = result.parts.map((part) => part.term).filter(Boolean).join(", ");
      box.innerHTML = `<strong>Ergebnis ${index + 1}</strong><div class="genretool__parts">${result.parts.map((part, partIndex) => `<button class="genretool__part ${part.locked ? "is-locked" : ""}" data-action="lock" data-result="${index}" data-part="${partIndex}">${CATEGORIES[part.category]}: ${escapeHtml(part.term || "fehlt")}</button>`).join("")}</div><div class="genretool__row"><button data-action="reroll" data-result="${index}">Offenes neu würfeln</button><button data-action="copy-result" data-result="${index}">Kopieren</button></div><p class="genretool__meta">${escapeHtml(text)}</p>`;
      els.results.append(box);
    });
  }

  function renderHistory() {
    els.history.innerHTML = state.history.length ? "" : '<p class="genretool__meta">Noch kein Verlauf.</p>';
    state.history.slice(0, 40).forEach((text) => {
      const row = document.createElement("div");
      row.className = "genretool__history-item";
      row.textContent = text;
      els.history.append(row);
    });
  }
  function render() { renderList(); renderResults(); renderHistory(); els.undo.disabled = !undoStack.length; els.redo.disabled = !redoStack.length; }
  function escapeHtml(value) { return value.replace(/[&<>"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[char])); }

  function randomPart(category, used = new Set()) {
    const pool = state.items.filter((item) => item.category === category && !used.has(item.term.toLowerCase()));
    if (!pool.length) return { category, term: "", locked: false };
    const item = pool[Math.floor(Math.random() * pool.length)];
    used.add(item.term.toLowerCase());
    return { category, term: item.term, locked: false };
  }
  function buildResult(existing = null) {
    const used = new Set();
    const parts = Object.keys(CATEGORIES).map((category, index) => {
      const old = existing?.parts[index];
      if (old?.locked) { used.add(old.term.toLowerCase()); return old; }
      return randomPart(category, used);
    });
    return { parts };
  }
  function addHistory(text) { state.history.unshift(`${new Date().toLocaleString()}: ${text}`); state.history = state.history.slice(0, 100); }

  function seedRows(data) {
    const aliases = { genres: "genre", moods: "mood", styles: "style", effects: "effect", themes: "theme", special: "special" };
    return Object.entries(data?.data || {}).flatMap(([key, values]) => {
      const category = aliases[key] || key;
      return Array.isArray(values) ? values.map((term) => ({ category, term })) : [];
    });
  }

  async function loadSeedIfEmpty() {
    if (state.items.length) return render();
    try {
      const response = await fetch(SEED_URL, { cache: "no-store" });
      if (!response.ok) throw new Error("Seed-Datei nicht erreichbar");
      const rows = seedRows(await response.json());
      rows.forEach((row) => addItem(row.category, row.term));
      save(`${state.items.length} Startbegriffe geladen und lokal gespeichert.`);
    } catch {
      setStatus("Startdaten konnten nicht geladen werden. Bitte Modul über einen lokalen Server öffnen oder eine Datei importieren. Nichts wurde gespeichert.");
      render();
    }
  }
  function copyText(text) {
    navigator.clipboard.writeText(text).then(() => setStatus("Text wurde kopiert. Daten wurden nicht verändert."), () => setStatus("Kopieren fehlgeschlagen. Bitte Text manuell markieren. Daten wurden nicht verändert."));
  }

  els.form.addEventListener("submit", (event) => {
    event.preventDefault();
    snapshot();
    const error = addItem(els.category.value, els.term.value);
    if (error) { undoStack.pop(); setStatus(error); return; }
    els.term.value = "";
    save("Eintrag gespeichert. Doppelungen wurden verhindert.");
  });
  els.search.addEventListener("input", renderList);
  els.filter.addEventListener("change", renderList);
  els.list.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-action]");
    if (!button) return;
    const item = state.items.find((entry) => entry.id === button.dataset.id);
    if (!item) return;
    if (button.dataset.action === "copy") return copyText(item.term);
    if (button.dataset.action === "edit") {
      const value = prompt("Begriff bearbeiten", item.term);
      const term = cleanTerm(value || "");
      if (!term) return setStatus("Bearbeitung abgebrochen. Nichts wurde gespeichert.");
      if (exists(term, item.id)) return setStatus("Doppelter Begriff in der Datenbank. Nichts wurde gespeichert.");
      snapshot(); item.term = term; save("Eintrag bearbeitet und lokal gespeichert."); return;
    }
    if (button.dataset.action === "delete" && !confirm("Eintrag wirklich löschen? Es wird vorher ein Undo-Punkt erstellt.")) return setStatus("Löschen abgebrochen. Nichts wurde verändert.");
    snapshot();
    if (button.dataset.action === "fav") item.favorite = !item.favorite;
    if (button.dataset.action === "delete") state.items = state.items.filter((entry) => entry.id !== item.id);
    save(button.dataset.action === "delete" ? "Eintrag gelöscht. Undo ist möglich." : "Favorit geändert und gespeichert.");
  });
  els.generate.addEventListener("click", () => {
    const amount = Math.min(12, Math.max(1, Number(els.resultCount.value) || 1));
    currentResults = Array.from({ length: amount }, () => buildResult());
    const lines = currentResults.map((result) => result.parts.map((part) => part.term).filter(Boolean).join(", ")).filter(Boolean);
    if (!lines.length) return setStatus("Keine Begriffe vorhanden. Bitte zuerst Einträge speichern. Nichts wurde verändert.");
    snapshot(); addHistory(lines.join(" | ")); save("Zufallsergebnisse erzeugt und im Verlauf gespeichert."); copyText(lines.join("\n"));
  });
  els.results.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-action]");
    if (!button) return;
    const result = currentResults[Number(button.dataset.result)];
    if (!result) return;
    if (button.dataset.action === "copy-result") return copyText(result.parts.map((part) => part.term).filter(Boolean).join(", "));
    if (button.dataset.action === "lock") result.parts[Number(button.dataset.part)].locked = !result.parts[Number(button.dataset.part)].locked;
    if (button.dataset.action === "reroll") currentResults[Number(button.dataset.result)] = buildResult(result);
    renderResults(); setStatus("Ergebnis angepasst. Archivdaten wurden nicht verändert.");
  });
  els.undo.addEventListener("click", () => { if (!undoStack.length) return; redoStack.push(JSON.stringify(state)); restore(undoStack.pop()); });
  els.redo.addEventListener("click", () => { if (!redoStack.length) return; undoStack.push(JSON.stringify(state)); restore(redoStack.pop()); });
  els.export.addEventListener("click", () => { download(`genretool-export-${new Date().toISOString().slice(0, 10)}.json`, JSON.stringify(state, null, 2)); setStatus("Export erstellt. Lokale Daten wurden nicht verändert."); });
  els.backup.addEventListener("click", () => { download(`genretool-backup-${new Date().toISOString().replace(/[:.]/g, "-")}.json`, JSON.stringify(state, null, 2)); setStatus("Backup-Datei erstellt. Lokale Daten wurden nicht verändert."); });
  els.reset.addEventListener("click", () => { if (!confirm("GenreTool wirklich zurücksetzen? Vorher wird ein Undo-Punkt erstellt.")) return setStatus("Zurücksetzen abgebrochen. Nichts wurde verändert."); snapshot(); state.items = []; state.history = []; currentResults = []; save("GenreTool zurückgesetzt. Undo ist möglich."); });
  els.import.addEventListener("change", async () => {
    const file = els.import.files[0]; els.import.value = "";
    if (!file) return;
    if (file.size > 8000000) return setStatus("Import ist zu groß. Nichts wurde gespeichert.");
    const text = await file.text();
    snapshot();
    let added = 0;
    try {
      added = importText(text, file.name);
    } catch {
      undoStack.pop();
      return setStatus("Import konnte nicht gelesen werden. Die Datei ist kein gültiges JSON/TXT/CSV. Nichts wurde gespeichert.");
    }
    if (!added) { undoStack.pop(); return setStatus("Import enthielt keine neuen gültigen Begriffe. Nichts wurde gespeichert."); }
    save(`${added} neue Begriffe importiert. Doppelungen wurden übersprungen.`);
  });
  function importText(text, name) {
    let rows = [];
    if (name.endsWith(".json")) {
      const data = JSON.parse(text);
      rows = Array.isArray(data.items) ? data.items : [];
    } else {
      rows = text.split(/[\n,;]/).map((term) => ({ category: els.category.value, term }));
    }
    let added = 0;
    rows.forEach((row) => { if (!addItem(row.category || els.category.value, row.term || row.name || row.value || "")) added += 1; });
    return added;
  }
  loadSeedIfEmpty();
})();
