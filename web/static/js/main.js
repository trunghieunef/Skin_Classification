/* ============================================================
   main.js — DermAI Frontend Logic
   Drag & drop, fetch API, animated results
   ============================================================ */

'use strict';

// ── Constants ──────────────────────────────────────────────────────
const CLASS_META = {
  akiec: { name: 'Actinic Keratoses',      risk: 'medium' },
  bcc:   { name: 'Basal Cell Carcinoma',   risk: 'high'   },
  bkl:   { name: 'Benign Keratosis',       risk: 'low'    },
  df:    { name: 'Dermatofibroma',         risk: 'low'    },
  mel:   { name: 'Melanoma',               risk: 'critical'},
  nv:    { name: 'Melanocytic Nevi',       risk: 'low'    },
  vasc:  { name: 'Vascular Lesions',       risk: 'low'    },
};

const RISK_LABEL = {
  low:      '🟢 Lành tính',
  medium:   '🟡 Cần theo dõi',
  high:     '🔴 Nguy hiểm',
  critical: '🚨 Rất nguy hiểm',
};

const CLASS_ORDER = ['nv','mel','bkl','bcc','akiec','df','vasc'];

// ── DOM References ──────────────────────────────────────────────────
const dropZone      = document.getElementById('dropZone');
const fileInput     = document.getElementById('fileInput');
const browseBtn     = document.getElementById('browseBtn');
const dropContent   = document.getElementById('dropContent');
const previewContent = document.getElementById('previewContent');
const previewImg    = document.getElementById('previewImg');
const clearBtn      = document.getElementById('clearBtn');
const fileInfo      = document.getElementById('fileInfo');
const fileName      = document.getElementById('fileName');
const fileSize      = document.getElementById('fileSize');
const analyzeBtn    = document.getElementById('analyzeBtn');
const btnText       = analyzeBtn.querySelector('.btn-text');
const btnSpinner    = analyzeBtn.querySelector('.btn-spinner');
const btnArrow      = analyzeBtn.querySelector('.btn-arrow');

const placeholder    = document.getElementById('placeholder');
const loadingState   = document.getElementById('loadingState');
const resultsContent = document.getElementById('resultsContent');
const errorState     = document.getElementById('errorState');

const predClass      = document.getElementById('predClass');
const predFullname   = document.getElementById('predFullname');
const confPercent    = document.getElementById('confPercent');
const ringFill       = document.getElementById('ringFill');
const riskBadge      = document.getElementById('riskBadge');
const riskDesc       = document.getElementById('riskDesc');
const probBars       = document.getElementById('probBars');
const infoDesc       = document.getElementById('infoDesc');
const recText        = document.getElementById('recText');
const resetBtn       = document.getElementById('resetBtn');
const errorMsg       = document.getElementById('errorMsg');
const retryBtn       = document.getElementById('retryBtn');
const statusDot      = document.getElementById('statusDot');
const statusText     = document.getElementById('statusText');
const classesGrid    = document.getElementById('classesGrid');

let selectedFile = null;

// ── Health Check ────────────────────────────────────────────────────
async function checkHealth() {
  try {
    const res  = await fetch('/api/health', { signal: AbortSignal.timeout(4000) });
    const data = await res.json();
    if (data.model_loaded) {
      statusDot.className  = 'status-dot online';
      statusText.textContent = 'Model sẵn sàng';
    } else {
      statusDot.className  = 'status-dot offline';
      statusText.textContent = 'Model chưa được load';
    }
  } catch {
    statusDot.className  = 'status-dot offline';
    statusText.textContent = 'Không kết nối được server';
  }
}

