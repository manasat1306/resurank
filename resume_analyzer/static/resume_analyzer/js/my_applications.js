(function () {
  var KEY = 'resurank_applications';

  function loadList() {
    try {
      var data = JSON.parse(localStorage.getItem(KEY) || '[]');
      return Array.isArray(data) ? data : [];
    } catch (e) {
      return [];
    }
  }

  function saveList(list) {
    try {
      localStorage.setItem(KEY, JSON.stringify(list));
    } catch (e) {}
  }

  // 1. Success page: remember this application
  var saveBox = document.getElementById('save-application');
  if (saveBox) {
    var token = saveBox.dataset.token;
    var title = saveBox.dataset.title;
    var list = loadList().filter(function (item) {
      return item.token !== token;
    });
    list.unshift({ token: token, title: title, date: new Date().toISOString() });
    saveList(list);
  }

  // 2. Track page: fill the dropdown
  var select = document.getElementById('my-applications');
  var codeInput = document.getElementById('code-input');
  var wrapper = document.getElementById('my-applications-box');
  if (select && codeInput && wrapper) {
    var saved = loadList();
    if (saved.length > 0) {
      saved.forEach(function (item) {
        var option = document.createElement('option');
        option.value = item.token;
        var d = new Date(item.date);
        option.textContent = item.title + ' (applied ' + d.toLocaleDateString() + ')';
        select.appendChild(option);
      });
      wrapper.classList.remove('hidden');
      select.addEventListener('change', function () {
        codeInput.value = select.value;
      });
    }
  }
})();