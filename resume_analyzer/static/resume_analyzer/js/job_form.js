// weight slider
const sw = document.getElementById('sw');
function updateWeights() {
  document.getElementById('sw-label').textContent = sw.value + '%';
  document.getElementById('sim-label').textContent = (100 - sw.value) + '%';
}
sw.addEventListener('input', updateWeights);
updateWeights();

// skill chips
function setupChips(boxId, hiddenId, chipClass) {
  const box = document.getElementById(boxId);
  const hidden = document.getElementById(hiddenId);
  const input = box.querySelector('input');
  let skills = hidden.value ? hidden.value.split(',').map(s => s.trim()).filter(Boolean) : [];

  function render() {
    box.querySelectorAll('.chip').forEach(c => c.remove());
    skills.forEach((s, i) => {
      const chip = document.createElement('span');
      chip.className = 'chip text-xs px-2 py-1 rounded-full flex items-center gap-1 ' + chipClass;
      chip.textContent = s;
      const x = document.createElement('button');
      x.type = 'button';
      x.textContent = '×';
      x.onclick = () => { skills.splice(i, 1); render(); };
      chip.appendChild(x);
      box.insertBefore(chip, input);
    });
    hidden.value = skills.join(',');
  }

  function add(value) {
    const v = value.trim();
    if (v && !skills.some(s => s.toLowerCase() === v.toLowerCase())) skills.push(v);
    input.value = '';
    render();
  }

  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ',') { e.preventDefault(); add(input.value); }
    else if (e.key === 'Backspace' && !input.value && skills.length) { skills.pop(); render(); }
  });
  input.addEventListener('blur', () => add(input.value));
  box.addEventListener('click', () => input.focus());
  render();
}

setupChips('req-box', 'req-hidden', 'bg-indigo-50 text-indigo-700');
setupChips('pref-box', 'pref-hidden', 'bg-purple-50 text-purple-700');