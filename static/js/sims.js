// sims.html scripts (robusto si faltan elementos opcionales) + "Ir a" limitado al # de páginas
(function () {
  // ===== Config =====
  const hourlyMs  = 60 * 60 * 1000;
  const pollMs    = 4000;

  // ===== DOM (todos opcionales salvo la tabla) =====
  const tbody      = document.querySelector('#simsTable tbody');
  const emptyMsg   = document.getElementById('emptyMsg');

  const bar        = document.getElementById('bar');
  const prog       = document.getElementById('progressText');

  const pageSizeSel= document.getElementById('pageSize');
  const filterInput= document.getElementById('filter');

  const btnRefresh = document.getElementById('btnRefresh');

  const btnFirst   = document.getElementById('btnFirst');
  const btnPrev    = document.getElementById('btnPrev');
  const btnNext    = document.getElementById('btnNext');
  const btnLast    = document.getElementById('btnLast');
  const pageInfo   = document.getElementById('pageInfo');

  const gotoInput  = document.getElementById('gotoInput');
  const gotoBtn    = document.getElementById('gotoBtn');

  const cfgBatch   = document.getElementById('cfgBatch');
  const cfgPar     = document.getElementById('cfgPar');
  const cfgWorkers = document.getElementById('cfgWorkers');

  const lastRefresh= document.getElementById('lastRefresh');
  const nextPlanned= document.getElementById('nextPlanned');

  const bannerLastRefresh = document.getElementById('bannerLastRefresh');
  const bannerNextPlanned = document.getElementById('bannerNextPlanned');
  const updateBanner      = document.getElementById('updateBanner');

  if (!tbody) return;

  // ===== Estado =====
  let currentPage = 0; // 0-index
  let totalFiltered = 0;
  let currentPageIccids = [];
  let lastPageCount = 1;
  let sortColumn = null;
  let sortDirection = "asc";
  let currentData = [];

  const clamp = (n, lo, hi) => Math.min(Math.max(n, lo), hi);

  function statusBadge(status){
    const st = (status||'').toUpperCase();
    let cls = 'status-other';
    if (st === 'ONLINE') cls = 'status-online';
    else if (st === 'OFFLINE') cls = 'status-offline';
    else if (st === 'ERROR' || st === 'TIMEOUT') cls = 'status-error';
    return `<span class="badge ${cls}">${st}</span>`;
  }

  function fmtIso(iso){
    if (!iso) return '';
    const d = new Date(iso);
    if (isNaN(d.getTime())) return iso;
    if (typeof Intl !== 'undefined' && Intl.DateTimeFormat) {
      return new Intl.DateTimeFormat(undefined, {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit', hour12: false,
        timeZoneName: 'short'
      }).format(d).replace(',', '');
    }
    const pad = n => String(n).padStart(2,'0');
    return `${pad(d.getDate())}/${pad(d.getMonth()+1)}/${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }


  function sortData(data, column, direction) {
    if (!column) return data;
    const sorted = [...data].sort((a, b) => {
      let valA = a[column] || "";
      let valB = b[column] || "";
      valA = String(valA).toLowerCase();
      valB = String(valB).toLowerCase();
      if (valA < valB) return direction === "asc" ? -1 : 1;
      if (valA > valB) return direction === "asc" ? 1 : -1;
      return 0;
    });
    return sorted;
  }

  function renderRows(items, startIndex){
    tbody.innerHTML = '';
    currentData = items;
    const sortedItems = sortData(items, sortColumn, sortDirection);
    currentPageIccids = [];

    if (!items.length){
      if (emptyMsg) emptyMsg.style.display = '';
      return;
    }
    if (emptyMsg) emptyMsg.style.display = 'none';

    sortedItems.forEach((it, idx) => {
      currentPageIccids.push(it.iccid);
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="text-muted">${startIndex + idx + 1}</td>
        <td class="mono">${it.iccid || ''}</td>
        <td class="mono">${it.msisdn || ''}</td>
        <td>${it.sim_id || ''}</td>
        <td>${it.country || ''}</td>
        <td>${it.operator || ''}</td>
        <td>${it.billing_status || "-"}</td>
        <td>${it.start_fmt || ''}</td>
        <td>${statusBadge(it.status || '')}</td>
        <td>${it.usage || ''}</td>
        <td>${fmtIso(it.updated_at || '')}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  function updatePageInfo(pageCount, start, end){
    lastPageCount = Math.max(1, pageCount);

    // Actualiza label de páginas
    const humanStart = totalFiltered === 0 ? 0 : start + 1;
    const humanEnd   = end;
    if (pageInfo) {
      pageInfo.textContent = `Página ${currentPage+1} de ${lastPageCount} — mostrando ${humanStart}–${humanEnd} de ${totalFiltered}`;
    }

    // Habilita/inhabilita navegación
    if (btnFirst) btnFirst.disabled = (currentPage === 0);
    if (btnPrev)  btnPrev.disabled  = (currentPage === 0);
    if (btnNext)  btnNext.disabled  = (currentPage >= lastPageCount - 1);
    if (btnLast)  btnLast.disabled  = (currentPage >= lastPageCount - 1);

    // Limita "Ir a"
    if (gotoInput) {
      gotoInput.setAttribute('min', '1');
      gotoInput.setAttribute('max', String(lastPageCount));

      // si hay un valor fuera de rango, se recorta automáticamente
      const val = parseInt(gotoInput.value || '1', 10);
      if (!isNaN(val)) {
        gotoInput.value = String(clamp(val, 1, lastPageCount));
      } else {
        gotoInput.value = '1';
      }

      // desactiva si solo hay 1 página
      gotoInput.disabled = lastPageCount <= 1;
    }
    if (gotoBtn) {
      gotoBtn.disabled = lastPageCount <= 1;
    }
  }

  async function fetchBatch(offset, limit, q){
    const res = await fetch('/api/sims/batch', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ offset, limit, q })
    });
    if (!res.ok) throw new Error('HTTP '+res.status);
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || 'Error lote');

    // progreso + config + última/next ejecución (todo opcional)
    if (data.meta && data.meta.progress) {
      const { total = 0, done = 0 } = data.meta.progress;
      const pct = total ? Math.round((done / total) * 100) : 0;
      if (bar)  bar.style.width = pct + '%';
      if (bar)  bar.textContent = pct + '%';
      if (prog) prog.textContent = (done >= total && total > 0)
        ? 'Completado'
        : `Actualizados ${done} de ${total}`;
    }
    if (data.meta && data.meta.config){
      if (cfgBatch)   cfgBatch.textContent   = `Lote (bg): ${data.meta.config.batch_size}`;
      if (cfgPar)     cfgPar.textContent     = `Paralelo (página): ${data.meta.config.ondemand_workers}`;
      if (cfgWorkers) cfgWorkers.textContent = `Workers (bg): ${data.meta.config.workers}`;
    }
    if (data.meta && data.meta.last_full_refresh){
      if (lastRefresh) lastRefresh.textContent = fmtIso(data.meta.last_full_refresh);
      if (bannerLastRefresh) bannerLastRefresh.textContent = fmtIso(data.meta.last_full_refresh);
    }

    totalFiltered = (data.meta && typeof data.meta.filtered === 'number') ? data.meta.filtered : data.count;

    return data.items;
  }

  async function loadPage(){
    const sel = pageSizeSel ? pageSizeSel.value : '50';
    const pageSize = sel === 'all' ? 500 : parseInt(sel || '50', 10);

    const q = (filterInput && filterInput.value ? filterInput.value : '').trim();
    const offset = currentPage * pageSize;

    const items = await fetchBatch(offset, pageSize, q);
    renderRows(items, offset);

    const pageCount = Math.max(1, Math.ceil(totalFiltered / pageSize));
    const end = Math.min(offset + items.length, totalFiltered);
    updatePageInfo(pageCount, offset, end);

    // reactivar navegación por si venías de "Todos"
    if (btnFirst) btnFirst.disabled = (currentPage === 0);
    if (btnPrev)  btnPrev.disabled  = (currentPage === 0);
    if (btnNext)  btnNext.disabled  = (currentPage >= pageCount - 1);
    if (btnLast)  btnLast.disabled  = (currentPage >= pageCount - 1);
  }

  // Botón "Actualizar ahora" (solo página visible)
  async function refreshNow(){
    const iccids = currentPageIccids.slice();
    if (!iccids.length || !btnRefresh) return;
    btnRefresh.disabled = true;
    btnRefresh.textContent = 'Actualizando...';
    try{
      const res = await fetch('/api/sims/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ iccids })
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.error || 'Error refresh');

      const map = new Map(data.items.map(x => [x.iccid, x]));
      for (const tr of tbody.rows){
        const ic = tr.cells[1].innerText.trim();
        const it = map.get(ic);
        if (it){
          tr.cells[2].innerText = it.msisdn || '';
          tr.cells[3].innerText = it.sim_id || '';
          tr.cells[4].innerText = it.country || '';
          tr.cells[5].innerText = it.operator || '';
          tr.cells[6].innerText = it.billing_status || '-';
          tr.cells[7].innerText = it.start_fmt || '';
          const st = (it.status||'').toUpperCase();
          let cls='status-other'; if(st==='ONLINE')cls='status-online'; else if(st==='OFFLINE')cls='status-offline'; else if(st==='ERROR'||st==='TIMEOUT')cls='status-error';
          tr.cells[8].innerHTML = `<span class="badge ${cls}">${st}</span>`;
          tr.cells[9].innerText = it.usage || '';
          tr.cells[10].innerText = fmtIso(it.updated_at || '');
        }
      }
    } catch(e){
      console.error(e);
      alert('No se pudo actualizar. Reintenta.');
    } finally {
      btnRefresh.disabled = false;
      btnRefresh.textContent = 'Actualizar ahora';
    }
  }

  async function pollStatus(){
    try {
      const r = await fetch('/api/sims/status');
      if (!r.ok) return;
      const j = await r.json();
      if (!j.ok) return;
      const total = (j.meta?.progress?.total) || j.total_sims || 0;
      const done  = (j.meta?.progress?.done)  || 0;
      const pct = total ? Math.round((done / total) * 100) : 0;
      if (bar)  bar.style.width = pct + '%';
      if (bar)  bar.textContent = pct + '%';
      if (prog) prog.textContent = (done >= total && total > 0)
        ? 'Completado'
        : `Actualizados ${done} de ${total}`;

      if (j.config){
        if (cfgBatch)   cfgBatch.textContent   = `Lote (bg): ${j.config.batch_size}`;
        if (cfgPar)     cfgPar.textContent     = `Paralelo (página): ${j.config.ondemand_workers}`;
        if (cfgWorkers) cfgWorkers.textContent = `Workers (bg): ${j.config.workers}`;
      }
      if (j.meta?.last_full_refresh && lastRefresh){
        lastRefresh.textContent = fmtIso(j.meta.last_full_refresh);
      }
      if (j.next_planned && nextPlanned){
        nextPlanned.textContent = fmtIso(j.next_planned);
      }

      // Actualizar banner superior
      if (j.meta?.last_full_refresh){
        if (bannerLastRefresh) bannerLastRefresh.textContent = fmtIso(j.meta.last_full_refresh);
        if (updateBanner) {
          updateBanner.classList.remove('alert-warning');
          updateBanner.classList.add('alert-info');
        }
      } else {
        if (bannerLastRefresh) bannerLastRefresh.textContent = 'En progreso...';
        if (updateBanner) {
          updateBanner.classList.remove('alert-info');
          updateBanner.classList.add('alert-warning');
        }
      }
      if (j.next_planned && bannerNextPlanned){
        bannerNextPlanned.textContent = fmtIso(j.next_planned);
      }
    } catch(e) {}
  }

  // ===== Navegación y eventos =====
  if (btnFirst) btnFirst.addEventListener('click', async () => { currentPage = 0; await loadPage(); });
  if (btnPrev)  btnPrev.addEventListener('click',  async () => { if (currentPage > 0){ currentPage--; await loadPage(); }});
  if (btnNext)  btnNext.addEventListener('click',  async () => {
    const sel = pageSizeSel ? pageSizeSel.value : '50';
    const pageSize = sel === 'all' ? 500 : parseInt(sel || '50', 10);
    const pageCount = Math.max(1, Math.ceil(totalFiltered / pageSize));
    if (currentPage < pageCount - 1){ currentPage++; await loadPage(); }
  });
  if (btnLast)  btnLast.addEventListener('click',  async () => {
    const sel = pageSizeSel ? pageSizeSel.value : '50';
    const pageSize = sel === 'all' ? 500 : parseInt(sel || '50', 10);
    const pageCount = Math.max(1, Math.ceil(totalFiltered / pageSize));
    currentPage = pageCount - 1;
    await loadPage();
  });

  function gotoPage(n){
    const sel = pageSizeSel ? pageSizeSel.value : '50';
    const pageSize = sel === 'all' ? 500 : parseInt(sel || '50', 10);
    const pageCount = Math.max(1, Math.ceil(totalFiltered / pageSize));
    const target = clamp(n, 1, pageCount) - 1;  // <= aquí limitamos definitivamente
    currentPage = target;
    loadPage();
  }

  if (gotoBtn) gotoBtn.addEventListener('click', (e) => {
    e.preventDefault();
    const n = parseInt((gotoInput && gotoInput.value) || '1', 10);
    if (!isNaN(n)) gotoPage(n);
  });

  if (gotoInput) gotoInput.addEventListener('input', () => {
    // En vivo, no dejar escribir más que el máximo
    const val = parseInt(gotoInput.value || '1', 10);
    if (!isNaN(val)) {
      gotoInput.value = String(clamp(val, 1, lastPageCount));
    }
  });

  if (gotoInput) gotoInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter'){
      e.preventDefault();
      const n = parseInt((gotoInput && gotoInput.value) || '1', 10);
      if (!isNaN(n)) gotoPage(n);
    }
  });

  if (filterInput) filterInput.addEventListener('input', async () => { currentPage = 0; await loadPage(); });
  if (pageSizeSel) pageSizeSel.addEventListener('change', async () => { currentPage = 0; await loadPage(); });
  if (btnRefresh)  btnRefresh.addEventListener('click', refreshNow);

  // ===== Tareas periódicas =====
  async function runAllBatches(){
    if (!pageSizeSel) return;
    const pageSize = parseInt(pageSizeSel.value || '50', 10);
    const q = (filterInput && filterInput.value ? filterInput.value : '').trim();

    try {
      const first = await fetch('/api/sims/batch', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ offset: 0, limit: 1, q })
      });
      if (!first.ok) return;
      const firstJson = await first.json();
      if (!firstJson.ok) return;
      const total = firstJson.meta?.filtered ?? firstJson.count ?? 0;

      for (let offset = 0; offset < total; offset += pageSize) {
        try {
          await fetch('/api/sims/batch', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ offset, limit: pageSize, q })
          });
        } catch(e) { console.error(e); }
      }
    } catch(e) { console.error(e); }
  }

  // ===== Init =====
  (async function init(){
    await loadPage();
    setInterval(runAllBatches, hourlyMs);
    setInterval(pollStatus,    pollMs);
    await pollStatus();

    // Event listeners para ordenamiento
    document.querySelectorAll("th.sortable").forEach(th => {
      th.addEventListener("click", () => {
        const column = th.dataset.col;
        if (sortColumn === column) {
          sortDirection = sortDirection === "asc" ? "desc" : "asc";
        } else {
          sortColumn = column;
          sortDirection = "asc";
        }
        document.querySelectorAll("th.sortable").forEach(h => {
          h.classList.remove("asc", "desc");
        });
        th.classList.add(sortDirection);
        if (currentData.length > 0) {
          renderRows(currentData, (currentPage * parseInt(pageSizeSel?.value || 50)));
        }
      });
    });
  })();
})();
