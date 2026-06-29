/* ================================================================
   Élan Parfums CRM — elan.js
   ================================================================ */

document.addEventListener('DOMContentLoaded', () => {

  // ── Auto-dismiss alerts ──────────────────────────────────────────
  document.querySelectorAll('.alert').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity .4s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 400);
    }, 4000);
  });

  // ── Style Django form widgets ────────────────────────────────────
  document.querySelectorAll(
    '.form-group input:not([type=checkbox]):not([type=radio]),' +
    '.form-group select,.form-group textarea'
  ).forEach(el => el.classList.add('form-control'));

  // ── Revenue bar chart ────────────────────────────────────────────
  const chart = document.querySelector('.bar-chart');
  if (chart) {
    const bars = chart.querySelectorAll('.bar');
    const vals = Array.from(bars).map(b => parseFloat(b.dataset.val) || 0);
    const max  = Math.max(...vals, 1);
    bars.forEach(b => {
      b.style.height = (Math.round((parseFloat(b.dataset.val) / max) * 82) || 4) + 'px';
    });
  }

  // ── Pipeline stage bars (admin dashboard) ───────────────────────
  const pipelineWrap = document.getElementById('pipeline-stages');
  if (pipelineWrap) {
    const stageBars = pipelineWrap.querySelectorAll('.db-stage-bar');
    const counts    = Array.from(stageBars).map(b => parseInt(b.dataset.count) || 0);
    const maxCount  = Math.max(...counts, 1);
    stageBars.forEach(b => {
      b.style.width = Math.round((parseInt(b.dataset.count) / maxCount) * 100) + '%';
    });
  }

  // ── Global Search ────────────────────────────────────────────────
  const searchWrap  = document.getElementById('search-wrap');
  const searchInput = document.getElementById('global-search-input');
  const searchBar   = document.getElementById('search-trigger');
  const searchDrop  = document.getElementById('search-dropdown');
  const searchEmpty = document.getElementById('search-empty');
  const searchRes   = document.getElementById('search-results');

  const BADGE = {
    Contact: 'sri-contact', Lead: 'sri-lead', Deal: 'sri-deal',
    Fragrance: 'sri-fragrance', Sale: 'sri-sale',
  };

  let searchTimer = null;

  function openSearch()  { searchBar?.classList.add('focused');    searchDrop?.classList.add('open'); searchInput?.focus(); }
  function closeSearch() { searchBar?.classList.remove('focused'); searchDrop?.classList.remove('open'); }

  if (searchInput) {
    searchBar.addEventListener('click', openSearch);

    searchInput.addEventListener('input', () => {
      clearTimeout(searchTimer);
      const q = searchInput.value.trim();
      if (q.length < 2) {
        searchRes.innerHTML = '';
        searchEmpty.style.display = 'block';
        searchEmpty.textContent = 'Start typing to search…';
        return;
      }
      searchEmpty.textContent = 'Searching…';
      searchEmpty.style.display = 'block';
      searchRes.innerHTML = '';

      searchTimer = setTimeout(() => {
        fetch(`/search/?q=${encodeURIComponent(q)}`)
          .then(r => r.json())
          .then(data => {
            searchEmpty.style.display = 'none';
            if (!data.results?.length) {
              searchRes.innerHTML = '<div class="search-no-results">No results found</div>';
              return;
            }
            searchRes.innerHTML = data.results.map(item => `
              <a href="${item.url}" class="search-result-item">
                <span class="sri-badge ${BADGE[item.type] || ''}">${item.type}</span>
                <div class="sri-body">
                  <div class="sri-name">${item.name}</div>
                  ${item.sub ? `<div class="sri-sub">${item.sub}</div>` : ''}
                </div>
              </a>`).join('');
          })
          .catch(() => { searchEmpty.style.display = 'block'; searchEmpty.textContent = 'Search unavailable'; });
      }, 280);
    });

    searchInput.addEventListener('keydown', e => {
      if (e.key === 'Escape') { closeSearch(); searchInput.value = ''; searchRes.innerHTML = ''; }
    });

    document.addEventListener('click', e => {
      if (searchWrap && !searchWrap.contains(e.target)) closeSearch();
    });
  }

  // ── Notification Bell ────────────────────────────────────────────
  const bellBtn   = document.getElementById('bell-btn');
  const bellWrap  = document.getElementById('bell-wrap');
  const notifDrop = document.getElementById('notif-dropdown');

  if (bellBtn && notifDrop) {
    bellBtn.addEventListener('click', e => {
      e.stopPropagation();
      const open = notifDrop.classList.contains('open');
      if (searchDrop) searchDrop.classList.remove('open');
      notifDrop.classList.toggle('open', !open);
      bellBtn.classList.toggle('active', !open);
    });
    document.addEventListener('click', e => {
      if (bellWrap && !bellWrap.contains(e.target)) {
        notifDrop.classList.remove('open');
        bellBtn.classList.remove('active');
      }
    });
  }

  // ── POS ─────────────────────────────────────────────────────────
  if (document.getElementById('pos-form')) {
    POS.init();
  }

}); // end DOMContentLoaded


