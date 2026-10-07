document.addEventListener('DOMContentLoaded', function () {
  var modal = document.getElementById('skill-modal');
  if (!modal) return;

  var title = document.getElementById('skill-modal-title');
  var note = document.getElementById('skill-modal-note');
  var evidenceBox = document.getElementById('skill-modal-evidence-box');
  var evidenceText = document.getElementById('skill-modal-evidence');
  var closeBtn = document.getElementById('skill-modal-close');

  function openModal(chip) {
    var skill = chip.dataset.skill;
    var severity = chip.dataset.severity;
    var text = chip.dataset.note;

    title.textContent = skill + ' — Missing skill';

    if (text && text.trim() !== '') {
      note.textContent = text;
    } else {
      note.textContent = skill + ' is listed as a required skill for this job (' +
        severity + ' gap). It was not clearly found in the resume text.';
    }

    var evidence = chip.dataset.evidence;
    if (evidence && evidence.trim() !== '') {
      evidenceText.textContent = '"' + evidence + '"';
      evidenceBox.classList.remove('hidden');
    } else {
      evidenceBox.classList.add('hidden');
    }
    modal.classList.remove('hidden');
    modal.classList.add('flex');
  }

  function closeModal() {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }

  document.querySelectorAll('.skill-chip').forEach(function (chip) {
    chip.addEventListener('click', function () {
      openModal(chip);
    });
  });

  closeBtn.addEventListener('click', closeModal);

  modal.addEventListener('click', function (e) {
    if (e.target === modal) closeModal();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeModal();
  });
});