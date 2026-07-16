(() => {
  const script = document.currentScript;
  const root = script?.parentElement?.querySelector('[data-audio-playlist]') || document.querySelector('[data-audio-playlist]');
  if (!root) return;

  const key = `mmt2026.audioPlaylist.${script?.dataset.moduleRoot || 'audio-playlist'}`;
  const maxFiles = 100;
  const maxBytes = 8_000_000;
  const input = root.querySelector('[data-files]');
  const player = root.querySelector('[data-player]');
  const list = root.querySelector('[data-list]');
  const status = root.querySelector('[data-status]');
  let items = safeRead();

  function safeRead() {
    try {
      const value = JSON.parse(localStorage.getItem(key) || '[]');
      return Array.isArray(value) ? value.slice(0, maxFiles) : [];
    } catch (_) {
      statusText('Gespeicherte Playlist war beschädigt. Sie wurde nicht geladen; es wurde nichts überschrieben.');
      return [];
    }
  }

  function statusText(message) { if (status) status.textContent = message; }
  function save() { localStorage.setItem(key, JSON.stringify(items.map(({ url, ...x }) => x))); }
  function revokeItem(item) { if (item?.url) URL.revokeObjectURL(item.url); }
  function validFile(file) { return file.type.startsWith('audio/') && file.size <= maxBytes; }

  function render() {
    list.replaceChildren();
    statusText(items.length ? `${items.length} Audioeinträge in der Playlist.` : 'Noch keine Audios geladen.');
    items.forEach((it, i) => {
      const row = document.createElement('div');
      row.className = 'tool-item';
      const name = document.createElement('input');
      name.value = it.name;
      name.setAttribute('aria-label', 'Audiobezeichnung');
      name.addEventListener('input', event => { it.name = event.target.value.slice(0, 160) || 'Audio'; save(); });
      const actions = document.createElement('div');
      actions.className = 'tool-actions';
      const play = document.createElement('button');
      play.className = 'small-button';
      play.type = 'button';
      play.textContent = '▶';
      play.addEventListener('click', async () => {
        if (!it.url) { statusText('Diese Datei bitte erneut laden; Browser-Sitzungszugriff ist abgelaufen.'); return; }
        player.src = it.url;
        try { await player.play(); } catch (_) { statusText('Audio konnte nicht gestartet werden. Bitte Browserfreigabe und Dateiformat prüfen.'); }
      });
      const del = document.createElement('button');
      del.className = 'danger-button';
      del.type = 'button';
      del.textContent = '×';
      del.addEventListener('click', () => { revokeItem(items[i]); items.splice(i, 1); save(); render(); });
      actions.append(play, del);
      const meta = document.createElement('small');
      meta.className = 'muted';
      meta.textContent = `${it.type || 'Audio'} · ${it.size || 0} Byte`;
      row.append(name, actions, meta);
      list.append(row);
    });
  }

  root.querySelector('[data-add]').addEventListener('click', () => {
    const selected = [...input.files].filter(validFile).slice(0, maxFiles - items.length);
    selected.forEach(file => items.push({ name: file.name, type: file.type, size: file.size, url: URL.createObjectURL(file) }));
    save();
    render();
    statusText(`${selected.length} Audiodateien geladen. Zu große oder nicht passende Dateien wurden übersprungen.`);
  });
  root.querySelector('[data-clear]').addEventListener('click', () => {
    if (confirm('Playlist wirklich leeren?')) { items.forEach(revokeItem); items = []; save(); render(); }
  });
  window.addEventListener('pagehide', () => items.forEach(revokeItem), { once: true });
  render();
})();