/* ================================================================
   POS module — cart, payment tabs, overlay
   ================================================================ */

const POS = (() => {
  // Cart state: Map<fragId, {id, name, price, qty, stock}>
  const cart = new Map();

  // ── DOM refs (populated in init) ──
  let itemsEl, emptyEl, countEl, subtotalEl, totalEl,
      discountDisplayEl, discountRow,
      discountInput, tenderedInput, changeRow, changeDisplay,
      submitBtn, form, overlay,
      stateProcessing, stateSuccess, stateError,
      payTabsEl, cashExtras, mpesaExtras,
      currentMethod = 'cash';

  function init() {
    itemsEl          = document.getElementById('cart-items');
    emptyEl          = document.getElementById('cart-empty-msg');
    countEl          = document.getElementById('cart-count');
    subtotalEl       = document.getElementById('display-subtotal');
    totalEl          = document.getElementById('cart-total');
    discountDisplayEl= document.getElementById('display-discount');
    discountRow      = document.getElementById('discount-row');
    discountInput    = document.getElementById('discount-input');
    tenderedInput    = document.getElementById('tendered-input');
    changeRow        = document.getElementById('change-row');
    changeDisplay    = document.getElementById('change-display');
    submitBtn        = document.getElementById('pos-submit-btn');
    form             = document.getElementById('pos-form');
    overlay          = document.getElementById('pos-overlay');
    stateProcessing  = document.getElementById('overlay-processing');
    stateSuccess     = document.getElementById('overlay-success');
    stateError       = document.getElementById('overlay-error');
    payTabsEl        = document.getElementById('pay-tabs');
    cashExtras       = document.getElementById('cash-extras');
    mpesaExtras      = document.getElementById('mpesa-extras');

    // Payment tabs
    payTabsEl?.querySelectorAll('.pos-pay-tab').forEach(tab => {
      tab.addEventListener('click', () => switchPayment(tab.dataset.method));
    });

    // Discount input
    discountInput?.addEventListener('input', render);

    // Cash tendered
    tenderedInput?.addEventListener('input', updateChange);

    // Clear-cart button
    document.getElementById('pos-clear-btn')?.addEventListener('click', clearCart);

    // Submit
    submitBtn?.addEventListener('click', submitSale);

    // POS search
    const posSearch = document.getElementById('pos-search');
    posSearch?.addEventListener('input', () => filterGrid(posSearch.value));
    posSearch?.addEventListener('keydown', e => {
      if (e.key === 'Escape') { posSearch.value = ''; filterGrid(''); }
    });

    // Overlay dismiss
    document.getElementById('overlay-dismiss')?.addEventListener('click', hideOverlay);

    render();
  }

  // ── Add to cart ──────────────────────────────────────────────────
  function addToCart(id, name, price, stock) {
    const existing = cart.get(id);
    if (existing) {
      if (existing.qty >= existing.stock) return showStockWarning(name);
      existing.qty++;
    } else {
      cart.set(id, { id, name, price: parseFloat(price), qty: 1, stock: parseInt(stock) });
    }
    flashRipple(id);
    floatAdd(id);
    pulseBadge();
    render();
  }

  // ── Qty controls ─────────────────────────────────────────────────
  function increment(id) {
    const item = cart.get(id);
    if (!item) return;
    if (item.qty >= item.stock) return showStockWarning(item.name);
    item.qty++;
    render();
  }

  function decrement(id) {
    const item = cart.get(id);
    if (!item) return;
    item.qty--;
    if (item.qty <= 0) removeItem(id);
    else render();
  }

  function removeItem(id) {
    const row = document.querySelector(`.cart-item-row[data-id="${id}"]`);
    if (row) {
      row.classList.add('removing');
      row.addEventListener('animationend', () => { cart.delete(id); render(); }, { once: true });
    } else {
      cart.delete(id);
      render();
    }
  }

  function clearCart() {
    cart.clear();
    render();
  }

  // ── Render cart ──────────────────────────────────────────────────
  function render() {
    if (!itemsEl) return;

    const items = [...cart.values()];
    // Remove stale rows (not in removing state)
    itemsEl.querySelectorAll('.cart-item-row:not(.removing)').forEach(r => {
      if (!cart.has(parseInt(r.dataset.id))) r.remove();
    });

    // Hide / show empty message
    emptyEl.style.display = items.length ? 'none' : 'flex';

    // Add / update rows
    items.forEach(item => {
      let row = itemsEl.querySelector(`.cart-item-row[data-id="${item.id}"]`);
      if (!row) {
        row = document.createElement('div');
        row.className = 'cart-item-row';
        row.dataset.id = item.id;
        itemsEl.appendChild(row);
      }
      const lineTotal = (item.price * item.qty).toLocaleString();
      row.innerHTML = `
        <div class="cart-item-info">
          <div class="cart-item-name">${item.name}</div>
          <div class="cart-item-price">TZS ${item.price.toLocaleString()} each</div>
        </div>
        <div class="cart-qty-wrap">
          <button class="cart-qty-btn" onclick="POS.decrement(${item.id})">−</button>
          <span class="cart-qty-num">${item.qty}</span>
          <button class="cart-qty-btn" onclick="POS.increment(${item.id})">+</button>
        </div>
        <span class="cart-item-line">TZS ${lineTotal}</span>
        <button class="cart-remove-btn" onclick="POS.removeItem(${item.id})" title="Remove">×</button>`;
    });

    // Totals
    const subtotal  = items.reduce((s, i) => s + i.price * i.qty, 0);
    const discount  = Math.max(parseFloat(discountInput?.value || 0) || 0, 0);
    const total     = Math.max(subtotal - discount, 0);
    const itemCount = items.reduce((s, i) => s + i.qty, 0);

    if (subtotalEl)        subtotalEl.textContent       = 'TZS ' + subtotal.toLocaleString();
    if (totalEl)           totalEl.textContent           = 'TZS ' + total.toLocaleString();
    if (countEl)           countEl.textContent           = itemCount;
    if (discountRow)       discountRow.style.display     = discount > 0 ? 'flex' : 'none';
    if (discountDisplayEl) discountDisplayEl.textContent = '−TZS ' + discount.toLocaleString();

    // Enable / disable submit
    if (submitBtn) submitBtn.disabled = items.length === 0;

    // Refresh change display
    updateChange();
  }

  // ── Payment ──────────────────────────────────────────────────────
  function switchPayment(method) {
    currentMethod = method;
    payTabsEl.querySelectorAll('.pos-pay-tab').forEach(t => {
      t.classList.toggle('active', t.dataset.method === method);
    });
    if (cashExtras)  cashExtras.style.display  = method === 'cash'  ? '' : 'none';
    if (mpesaExtras) mpesaExtras.style.display = method === 'mpesa' ? '' : 'none';
    updateChange();
  }

  function updateChange() {
    if (currentMethod !== 'cash' || !tenderedInput || !changeRow) return;
    const subtotal = [...cart.values()].reduce((s, i) => s + i.price * i.qty, 0);
    const discount = Math.max(parseFloat(discountInput?.value || 0) || 0, 0);
    const total    = Math.max(subtotal - discount, 0);
    const tendered = parseFloat(tenderedInput.value) || 0;
    const change   = tendered - total;

    changeRow.style.display = tendered > 0 ? 'flex' : 'none';
    if (changeDisplay) {
      if (change >= 0) {
        changeDisplay.textContent = 'TZS ' + change.toLocaleString();
        changeDisplay.style.color = 'var(--teal)';
        changeRow.style.background = 'rgba(5,150,105,.06)';
        changeRow.style.borderTopColor = 'rgba(5,150,105,.2)';
      } else {
        changeDisplay.textContent = '−TZS ' + Math.abs(change).toLocaleString() + ' short';
        changeDisplay.style.color = 'var(--red)';
        changeRow.style.background = 'rgba(220,38,38,.06)';
        changeRow.style.borderTopColor = 'rgba(220,38,38,.15)';
      }
    }
  }

  // ── AJAX sale submission ─────────────────────────────────────────
  function submitSale() {
    if (cart.size === 0) return;

    // Build FormData
    const fd = new FormData(form);
    const items = [...cart.values()];
    items.forEach((item, idx) => {
      fd.append(`items[${idx}][id]`,    item.id);
      fd.append(`items[${idx}][qty]`,   item.qty);
      fd.append(`items[${idx}][price]`, item.price);
    });

    const subtotal = items.reduce((s, i) => s + i.price * i.qty, 0);
    const discount = Math.max(parseFloat(discountInput?.value || 0) || 0, 0);
    const total    = Math.max(subtotal - discount, 0);
    fd.set('subtotal',        subtotal);
    fd.set('discount',        discount);
    fd.set('total',           total);
    fd.set('payment_method',  currentMethod);
    fd.set('tendered',        tenderedInput?.value || 0);
    fd.set('contact',         document.getElementById('contact-select')?.value || '');

    // Show overlay
    showOverlay('processing');

    // Disable button
    const label   = submitBtn.querySelector('.pos-cta-label');
    const loading = submitBtn.querySelector('.pos-cta-loading');
    if (label)   label.style.display   = 'none';
    if (loading) loading.style.display = 'flex';
    submitBtn.disabled = true;

    fetch(form.action, {
      method: 'POST',
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      body: fd,
    })
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          showSuccess(data);
          setTimeout(() => { window.location.href = data.redirect; }, 2200);
        } else {
          showError(data.error || 'Sale failed. Please try again.');
          resetButton();
        }
      })
      .catch(err => {
        showError('Network error — check your connection and try again.');
        console.error(err);
        resetButton();
      });
  }

  function resetButton() {
    const label   = submitBtn?.querySelector('.pos-cta-label');
    const loading = submitBtn?.querySelector('.pos-cta-loading');
    if (label)   label.style.display   = '';
    if (loading) loading.style.display = 'none';
    if (submitBtn) submitBtn.disabled = cart.size === 0;
  }

  // ── Overlay helpers ──────────────────────────────────────────────
  function showOverlay(state) {
    overlay.style.display = 'flex';
    [stateProcessing, stateSuccess, stateError].forEach(s => s && (s.style.display = 'none'));
    if (state === 'processing' && stateProcessing) stateProcessing.style.display = 'flex';
    if (state === 'success'    && stateSuccess)    stateSuccess.style.display    = 'flex';
    if (state === 'error'      && stateError)      stateError.style.display      = 'flex';
  }

  function showSuccess(data) {
    showOverlay('success');

    document.getElementById('overlay-ref').textContent   = data.reference;
    document.getElementById('overlay-title').textContent = 'Sale completed!';

    const details = document.getElementById('overlay-details');
    if (details) {
      const change = parseFloat(data.change) || 0;
      details.innerHTML = `
        <div class="ol-row"><span>Total</span><span class="ol-val">TZS ${parseFloat(data.total).toLocaleString()}</span></div>
        <div class="ol-row"><span>Payment</span><span class="ol-val">${data.payment}</span></div>
        <div class="ol-row"><span>Customer</span><span class="ol-val">${data.customer}</span></div>
        ${change > 0 ? `<div class="ol-row" style="color:var(--teal)"><span>Change</span><span class="ol-val">TZS ${change.toLocaleString()}</span></div>` : ''}
      `;
    }
    // Reset check animation by cloning nodes
    ['overlay-check-ring', 'overlay-check-tick'].forEach(cls => {
      const el = document.querySelector(`.${cls}`);
      if (el) { const c = el.cloneNode(true); el.parentNode.replaceChild(c, el); }
    });
    // Countdown
    let secs = 2;
    const rdEl = document.getElementById('overlay-redirect');
    if (rdEl) {
      rdEl.textContent = `Redirecting in ${secs}s…`;
      const t = setInterval(() => {
        secs--;
        if (rdEl) rdEl.textContent = `Redirecting in ${secs}s…`;
        if (secs <= 0) clearInterval(t);
      }, 1000);
    }
    // Clear cart on success
    cart.clear();
  }

  function showError(msg) {
    showOverlay('error');
    const el = document.getElementById('overlay-error-msg');
    if (el) el.textContent = msg;
  }

  function hideOverlay() {
    overlay.style.display = 'none';
    resetButton();
  }

  // ── Product grid filter ──────────────────────────────────────────
  function filterGrid(q) {
    q = q.toLowerCase().trim();
    document.querySelectorAll('#pos-grid [data-name]').forEach(el => {
      const hit = !q || el.dataset.name.includes(q) || (el.dataset.brand || '').includes(q);
      el.style.display = hit ? '' : 'none';
    });
  }

  // ── Micro-animations ─────────────────────────────────────────────
  function flashRipple(id) {
    const card = document.querySelector(`#pos-grid [data-id="${id}"]`);
    if (!card) return;
    card.classList.remove('rippling');
    void card.offsetWidth;
    card.classList.add('rippling');
    setTimeout(() => card.classList.remove('rippling'), 360);
  }

  function floatAdd(id) {
    const card = document.querySelector(`#pos-grid [data-id="${id}"]`);
    if (!card) return;
    const rect = card.getBoundingClientRect();
    const el   = document.createElement('div');
    el.className = 'pos-float-add';
    el.textContent = '+1';
    el.style.left = (rect.left + rect.width / 2 - 18) + 'px';
    el.style.top  = (rect.top + 12) + 'px';
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 560);
  }

  function pulseBadge() {
    if (!countEl) return;
    countEl.classList.remove('pulse');
    void countEl.offsetWidth;
    countEl.classList.add('pulse');
  }

  function showStockWarning(name) {
    // Brief red flash on the count badge
    if (countEl) {
      countEl.style.background = 'var(--red)';
      setTimeout(() => { countEl.style.background = ''; }, 600);
    }
  }

  // Public API
  return { init, addToCart, increment, decrement, removeItem };
})();
