// index.html scripts (externo)
(function () {
  const form = document.getElementById('searchForm');
  const overlay = document.getElementById('loadingOverlay');
  const resultSection = document.getElementById('resultSection');
  const errBox = document.getElementById('errBox');

  if (form) {
    form.addEventListener('submit', () => {
      if (resultSection) resultSection.style.display = 'none'; // borra visualmente lo anterior
      if (errBox) errBox.style.display = 'none';
      overlay.style.display = 'flex';
    });
  }

  window.addEventListener('load', () => {
    if (overlay) overlay.style.display = 'none';
    if (resultSection) resultSection.style.display = '';
  });
})();
