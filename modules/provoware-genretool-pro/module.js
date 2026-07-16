(() => {
  "use strict";

  const root = document.querySelector('[data-module-id="provoware-genretool-pro"]');
  if (!root) return;

  const STORAGE_KEY = "multimodultool2026.provoware-genretool-pro.v2";
  const BACKUP_KEY = `${STORAGE_KEY}.backup`;
  const moduleBase = document.currentScript?.dataset.moduleBase || globalThis.location.href;
  const SEED_URL = new URL("genres_db.json", moduleBase).href;
  const MAX_ITEMS = 5000;
  const MAX_IMPORT_BYTES = 8_000_000;
  const PAGE_SIZE = 40;
  const HISTORY_LIMIT = 50;
  const CATEGORY_DEFS = [
    ["genres", "Genres"],
    ["moods", "Stimmungen"],
    ["styles", "Stile"],
    ["effects", "Effekte"],
    ["themes", "Themen"],
    ["special", "Besonderes"]
  ];
  const CATEGORY_LABELS = Object.fromEntries(CATEGORY_DEFS);
  const CATEGORY_ALIASES = {
    genre: "genres", genres: "genres",
    mood: "moods", moods: "moods",
    style: "styles", styles: "styles",
    effect: "effects", effects: "effects",
    theme: "themes", themes: "themes",
    special: "special", besondere: "special", besonderes: "special"
  };

  const q = (selector) => root.querySelector(selector);
  const qa = (selector) => [...root.querySelectorAll(selector)];
  const els = {
    status: q('[data-role="status"]'),
    form: q('[data-role="entry-form"]'),
    entryCategory: q('[data-role="entry-category"]'),
    entryTerms: q('[data-role="entry-terms"]'),
    count: q('[data-role="count"]'),
    search: q('[data-role="search"]'),
    filterCategory: q('[data-role="filter-category"]'),
    sort: q('[data-role="sort"]'),
    list: q('[data-role="list"]'),
    pageInfo: q('[data-role="page-info"]'),
    categoryMixer: q('[data-role="category-mixer"]'),
    resultCount: q('[data-role="result-count"]'),
    avoidRecent: q('[data-role="avoid-recent"]'),
    favoritesFirst: q('[data-role="favorites-first"]'),
    autoCopy: q('[data-role="auto-copy"]'),
    results: q('[data-role="results"]'),
    history: q('[data-role="history"]'),
    importInput: q('[data-role="import"]'),
    editDialog: q('[data-role="edit-dialog"]'),
    editForm: q('[data-role="edit-form"]'),
    editCategory: q('[data-role="edit-category"]'),
    editTerm: q('[data-role="edit-term"]')
  };

  let state = loadState();
  let undoStack = [];
  let redoStack = [];
  let page = 1;
  let currentResults = [];
  let editingId = "";

  function emptyState() {
    return {
      schemaVersion: 2,
      items: [],
      history: [],
      recentTerms: [],
      updatedAt: new Date().toISOString()
    };
  }

  function cleanTerm(value) {
    return String(value ?? "")
      .replace(/[\u0000-\u001F\u007F]+/g, " ")
      .replace(/\s+/g, " ")
      .trim()
      .slice(0, 80);
  }

  function normalizeKey(value) {
    return cleanTerm(value).toLocaleLowerCase("de-DE");
  }

  function normalizeCategory(value) {
    return CATEGORY_ALIASES[String(value ?? "").toLowerCase()] || "";
  }

  function newId() {
    return globalThis.crypto?.randomUUID?.() || `gt-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 9)}`;
  }

  function normalizeItem(raw, existingKeys = new Set()) {
    const category = normalizeCategory(raw?.category);
    const term = cleanTerm(raw?.term ?? raw?.name ?? raw?.value);
    const key = normalizeKey(term);
    if (!category || !term || existingKeys.has(key)) return null;
    existingKeys.add(key);
    return {
      id: cleanTerm(raw?.id) || newId(),
      category,
      term,
      favorite: Boolean(raw?.favorite),
      source: raw?.source === "custom" ? "custom" : "seed",
      createdAt: cleanTerm(raw?.createdAt) || new Date().toISOString()
    };
  }

  function normalizeState(raw) {
    const output = emptyState();
    const keys = new Set();
    output.items = (Array.isArray(raw?.items) ? raw.items : [])
      .slice(0, MAX_ITEMS)
      .map(item => normalizeItem(item, keys))
      .filter(Boolean);
    output.history = (Array.isArray(raw?.history) ? raw.history : [])
      .slice(0, HISTORY_LIMIT)
      .map(entry => ({
        id: cleanTerm(entry?.id) || newId(),
        text: cleanTerm(entry?.text ?? entry),
        createdAt: cleanTerm(entry?.createdAt) || new Date().toISOString()
      }))
      .filter(entry => entry.text);
    output.recentTerms = (Array.isArray(raw?.recentTerms) ? raw.recentTerms : [])
      .map(normalizeKey)
      .filter(Boolean)
      .slice(0, 100);
    output.updatedAt = cleanTerm(raw?.updatedAt) || new Date().toISOString();
    return output;
  }

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? normalizeState(JSON.parse(raw)) : emptyState();
    } catch (error) {
      console.warn("GenreTool-Speicher konnte nicht gelesen werden", error);
      return emptyState();
    }
  }

  function persist(message = "Lokal gespeichert.") {
    try {
      state.updatedAt = new Date().toISOString();
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      setStatus(message, "success");
      renderAll();
      return true;
    } catch (error) {
      console.error(error);
      setStatus("Speichern fehlgeschlagen. Browser-Speicher prüfen oder Daten exportieren.", "error");
      return false;
    }
  }

  function setStatus(message, level = "info") {
    els.status.textContent = message;
    els.status.dataset.level = level;
  }

  function snapshot() {
    undoStack.push(JSON.stringify(state));
    if (undoStack.length > 30) undoStack.shift();
    redoStack = [];
  }

  function restoreSnapshot(raw, message) {
    state = normalizeState(JSON.parse(raw));
    persist(message);
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, char => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[char]);
  }

  function populateControls() {
    const options = CATEGORY_DEFS.map(([id, label]) => `<option value="${id}">${label}</option>`).join("");
    els.entryCategory.innerHTML = options;
    els.editCategory.innerHTML = options;
    els.filterCategory.insertAdjacentHTML("beforeend", options);
    els.categoryMixer.innerHTML = CATEGORY_DEFS.map(([id, label]) =>
      `<label><input type="checkbox" value="${id}" checked> ${label}</label>`
    ).join("");
  }

  function hasTerm(term, ignoreId = "") {
    const key = normalizeKey(term);
    return state.items.some(item => item.id !== ignoreId && normalizeKey(item.term) === key);
  }

  function splitTerms(value) {
    return String(value).split(/[\n,;]+/).map(cleanTerm).filter(Boolean);
  }

  function addTerms(category, terms, source = "custom") {
    const normalizedCategory = normalizeCategory(category);
    if (!normalizedCategory) return { added: 0, skipped: terms.length, full: false };
    let added = 0;
    let skipped = 0;
    for (const term of terms) {
      if (state.items.length >= MAX_ITEMS) return { added, skipped, full: true };
      if (!term || hasTerm(term)) { skipped += 1; continue; }
      state.items.push({
        id: newId(), category: normalizedCategory, term: cleanTerm(term),
        favorite: false, source, createdAt: new Date().toISOString()
      });
      added += 1;
    }
    return { added, skipped, full: false };
  }

  function filteredItems() {
    const needle = normalizeKey(els.search.value);
    const category = els.filterCategory.value;
    const list = state.items.filter(item =>
      (category === "all" || item.category === category) &&
      (!needle || normalizeKey(item.term).includes(needle))
    );
    const collator = new Intl.Collator("de-DE", { sensitivity: "base", numeric: true });
    const sort = els.sort.value;
    list.sort((a, b) => {
      if (sort === "favorites" && a.favorite !== b.favorite) return a.favorite ? -1 : 1;
      if (sort === "custom" && a.source !== b.source) return a.source === "custom" ? -1 : 1;
      const base = collator.compare(a.term, b.term);
      return sort === "za" ? -base : base;
    });
    return list;
  }

  function renderArchive() {
    const all = filteredItems();
    const pages = Math.max(1, Math.ceil(all.length / PAGE_SIZE));
    page = Math.min(Math.max(1, page), pages);
    const visible = all.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
    els.count.textContent = `${state.items.length} Einträge · ${all.length} sichtbar`;
    els.pageInfo.textContent = `Seite ${page} von ${pages}`;
    q('[data-action="page-prev"]').disabled = page <= 1;
    q('[data-action="page-next"]').disabled = page >= pages;
    els.list.innerHTML = visible.length ? visible.map(item => `
      <article class="genretool__item" data-id="${escapeHtml(item.id)}">
        <div class="genretool__row">
          <div class="genretool__item-main"><strong>${escapeHtml(item.term)}</strong><span class="genretool__chip">${escapeHtml(CATEGORY_LABELS[item.category])}</span></div>
          <div class="genretool__item-actions">
            <button type="button" class="genretool__secondary" data-item-action="favorite">${item.favorite ? "★" : "☆"}</button>
            <button type="button" class="genretool__secondary" data-item-action="copy">Kopieren</button>
            <button type="button" class="genretool__secondary" data-item-action="edit">Bearbeiten</button>
            <button type="button" class="genretool__danger" data-item-action="delete">Löschen</button>
          </div>
        </div>
      </article>`).join("") : '<div class="genretool__empty">Keine passenden Einträge.</div>';
  }

  function selectedCategories() {
    return qa('[data-role="category-mixer"] input:checked').map(input => input.value);
  }

  function weightedPick(pool) {
    if (!pool.length) return null;
    if (!els.favoritesFirst.checked) return pool[Math.floor(Math.random() * pool.length)];
    const favorites = pool.filter(item => item.favorite);
    const source = favorites.length && Math.random() < 0.7 ? favorites : pool;
    return source[Math.floor(Math.random() * source.length)];
  }

  function pickItem(category, used, recent) {
    let pool = state.items.filter(item => item.category === category && !used.has(normalizeKey(item.term)));
    if (els.avoidRecent.checked) {
      const fresh = pool.filter(item => !recent.has(normalizeKey(item.term)));
      if (fresh.length) pool = fresh;
    }
    const item = weightedPick(pool);
    if (item) used.add(normalizeKey(item.term));
    return item;
  }

  function buildResult(previous = null) {
    const categories = selectedCategories();
    const used = new Set();
    const recent = new Set(state.recentTerms);
    return {
      id: previous?.id || newId(),
      parts: categories.map(category => {
        const locked = previous?.parts?.find(part => part.category === category && part.locked);
        if (locked) { used.add(normalizeKey(locked.term)); return locked; }
        const item = pickItem(category, used, recent);
        return { category, term: item?.term || "Kein Eintrag", itemId: item?.id || "", locked: false };
      })
    };
  }

  function resultText(result) {
    return result.parts.map(part => `${CATEGORY_LABELS[part.category]}: ${part.term}`).join(" | ");
  }

  function renderResults() {
    els.results.innerHTML = currentResults.length ? currentResults.map((result, resultIndex) => `
      <article class="genretool__result" data-result-index="${resultIndex}">
        <div class="genretool__row"><strong>Ergebnis ${resultIndex + 1}</strong><button type="button" class="genretool__secondary" data-result-action="copy">Kopieren</button></div>
        <div class="genretool__parts">${result.parts.map((part, partIndex) => `
          <div class="genretool__part ${part.locked ? "is-locked" : ""}">
            <span><strong>${escapeHtml(CATEGORY_LABELS[part.category])}:</strong> ${escapeHtml(part.term)}</span>
            <button type="button" class="genretool__secondary" data-result-action="lock" data-part-index="${partIndex}">${part.locked ? "🔒" : "🔓"}</button>
          </div>`).join("")}</div>
        <button type="button" class="genretool__secondary" data-result-action="reroll">Offene Teile neu würfeln</button>
      </article>`).join("") : '<div class="genretool__empty">Noch keine Ergebnisse erzeugt.</div>';
  }

  function renderHistory() {
    els.history.innerHTML = state.history.length ? state.history.map(entry => `
      <div class="genretool__history-item"><div class="genretool__row"><span>${escapeHtml(entry.text)}</span><button type="button" class="genretool__secondary" data-history-id="${escapeHtml(entry.id)}">Kopieren</button></div></div>`).join("") : '<div class="genretool__empty">Noch kein Verlauf.</div>';
  }

  function renderButtons() {
    q('[data-action="undo"]').disabled = !undoStack.length;
    q('[data-action="redo"]').disabled = !redoStack.length;
  }

  function renderAll() {
    renderArchive();
    renderResults();
    renderHistory();
    renderButtons();
  }

  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
      setStatus("In die Zwischenablage kopiert.", "success");
    } catch {
      const area = document.createElement("textarea");
      area.value = text;
      area.style.position = "fixed";
      area.style.opacity = "0";
      document.body.append(area);
      area.select();
      const ok = document.execCommand("copy");
      area.remove();
      setStatus(ok ? "In die Zwischenablage kopiert." : "Kopieren fehlgeschlagen.", ok ? "success" : "error");
    }
  }

  function download(filename, content, type = "application/json") {
    const url = URL.createObjectURL(new Blob([content], { type: `${type};charset=utf-8` }));
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  function seedRows(seed) {
    return Object.entries(seed?.data || {}).flatMap(([category, values]) =>
      Array.isArray(values) ? values.map(term => ({ category, term, source: "seed" })) : []
    );
  }

  async function fetchSeed() {
    const response = await fetch(SEED_URL, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const seed = await response.json();
    const rows = seedRows(seed);
    if (!rows.length) throw new Error("Startdaten sind leer");
    return rows;
  }

  async function loadSeedIfEmpty() {
    if (state.items.length) {
      setStatus(`${state.items.length} Begriffe geladen.`, "success");
      renderAll();
      return;
    }
    try {
      const rows = await fetchSeed();
      addTermsFromRows(rows);
      persist(`${state.items.length} Startbegriffe geladen.`);
    } catch (error) {
      console.warn(error);
      setStatus("Startdaten konnten nicht geladen werden. Bitte über den lokalen Server starten oder eine Datei importieren.", "error");
      renderAll();
    }
  }

  function addTermsFromRows(rows) {
    let added = 0;
    let skipped = 0;
    for (const row of rows) {
      const category = normalizeCategory(row?.category);
      const term = cleanTerm(row?.term ?? row?.name ?? row?.value);
      const result = addTerms(category, [term], row?.source === "custom" ? "custom" : "seed");
      added += result.added;
      skipped += result.skipped;
      if (result.full) break;
    }
    return { added, skipped };
  }

  function parseImport(text, filename) {
    const lower = filename.toLowerCase();
    if (lower.endsWith(".json")) {
      const data = JSON.parse(text);
      if (Array.isArray(data)) return data;
      if (Array.isArray(data.items)) return data.items;
      const rows = seedRows(data);
      if (rows.length) return rows;
      throw new Error("JSON enthält keine unterstützten Einträge");
    }
    const selected = els.entryCategory.value;
    if (lower.endsWith(".csv")) {
      return text.split(/\r?\n/).filter(Boolean).map(line => {
        const [first, ...rest] = line.split(/[;,]/);
        const possibleCategory = normalizeCategory(first);
        return possibleCategory
          ? { category: possibleCategory, term: rest.join(" ") }
          : { category: selected, term: line };
      });
    }
    return splitTerms(text).map(term => ({ category: selected, term }));
  }

  function validateDatabase() {
    const keys = new Set();
    const duplicates = [];
    const invalid = [];
    state.items.forEach(item => {
      const key = normalizeKey(item.term);
      if (!CATEGORY_LABELS[item.category] || !key) invalid.push(item);
      if (keys.has(key)) duplicates.push(item.term);
      keys.add(key);
    });
    if (!invalid.length && !duplicates.length) {
      setStatus(`Datenbank geprüft: ${state.items.length} gültige, eindeutige Einträge.`, "success");
      return;
    }
    setStatus(`Prüfung: ${invalid.length} ungültig, ${duplicates.length} doppelt. Export empfohlen.`, "error");
  }

  function openEdit(item) {
    editingId = item.id;
    els.editCategory.value = item.category;
    els.editTerm.value = item.term;
    if (typeof els.editDialog.showModal === "function") els.editDialog.showModal();
    else els.editDialog.setAttribute("open", "");
    els.editTerm.focus();
  }

  els.form.addEventListener("submit", event => {
    event.preventDefault();
    const terms = splitTerms(els.entryTerms.value);
    if (!terms.length) return setStatus("Keine gültigen Begriffe eingegeben.", "error");
    snapshot();
    const result = addTerms(els.entryCategory.value, terms, "custom");
    if (!result.added) { undoStack.pop(); return setStatus("Keine neuen Begriffe gespeichert. Doppelungen wurden übersprungen.", "error"); }
    els.entryTerms.value = "";
    page = 1;
    persist(`${result.added} Begriffe gespeichert${result.skipped ? `, ${result.skipped} übersprungen` : ""}.`);
  });

  [els.search, els.filterCategory, els.sort].forEach(control => control.addEventListener("input", () => { page = 1; renderArchive(); }));

  els.list.addEventListener("click", event => {
    const button = event.target.closest("button[data-item-action]");
    if (!button) return;
    const item = state.items.find(entry => entry.id === button.closest("[data-id]")?.dataset.id);
    if (!item) return;
    const action = button.dataset.itemAction;
    if (action === "copy") return copyText(item.term);
    if (action === "edit") return openEdit(item);
    if (action === "delete" && !confirm(`„${item.term}“ wirklich löschen?`)) return setStatus("Löschen abgebrochen.");
    snapshot();
    if (action === "favorite") item.favorite = !item.favorite;
    if (action === "delete") state.items = state.items.filter(entry => entry.id !== item.id);
    persist(action === "delete" ? "Eintrag gelöscht. Rückgängig ist möglich." : "Favorit gespeichert.");
  });

  els.editForm.addEventListener("submit", event => {
    event.preventDefault();
    const item = state.items.find(entry => entry.id === editingId);
    const term = cleanTerm(els.editTerm.value);
    const category = normalizeCategory(els.editCategory.value);
    if (!item || !term || !category) return setStatus("Bearbeitung ungültig.", "error");
    if (hasTerm(term, item.id)) return setStatus("Dieser Begriff existiert bereits.", "error");
    snapshot();
    item.term = term;
    item.category = category;
    item.source = "custom";
    els.editDialog.close?.();
    editingId = "";
    persist("Eintrag aktualisiert.");
  });

  q('[data-action="edit-cancel"]').addEventListener("click", () => { els.editDialog.close?.(); editingId = ""; });
  q('[data-action="page-prev"]').addEventListener("click", () => { page -= 1; renderArchive(); });
  q('[data-action="page-next"]').addEventListener("click", () => { page += 1; renderArchive(); });
  q('[data-action="validate"]').addEventListener("click", validateDatabase);

  q('[data-action="generate"]').addEventListener("click", async () => {
    const categories = selectedCategories();
    if (!categories.length) return setStatus("Mindestens eine Kategorie auswählen.", "error");
    if (!categories.some(category => state.items.some(item => item.category === category))) return setStatus("Für die Auswahl fehlen Begriffe.", "error");
    const amount = Math.min(12, Math.max(1, Number(els.resultCount.value) || 1));
    currentResults = Array.from({ length: amount }, () => buildResult());
    const texts = currentResults.map(resultText);
    snapshot();
    state.history.unshift(...texts.map(text => ({ id: newId(), text, createdAt: new Date().toISOString() })));
    state.history = state.history.slice(0, HISTORY_LIMIT);
    state.recentTerms = currentResults.flatMap(result => result.parts.map(part => normalizeKey(part.term))).filter(Boolean).slice(-100);
    persist(`${amount} Kombinationen erzeugt.`);
    if (els.autoCopy.checked) await copyText(texts.join("\n"));
  });

  els.results.addEventListener("click", event => {
    const button = event.target.closest("button[data-result-action]");
    if (!button) return;
    const index = Number(button.closest("[data-result-index]")?.dataset.resultIndex);
    const result = currentResults[index];
    if (!result) return;
    const action = button.dataset.resultAction;
    if (action === "copy") return copyText(resultText(result));
    if (action === "lock") {
      const part = result.parts[Number(button.dataset.partIndex)];
      if (part) part.locked = !part.locked;
    }
    if (action === "reroll") currentResults[index] = buildResult(result);
    renderResults();
    setStatus("Mixer-Ergebnis angepasst. Archiv unverändert.");
  });

  q('[data-action="copy-all"]').addEventListener("click", () => {
    if (!currentResults.length) return setStatus("Keine Ergebnisse zum Kopieren.", "error");
    copyText(currentResults.map(resultText).join("\n"));
  });
  q('[data-action="unlock-all"]').addEventListener("click", () => {
    currentResults.forEach(result => result.parts.forEach(part => { part.locked = false; }));
    renderResults();
    setStatus("Alle Sperren gelöst.");
  });

  els.history.addEventListener("click", event => {
    const button = event.target.closest("button[data-history-id]");
    const entry = state.history.find(item => item.id === button?.dataset.historyId);
    if (entry) copyText(entry.text);
  });

  q('[data-action="undo"]').addEventListener("click", () => {
    if (!undoStack.length) return;
    redoStack.push(JSON.stringify(state));
    restoreSnapshot(undoStack.pop(), "Änderung rückgängig gemacht.");
  });
  q('[data-action="redo"]').addEventListener("click", () => {
    if (!redoStack.length) return;
    undoStack.push(JSON.stringify(state));
    restoreSnapshot(redoStack.pop(), "Änderung wiederholt.");
  });

  q('[data-action="export"]').addEventListener("click", () => {
    download(`provoware-genretool-${new Date().toISOString().slice(0, 10)}.json`, JSON.stringify(state, null, 2));
    setStatus("Datenbank exportiert.", "success");
  });
  q('[data-action="backup"]').addEventListener("click", () => {
    try {
      localStorage.setItem(BACKUP_KEY, JSON.stringify({ createdAt: new Date().toISOString(), state }));
      download(`provoware-genretool-backup-${new Date().toISOString().replace(/[:.]/g, "-")}.json`, JSON.stringify(state, null, 2));
      setStatus("Lokales Backup und Backup-Datei erstellt.", "success");
    } catch {
      setStatus("Backup konnte nicht gespeichert werden.", "error");
    }
  });

  els.importInput.addEventListener("change", async () => {
    const file = els.importInput.files?.[0];
    els.importInput.value = "";
    if (!file) return;
    if (file.size > MAX_IMPORT_BYTES) return setStatus("Import abgelehnt: Datei größer als 8 MB.", "error");
    try {
      const rows = parseImport(await file.text(), file.name);
      if (!rows.length) throw new Error("keine Einträge");
      snapshot();
      const result = addTermsFromRows(rows.map(row => ({ ...row, source: "custom" })));
      if (!result.added) { undoStack.pop(); return setStatus("Keine neuen gültigen Begriffe gefunden.", "error"); }
      persist(`${result.added} Begriffe importiert${result.skipped ? `, ${result.skipped} übersprungen` : ""}.`);
    } catch (error) {
      console.error(error);
      setStatus("Import fehlgeschlagen. JSON-, TXT- oder CSV-Struktur prüfen.", "error");
    }
  });

  q('[data-action="reset"]').addEventListener("click", async () => {
    if (!confirm("Eigene Änderungen verwerfen und Startdaten neu laden?")) return setStatus("Zurücksetzen abgebrochen.");
    snapshot();
    try {
      state = emptyState();
      addTermsFromRows(await fetchSeed());
      currentResults = [];
      persist(`${state.items.length} Startbegriffe wiederhergestellt.`);
    } catch (error) {
      state = normalizeState(JSON.parse(undoStack.pop()));
      setStatus("Startdaten konnten nicht geladen werden. Alter Stand bleibt erhalten.", "error");
    }
  });

  populateControls();
  renderAll();
  loadSeedIfEmpty();
})();
