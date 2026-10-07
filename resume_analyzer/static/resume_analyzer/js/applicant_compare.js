document.addEventListener('DOMContentLoaded', function () {
    var btn = document.getElementById('compare-btn');
    var hint = document.getElementById('compare-hint');
    var selectAll = document.getElementById('compare-select-all');
    var checks = Array.from(document.querySelectorAll('.compare-check'));

    if (!btn || checks.length === 0) return;

    var offClasses = ['bg-white', 'text-slate-600', 'border-slate-200', 'hover:bg-slate-50'];
    var onClasses = ['bg-indigo-600', 'text-white', 'border-indigo-600', 'hover:bg-indigo-700'];

    // Make checkboxes bigger and rows clickable
    checks.forEach(function (box) {
        box.classList.add('h-4', 'w-4', 'cursor-pointer');
        var row = box.closest('.applicant-row');
        if (row) row.classList.add('cursor-pointer');
    });

    function isVisible(box) {
        var row = box.closest('.applicant-row');
        return row && row.style.display !== 'none';
    }

    function refresh() {
        // Untick rows hidden by the filters
        checks.forEach(function (box) {
            if (!isVisible(box)) box.checked = false;
        });

        var count = checks.filter(function (box) { return box.checked; }).length;

        // Highlight selected rows, lock other boxes at 4
        checks.forEach(function (box) {
            var row = box.closest('.applicant-row');
            if (row) row.classList.toggle('bg-indigo-50', box.checked);
            box.disabled = (count >= 4 && !box.checked);
        });

        var ok = count >= 2 && count <= 4;
        btn.disabled = !ok;
        btn.classList.toggle('cursor-not-allowed', !ok);
        btn.classList.toggle('opacity-60', !ok);

        // Highlight the Compare button when ready
        offClasses.forEach(function (c) { btn.classList.toggle(c, !ok); });
        onClasses.forEach(function (c) { btn.classList.toggle(c, ok); });

        if (count === 0) {
            hint.textContent = 'Tick 2 to 4 candidates';
        } else if (count === 1) {
            hint.textContent = '1 selected. Tick at least 1 more.';
        } else if (count < 4) {
            hint.textContent = count + ' selected. Ready to compare.';
        } else {
            hint.textContent = '4 selected (maximum)';
        }
    }

    checks.forEach(function (box) {
        box.addEventListener('change', refresh);
    });

    // Click anywhere on a row to tick or untick it
    document.querySelectorAll('.applicant-row').forEach(function (row) {
        row.addEventListener('click', function (e) {
            if (e.target.closest('a, button, input, select, label')) return;
            var box = row.querySelector('.compare-check');
            if (!box || box.disabled) return;
            box.checked = !box.checked;
            refresh();
        });
    });

    // Header checkbox: select the top 4 visible rows, or clear all
    if (selectAll) {
        selectAll.classList.add('h-4', 'w-4', 'cursor-pointer');
        selectAll.addEventListener('change', function () {
            checks.forEach(function (box) { box.checked = false; });
            if (selectAll.checked) {
                checks.filter(isVisible).slice(0, 4).forEach(function (box) {
                    box.checked = true;
                });
            }
            refresh();
        });
    }

    btn.addEventListener('click', function () {
        var ids = checks
            .filter(function (box) { return box.checked; })
            .map(function (box) { return box.value; });

        if (ids.length < 2 || ids.length > 4) return;
        window.location.href = btn.dataset.url + '?ids=' + ids.join(',');
    });

    // When filters change, the visible rows change too
    document.addEventListener('input', refresh);
    document.addEventListener('click', function (e) {
        if (e.target.closest('#clear-filters')) refresh();
    });

    refresh();
});