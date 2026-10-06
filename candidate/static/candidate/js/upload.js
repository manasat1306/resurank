(function () {
  var nameInput = document.getElementById('id_candidate_name');
  var emailInput = document.getElementById('id_candidate_email');
  var fileInput = document.querySelector('[data-file-input]');
  var emptyBox = document.querySelector('[data-file-empty]');
  var panel = document.querySelector('[data-file-panel]');
  var fileName = document.querySelector('[data-file-name]');
  var fileSize = document.querySelector('[data-file-size]');
  var removeBtn = document.querySelector('[data-file-remove]');
  var hint = document.querySelector('[data-upload-hint]');

  if (!fileInput || !nameInput || !emailInput) return;

  function updateLock() {
    var ready = nameInput.value.trim() !== '' && emailInput.value.trim() !== '';
    fileInput.disabled = !ready;
    emptyBox.classList.toggle('opacity-50', !ready);
    emptyBox.classList.toggle('cursor-not-allowed', !ready);
    emptyBox.classList.toggle('cursor-pointer', ready);
    if (hint) hint.classList.toggle('hidden', ready);
  }

  function showFile() {
    var file = fileInput.files[0];
    if (!file) return;
    fileName.textContent = file.name;
    fileSize.textContent = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
    emptyBox.classList.add('hidden');
    panel.classList.remove('hidden');
  }

  function removeFile() {
    fileInput.value = '';
    panel.classList.add('hidden');
    emptyBox.classList.remove('hidden');
  }

  nameInput.addEventListener('input', updateLock);
  emailInput.addEventListener('input', updateLock);
  fileInput.addEventListener('change', showFile);
  removeBtn.addEventListener('click', removeFile);

  updateLock();
})();