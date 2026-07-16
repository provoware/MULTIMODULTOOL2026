(() => {
  const script = document.currentScript;
  const root = script?.parentElement?.querySelector('[data-image-preview]') || document.querySelector('[data-image-preview]');
  if (!root) return;

  const maxFiles = 100;
  const maxBytes = 8_000_000;
  const input = root.querySelector('[data-files]');
  const box = root.querySelector('[data-preview]');
  const list = root.querySelector('[data-list]');
  const status = root.querySelector('[data-status]');
  let files = [];
  let index = 0;

  function clearUrls() { files.forEach(file => URL.revokeObjectURL(file.url)); }
  function validFile(file) { return file.type.startsWith('image/') && file.size <= maxBytes; }

  function show() {
    if (!files.length) { box.textContent = 'Bitte Bilder auswählen.'; status.textContent = 'Noch keine Bilder geladen.'; list.replaceChildren(); return; }
    const file = files[index];
    box.replaceChildren();
    const img = new Image();
    img.src = file.url;
    img.alt = file.name;
    box.append(img);
    status.textContent = `${index + 1}/${files.length}: ${file.name}`;
    list.replaceChildren();
    files.forEach((it, i) => {
      const button = document.createElement('button');
      button.className = 'small-button';
      button.type = 'button';
      button.textContent = it.name;
      button.addEventListener('click', () => { index = i; show(); });
      list.append(button);
    });
  }

  root.querySelector('[data-load]').addEventListener('click', () => {
    clearUrls();
    files = [...input.files].filter(validFile).slice(0, maxFiles).map(file => ({ name: file.name, url: URL.createObjectURL(file) }));
    index = 0;
    show();
    if (input.files.length !== files.length) status.textContent += ' Einige Dateien wurden wegen Typ oder Größe übersprungen.';
  });
  root.querySelector('[data-prev]').addEventListener('click', () => { if (files.length) { index = (index + files.length - 1) % files.length; show(); } });
  root.querySelector('[data-next]').addEventListener('click', () => { if (files.length) { index = (index + 1) % files.length; show(); } });
  window.addEventListener('pagehide', clearUrls, { once: true });
  show();
})();
