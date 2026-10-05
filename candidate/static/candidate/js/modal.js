(function () {
  function openModal(id) {
    var modal = document.getElementById(id);
    if (!modal) return;
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.body.classList.add('overflow-hidden');
  }

  function closeAll() {
    document.querySelectorAll('.modal').forEach(function (m) {
      m.classList.add('hidden');
      m.classList.remove('flex');
    });
    document.body.classList.remove('overflow-hidden');
  }

  document.addEventListener('click', function (e) {
    var opener = e.target.closest('[data-modal-open]');
    if (opener) {
      e.preventDefault();
      openModal(opener.dataset.modalOpen);
      return;
    }
    if (e.target.closest('[data-modal-close]')) closeAll();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeAll();
  });
})();