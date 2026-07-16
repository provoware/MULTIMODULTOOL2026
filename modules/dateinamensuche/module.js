(() => {
  const script = document.currentScript;
  const root = script?.parentElement?.querySelector('[data-file-search]') || document.querySelector('[data-file-search]');
  if (!root) return;

  const maxFiles = 2000;
  const maxShown = 500;
  const maxOpenBytes = 8_000_000;
  const safeOpenTypes = /^(text\/plain|application\/json|image\/|audio\/|video\/|application\/pdf)/;
  const input = root.querySelector('[data-files]');
  const query = root.querySelector('[data-query]');
  const mode = root.querySelector('[data-mode]');
  const list = root.querySelector('[data-list]');
  const status = root.querySelector('[data-status]');
  let files = [];
  let openUrl = null;

  function copy(text) {
    navigator.clipboard?.writeText(text).then(
      () => { status.textContent = 'Pfad wurde kopiert.'; },
      () => { status.textContent = 'Kopieren nicht möglich. Bitte Pfad manuell markieren.'; }
    );
  }

  input.addEventListener('change', () => {
    files = [...input.files].slice(0, maxFiles);
    status.textContent = `${files.length} Dateien zur Suche bereit${input.files.length > maxFiles ? '; weitere Dateien wurden begrenzt.' : '.'}`;
  });

  root.querySelector('[data-search]').addEventListener('click', () => {
    const terms = query.value.toLowerCase().split(/\s+/).filter(Boolean);
    list.replaceChildren();
    if (!files.length) { status.textContent = 'Bitte zuerst einen Ordner auswählen. Nichts wurde verändert.'; return; }
    const hits = files.filter(file => {
      const name = (file.webkitRelativePath || file.name).toLowerCase();
      return terms.length ? (mode.value === 'all' ? terms.every(term => name.includes(term)) : terms.some(term => name.includes(term))) : true;
    }).slice(0, maxShown);
    status.textContent = `${hits.length} Treffer angezeigt${hits.length === maxShown ? '; Anzeige begrenzt.' : '.'}`;
    hits.forEach(file => {
      const path = file.webkitRelativePath || file.name;
      const row = document.createElement('div');
      row.className = 'tool-item';
      const info = document.createElement('div');
      const strong = document.createElement('strong');
      strong.textContent = file.name;
      const small = document.createElement('small');
      small.className = 'muted';
      small.append(document.createElement('br'), path);
      info.append(strong, small);
      const actions = document.createElement('div');
      actions.className = 'tool-actions';
      const open = document.createElement('button');
      open.className = 'small-button';
      open.type = 'button';
      open.textContent = 'Öffnen';
      open.addEventListener('click', () => {
        if (file.size > maxOpenBytes || !safeOpenTypes.test(file.type || '')) { status.textContent = 'Diese Datei wird aus Sicherheitsgründen nicht geöffnet. Name und Pfad bleiben kopierbar.'; return; }
        if (openUrl) URL.revokeObjectURL(openUrl);
        openUrl = URL.createObjectURL(file);
        window.open(openUrl, '_blank', 'noopener');
      });
      const copyButton = document.createElement('button');
      copyButton.className = 'small-button';
      copyButton.type = 'button';
      copyButton.textContent = 'Kopieren';
      copyButton.addEventListener('click', () => copy(path));
      actions.append(open, copyButton);
      row.append(info, actions);
      list.append(row);
    });
  });
  window.addEventListener('pagehide', () => { if (openUrl) URL.revokeObjectURL(openUrl); }, { once: true });
})();
