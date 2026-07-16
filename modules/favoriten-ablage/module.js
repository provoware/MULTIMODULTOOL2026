(() => {
  const script = document.currentScript;
  const root = script?.parentElement?.querySelector('[data-favorites]') || document.querySelector('[data-favorites]');
  if (!root) return;

  const key = `mmt2026.favorites.${script?.dataset.moduleRoot || 'favoriten-ablage'}`;
  const maxItems = 500;
  const maxFiles = 100;
  const maxBytes = 8_000_000;
  const input = root.querySelector('[data-files]');
  const note = root.querySelector('[data-note]');
  const kind = root.querySelector('[data-kind]');
  const list = root.querySelector('[data-list]');
  const status = root.querySelector('[data-status]');
  let items = readItems();

  function readItems() {
    try {
      const parsed = JSON.parse(localStorage.getItem(key) || '[]');
      return Array.isArray(parsed) ? parsed.slice(0, maxItems) : [];
    } catch (_) {
      status.textContent = 'Favoritenspeicher war beschädigt. Es wurde nichts überschrieben.';
      return [];
    }
  }
  function save() { localStorage.setItem(key, JSON.stringify(items)); }
  function copy(text) {
    navigator.clipboard?.writeText(text).then(
      () => { status.textContent = 'Favorit wurde kopiert.'; },
      () => { status.textContent = 'Kopieren nicht möglich. Bitte Text manuell übernehmen.'; }
    );
  }

  function render() {
    list.replaceChildren();
    status.textContent = `${items.length} Favoriten gespeichert.`;
    items.forEach((it, i) => {
      const row = document.createElement('div');
      row.className = 'tool-item';
      const info = document.createElement('div');
      const strong = document.createElement('strong');
      strong.textContent = it.name;
      const meta = document.createElement('small');
      meta.className = 'muted';
      meta.append(document.createElement('br'), `${it.kind} · ${it.time}`);
      info.append(strong, meta);
      const actions = document.createElement('div');
      actions.className = 'tool-actions';
      const copyButton = document.createElement('button');
      copyButton.className = 'small-button';
      copyButton.type = 'button';
      copyButton.textContent = 'Kopieren';
      copyButton.addEventListener('click', () => copy(it.name));
      const del = document.createElement('button');
      del.className = 'danger-button';
      del.type = 'button';
      del.textContent = '×';
      del.addEventListener('click', () => { items.splice(i, 1); save(); render(); });
      actions.append(copyButton, del);
      row.append(info, actions);
      list.append(row);
    });
  }

  root.querySelector('[data-add]').addEventListener('click', () => {
    [...input.files].filter(file => file.size <= maxBytes).slice(0, maxFiles).forEach(file => items.unshift({ name: file.name, kind: kind.value, time: new Date().toLocaleString('de-DE'), size: file.size, type: file.type }));
    if (note.value.trim()) items.unshift({ name: note.value.trim().slice(0, 500), kind: kind.value, time: new Date().toLocaleString('de-DE') });
    note.value = '';
    items = items.slice(0, maxItems);
    save();
    render();
  });
  root.querySelector('[data-export]').addEventListener('click', () => {
    const url = URL.createObjectURL(new Blob([JSON.stringify(items, null, 2)], { type: 'application/json' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = 'favoriten-ablage.json';
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  render();
})();
