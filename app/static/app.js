const qs = (sel)=>document.querySelector(sel);
const statusEl = qs('#status');
const labelEl = statusEl.querySelector('.label');
const detailsEl = qs('#details');

function setStatus(kind, text, details) {
  statusEl.className = `status ${kind}`;
  labelEl.textContent = text;
  detailsEl.textContent = details || '';
}

const FLAGS = {
  USD: '🇺🇸', EUR: '🇪🇺', GBP: '🇬🇧', JPY: '🇯🇵', AUD: '🇦🇺',
  CAD: '🇨🇦', CHF: '🇨🇭', CNY: '🇨🇳', SEK: '🇸🇪', NZD: '🇳🇿', BRL: '🇧🇷'
};

function initCustomSelect(forId){
  const select = qs(`#${forId}`);
  const root = document.querySelector(`.custom-select[data-for="${forId}"]`);
  if (!select || !root) return;
  const button = root.querySelector('.custom-select__button');
  const list = root.querySelector('.custom-select__list');
  // Initialize from select's current value
  const setButton = (val)=>{
    const li = list.querySelector(`.custom-select__option[data-value="${val}"]`);
    if (!li) return;
    const img = li.querySelector('img').cloneNode(true);
    const code = li.querySelector('.code').textContent;
    button.innerHTML = '';
    button.appendChild(img);
    const span = document.createElement('span');
    span.className = 'code';
    span.textContent = code;
    button.appendChild(span);
  };
  setButton(select.value);
  // Toggle open
  button.addEventListener('click', ()=>{
    const isOpen = root.classList.contains('open');
    document.querySelectorAll('.custom-select.open').forEach(el=>el.classList.remove('open'));
    root.classList.toggle('open', !isOpen);
    button.setAttribute('aria-expanded', String(!isOpen));
  });
  // Option click
  list.addEventListener('click', (e)=>{
    const li = e.target.closest('.custom-select__option');
    if (!li) return;
    const val = li.getAttribute('data-value');
    select.value = val;
    setButton(val);
    root.classList.remove('open');
    button.setAttribute('aria-expanded', 'false');
  });
  // Close on outside click
  document.addEventListener('click', (e)=>{
    if (!root.contains(e.target)){
      root.classList.remove('open');
      button.setAttribute('aria-expanded', 'false');
    }
  });
}

document.addEventListener('DOMContentLoaded', ()=>{
  initCustomSelect('base');
  initCustomSelect('target');
});

async function check() {
  const base = qs('#base').value;
  const target = qs('#target').value;
  if (base === target) {
    setStatus('red', 'Pick different currencies');
    return;
  }
  setStatus('neutral', 'Checking...');
  try {
    const res = await fetch(`/api/signal?base=${encodeURIComponent(base)}&target=${encodeURIComponent(target)}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Request failed');
    const { signal, label, latest, p50, p75, days } = data;
    const baseLabel = `${FLAGS[base] ?? ''} ${base}`.trim();
    const targetLabel = `${FLAGS[target] ?? ''} ${target}`.trim();
    setStatus(
      signal,
      label,
      latest ? `${baseLabel}/${targetLabel} = ${latest.toFixed(4)} | p50=${p50.toFixed(4)} p75=${p75.toFixed(4)} over ${days}d` : ''
    );
  } catch (e) {
    setStatus('red', 'Error fetching signal', e.message);
  }
}

qs('#check').addEventListener('click', check);
