document.addEventListener('DOMContentLoaded', function () {
    var rows = Array.from(document.querySelectorAll('.applicant-row'));
    var minScore = document.getElementById('filter-min-score');
    var minScoreValue = document.getElementById('min-score-value');
    var statusSel = document.getElementById('filter-status');
    var missingSel = document.getElementById('filter-missing');
    var severitySel = document.getElementById('filter-severity');
    var nameInput = document.getElementById('filter-name');
    var showingText = document.getElementById('showing-text');
    var clearBtn = document.getElementById('clear-filters');

    function split(value) {
        return (value || '').split('|').filter(function (x) { return x !== ''; });
    }

    // Fill the Missing skill dropdown from the real data
    var skills = [];
    rows.forEach(function (row) {
        split(row.dataset.missing).forEach(function (s) {
            if (skills.indexOf(s) === -1) skills.push(s);
        });
    });
    skills.sort().forEach(function (s) {
        var opt = document.createElement('option');
        opt.value = s;
        opt.textContent = s;
        missingSel.appendChild(opt);
    });

    function applyFilters() {
        var min = parseInt(minScore.value, 10);
        var status = statusSel.value;
        var skill = missingSel.value;
        var severity = severitySel.value;
        var name = nameInput.value.trim().toLowerCase();
        var visible = 0;

        minScoreValue.textContent = min;

        rows.forEach(function (row) {
            var show = true;
            var missing = split(row.dataset.missing);
            var severities = split(row.dataset.severity);

            if (parseFloat(row.dataset.score) < min) show = false;
            if (status && row.dataset.status !== status) show = false;
            if (name && row.dataset.name.indexOf(name) === -1) show = false;

            if (skill && severity) {
                var i = missing.indexOf(skill);
                if (i === -1 || severities[i] !== severity) show = false;
            } else if (skill) {
                if (missing.indexOf(skill) === -1) show = false;
            } else if (severity) {
                if (severities.indexOf(severity) === -1) show = false;
            }

            row.style.display = show ? '' : 'none';
            if (show) visible++;
        });

        showingText.textContent = 'Showing ' + visible + ' of ' + rows.length + ' applicants';
    }

    [minScore, statusSel, missingSel, severitySel].forEach(function (el) {
        el.addEventListener('input', applyFilters);
    });
    nameInput.addEventListener('input', applyFilters);

    clearBtn.addEventListener('click', function () {
        minScore.value = 0;
        statusSel.value = '';
        missingSel.value = '';
        severitySel.value = '';
        nameInput.value = '';
        applyFilters();
    });

    applyFilters();
});