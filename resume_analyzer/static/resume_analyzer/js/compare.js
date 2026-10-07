(function () {
  var MAX = 4;
  var MIN = 2;

  var form = document.getElementById('compare-form');
  if (!form) return;

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

  function refresh() {
    var chosen = selected();
    var n = chosen.length;

    countEl.textContent = n + ' of ' + MAX + ' selected';
    idsInput.value = chosen.map(function (c) { return c.value; }).join(',');
    submitBtn.disabled = n < MIN;

    if (n < MIN) {
      hintEl.textContent = 'Select at least 2 candidates';
    } else if (n >= MAX) {
      hintEl.textContent = 'Maximum 4 candidates';
    } else {
      hintEl.textContent = n + ' candidates ready to compare';
    }

    checks.forEach(function (c) {
      var card = c.closest('.picker-card');
      var locked = n >= MAX && !c.checked;
      c.disabled = locked;
      card.classList.toggle('opacity-50', locked);
      card.classList.toggle('cursor-not-allowed', locked);
      card.classList.toggle('border-indigo-500', c.checked);
      card.classList.toggle('bg-indigo-50/60', c.checked);
    });
  }

  checks.forEach(function (c) { c.addEventListener('change', refresh); });

  clearBtn.addEventListener('click', function () {
    checks.forEach(function (c) { c.checked = false; });
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
    if (selected().length < MIN) e.preventDefault();
  });

  refresh();
})();