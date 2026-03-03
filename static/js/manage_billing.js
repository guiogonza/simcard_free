// Gestión de Billing Status
(function () {
  // DOM Elements
  const searchForm = document.getElementById('searchForm');
  const searchField = document.getElementById('searchField');
  const searchValue = document.getElementById('searchValue');
  const resultsSection = document.getElementById('resultsSection');
  const noResults = document.getElementById('noResults');
  const resultsTableBody = document.getElementById('resultsTableBody');
  const resultCount = document.getElementById('resultCount');
  const selectAllCheckbox = document.getElementById('selectAllCheckbox');
  const selectAllBtn = document.getElementById('selectAllBtn');
  const changeStatusBtn = document.getElementById('changeStatusBtn');
  const loadingOverlay = document.getElementById('loadingOverlay');
  const alertContainer = document.getElementById('alertContainer');
  
  // Modal elements
  const changeStatusModal = new bootstrap.Modal(document.getElementById('changeStatusModal'));
  const operationSelect = document.getElementById('operationSelect');
  const executionTypeSelect = document.getElementById('executionTypeSelect');
  const confirmCheckbox = document.getElementById('confirmCheckbox');
  const confirmChangeBtn = document.getElementById('confirmChangeBtn');
  const selectedCount = document.getElementById('selectedCount');
  const selectedSimsList = document.getElementById('selectedSimsList');

  let currentResults = [];
  let selectedSims = new Set();

  // Utility functions
  function showLoading() {
    loadingOverlay.style.display = 'flex';
  }

  function hideLoading() {
    loadingOverlay.style.display = 'none';
  }

  function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    alertContainer.appendChild(alertDiv);
    
    // Auto-dismiss después de 5 segundos
    setTimeout(() => {
      alertDiv.remove();
    }, 5000);
  }

  function getBillingStatusBadge(status) {
    const st = (status || '').toLowerCase();
    let cssClass = 'bg-secondary';
    if (st === 'in billing') cssClass = 'status-in-billing';
    else if (st === 'retired') cssClass = 'status-retired';
    else if (st === 'suspended') cssClass = 'status-suspended';
    return `<span class="badge ${cssClass}">${status || '—'}</span>`;
  }

  function getDataSessionBadge(status) {
    const st = (status || '').toUpperCase();
    let cssClass = 'bg-secondary';
    if (st === 'ONLINE') cssClass = 'status-online';
    else if (st === 'OFFLINE') cssClass = 'status-offline';
    return `<span class="badge ${cssClass}">${st || '—'}</span>`;
  }

  function updateSelectedCount() {
    changeStatusBtn.disabled = selectedSims.size === 0;
    changeStatusBtn.textContent = `Cambiar estado de seleccionadas (${selectedSims.size})`;
  }

  function updateModalSummary() {
    selectedCount.textContent = selectedSims.size;
    selectedSimsList.innerHTML = '';
    
    const selectedData = currentResults.filter(sim => selectedSims.has(sim.iccid));
    selectedData.forEach(sim => {
      const div = document.createElement('div');
      div.className = 'mb-1';
      div.innerHTML = `<span class="mono">${sim.iccid}</span> - ${sim.msisdn || 'N/A'}`;
      selectedSimsList.appendChild(div);
    });
  }

  // Search form handler
  searchForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const field = searchField.value;
    const value = searchValue.value.trim();
    
    if (!value) {
      showAlert('Por favor ingresa un valor de búsqueda', 'warning');
      return;
    }

    showLoading();
    resultsSection.style.display = 'none';
    noResults.style.display = 'none';
    selectedSims.clear();
    updateSelectedCount();

    try {
      // Llamar a la API para obtener datos
      const response = await fetch('/api/sims/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          offset: 0,
          limit: 500,
          q: value
        })
      });

      if (!response.ok) {
        throw new Error('Error en la búsqueda');
      }

      const data = await response.json();
      
      if (!data.ok) {
        throw new Error(data.error || 'Error desconocido');
      }

      currentResults = data.items || [];

      // Filtrar según el campo específico si no es "any"
      if (field !== 'any') {
        currentResults = currentResults.filter(item => {
          const fieldValue = (item[field] || '').toLowerCase();
          return fieldValue.includes(value.toLowerCase());
        });
      }

      if (currentResults.length === 0) {
        noResults.style.display = 'block';
      } else {
        renderResults();
        resultsSection.style.display = 'block';
      }

    } catch (error) {
      console.error('Error:', error);
      showAlert(`Error al buscar: ${error.message}`, 'danger');
    } finally {
      hideLoading();
    }
  });

  function renderResults() {
    resultsTableBody.innerHTML = '';
    resultCount.textContent = currentResults.length;
    selectAllCheckbox.checked = false;

    currentResults.forEach((sim, index) => {
      const row = document.createElement('tr');
      const isSelected = selectedSims.has(sim.iccid);
      if (isSelected) row.classList.add('selected-row');
      
      row.innerHTML = `
        <td>
          <input type="checkbox" class="sim-checkbox" data-iccid="${sim.iccid}" 
                 ${isSelected ? 'checked' : ''}>
        </td>
        <td class="mono small">${sim.iccid || '—'}</td>
        <td class="mono small">${sim.imsi || '—'}</td>
        <td class="mono small">${sim.msisdn || '—'}</td>
        <td>${getBillingStatusBadge(sim.billing_status)}</td>
        <td>${getDataSessionBadge(sim.status)}</td>
        <td>${sim.country || '—'}</td>
        <td>${sim.operator || '—'}</td>
        <td>${sim.usage || '—'}</td>
      `;
      
      const checkbox = row.querySelector('.sim-checkbox');
      checkbox.addEventListener('change', (e) => {
        const iccid = e.target.dataset.iccid;
        if (e.target.checked) {
          selectedSims.add(iccid);
          row.classList.add('selected-row');
        } else {
          selectedSims.delete(iccid);
          row.classList.remove('selected-row');
        }
        updateSelectedCount();
      });
      
      resultsTableBody.appendChild(row);
    });
  }

  // Select all functionality
  selectAllCheckbox.addEventListener('change', (e) => {
    const checkboxes = document.querySelectorAll('.sim-checkbox');
    checkboxes.forEach(cb => {
      cb.checked = e.target.checked;
      const iccid = cb.dataset.iccid;
      const row = cb.closest('tr');
      if (e.target.checked) {
        selectedSims.add(iccid);
        row.classList.add('selected-row');
      } else {
        selectedSims.delete(iccid);
        row.classList.remove('selected-row');
      }
    });
    updateSelectedCount();
  });

  selectAllBtn.addEventListener('click', () => {
    selectAllCheckbox.checked = true;
    selectAllCheckbox.dispatchEvent(new Event('change'));
  });

  // Open modal
  changeStatusBtn.addEventListener('click', () => {
    if (selectedSims.size === 0) return;
    
    updateModalSummary();
    operationSelect.value = '';
    executionTypeSelect.value = 'permanent';
    confirmCheckbox.checked = false;
    confirmChangeBtn.disabled = true;
    
    changeStatusModal.show();
  });

  // Enable confirm button when all fields are filled
  [operationSelect, confirmCheckbox].forEach(element => {
    element.addEventListener('change', () => {
      confirmChangeBtn.disabled = !(operationSelect.value && confirmCheckbox.checked);
    });
  });

  // Confirm change
  confirmChangeBtn.addEventListener('click', async () => {
    const operation = operationSelect.value;
    const executionType = executionTypeSelect.value;
    const iccids = Array.from(selectedSims);

    if (!operation || !confirmCheckbox.checked) {
      showAlert('Por favor completa todos los campos requeridos', 'warning');
      return;
    }

    changeStatusModal.hide();
    showLoading();

    try {
      const response = await fetch('/api/sims/change-billing-status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          iccids: iccids,
          operation: operation,
          execution_type: executionType
        })
      });

      if (!response.ok) {
        throw new Error('Error en la solicitud');
      }

      const data = await response.json();

      if (!data.ok) {
        throw new Error(data.error || 'Error desconocido');
      }

      const successCount = data.successful || 0;
      const failedCount = data.failed || 0;

      let message = `✅ Operación completada: ${successCount} exitosas`;
      if (failedCount > 0) {
        message += `, ${failedCount} fallidas`;
      }

      showAlert(message, failedCount > 0 ? 'warning' : 'success');

      // Mostrar errores si los hay
      if (data.errors && data.errors.length > 0) {
        const errorList = data.errors.map(e => `• ${e.iccid}: ${e.error}`).join('<br>');
        showAlert(`<strong>Errores:</strong><br>${errorList}`, 'danger');
      }

      // Limpiar selección
      selectedSims.clear();
      updateSelectedCount();
      
      // Re-buscar para actualizar datos
      if (currentResults.length > 0) {
        searchForm.dispatchEvent(new Event('submit'));
      }

    } catch (error) {
      console.error('Error:', error);
      showAlert(`Error al cambiar el estado: ${error.message}`, 'danger');
    } finally {
      hideLoading();
    }
  });

})();
