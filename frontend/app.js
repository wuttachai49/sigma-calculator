/* Sigma Metric Calculator — frontend logic */

const API = '';  // same origin when served by FastAPI

// ── Tabs ──────────────────────────────────────────────────────────────────────
document.querySelectorAll('.tab').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(s => {
      s.classList.remove('active');
      s.classList.add('hidden');
    });
    btn.classList.add('active');
    const target = document.getElementById('tab-' + btn.dataset.tab);
    target.classList.remove('hidden');
    target.classList.add('active');
  });
});

// ── Analyte Database (loaded once) ────────────────────────────────────────────
let allAnalytes = [];

async function loadAnalytes() {
  try {
    const res = await fetch(`${API}/api/analytes`);
    const data = await res.json();
    allAnalytes = data.analytes;
  } catch (_) { /* backend not running — demo mode */ }
}
loadAnalytes();

// ── Calculator ────────────────────────────────────────────────────────────────
const deptSelect    = document.getElementById('dept-select');
const analyteInput  = document.getElementById('analyte-input');
const dropdown      = document.getElementById('analyte-dropdown');
const teaInput      = document.getElementById('tea-input');
const biasInput     = document.getElementById('bias-input');
const cvInput       = document.getElementById('cv-input');
const teaSourceInput= document.getElementById('tea-source-input');
const teaSourceBadge= document.getElementById('tea-source-badge');
const calcBtn       = document.getElementById('calc-btn');
const resultCard    = document.getElementById('result-card');
const resultContent = document.getElementById('result-content');
const resultPlaceholder = document.getElementById('result-placeholder');
const historyCard   = document.getElementById('history-card');
const historyTbody  = document.getElementById('history-tbody');
const clearHistory  = document.getElementById('clear-history');

let sessionHistory  = [];

// Filter dropdown based on dept + text
function updateDropdown() {
  const dept  = deptSelect.value;
  const query = analyteInput.value.trim().toLowerCase();
  const filtered = allAnalytes.filter(a =>
    (!dept || a.department === dept) &&
    (!query || a.name.toLowerCase().includes(query))
  ).slice(0, 30);

  if (filtered.length === 0 || !query) {
    dropdown.classList.add('hidden');
    return;
  }
  dropdown.innerHTML = filtered.map(a => `
    <div class="dropdown-item" data-name="${a.name}" data-tea="${a.tea}" data-source="${a.source}" data-dept="${a.department}">
      <span>${a.name}</span>
      <span class="item-tea">TEa ${a.tea}% · ${a.source}</span>
    </div>
  `).join('');
  dropdown.classList.remove('hidden');
}

analyteInput.addEventListener('input', updateDropdown);
deptSelect.addEventListener('change', updateDropdown);

dropdown.addEventListener('click', e => {
  const item = e.target.closest('.dropdown-item');
  if (!item) return;
  analyteInput.value  = item.dataset.name;
  teaInput.value      = item.dataset.tea;
  teaSourceInput.value= item.dataset.source;
  teaSourceBadge.textContent = item.dataset.source;
  teaSourceBadge.classList.remove('hidden');
  if (!deptSelect.value) deptSelect.value = item.dataset.dept;
  dropdown.classList.add('hidden');
});

document.addEventListener('click', e => {
  if (!e.target.closest('.analyte-input-wrap')) dropdown.classList.add('hidden');
});

teaInput.addEventListener('input', () => {
  teaSourceBadge.classList.add('hidden');
  teaSourceBadge.textContent = '';
});

