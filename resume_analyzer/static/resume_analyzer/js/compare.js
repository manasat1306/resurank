(function () {
  var form = document.getElementById('compare-form');
  if (!form) return;

  // Maximum comes from the server (Free = 4, Pro = 100 which means unlimited)
  var MAX = parseInt(form.dataset.max, 10) || 4;
  var UNLIMITED = MAX >= 100;
  var MIN = 2;
  var limitHit = false;

  var checks = Array.prototype.slice.call(document.querySelectorAll('.picker-check'));
  var cards = Array.prototype.slice.call(document.querySelectorAll('.picker-card'));
  var idsInput = document.getElementById('compare-ids');
  var countEl = document.getElementById('selected-count');
  var hintEl = document.getElementById('picker-hint');
  var submitBtn = document.getElementById('picker-submit');
  var clearBtn = document.getElementById('picker-clear');
  var searchInput = document.getElementById('picker-search');
  var emptyMsg = document.getElementById('picker-empty');

  function selected() {
    return checks.filter(function (c) { return c.checked; });
  }

  function showUpgradeModal() {
    if (document.getElementById('upgrade-modal')) return;

    var overlay = document.createElement('div');
    overlay.id = 'upgrade-modal';
    overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;z-index:9999;background:rgba(15,23,42,0.55);display:flex;align-items:center;justify-content:center;padding:16px';

    overlay.innerHTML =
      '<div style="position:relative;background:#ffffff;border-radius:20px;max-width:420px;width:100%;padding:32px;text-align:center;box-shadow:0 20px 50px rgba(0,0,0,0.3)">' +
        '<button id="upgrade-modal-x" type="button" aria-label="Close" style="position:absolute;top:12px;right:16px;border:none;background:none;font-size:28px;line-height:1;color:#94a3b8;cursor:pointer">&times;</button>' +
        '<div style="height:56px;width:56px;margin:0 auto 16px;border-radius:16px;background:#eef2ff;color:#4f46e5;display:flex;align-items:center;justify-content:center;font-size:28px"><i class="ti ti-crown"></i></div>' +
        '<div style="font-size:20px;font-weight:700;color:#0f172a;margin-bottom:8px">You reached your compare limit</div>' +
        '<div style="font-size:14px;color:#64748b;margin-bottom:24px">The Free plan lets you compare up to ' + MAX + ' candidates at a time. Upgrade to Pro to compare unlimited candidates.</div>' +
        '<a href="/plans/checkout/" style="display:block;background:linear-gradient(to right,#4f46e5,#7c3aed);color:#ffffff;font-weight:600;font-size:14px;padding:12px 16px;border-radius:10px;text-decoration:none;margin-bottom:10px">Upgrade to Pro</a>' +
        '<button id="upgrade-modal-later" type="button" style="border:none;background:none;color:#64748b;font-size:13px;cursor:pointer;padding:6px">Maybe later</button>' +
      '</div>';

    document.body.appendChild(overlay);

    function closeModal() {
      overlay.remove();
      document.removeEventListener('keydown', onKey);
    }
    function onKey(e) {
      if (e.key === 'Escape') closeModal();
    }

    document.getElementById('upgrade-modal-x').addEventListener('click', closeModal);
    document.getElementById('upgrade-modal-later').addEventListener('click', closeModal);
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeModal();
    });
    document.addEventListener('keydown', onKey);
  }

  function refresh() {
    var chosen = selected();
    var n = chosen.length;

    countEl.textContent = UNLIMITED ? n + ' selected' : n + ' of ' + MAX + ' selected';
    idsInput.value = chosen.map(function (c) { return c.value; }).join(',');
    submitBtn.disabled = n < MIN;

    if (limitHit && !UNLIMITED) {
      hintEl.style.color = '#d97706';
      hintEl.innerHTML = 'Free plan allows up to ' + MAX + ' candidates. ' +
        '<a href="/plans/checkout/" class="font-semibold underline">Upgrade to Pro</a> to compare more.';
    } else {
      hintEl.style.color = '';
      if (n < MIN) {
        hintEl.textContent = 'Select at least 2 candidates';
      } else if (!UNLIMITED && n >= MAX) {
        hintEl.textContent = n + ' selected (maximum on your plan)';
      } else {
        hintEl.textContent = n + ' candidates ready to compare';
      }
    }

    checks.forEach(function (c) {
      var card = c.closest('.picker-card');
      card.classList.toggle('border-indigo-500', c.checked);
      card.classList.toggle('bg-indigo-50/60', c.checked);
    });
  }

  checks.forEach(function (c) {
    c.addEventListener('change', function () {
      if (c.checked && selected().length > MAX) {
        c.checked = false;
        limitHit = true;
        showUpgradeModal();
      } else {
        limitHit = false;
      }
      refresh();
    });
  });

  clearBtn.addEventListener('click', function () {
    checks.forEach(function (c) { c.checked = false; });
    limitHit = false;
    refresh();
  });

  searchInput.addEventListener('input', function () {
    var q = searchInput.value.trim().toLowerCase();
    var visible = 0;
    cards.forEach(function (card) {
      var match = card.getAttribute('data-name').indexOf(q) !== -1;
      card.classList.toggle('hidden', !match);
      if (match) visible++;
    });
    emptyMsg.classList.toggle('hidden', visible !== 0);
  });

  form.addEventListener('submit', function (e) {
    var n = selected().length;
    if (n < MIN || n > MAX) e.preventDefault();
  });

  refresh();
})();