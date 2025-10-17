const qs = (sel)=>document.querySelector(sel);
const statusEl = qs('#status');
const labelEl = statusEl.querySelector('.label');
const detailsEl = qs('#details');

function setStatus(kind, text, details) {
  statusEl.className = `status ${kind}`;
  labelEl.textContent = text;
  detailsEl.textContent = details || '';
}

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
    setStatus(signal, label, latest ? `${base}/${target} = ${latest.toFixed(4)} | p50=${p50.toFixed(4)} p75=${p75.toFixed(4)} over ${days}d` : '');
  } catch (e) {
    setStatus('red', 'Error fetching signal', e.message);
  }
}

qs('#check').addEventListener('click', check);
