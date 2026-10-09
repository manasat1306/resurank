(function () {
  var root = document.documentElement;
  var buttons = document.querySelectorAll('[data-theme-choice]');

  function currentTheme() {
    return root.classList.contains('dark') ? 'dark' : 'light';
  }

  function paint() {
    var active = currentTheme();
    buttons.forEach(function (btn) {
      var on = btn.getAttribute('data-theme-choice') === active;
      btn.classList.toggle('ring-2', on);
      btn.classList.toggle('ring-indigo-500', on);
    });
  }

  buttons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var choice = btn.getAttribute('data-theme-choice');
      if (choice === 'dark') {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
      try { localStorage.setItem('theme', choice); } catch (e) {}
      paint();
    });
  });

  paint();
})();