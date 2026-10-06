(function () {
  var form = document.querySelector('[data-live-search]');
  var input = document.querySelector('[data-search-input]');
  var results = document.getElementById('job-results');
  var filters = document.querySelectorAll('[data-filter]');
  if (!form || !input || !results) return;

  var timer = null;
  var latest = 0;

  function buildUrl() {
    var params = new URLSearchParams();
    new FormData(form).forEach(function (value, key) {
      value = String(value).trim();
      if (value !== '') params.append(key, value);
    });
    var qs = params.toString();
    return form.action + (qs ? '?' + qs : '');
  }

  function load() {
    var url = buildUrl();
    var id = ++latest;
    fetch(url)
      .then(function (r) { return r.text(); })
      .then(function (html) {
        if (id !== latest) return;
        var doc = new DOMParser().parseFromString(html, 'text/html');
        var fresh = doc.getElementById('job-results');
        if (fresh) results.innerHTML = fresh.innerHTML;
        history.replaceState(null, '', url);
      });
  }

  input.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(load, 300);
  });

  filters.forEach(function (el) {
    el.addEventListener('change', load);
  });

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    clearTimeout(timer);
    load();
  });
})();