document.addEventListener('DOMContentLoaded', function () {
  var form = document.querySelector('form[enctype="multipart/form-data"]');
  if (!form) return;

  var jobSel = form.querySelector('[name="job"]');
  var nameInput = form.querySelector('[name="candidate_name"]');
  var fileInput = document.getElementById('resume-input');
  var dropZone = document.getElementById('drop-zone');
  var fileCard = document.getElementById('file-card');
  var fileName = document.getElementById('file-name');
  var fileSize = document.getElementById('file-size');
  var removeBtn = document.getElementById('file-remove');
  var errorBox = document.getElementById('file-error');
  var submitBtn = document.getElementById('analyze-btn');
  var submitText = document.getElementById('analyze-btn-text');
  var MAX_SIZE = 5 * 1024 * 1024;
  var lockHint = document.getElementById('lock-hint');

  function formatSize(bytes) {
    if (bytes < 1024 * 1024) return Math.max(1, Math.round(bytes / 1024)) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  function showError(message) {
    errorBox.textContent = message;
    errorBox.classList.remove('hidden');
  }

  function clearError() {
    errorBox.textContent = '';
    errorBox.classList.add('hidden');
  }

  function refreshButton() {
    var detailsReady = !!(jobSel.value && nameInput.value.trim());
    var hasFile = fileInput.files.length > 0;
    submitBtn.disabled = !(detailsReady && hasFile);

    var locked = !detailsReady && !hasFile;
    fileInput.disabled = locked;
    dropZone.classList.toggle('opacity-50', locked);
    dropZone.classList.toggle('cursor-not-allowed', locked);
    if (lockHint) lockHint.classList.toggle('hidden', !locked);
  }

  function showEmpty() {
    fileInput.value = '';
    fileCard.classList.add('hidden');
    fileCard.classList.remove('flex');
    dropZone.classList.remove('hidden');
    refreshButton();
  }

  function useFile(file) {
    clearError();
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      showError('Please upload a PDF file.');
      showEmpty();
      return;
    }
    if (file.size > MAX_SIZE) {
      showError('File is too large. Maximum size is 5 MB.');
      showEmpty();
      return;
    }
    fileName.textContent = file.name;
    fileSize.textContent = formatSize(file.size);
    dropZone.classList.add('hidden');
    fileCard.classList.remove('hidden');
    fileCard.classList.add('flex');
    refreshButton();
  }

  fileInput.addEventListener('change', function () {
    if (fileInput.files.length) useFile(fileInput.files[0]);
    else showEmpty();
  });

  removeBtn.addEventListener('click', function () {
    clearError();
    showEmpty();
  });

  ['dragenter', 'dragover'].forEach(function (name) {
    dropZone.addEventListener(name, function (e) {
      e.preventDefault();
      if (fileInput.disabled) return;
      dropZone.classList.add('border-indigo-500', 'bg-indigo-50');
    });
  });

  ['dragleave', 'drop'].forEach(function (name) {
    dropZone.addEventListener(name, function (e) {
      e.preventDefault();
      dropZone.classList.remove('border-indigo-500', 'bg-indigo-50');
    });
  });

  dropZone.addEventListener('drop', function (e) {
    if (fileInput.disabled) return;
    if (e.dataTransfer.files.length) {
      fileInput.files = e.dataTransfer.files;
      useFile(fileInput.files[0]);
    }
  });

  jobSel.addEventListener('change', refreshButton);
  nameInput.addEventListener('input', refreshButton);

  form.addEventListener('submit', function () {
    submitText.textContent = 'Analyzing...';
    submitBtn.classList.add('opacity-70');
  });

  refreshButton();
});