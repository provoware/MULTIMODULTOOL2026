(() => {
  const script = document.currentScript;
  const root = script?.parentElement?.querySelector('[data-songtext-studio]') || document.querySelector('[data-songtext-studio]');
  if (!root || root.dataset.initialized) return;
  root.dataset.initialized = 'true';

  const $ = s => root.querySelector(s);
  const KEY = `mmt2026.songtextStudio.${script?.dataset.moduleRoot || 'songtext-studio'}.v1`;
  const VERSION = '1.0.0';
  const PARTS = [['intro','Intro'],['strophe-1','Strophe 1'],['pre-chorus','Pre-Chorus'],['refrain','Refrain'],['strophe-2','Strophe 2'],['bridge','Bridge'],['outro','Outro']];
  const fields = {
    title: $('[data-title]'), genre: $('[data-genre]'), status: $('[data-status]'), tags: $('[data-tags]'),
    section: $('[data-section-select]'), text: $('[data-section-text]'), preview: $('[data-preview]'),
    fragmentTitle: $('[data-fragment-title]'), fragmentType: $('[data-fragment-type]'), fragmentText: $('[data-fragment-text]'),
    archiveSearch: $('[data-archive-search]'), archiveStatus: $('[data-archive-status]'), archiveSort: $('[data-archive-sort]')
  };
  const now = () => new Date().toISOString();
  const id = () => crypto?.randomUUID?.() || `id-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const clean = (v, n = 200000) => String(v ?? '').slice(0, n);
  const clone = v => JSON.parse(JSON.stringify(v));
  const dateKey = (d = new Date()) => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  const stamp = (d = new Date()) => `${dateKey(d)}_${String(d.getHours()).padStart(2,'0')}-${String(d.getMinutes()).padStart(2,'0')}-${String(d.getSeconds()).padStart(2,'0')}`;
  const words = v => clean(v).trim().match(/\S+/g)?.length || 0;
  const fullText = song => song.sections.map(x => x.text).filter(Boolean).join('\n\n');
  const safeName = v => clean(v,120).normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^\p{L}\p{N}_-]+/gu,'-').replace(/-+/g,'-').replace(/^-|-$/g,'') || `songs_${dateKey()}`;
  const tell = (msg, level = 'info') => { $('[data-live-status]').textContent = msg; $('[data-live-status]').dataset.level = level; };
  const blankSong = () => ({ id:null, title:'', genre:'', status:'idee', tags:'', sections:PARTS.map(([id,label])=>({id,label,text:'',standard:true})), createdAt:now(), updatedAt:now(), storageName:'', revision:0 });
  const defaults = () => ({ schemaVersion:1, moduleVersion:VERSION, current:blankSong(), songs:[], fragments:[], fragmentDraft:{title:'',type:'hook',text:'',editId:null}, settings:{activeSection:'strophe-1',spellcheck:true,previewHeadings:true}, lastSavedAt:'' });

  const normalizeSong = src => {
    const base = blankSong();
    const sections = Array.isArray(src?.sections) ? src.sections.slice(0,40).map((x,i)=>({id:clean(x?.id,80)||`bereich-${i+1}`,label:clean(x?.label,60)||`Bereich ${i+1}`,text:clean(x?.text),standard:Boolean(x?.standard)})) : base.sections;
    return {...base,id:src?.id?clean(src.id,100):null,title:clean(src?.title,160),genre:clean(src?.genre,220),status:['idee','entwurf','arbeit','fertig','archiv'].includes(src?.status)?src.status:'idee',tags:clean(src?.tags,240),sections:sections.length?sections:base.sections,createdAt:clean(src?.createdAt,40)||base.createdAt,updatedAt:clean(src?.updatedAt,40)||base.updatedAt,storageName:clean(src?.storageName,180),revision:Math.max(0,Number(src?.revision)||0)};
  };
  const normalize = src => ({...defaults(),current:normalizeSong(src?.current),songs:Array.isArray(src?.songs)?src.songs.slice(0,300).map(normalizeSong):[],fragments:Array.isArray(src?.fragments)?src.fragments.slice(0,200).map(x=>({id:clean(x?.id,100)||id(),title:clean(x?.title,100)||'Baustein',type:['hook','fragment','reim','claim'].includes(x?.type)?x.type:'fragment',text:clean(x?.text,2000),updatedAt:clean(x?.updatedAt,40)||now()})):[],fragmentDraft:{title:clean(src?.fragmentDraft?.title,100),type:['hook','fragment','reim','claim'].includes(src?.fragmentDraft?.type)?src.fragmentDraft.type:'hook',text:clean(src?.fragmentDraft?.text,2000),editId:src?.fragmentDraft?.editId?clean(src.fragmentDraft.editId,100):null},settings:{activeSection:clean(src?.settings?.activeSection,80)||'strophe-1',spellcheck:src?.settings?.spellcheck!==false,previewHeadings:src?.settings?.previewHeadings!==false},lastSavedAt:clean(src?.lastSavedAt,40)});
  let state;
  try { state = localStorage.getItem(KEY) ? normalize(JSON.parse(localStorage.getItem(KEY))) : defaults(); }
  catch { state = defaults(); tell('Gespeicherte Songdaten waren nicht lesbar. Alte Daten wurden nicht überschrieben.','error'); }

  const active = () => state.current.sections.find(x=>x.id===state.settings.activeSection) || state.current.sections[0];
  const sync = () => {
    if (active()) active().text = clean(fields.text.value);
    state.current.title = clean(fields.title.value,160); state.current.genre = clean(fields.genre.value,220);
    state.current.status = fields.status.value; state.current.tags = clean(fields.tags.value,240); state.current.updatedAt = now();
    state.fragmentDraft = {title:clean(fields.fragmentTitle.value,100),type:fields.fragmentType.value,text:clean(fields.fragmentText.value,2000),editId:state.fragmentDraft.editId||null};
  };
  const persist = (reason='Autosave', doSync=true) => {
    if (doSync) sync(); state.moduleVersion=VERSION; state.lastSavedAt=now();
    try { localStorage.setItem(KEY,JSON.stringify(state)); $('[data-save-state]').textContent=reason; $('[data-save-time]').textContent=new Date(state.lastSavedAt).toLocaleString('de-DE'); tell(`${reason} abgeschlossen. Daten liegen lokal im Browser.`); return true; }
    catch { tell('Speichern fehlgeschlagen. Browser-Speicher prüfen oder Archiv exportieren.','error'); return false; }
  };

  function renderSections() {
    fields.section.replaceChildren();
    state.current.sections.forEach(x=>{const o=document.createElement('option');o.value=x.id;o.textContent=x.label;fields.section.append(o);});
    if (!state.current.sections.some(x=>x.id===state.settings.activeSection)) state.settings.activeSection=state.current.sections[0]?.id||'';
    fields.section.value=state.settings.activeSection; fields.text.value=active()?.text||'';
  }
  function renderPreview() {
    if (active()) active().text=clean(fields.text.value);
    const blocks=state.current.sections.filter(x=>x.text.trim()).map(x=>state.settings.previewHeadings?`${x.label}:\n${x.text.trim()}`:x.text.trim());
    fields.preview.textContent=blocks.join('\n\n')||'Der Song ist noch leer.';
    $('[data-section-words]').textContent=words(fields.text.value); $('[data-section-chars]').textContent=fields.text.value.length;
    const all=fullText(state.current); $('[data-song-words]').textContent=words(all); $('[data-song-chars]').textContent=all.length;
  }
  function renderEditor() {
    fields.title.value=state.current.title; fields.genre.value=state.current.genre; fields.status.value=state.current.status; fields.tags.value=state.current.tags;
    fields.fragmentTitle.value=state.fragmentDraft.title; fields.fragmentType.value=state.fragmentDraft.type; fields.fragmentText.value=state.fragmentDraft.text;
    $('[data-spellcheck]').checked=state.settings.spellcheck; $('[data-preview-headings]').checked=state.settings.previewHeadings;
    fields.text.spellcheck=fields.fragmentText.spellcheck=state.settings.spellcheck; renderSections(); renderPreview();
  }
  const button = (label,cls,fn) => { const b=document.createElement('button');b.type='button';b.className=cls;b.textContent=label;b.addEventListener('click',fn);return b; };
  function renderFragments() {
    const list=$('[data-fragment-list]'); list.replaceChildren();
    state.fragments.forEach(item=>{const wrap=document.createElement('div');wrap.className='songtext-fragment-item';const type=document.createElement('span');type.className='songtext-fragment-type';type.textContent=item.type;const main=button(item.title,'small-button songtext-fragment-main',()=>{const sep=fields.text.value&&!fields.text.value.endsWith('\n')?'\n':'';fields.text.value+=`${sep}${item.text}`;renderPreview();persist('Baustein eingefügt');});const edit=button('Bearbeiten','small-button',()=>{state.fragmentDraft={title:item.title,type:item.type,text:item.text,editId:item.id};renderEditor();persist('Baustein geöffnet');});const del=button('×','danger-button',()=>{if(confirm(`Baustein „${item.title}“ löschen?`)){state.fragments=state.fragments.filter(x=>x.id!==item.id);persist('Baustein gelöscht');renderFragments();renderStats();}});wrap.append(type,main,edit,del);list.append(wrap);});
  }
  function saveFragment() {
    sync(); if(!state.fragmentDraft.text.trim()) return tell('Bitte zuerst einen Hook oder ein Satzfragment eingeben.','warning');
    const entry={id:state.fragmentDraft.editId||id(),title:state.fragmentDraft.title.trim()||'Baustein',type:state.fragmentDraft.type,text:state.fragmentDraft.text.trim(),updatedAt:now()};
    const i=state.fragments.findIndex(x=>x.id===entry.id); if(i>=0)state.fragments[i]=entry;else state.fragments.unshift(entry);
    state.fragments=state.fragments.slice(0,200);state.fragmentDraft={title:'',type:'hook',text:'',editId:null};renderEditor();persist('Baustein gespeichert',false);renderFragments();renderStats();
  }
  function addSection() { const input=$('[data-new-section-name]');const label=clean(input.value.trim(),60);if(!label)return tell('Bitte einen Namen für den neuen Bereich eingeben.','warning');const sid=`bereich-${safeName(label).toLowerCase()}-${Date.now().toString(36)}`;state.current.sections.push({id:sid,label,text:'',standard:false});state.settings.activeSection=sid;input.value='';renderSections();renderPreview();persist('Bereich angelegt'); }
  function removeSection() { const part=active();if(!part)return;if(state.current.sections.length<=1)return tell('Mindestens ein Songbereich muss erhalten bleiben.','warning');if(!confirm(`Bereich „${part.label}“ entfernen?`))return;state.current.sections=state.current.sections.filter(x=>x.id!==part.id);state.settings.activeSection=state.current.sections[0].id;renderSections();renderPreview();persist('Bereich entfernt'); }
  function ensureTitle(song) { if(!song.title.trim())song.title=`songs_${dateKey()}`;if(!song.storageName)song.storageName=`${safeName(song.title)}_${stamp()}`; }
  function saveSong() { sync();const song=clone(state.current);ensureTitle(song);song.id=song.id||id();song.revision=(song.revision||0)+1;song.updatedAt=now();const i=state.songs.findIndex(x=>x.id===song.id);if(i>=0)state.songs[i]=song;else state.songs.unshift(song);state.current=clone(song);persist('Song gespeichert');renderEditor();renderArchive();renderStats(); }
  function newSong() { sync();if(fullText(state.current).trim()&&!confirm('Neuen Song beginnen? Der aktuelle Entwurf bleibt nur erhalten, wenn er gespeichert wurde.'))return;state.current=blankSong();state.settings.activeSection='strophe-1';renderEditor();persist('Neuer Song geöffnet',false); }
  function openSong(songId) { const song=state.songs.find(x=>x.id===songId);if(!song)return;state.current=clone(song);state.settings.activeSection=song.sections[0]?.id||'';renderEditor();persist('Song geöffnet',false); }
  function duplicateSong(songId) { const src=state.songs.find(x=>x.id===songId);if(!src)return;const copy=clone(src);copy.id=id();copy.title=`${src.title} – Kopie`;copy.storageName=`${safeName(copy.title)}_${stamp()}`;copy.createdAt=copy.updatedAt=now();copy.revision=1;state.songs.unshift(copy);persist('Song dupliziert');renderArchive();renderStats(); }
  function deleteSong(songId) { const song=state.songs.find(x=>x.id===songId);if(song&&confirm(`Song „${song.title}“ löschen?`)){state.songs=state.songs.filter(x=>x.id!==songId);persist('Song gelöscht');renderArchive();renderStats();} }
  function compose(song) { const h=[song.title||`songs_${dateKey()}`,song.genre?`Genre: ${song.genre}`:'',song.tags?`Tags: ${song.tags}`:''].filter(Boolean).join('\n');const body=song.sections.filter(x=>x.text.trim()).map(x=>`${x.label}:\n${x.text.trim()}`).join('\n\n');return `${h}\n\n${body}`.trim(); }
  function download(name,content,mime) { const url=URL.createObjectURL(new Blob([content],{type:mime}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000); }
  function exportSong(song=state.current) { if(song===state.current)sync();const copy=clone(song);ensureTitle(copy);download(`${copy.storageName||`${safeName(copy.title)}_${stamp()}`}.txt`,compose(copy),'text/plain;charset=utf-8');tell('Song als TXT exportiert.'); }
  function exportArchive() { download(`songtext-archiv_${stamp()}.json`,JSON.stringify({schemaVersion:1,moduleVersion:VERSION,exportedAt:now(),songs:state.songs,fragments:state.fragments},null,2),'application/json;charset=utf-8');tell('Archiv als JSON exportiert.'); }
  function renderArchive() {
    const q=fields.archiveSearch.value.trim().toLocaleLowerCase('de-DE'), status=fields.archiveStatus.value, sort=fields.archiveSort.value;
    let songs=state.songs.filter(s=>(status==='all'||s.status===status)&&(!q||[s.title,s.genre,s.tags,fullText(s)].join(' ').toLocaleLowerCase('de-DE').includes(q)));
    songs.sort((a,b)=>sort==='title-asc'?a.title.localeCompare(b.title,'de'):sort==='created-desc'?b.createdAt.localeCompare(a.createdAt):sort==='words-desc'?words(fullText(b))-words(fullText(a)):b.updatedAt.localeCompare(a.updatedAt));
    const list=$('[data-archive-list]');list.replaceChildren();if(!songs.length){const e=document.createElement('div');e.className='songtext-archive-empty';e.textContent='Keine Songs für diesen Filter gefunden.';list.append(e);return;}
    songs.forEach(song=>{const card=document.createElement('article');card.className='songtext-song-card';const info=document.createElement('div');const h=document.createElement('h4');h.textContent=song.title;const p=document.createElement('p');p.textContent=`${song.genre||'Ohne Genre'} · ${song.status} · ${words(fullText(song))} Wörter · Revision ${song.revision} · ${new Date(song.updatedAt).toLocaleString('de-DE')}`;const n=document.createElement('span');n.className='songtext-storage-name';n.textContent=song.storageName;info.append(h,p,n);const actions=document.createElement('div');actions.className='songtext-actions';actions.append(button('Öffnen','primary-button',()=>openSong(song.id)),button('Duplizieren','small-button',()=>duplicateSong(song.id)),button('TXT','small-button',()=>exportSong(song)),button('Löschen','danger-button',()=>deleteSong(song.id)));card.append(info,actions);list.append(card);});
  }
  function renderStats() { const tw=state.songs.reduce((n,s)=>n+words(fullText(s)),0),tc=state.songs.reduce((n,s)=>n+fullText(s).length,0),genres=new Set(state.songs.map(s=>s.genre.trim().toLowerCase()).filter(Boolean));const data=[[state.songs.length,'Songs im Archiv'],[tw,'Wörter gesamt'],[tc,'Zeichen gesamt'],[state.songs.length?Math.round(tw/state.songs.length):0,'Wörter je Song'],[genres.size,'Genres'],[state.fragments.length,'Hooks und Fragmente'],[state.songs.filter(s=>s.status==='fertig').length,'Fertige Songs'],[state.songs.reduce((n,s)=>n+s.revision,0),'Revisionen']];const grid=$('[data-stat-grid]');grid.replaceChildren();data.forEach(([v,l])=>{const c=document.createElement('div');c.className='songtext-stat-card';const strong=document.createElement('strong');strong.textContent=Number(v).toLocaleString('de-DE');const span=document.createElement('span');span.textContent=l;c.append(strong,span);grid.append(c);}); }
  const esc = v => v.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
  const targets = () => $('[data-replace-scope]').value==='song'?state.current.sections:[active()].filter(Boolean);
  function countFind() { sync();const needle=$('[data-find]').value;if(!needle)return tell('Bitte einen Suchtext eingeben.','warning');const flags=$('[data-case-sensitive]').checked?'g':'gi';const count=targets().reduce((n,s)=>n+(s.text.match(new RegExp(esc(needle),flags))?.length||0),0);$('[data-replace-result]').textContent=`${count} Treffer`;tell(`${count} Treffer gefunden.`); }
  function replaceAll() { sync();const needle=$('[data-find]').value;if(!needle)return tell('Bitte einen Suchtext eingeben.','warning');const flags=$('[data-case-sensitive]').checked?'g':'gi';let count=0;targets().forEach(s=>{const re=new RegExp(esc(needle),flags);count+=s.text.match(re)?.length||0;s.text=s.text.replace(re,()=>$('[data-replace]').value);});fields.text.value=active()?.text||'';$('[data-replace-result]').textContent=`${count} ersetzt`;renderPreview();persist(`${count} Treffer ersetzt`); }

  fields.section.addEventListener('change',()=>{if(active())active().text=clean(fields.text.value);state.settings.activeSection=fields.section.value;fields.text.value=active()?.text||'';renderPreview();persist('Bereich gewechselt');});
  fields.text.addEventListener('input',renderPreview);[fields.title,fields.genre,fields.status,fields.tags].forEach(x=>x.addEventListener('input',renderPreview));
  root.addEventListener('focusout',e=>{if(e.target.matches?.('[data-persist]')){persist('Autosave');renderArchive();renderStats();}});
  $('[data-save-song]').onclick=saveSong;$('[data-new-song]').onclick=newSong;$('[data-export-song]').onclick=()=>exportSong();$('[data-export-archive]').onclick=exportArchive;
  $('[data-add-section]').onclick=addSection;$('[data-remove-section]').onclick=removeSection;$('[data-save-fragment]').onclick=saveFragment;$('[data-clear-fragment]').onclick=()=>{state.fragmentDraft={title:'',type:'hook',text:'',editId:null};renderEditor();persist('Bausteinentwurf geleert',false);};
  $('[data-count-find]').onclick=countFind;$('[data-replace-all]').onclick=replaceAll;
  $('[data-paste-genre]').onclick=async()=>{try{fields.genre.value=clean((await navigator.clipboard.readText()).trim(),220);persist('Genre eingefügt');}catch{tell('Zwischenablage wurde blockiert. Browserberechtigung prüfen oder manuell einfügen.','error');}};
  $('[data-copy-genre]').onclick=async()=>{try{await navigator.clipboard.writeText(fields.genre.value);tell('Genre kopiert.');}catch{tell('Kopieren wurde vom Browser blockiert.','error');}};
  $('[data-spellcheck]').onchange=e=>{state.settings.spellcheck=e.target.checked;fields.text.spellcheck=fields.fragmentText.spellcheck=e.target.checked;persist(e.target.checked?'Rechtschreibprüfung aktiviert':'Rechtschreibprüfung deaktiviert');};
  $('[data-preview-headings]').onchange=e=>{state.settings.previewHeadings=e.target.checked;renderPreview();persist('Vorschau angepasst');};
  [fields.archiveSearch,fields.archiveStatus,fields.archiveSort].forEach(x=>x.addEventListener('input',renderArchive));

  renderEditor();renderFragments();renderArchive();renderStats();
  if(state.lastSavedAt){$('[data-save-state]').textContent='Lokaler Stand geladen';$('[data-save-time]').textContent=new Date(state.lastSavedAt).toLocaleString('de-DE');}
})();
