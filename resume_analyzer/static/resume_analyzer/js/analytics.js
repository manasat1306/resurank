(function () {
  var dataEl = document.getElementById('analytics-data');
  if (!dataEl || typeof Chart === 'undefined') return;
  var data = JSON.parse(dataEl.textContent);

  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.color = '#64748b';

  // 1. Weekly line chart
  var weeklyEl = document.getElementById('chart-weekly');
  if (weeklyEl) {
    var ctx = weeklyEl.getContext('2d');
    var grad = ctx.createLinearGradient(0, 0, 0, 260);
    grad.addColorStop(0, 'rgba(79,70,229,0.25)');
    grad.addColorStop(1, 'rgba(79,70,229,0)');

    new Chart(weeklyEl, {
      type: 'line',
      data: {
        labels: data.weekly.map(function (w) { return w.label; }),
        datasets: [{
          label: 'Applications',
          data: data.weekly.map(function (w) { return w.count; }),
          borderColor: '#4f46e5',
          backgroundColor: grad,
          fill: true,
          tension: 0.4,
          borderWidth: 3,
          pointRadius: 5,
          pointBackgroundColor: '#ffffff',
          pointBorderColor: '#4f46e5',
          pointBorderWidth: 2,
          pointHoverRadius: 7
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: {
            beginAtZero: true,
            ticks: { precision: 0 },
            grid: { color: '#f1f5f9' }
          }
        }
      }
    });
  }

  // 2. Status donut
  var statusEl = document.getElementById('chart-status');
  if (statusEl) {
    var colors = {
      new: '#94a3b8',
      under_review: '#818cf8',
      shortlisted: '#4f46e5',
      interview: '#06b6d4',
      selected: '#10b981',
      rejected: '#ef4444'
    };
    new Chart(statusEl, {
      type: 'doughnut',
      data: {
        labels: data.status.map(function (s) { return s.label; }),
        datasets: [{
          data: data.status.map(function (s) { return s.count; }),
          backgroundColor: data.status.map(function (s) { return colors[s.key]; }),
          borderWidth: 3,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '70%',
        plugins: { legend: { display: false } }
      }
    });
  }

  // 3. Score distribution bars
  var scoreEl = document.getElementById('chart-score');
  if (scoreEl) {
    var barColors = ['#ef4444', '#ef4444', '#f59e0b', '#f59e0b', '#22c55e', '#22c55e'];

    var countLabels = {
      id: 'countLabels',
      afterDatasetsDraw: function (chart) {
        var c = chart.ctx;
        c.save();
        c.font = '600 12px Inter, sans-serif';
        c.fillStyle = '#0f172a';
        c.textAlign = 'center';
        chart.getDatasetMeta(0).data.forEach(function (bar, i) {
          c.fillText(chart.data.datasets[0].data[i], bar.x, bar.y - 6);
        });
        c.restore();
      }
    };

    new Chart(scoreEl, {
      type: 'bar',
      data: {
        labels: data.scores.map(function (b) { return b.label; }),
        datasets: [{
          data: data.scores.map(function (b) { return b.count; }),
          backgroundColor: barColors,
          borderRadius: 8,
          borderSkipped: false,
          maxBarThickness: 56
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: { padding: { top: 20 } },
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: {
            beginAtZero: true,
            ticks: { precision: 0 },
            grid: { color: '#f1f5f9' }
          }
        }
      },
      plugins: [countLabels]
    });
  }
})();