// ── Class Cards Builder ─────────────────────────────────────────────
function buildClassCards() {
  Object.entries(CLASS_META).forEach(([code, meta]) => {
    const card = document.createElement('div');
    card.className = 'class-card';

    const riskColors = {
      low:      { color: '#10b981', bg: 'rgba(16,185,129,0.12)' },
      medium:   { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' },
      high:     { color: '#ef4444', bg: 'rgba(239,68,68,0.12)'  },
      critical: { color: '#ff6b6b', bg: 'rgba(220,38,38,0.15)'  },
    };
    const rc = riskColors[meta.risk];

    card.innerHTML = `
      <span class="class-code">${code.toUpperCase()}</span>
      <p class="class-name">${meta.name}</p>
      <span class="class-risk" style="color:${rc.color}; background:${rc.bg}">
        ${RISK_LABEL[meta.risk].replace(/^[^\s]+\s/, '')}
      </span>
    `;
    classesGrid.appendChild(card);
  });
}

// ── File Handling ───────────────────────────────────────────────────
function formatBytes(bytes) {
  if (bytes < 1024)       return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes/1024).toFixed(1)} KB`;
  return `${(bytes/1024/1024).toFixed(1)} MB`;
}

function showPreview(file) {
  selectedFile = file;
  const url = URL.createObjectURL(file);
  previewImg.src = url;
  dropContent.style.display  = 'none';
  previewContent.style.display = 'flex';

  fileInfo.style.display = 'flex';
  fileName.textContent   = file.name.length > 30
    ? file.name.substring(0, 27) + '…'
    : file.name;
  fileSize.textContent   = formatBytes(file.size);

  analyzeBtn.disabled = false;

  // Reset results
  showSection('placeholder');
}

function clearFile() {
  selectedFile = null;
  fileInput.value = '';
  previewImg.src  = '';
  dropContent.style.display   = 'flex';
  previewContent.style.display = 'none';
  fileInfo.style.display      = 'none';
  analyzeBtn.disabled         = true;
  showSection('placeholder');
}

function handleFile(file) {
  if (!file) return;
  const allowed = ['image/jpeg','image/png','image/bmp','image/webp'];
  if (!allowed.includes(file.type)) {
    showError('Định dạng không hỗ trợ. Hãy chọn file JPG, PNG, BMP hoặc WEBP.');
    return;
  }
  if (file.size > 16 * 1024 * 1024) {
    showError('File quá lớn. Tối đa 16 MB.');
    return;
  }
  showPreview(file);
}

// ── Event Listeners ─────────────────────────────────────────────────
browseBtn.addEventListener('click', () => fileInput.click());
clearBtn.addEventListener('click',  clearFile);
resetBtn.addEventListener('click',  clearFile);
retryBtn.addEventListener('click',  () => {
  showSection('placeholder');
  if (selectedFile) analyzeBtn.disabled = false;
});

fileInput.addEventListener('change', e => handleFile(e.target.files[0]));

// Drag & Drop
dropZone.addEventListener('dragover',  e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', e => { e.preventDefault(); dropZone.classList.remove('drag-over'); });
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  handleFile(e.dataTransfer.files[0]);
});
dropZone.addEventListener('click', e => {
  if (e.target === dropZone || e.target.closest('#dropContent')) {
    if (!selectedFile) fileInput.click();
  }
});

// ── Analyze ─────────────────────────────────────────────────────────
analyzeBtn.addEventListener('click', async () => {
  if (!selectedFile) return;

  // Button loading state
  btnText.style.display    = 'none';
  btnArrow.style.display   = 'none';
  btnSpinner.style.display = 'flex';
  analyzeBtn.disabled      = true;

  showSection('loading');

  try {
    const formData = new FormData();
    formData.append('file', selectedFile);

    const res = await fetch('/api/predict', {
      method: 'POST',
      body:   formData,
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || `Server error ${res.status}`);
    }

    displayResults(data);

  } catch (err) {
    showError(err.message || 'Không thể kết nối tới server. Hãy chắc chắn Flask đang chạy.');
  } finally {
    btnText.style.display    = 'inline';
    btnArrow.style.display   = 'block';
    btnSpinner.style.display = 'none';
    analyzeBtn.disabled      = false;
  }
});

// ── Display Results ─────────────────────────────────────────────────
function displayResults(data) {
  const { prediction, confidence, probabilities,
          description_vi, recommendation, risk_level, risk_label_vi } = data;

  // Prediction card
  predClass.textContent    = prediction.toUpperCase();
  predFullname.textContent = CLASS_META[prediction]?.name || prediction;

  // Confidence ring (circumference ≈ 201)
  const pct   = Math.round(confidence * 100);
  const offset = 201 - (201 * confidence);
  confPercent.textContent      = `${pct}%`;
  ringFill.style.strokeDashoffset = offset;

  // Color ring by confidence
  if (confidence >= 0.8)      ringFill.style.stroke = '#00d4aa';
  else if (confidence >= 0.6) ringFill.style.stroke = '#f59e0b';
  else                         ringFill.style.stroke = '#ef4444';

  // Risk badge
  const risk = risk_level || CLASS_META[prediction]?.risk || 'low';
  riskBadge.textContent  = risk_label_vi || RISK_LABEL[risk];
  riskBadge.className    = `risk-badge ${risk}`;
  riskDesc.textContent   = getRiskSubtext(risk);

  // Probability bars (sorted descending)
  probBars.innerHTML = '';
  const sorted = Object.entries(probabilities)
    .sort((a, b) => b[1] - a[1]);

  sorted.forEach(([cls, prob], i) => {
    const pctVal  = (prob * 100).toFixed(1);
    const isPred  = cls === prediction;

    const row = document.createElement('div');
    row.className = 'prob-row';
    row.innerHTML = `
      <span class="prob-name" style="${isPred ? 'color:var(--teal)' : ''}">${cls.toUpperCase()}</span>
      <div class="prob-bar-wrap">
        <div class="prob-bar-fill ${isPred ? 'predicted' : ''}" data-width="${prob * 100}"></div>
      </div>
      <span class="prob-val" style="${isPred ? 'color:var(--teal)' : 'color:var(--text-dim)'}">${pctVal}%</span>
    `;
    probBars.appendChild(row);

    // Animate bar after a tiny delay
    setTimeout(() => {
      const bar = row.querySelector('.prob-bar-fill');
      bar.style.width = `${Math.max(prob * 100, 0.5)}%`;
    }, 50 + i * 80);
  });

  // Info & recommendation
  infoDesc.textContent = description_vi || '—';
  recText.textContent  = recommendation || '—';

  showSection('results');
}

function getRiskSubtext(risk) {
  const map = {
    low:      'Không có dấu hiệu nguy hiểm rõ ràng',
    medium:   'Cần theo dõi và tham khảo bác sĩ',
    high:     'Nên khám bác sĩ da liễu sớm',
    critical: 'Cần đến bệnh viện kiểm tra ngay',
  };
  return map[risk] || '';
}

// ── Section Switcher ────────────────────────────────────────────────
function showSection(name) {
  placeholder.style.display    = name === 'placeholder' ? 'flex'  : 'none';
  loadingState.style.display   = name === 'loading'     ? 'flex'  : 'none';
  resultsContent.style.display = name === 'results'     ? 'block' : 'none';
  errorState.style.display     = name === 'error'       ? 'flex'  : 'none';
}

function showError(msg) {
  errorMsg.textContent = msg;
  showSection('error');
}

// ── Init ─────────────────────────────────────────────────────────────
checkHealth();
buildClassCards();

// Keyboard: Escape để clear
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && selectedFile) clearFile();
});

// Paste từ clipboard
document.addEventListener('paste', e => {
  const items = e.clipboardData?.items;
  if (!items) return;
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      handleFile(item.getAsFile());
      break;
    }
  }
});
