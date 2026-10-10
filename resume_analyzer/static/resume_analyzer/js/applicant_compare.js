document.addEventListener('DOMContentLoaded', function () {
    var btn = document.getElementById('compare-btn');
    var hint = document.getElementById('compare-hint');
    var selectAll = document.getElementById('compare-select-all');
    var checks = Array.from(document.querySelectorAll('.compare-check'));

    if (!btn || checks.length === 0) return;

    // Maximum comes from the server (Free = 4, Pro = 100 which means unlimited)
    var MAX = parseInt(btn.dataset.max, 10) || 4;
    var UNLIMITED = MAX >= 100;

    // True when the user tried to go over the Free limit
    var limitHit = false;

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

    function countChecked() {
        return checks.filter(function (box) { return box.checked; }).length;
    }

    function showUpgradeToast() {
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
        // Untick rows hidden by the filters
        checks.forEach(function (box) {
            if (!isVisible(box)) box.checked = false;
        });

        var count = countChecked();

        // Highlight selected rows (boxes stay clickable so we can show the upgrade popup)
        checks.forEach(function (box) {
            var row = box.closest('.applicant-row');
            if (row) row.classList.toggle('bg-indigo-50', box.checked);
        });

        var ok = count >= 2 && count <= MAX;
        btn.disabled = !ok;
        btn.classList.toggle('cursor-not-allowed', !ok);
        btn.classList.toggle('opacity-60', !ok);

        // Highlight the Compare button when ready
        offClasses.forEach(function (c) { btn.classList.toggle(c, !ok); });
        onClasses.forEach(function (c) { btn.classList.toggle(c, ok); });

        if (limitHit && !UNLIMITED) {
            hint.style.color = '#d97706';
            hint.innerHTML = 'Free plan allows up to ' + MAX + ' candidates. ' +
                '<a href="/plans/checkout/" class="font-semibold underline">Upgrade to Pro</a> to compare more.';
            return;
        }

        hint.style.color = '';
        if (count === 0) {
            hint.textContent = UNLIMITED ? 'Tick 2 or more candidates' : 'Tick 2 to ' + MAX + ' candidates';
        } else if (count === 1) {
            hint.textContent = '1 selected. Tick at least 1 more.';
        } else if (UNLIMITED || count < MAX) {
            hint.textContent = count + ' selected. Ready to compare.';
        } else {
            hint.textContent = count + ' selected (maximum on your plan)';
        }
    }

    // Called after a box is ticked or unticked
    function handleChange(box) {
        if (box.checked && countChecked() > MAX) {
            box.checked = false;
            limitHit = true;
            showUpgradeToast();
        } else {
            limitHit = false;
        }
        refresh();
    }

    checks.forEach(function (box) {
        box.addEventListener('change', function () { handleChange(box); });
    });

    // Click anywhere on a row to tick or untick it
    document.querySelectorAll('.applicant-row').forEach(function (row) {
        row.addEventListener('click', function (e) {
            if (e.target.closest('a, button, input, select, label')) return;
            var box = row.querySelector('.compare-check');
            if (!box || box.disabled) return;
            box.checked = !box.checked;
            handleChange(box);
        });
    });

    // Header checkbox: select the top visible rows (up to the maximum), or clear all
    if (selectAll) {
        selectAll.classList.add('h-4', 'w-4', 'cursor-pointer');
        selectAll.addEventListener('change', function () {
            checks.forEach(function (box) { box.checked = false; });
            limitHit = false;
            if (selectAll.checked) {
                var visible = checks.filter(isVisible);
                visible.slice(0, MAX).forEach(function (box) {
                    box.checked = true;
                });
                if (!UNLIMITED && visible.length > MAX) {
                    limitHit = true;
                    showUpgradeToast();
                }
            }
            refresh();
        });
    }

    btn.addEventListener('click', function () {
        var ids = checks
            .filter(function (box) { return box.checked; })
            .map(function (box) { return box.value; });

        if (ids.length < 2 || ids.length > MAX) return;
        window.location.href = btn.dataset.url + '?ids=' + ids.join(',');
    });

    // When filters change, the visible rows change too
    document.addEventListener('input', refresh);
    document.addEventListener('click', function (e) {
        if (e.target.closest('#clear-filters')) {
            limitHit = false;
            refresh();
        }
    });

    refresh();
});