// Calculate
calcBtn.addEventListener('click', async () => {
  const analyte = analyteInput.value.trim();
  const dept    = deptSelect.value;
  const tea     = parseFloat(teaInput.value);
  const bias    = parseFloat(biasInput.value);
  const cv      = parseFloat(cvInput.value);
  const src     = teaSourceInput.value.trim();

  if (!analyte || !dept || isNaN(tea) || isNaN(bias) || isNaN(cv)) {
    alert('Please fill in all required fields (Department, Analyte, TEa, Bias, CV).');
    return;
  }

  calcBtn.textContent = 'Calculating…';
  calcBtn.disabled = true;

  try {
    const res = await fetch(`${API}/api/calculate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ analyte, department: dept, tea, bias_pct: bias, cv_pct: cv, tea_source: src }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Server error');
    }
    const data = await res.json();
    displayResult(data);
    addToHistory(data);
  } catch (err) {
    alert('Error: ' + err.message);
  } finally {
    calcBtn.textContent = 'Calculate Sigma';
    calcBtn.disabled = false;
  }
});

function displayResult(d) {
  resultPlaceholder.classList.add('hidden');
  resultContent.classList.remove('hidden');

  // ── Trio: Sigma / QGI / Grade ──────────────────────────────────────────
  const sigmaEl = document.getElementById('res-sigma');
  sigmaEl.textContent = d.sigma;
  sigmaEl.style.color = d.grade_color;

  const qgiValEl = document.getElementById('res-qgi-value');
  qgiValEl.textContent = d.qgi;
  qgiValEl.style.color = d.qgi_color;

  const gradeEl = document.getElementById('res-grade');
  gradeEl.textContent = d.grade;
  gradeEl.style.color = d.grade_color;

  // ── Summary table ─────────────────────────────────────────────────────
  document.getElementById('res-analyte').textContent = d.analyte;
  document.getElementById('res-dept').textContent    = d.department;
  document.getElementById('res-tea').textContent     = d.tea + '%';
  document.getElementById('res-bias').textContent    = d.bias_pct + '%';
  document.getElementById('res-cv').textContent      = d.cv_pct + '%';
  document.getElementById('res-source').textContent  = d.tea_source || '—';

  // ── QC Rules ──────────────────────────────────────────────────────────
  document.getElementById('res-rules').innerHTML =
    d.qc_rules.map(r => `<span class="qc-rule-pill">${r.rule}</span>`).join('');

  // ── Show detailed section ─────────────────────────────────────────────
  document.getElementById('detail-results').classList.remove('hidden');

  // ── QGI Gauge ─────────────────────────────────────────────────────────
  const MAX_QGI = Math.max(d.qgi * 1.25, 2.0);  // dynamic scale — always shows needle with headroom
  const pct = Math.min(d.qgi / MAX_QGI, 1) * 100;
  document.getElementById('qgi-fill').style.width      = pct + '%';
  document.getElementById('qgi-fill').style.background = d.qgi_color;
  document.getElementById('qgi-needle').style.left     = pct + '%';
  document.getElementById('qgi-current-chip').textContent = `▶ QGI = ${d.qgi}`;
  document.getElementById('qgi-current-chip').style.color       = d.qgi_color;
  document.getElementById('qgi-current-chip').style.borderColor = d.qgi_color + '88';
  document.getElementById('qgi-current-chip').style.background  = d.qgi_color + '22';

  // ── QGI Interpretation card ───────────────────────────────────────────
  const interpCard = document.getElementById('qgi-interp-card');
  interpCard.className = 'card qgi-interp-card ' + _qgiZoneClass(d.qgi_label);
  document.getElementById('qgi-interp-title').textContent = `▸ ${d.analyte} — ${d.qgi_label}`;
  document.getElementById('qgi-interp-title').style.color = d.qgi_color;
  document.getElementById('res-qgi-action').textContent   = d.qgi_action;

  // ── Error Breakdown table ─────────────────────────────────────────────
  const tea  = d.tea;
  const bias = Math.abs(d.bias_pct);
  const cv   = d.cv_pct;
  const re   = parseFloat((1.65 * cv).toFixed(3));
  const te   = parseFloat((bias + re).toFixed(3));
  const biasPctTea = ((bias / tea) * 100).toFixed(1);
  const rePctTea   = ((re   / tea) * 100).toFixed(1);
  const tePctTea   = ((te   / tea) * 100).toFixed(1);

  const statusIcon = (v, good, warn) =>
    v <= good ? `<span style="color:#10b981">✓ Acceptable</span>` :
    v <= warn ? `<span style="color:#f59e0b">⚠ Borderline</span>` :
                `<span style="color:#ef4444">✗ Exceeds limit</span>`;

  document.getElementById('breakdown-tbody').innerHTML = `
    <tr>
      <td>TEa (allowable)</td>
      <td style="color:var(--accent-h);font-weight:700">${tea}%</td>
      <td style="font-weight:700">100.0%</td>
      <td style="color:#93c5fd">Reference</td>
    </tr>
    <tr>
      <td>|Bias%|</td>
      <td style="color:${bias/tea<.33?'#10b981':bias/tea<.5?'#f59e0b':'#ef4444'};font-weight:700">${bias}%</td>
      <td>${biasPctTea}%</td>
      <td>${statusIcon(+biasPctTea, 33, 50)}</td>
    </tr>
    <tr>
      <td>1.65 × CV (Random Error)</td>
      <td style="color:${+rePctTea<50?'#10b981':+rePctTea<75?'#f59e0b':'#ef4444'};font-weight:700">${re}%</td>
      <td>${rePctTea}%</td>
      <td>${statusIcon(+rePctTea, 50, 75)}</td>
    </tr>
    <tr style="background:var(--surface2)">
      <td style="font-weight:600">Total Error (Bias + 1.65×CV)</td>
      <td style="color:${+tePctTea<=100?'#10b981':'#ef4444'};font-weight:700">${te}%</td>
      <td style="font-weight:700">${tePctTea}%</td>
      <td>${+tePctTea<=100?'<span style="color:#10b981">✓ Within TEa</span>':'<span style="color:#ef4444">✗ Exceeds TEa</span>'}</td>
    </tr>
    <tr>
      <td>Sigma (σ)</td>
      <td style="color:${d.grade_color};font-weight:700">${d.sigma}</td>
      <td>—</td>
      <td style="color:${d.grade_color};font-weight:600">${d.grade}</td>
    </tr>
    <tr>
      <td>QGI</td>
      <td style="color:${d.sigma>=6?'#ffffff':d.qgi_color};font-weight:700">${d.qgi}</td>
      <td>—</td>
      <td style="color:${d.sigma>=6?'#ffffff':d.qgi_color};font-weight:600">${d.sigma>=6?'✓ World Class — QC minimal':''+d.qgi_label}</td>
    </tr>
  `;

  // ── QC Strategy ───────────────────────────────────────────────────────
  document.getElementById('qc-strategy-text').innerHTML = _qcStrategy(d.sigma, d.qgi_label, d.qc_rules);
}

function _qgiZoneClass(label) {
  if (label === 'Precision-limited') return 'zone-precision';
  if (label === 'Mixed')             return 'zone-balanced';
  if (label === 'Accuracy-limited')  {
    return 'zone-moderate'; // backend only has 3 zones; severe shown via color
  }
  return '';
}

function _qcStrategy(sigma, qgiLabel, rules) {
  let freq, n, note;
  if (sigma >= 6) {
    freq = '1 run / shift (or less)'; n = 'N = 2';
    note = 'World-class performance. Minimal QC burden. Consider risk-based QC reduction per CLSI EP23.';
  } else if (sigma >= 5) {
    freq = '1–2 runs / day'; n = 'N = 2';
    note = 'Excellent performance. Standard QC sufficient. Expand SQC boundaries if desired.';
  } else if (sigma >= 4) {
    freq = '2 runs / day'; n = 'N = 2–3';
    note = 'Good performance. Westgard multirule balances false rejection and error detection.';
  } else if (sigma >= 3) {
    freq = '3–4 runs / day (before each analytical run)'; n = 'N = 3';
    note = 'Marginal performance. Increased QC frequency and tighter rules required. ' +
           (qgiLabel === 'Precision-limited'
             ? 'QGI indicates CV is the priority — investigate reagent lot, pipetting, instrument maintenance.'
             : 'QGI indicates Bias is the priority — recalibrate, verify calibrator traceability, check EQA z-scores.');
  } else {
    freq = 'Continuous — suspend patient results until resolved'; n = 'N ≥ 4';
    note = 'CRITICAL: Performance does not meet quality goals. Results must not be reported. Immediate investigation required.';
  }

  const rulePills = rules.map(r => `<span class="qc-strategy-chip">${r.rule}</span>`).join('');
  return `
    <div class="qc-strategy-row">${rulePills}</div>
    <div class="qc-strategy-row">
      <span class="qc-strategy-chip">🕐 ${freq}</span>
      <span class="qc-strategy-chip">🔬 ${n} per level</span>
    </div>
    <div class="qc-strategy-note">${note}</div>
  `;
}

// Jump to OPSpecs from result
document.getElementById('opspecs-from-calc').addEventListener('click', () => {
  const tea  = parseFloat(teaInput.value);
  const cv   = parseFloat(cvInput.value);
  const bias = parseFloat(biasInput.value);
  if (!isNaN(tea))  document.getElementById('ops-tea').value  = tea;
  if (!isNaN(cv))   document.getElementById('ops-cv').value   = cv;
  if (!isNaN(bias)) document.getElementById('ops-bias').value = Math.abs(bias);
  document.querySelector('[data-tab="opspecs"]').click();
  plotOPSpecs();
});

// History
function addToHistory(d) {
  sessionHistory.push(d);
  historyCard.style.display = 'block';
  reportFab.classList.remove('hidden');
  const tr = document.createElement('tr');
  tr.innerHTML = `
    <td>${d.analyte}</td>
    <td>${d.department}</td>
    <td>${d.tea}</td>
    <td>${d.bias_pct}</td>
    <td>${d.cv_pct}</td>
    <td style="font-weight:700;color:${d.grade_color}">${d.sigma}</td>
    <td><span class="grade-pill" style="background:${d.grade_color}">${d.grade}</span></td>
    <td style="font-weight:700;color:${d.qgi_color}">${d.qgi}</td>
    <td><span class="grade-pill" style="background:${d.qgi_color}">${d.qgi_label}</span></td>
    <td>${d.qc_rules.map(r => `<span class="qc-rule-pill">${r.rule}</span>`).join(' ')}</td>
  `;
  historyTbody.prepend(tr);
}

clearHistory.addEventListener('click', () => {
  sessionHistory = [];
  historyTbody.innerHTML = '';
  historyCard.style.display = 'none';
});

// ── Batch Import ──────────────────────────────────────────────────────────────
const uploadArea  = document.getElementById('upload-area');
const fileInput   = document.getElementById('file-input');
const fileChip    = document.getElementById('batch-filename');
const batchBtn    = document.getElementById('batch-run-btn');
const batchError  = document.getElementById('batch-error');
const batchResults= document.getElementById('batch-results');
const batchTbody  = document.getElementById('batch-tbody');
const batchSummary= document.getElementById('batch-summary');

let batchFile = null;

uploadArea.addEventListener('click', () => fileInput.click());
uploadArea.addEventListener('dragover', e => { e.preventDefault(); uploadArea.classList.add('dragover'); });
uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
uploadArea.addEventListener('drop', e => {
  e.preventDefault();
  uploadArea.classList.remove('dragover');
  if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) handleFile(fileInput.files[0]);
});

function handleFile(f) {
  batchFile = f;
  fileChip.textContent = `📄 ${f.name}`;
  fileChip.classList.remove('hidden');
  batchBtn.disabled = false;
  batchError.classList.add('hidden');
  batchResults.classList.add('hidden');
}

batchBtn.addEventListener('click', async () => {
  if (!batchFile) return;
  batchBtn.textContent = 'Processing…';
  batchBtn.disabled = true;
  batchError.classList.add('hidden');

  const formData = new FormData();
  formData.append('file', batchFile);

  try {
    const res = await fetch(`${API}/api/batch`, { method: 'POST', body: formData });
    const data = await res.json();
    if (!res.ok) {
      batchError.textContent = data.detail || 'Upload failed.';
      batchError.classList.remove('hidden');
      return;
    }
    renderBatchResults(data);
  } catch (err) {
    batchError.textContent = 'Error: ' + err.message;
    batchError.classList.remove('hidden');
  } finally {
    batchBtn.textContent = 'Run Batch Calculation';
    batchBtn.disabled = false;
  }
});

function renderBatchResults(data) {
  batchTbody.innerHTML = '';
  data.results.forEach(d => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${d.analyte}</td>
      <td>${d.department}</td>
      <td>${d.tea}</td>
      <td>${d.bias_pct}</td>
      <td>${d.cv_pct}</td>
      <td style="font-weight:700;color:${d.grade_color}">${d.sigma}</td>
      <td><span class="grade-pill" style="background:${d.grade_color}">${d.grade}</span></td>
      <td style="font-weight:700;color:${d.qgi_color}">${d.qgi}</td>
      <td><span class="grade-pill" style="background:${d.qgi_color}">${d.qgi_label}</span></td>
      <td>${d.qc_rules.map(r => `<span class="qc-rule-pill">${r.rule}</span>`).join(' ')}</td>
    `;
    batchTbody.appendChild(tr);
  });

  const errCount = data.errors.length;
  batchSummary.innerHTML = `
    <div class="summary-chip"><span>Total processed:</span>${data.total}</div>
    ${errCount > 0 ? `<div class="summary-chip" style="border-color:rgba(239,68,68,.4);color:#fca5a5"><span>Errors:</span>${errCount}</div>` : ''}
  `;

  // store batch results for report generation
  batchReportData = data.results;
  if (data.results.length > 0) reportFab.classList.remove('hidden');

  batchResults.classList.remove('hidden');
  if (errCount > 0) {
    batchError.textContent = data.errors.map(e => `Row ${e.row}: ${e.error}`).join('\n');
    batchError.classList.remove('hidden');
  }
}

// Export CSV
document.getElementById('export-csv').addEventListener('click', () => {
  const rows = [['Analyte','Department','TEa%','Bias%','CV%','Sigma','Grade','QGI','QGI Label','QC Rules']];
  document.querySelectorAll('#batch-tbody tr').forEach(tr => {
    const cells = [...tr.querySelectorAll('td')];
    rows.push([
      cells[0].textContent.trim(),
      cells[1].textContent.trim(),
      cells[2].textContent.trim(),
      cells[3].textContent.trim(),
      cells[4].textContent.trim(),
      cells[5].textContent.trim(),
      cells[6].textContent.trim(),
      cells[7].textContent.trim(),
      cells[8].textContent.trim(),
      cells[9].textContent.trim(),
    ]);
  });
  const csv = rows.map(r => r.map(v => `"${v}"`).join(',')).join('\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
  a.download = 'sigma_results.csv';
  a.click();
});

// ── OPSpecs Chart ─────────────────────────────────────────────────────────────
document.getElementById('ops-plot-btn').addEventListener('click', plotOPSpecs);

async function plotOPSpecs() {
  const tea  = parseFloat(document.getElementById('ops-tea').value);
  const cvM  = parseFloat(document.getElementById('ops-cv').value);
  const biasM= parseFloat(document.getElementById('ops-bias').value);

  if (isNaN(tea) || tea <= 0) { alert('Please enter a valid TEa value.'); return; }

  try {
    const res  = await fetch(`${API}/api/opspecs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tea, cv_min: 0.3, cv_max: Math.max(tea / 1.5, 15) }),
    });
    const data = await res.json();
    renderOPSpecs(data, isNaN(cvM) ? null : cvM, isNaN(biasM) ? null : Math.abs(biasM));
  } catch (err) {
    alert('OPSpecs error: ' + err.message);
  }
}

function renderOPSpecs(data, methodCV, methodBias) {
  const traces = data.lines.map(line => ({
    x: line.cv,
    y: line.bias,
    mode: 'lines',
    name: line.label,
    line: { color: line.color, width: 2.5 },
    hovertemplate: `σ=${line.sigma}<br>CV: %{x:.2f}%<br>Max Bias: %{y:.2f}%<extra></extra>`,
  }));

  // Shade region below σ=6 line (acceptable zone) — subtle
  if (data.lines[0]) {
    const top = data.lines[0];
    traces.unshift({
      x: [...top.cv, ...top.cv.slice().reverse()],
      y: [...top.bias, new Array(top.bias.length).fill(0)],
      fill: 'toself',
      fillcolor: 'rgba(16,185,129,0.06)',
      line: { width: 0 },
      name: 'σ ≥ 6 zone',
      showlegend: false,
      hoverinfo: 'skip',
    });
  }

  // Method point
  if (methodCV !== null && methodBias !== null) {
    const sigma = (data.tea - methodBias) / methodCV;
    const color = sigmaColor(sigma);
    traces.push({
      x: [methodCV],
      y: [methodBias],
      mode: 'markers+text',
      name: 'Your method',
      marker: { color, size: 14, symbol: 'diamond', line: { color: '#fff', width: 2 } },
      text: [`σ = ${sigma.toFixed(2)}`],
      textposition: 'top right',
      textfont: { color, size: 13, family: 'Inter, sans-serif' },
      hovertemplate: `CV: ${methodCV}%<br>Bias: ${methodBias}%<br>σ = ${sigma.toFixed(2)}<extra></extra>`,
    });
  }

  const layout = {
    paper_bgcolor: '#1a1d27',
    plot_bgcolor:  '#0f1117',
    font: { color: '#e2e8f0', family: 'Inter, sans-serif', size: 12 },
    xaxis: {
      title: 'CV — Imprecision (%)',
      gridcolor: '#2e3248',
      zerolinecolor: '#2e3248',
      tickfont: { color: '#7c85a2' },
    },
    yaxis: {
      title: 'Bias — Inaccuracy (%)',
      gridcolor: '#2e3248',
      zerolinecolor: '#2e3248',
      tickfont: { color: '#7c85a2' },
      rangemode: 'tozero',
    },
    legend: {
      bgcolor: '#22263a',
      bordercolor: '#2e3248',
      borderwidth: 1,
      font: { color: '#e2e8f0', size: 12 },
    },
    margin: { t: 40, r: 20, b: 60, l: 60 },
    title: {
      text: `OPSpecs Chart — TEa = ${data.tea}%`,
      font: { size: 14, color: '#e2e8f0' },
      x: 0.05,
    },
    hovermode: 'closest',
    annotations: [
      {
        x: 0.5, y: 1.04,
        xref: 'paper', yref: 'paper',
        text: 'Plot your method point (CV, Bias) to see which σ region it occupies',
        showarrow: false,
        font: { size: 11, color: '#7c85a2' },
      }
    ],
  };

  Plotly.newPlot('opspecs-chart', traces, layout, { responsive: true, displayModeBar: false });
}

function sigmaColor(sigma) {
  if (sigma >= 6) return '#10b981';
  if (sigma >= 5) return '#3b82f6';
  if (sigma >= 4) return '#f59e0b';
  if (sigma >= 3) return '#f97316';
  return '#ef4444';
}

// ── Guide — Download Template ─────────────────────────────────────────────────
document.getElementById('download-template').addEventListener('click', () => {
  const csv = `analyte,department,tea,bias_pct,cv_pct,tea_source
Glucose,Clinical Chemistry,10,1.5,2.0,CLIA
Hemoglobin,Hematology,7,0.8,1.5,CLIA
TSH,Clinical Immunology,20,3.0,5.0,BV
Platelets,Hematology,25,2.0,4.5,CLIA
Total Cholesterol,Clinical Chemistry,10,1.0,2.5,NCEP
Ferritin,Clinical Immunology,20,5.0,7.0,BV`;
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
  a.download = 'sigma_template.csv';
  a.click();
});

// ── Auto-plot OPSpecs when tab opened with no chart ───────────────────────────
document.querySelector('[data-tab="opspecs"]').addEventListener('click', () => {
  const chart = document.getElementById('opspecs-chart');
  if (!chart.children.length) {
    plotOPSpecs();
  }
});

// ── Report ────────────────────────────────────────────────────────────────────
const reportFab   = document.getElementById('report-fab');
const reportModal = document.getElementById('report-modal');
let batchReportData = [];

reportFab.addEventListener('click', () => reportModal.classList.remove('hidden'));
document.getElementById('modal-close').addEventListener('click', () => reportModal.classList.add('hidden'));
reportModal.addEventListener('click', e => { if (e.target === reportModal) reportModal.classList.add('hidden'); });

function reportMeta() {
  return {
    lab:        document.getElementById('rpt-lab').value.trim(),
    analyzer:   document.getElementById('rpt-analyzer').value.trim(),
    department: document.getElementById('rpt-dept').value.trim(),
    period:     document.getElementById('rpt-period').value.trim(),
  };
}

function activeResults() {
  // Prefer batch results if on batch tab and they exist; otherwise session history
  const onBatch = document.getElementById('tab-batch').classList.contains('active');
  return (onBatch && batchReportData.length) ? batchReportData : sessionHistory;
}

async function downloadReport(format) {
  const results = activeResults();
  if (!results.length) {
    alert('No results to report. Run a calculation or batch import first.');
    return;
  }
  const rptError = document.getElementById('rpt-error');
  rptError.classList.add('hidden');

  const btn = format === 'pdf'
    ? document.getElementById('rpt-pdf-btn')
    : document.getElementById('rpt-excel-btn');
  const orig = btn.innerHTML;
  btn.innerHTML = `<span class="rpt-icon">⏳</span> Generating…`;
  btn.disabled = true;

  try {
    const res = await fetch(`${API}/api/report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ results, format, ...reportMeta() }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Server error');
    }
    const blob = await res.blob();
    const ext  = format === 'pdf' ? 'pdf' : 'xlsx';
    const a    = document.createElement('a');
    a.href     = URL.createObjectURL(blob);
    a.download = `sigma_report.${ext}`;
    a.click();
    reportModal.classList.add('hidden');
  } catch (err) {
    rptError.textContent = 'Error: ' + err.message;
    rptError.classList.remove('hidden');
  } finally {
    btn.innerHTML = orig;
    btn.disabled  = false;
  }
}

document.getElementById('rpt-excel-btn').addEventListener('click', () => downloadReport('excel'));
document.getElementById('rpt-pdf-btn').addEventListener('click',   () => downloadReport('pdf'));

// ── References ────────────────────────────────────────────────────────────────
const refCards      = document.getElementById('ref-cards');
const refSearch     = document.getElementById('ref-search');
const refCatFilter  = document.getElementById('ref-cat-filter');
const refTbody      = document.getElementById('analyte-ref-tbody');

let allReferences = [];
let allAnalytesFull = [];

const CAT_COLORS = {
  "Regulatory":               { bg: "rgba(239,68,68,.12)",    color: "#fca5a5",  border: "rgba(239,68,68,.3)"   },
  "Biological Variation":     { bg: "rgba(16,185,129,.12)",   color: "#6ee7b7",  border: "rgba(16,185,129,.3)"  },
  "Clinical Guidelines":      { bg: "rgba(99,102,241,.12)",   color: "#a5b4fc",  border: "rgba(99,102,241,.3)"  },
  "Standardization Program":  { bg: "rgba(245,158,11,.12)",   color: "#fcd34d",  border: "rgba(245,158,11,.3)"  },
  "EQA / Proficiency Testing":{ bg: "rgba(59,130,246,.12)",   color: "#93c5fd",  border: "rgba(59,130,246,.3)"  },
};

async function loadReferences() {
  try {
    const [refRes, analRes] = await Promise.all([
      fetch(`${API}/api/references`),
      fetch(`${API}/api/analytes`),
    ]);
    const refData   = await refRes.json();
    const analData  = await analRes.json();
    allReferences   = refData.references;
    allAnalytesFull = analData.analytes;

    // Populate category filter
    refData.categories.forEach(cat => {
      const opt = document.createElement('option');
      opt.value = cat; opt.textContent = cat;
      refCatFilter.appendChild(opt);
    });

    renderRefCards();
    renderAnalyteRefTable('');
  } catch (_) {}
}

function renderRefCards() {
  const query = refSearch.value.trim().toLowerCase();
  const cat   = refCatFilter.value;
  const filtered = allReferences.filter(r =>
    (!cat || r.category === cat) &&
    (!query || r.key.toLowerCase().includes(query)
            || r.full_name.toLowerCase().includes(query)
            || r.organization.toLowerCase().includes(query)
            || r.description.toLowerCase().includes(query))
  );

  if (!filtered.length) {
    refCards.innerHTML = '<p class="muted" style="padding:.5rem">No sources match your search.</p>';
    return;
  }

  refCards.innerHTML = filtered.map(r => {
    const c = CAT_COLORS[r.category] || { bg: 'var(--surface2)', color: 'var(--muted)', border: 'var(--border)' };
    return `
    <div class="ref-card">
      <div class="ref-card-top">
        <span class="ref-key">${r.key}</span>
        <span class="ref-cat-pill" style="background:${c.bg};color:${c.color};border:1px solid ${c.border}">${r.category}</span>
      </div>
      <div class="ref-full-name">${r.full_name}</div>
      <div class="ref-org">${r.organization}</div>
      <div class="ref-desc">${r.description}</div>
      <div class="ref-meta">
        <span class="ref-meta-chip">📄 ${r.document}</span>
        <span class="ref-meta-chip">📅 ${r.year}</span>
      </div>
      <a class="ref-link" href="${r.url}" target="_blank" rel="noopener noreferrer">${r.url}</a>
    </div>`;
  }).join('');
}

function renderAnalyteRefTable(dept) {
  const filtered = allAnalytesFull.filter(a => !dept || a.department === dept);
  refTbody.innerHTML = filtered.map(a => {
    const ref = allReferences.find(r => r.key === a.source) || allReferences.find(r => r.key.startsWith(a.source));
    const c   = CAT_COLORS[ref?.category] || { bg: 'var(--surface2)', color: 'var(--muted)', border: 'var(--border)' };
    const link = ref
      ? `<a href="${ref.url}" target="_blank" rel="noopener noreferrer" class="ref-link" style="border:none;padding:0">${ref.full_name}</a>`
      : `<span class="muted">${a.source}</span>`;
    return `
      <tr>
        <td style="font-weight:600">${a.name}</td>
        <td>${a.department}</td>
        <td style="font-weight:700;color:var(--accent-h)">${a.tea}%</td>
        <td><span class="ref-key" style="font-size:.7rem">${a.source}</span></td>
        <td>${link}</td>
      </tr>`;
  }).join('');
}

refSearch.addEventListener('input', renderRefCards);
refCatFilter.addEventListener('change', renderRefCards);

document.querySelectorAll('.ref-dept-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.ref-dept-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    renderAnalyteRefTable(btn.dataset.dept);
  });
});

// Load when tab is first opened
document.querySelector('[data-tab="references"]').addEventListener('click', () => {
  if (!allReferences.length) loadReferences();
});
