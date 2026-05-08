# DermAI UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the Flask frontend into a clean medical-style guided workflow with light mode by default, dark mode support, and clearer upload, review, and results states.

**Architecture:** Keep the backend API unchanged and concentrate all redesign work in the existing frontend trio: `index.html`, `style.css`, and `main.js`. Add one lightweight `unittest` regression file so the new markup hooks, theme contract, and JS state helpers have automated coverage without introducing new tooling.

**Tech Stack:** Flask, server-rendered HTML, vanilla CSS, vanilla JavaScript, Python `unittest`

---

## File Structure

### Files to Modify

- `web/templates/index.html`
  Responsibility: replace the current split dark layout with the new guided page shell, theme toggle, step indicators, upload/review card, results card, class reference section, and trust section while preserving the DOM hooks needed by the frontend logic.
- `web/static/css/style.css`
  Responsibility: replace the dark glassmorphism theme with a token-driven light-first design system, dark theme overrides, responsive guided-flow layout, accessible focus styles, and calmer motion.
- `web/static/js/main.js`
  Responsibility: preserve API integration and file handling while adding theme persistence, step-state management, inline workflow errors, and updated DOM rendering for the redesigned page.

### Files to Create

- `tests/test_web_ui.py`
  Responsibility: lightweight regression coverage for homepage structure plus source-level CSS and JS contract checks.

## Implementation Notes

- Keep `/api/health` and `/api/predict` unchanged.
- Reuse the existing IDs where it reduces JS churn, but prefer a cleaner DOM over preserving every current wrapper.
- Do not add a frontend framework or build tooling.
- Keep the class reference grid populated from `CLASS_META`; only the markup and styling should change.
- Light mode must be the initial `body[data-theme="light"]` state.

### Task 1: Add Regression Coverage for the New Frontend Contract

**Files:**
- Create: `tests/test_web_ui.py`

- [ ] **Step 1: Write the failing regression tests**

```python
import unittest
from pathlib import Path

from web.app import app


REPO_ROOT = Path(__file__).resolve().parents[1]


class HomePageUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.testing = True
        cls.client = app.test_client()

    def test_homepage_contains_guided_flow_shell(self):
        response = self.client.get("/")
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        for snippet in (
            'data-theme="light"',
            'id="themeToggle"',
            'id="stepUpload"',
            'id="stepReview"',
            'id="stepResults"',
            'id="reviewPanel"',
            'id="resultsPanel"',
            'id="trustSection"',
            'id="classesGrid"',
        ):
            self.assertIn(snippet, html)

    def test_stylesheet_defines_theme_and_accessibility_hooks(self):
        css = (REPO_ROOT / "web" / "static" / "css" / "style.css").read_text(encoding="utf-8")

        for snippet in (
            '[data-theme="dark"]',
            ".theme-toggle",
            ".flow-step.is-active",
            ".inline-error",
            ":focus-visible",
            "@media (prefers-reduced-motion: reduce)",
        ):
            self.assertIn(snippet, css)

    def test_script_defines_theme_and_flow_helpers(self):
        js = (REPO_ROOT / "web" / "static" / "js" / "main.js").read_text(encoding="utf-8")

        for snippet in (
            "const THEME_KEY = 'dermai-theme';",
            "function applyTheme(theme)",
            "function setFlowState(state)",
            "function showInlineError(message)",
            "themeToggle.addEventListener('click'",
            "localStorage.setItem(THEME_KEY, theme);",
        ):
            self.assertIn(snippet, js)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```powershell
python -m unittest tests.test_web_ui -v
```

Expected:

```text
FAIL: test_homepage_contains_guided_flow_shell
AssertionError: 'id="themeToggle"' not found in ...
```

- [ ] **Step 3: Commit the failing test scaffold**

```powershell
git add tests/test_web_ui.py
git commit -m "test: add ui contract regression"
```

### Task 2: Rebuild `index.html` Around the Guided 3-Step Flow

**Files:**
- Modify: `web/templates/index.html`
- Test: `tests/test_web_ui.py`

- [ ] **Step 1: Keep the homepage regression test failing against the current template**

Run:

```powershell
python -m unittest tests.test_web_ui.HomePageUiTest.test_homepage_contains_guided_flow_shell -v
```

Expected:

```text
FAIL: test_homepage_contains_guided_flow_shell
AssertionError: 'id="themeToggle"' not found in ...
```

- [ ] **Step 2: Replace the template body with the new page shell and DOM hooks**

Replace the `<head>` font import and the `<body>` content in `web/templates/index.html` with this structure:

```html
<link
  href="https://fonts.googleapis.com/css2?family=Fraunces:wght@600;700&family=Manrope:wght@400;500;600;700;800&display=swap"
  rel="stylesheet"
/>
```

```html
<body data-theme="light">
  <header class="topbar">
    <div class="topbar-inner">
      <div class="brand-block">
        <div class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"/>
          </svg>
        </div>
        <div>
          <p class="brand-kicker">DermAI</p>
          <h1 class="brand-name">Skin lesion screening assistant</h1>
        </div>
      </div>

      <div class="topbar-actions">
        <div class="status-pill" aria-live="polite">
          <span class="status-dot" id="statusDot"></span>
          <span id="statusText" class="status-label">Dang ket noi...</span>
        </div>

        <button
          class="theme-toggle"
          id="themeToggle"
          type="button"
          aria-label="Chuyen giao dien"
          aria-pressed="false"
        >
          <span class="theme-toggle__sun">Light</span>
          <span class="theme-toggle__moon">Dark</span>
        </button>
      </div>
    </div>
  </header>

  <main class="page-shell">
    <section class="hero">
      <div class="hero-copy">
        <p class="hero-eyebrow">EfficientNet-B3 · HAM10000</p>
        <h2 class="hero-title">Phan tich ton thuong da theo quy trinh ro rang va de hieu.</h2>
        <p class="hero-subtitle">
          Tai anh, kiem tra lai truoc khi chay mo hinh, sau do xem ket qua du doan,
          muc do rui ro va khuyen nghi tiep theo trong mot giao dien gon gang.
        </p>
      </div>
    </section>

    <section class="analyzer-shell" id="analyzerShell">
      <div class="flow-steps" aria-label="Cac buoc phan tich">
        <article class="flow-step is-active" id="stepUpload">
          <span class="flow-step__number">01</span>
          <div>
            <p class="flow-step__label">Upload</p>
            <p class="flow-step__copy">Chon anh dermoscopy hoac keo tha vao khung.</p>
          </div>
        </article>
        <article class="flow-step" id="stepReview">
          <span class="flow-step__number">02</span>
          <div>
            <p class="flow-step__label">Review</p>
            <p class="flow-step__copy">Kiem tra lai anh va thong tin file truoc khi phan tich.</p>
          </div>
        </article>
        <article class="flow-step" id="stepResults">
          <span class="flow-step__number">03</span>
          <div>
            <p class="flow-step__label">Results</p>
            <p class="flow-step__copy">Doc chan doan, do tin cay va khuyen nghi tiep theo.</p>
          </div>
        </article>
      </div>

      <div class="tool-grid">
        <section class="flow-card review-card" id="reviewPanel" data-state="empty">
          <div class="section-heading">
            <p class="section-kicker">Step 1 · Upload and review</p>
            <h3>Tai anh va xac nhan truoc khi mo hinh chay</h3>
          </div>

          <input type="file" id="fileInput" accept="image/*" hidden />
          <div class="inline-error" id="inlineError" hidden></div>

          <div class="drop-zone" id="dropZone">
            <div class="drop-content" id="dropContent">
              <div class="drop-icon" aria-hidden="true">
                <svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="4" y="4" width="56" height="56" rx="10" />
                  <path d="M20 42l8-8 8 6 8-10 8 12" />
                  <circle cx="24" cy="22" r="4" />
                </svg>
              </div>
              <p class="drop-title">Keo tha anh vao day</p>
              <p class="drop-copy">Anh ro net, can ton thuong nam giua khung hinh se cho ket qua de doc hon.</p>
              <div class="drop-actions">
                <button class="btn btn-primary" id="browseBtn" type="button">Chon anh</button>
                <p class="drop-hint">PNG, JPG, JPEG, BMP, WEBP · toi da 16 MB</p>
              </div>
            </div>

            <div class="preview-shell" id="previewContent" hidden>
              <img id="previewImg" src="" alt="Anh da chon" />
            </div>
          </div>

          <div class="file-meta" id="fileInfo" hidden>
            <div>
              <p class="meta-label">Tep duoc chon</p>
              <p class="meta-value" id="fileName">-</p>
            </div>
            <span class="file-size-badge" id="fileSize">-</span>
          </div>

          <div class="review-actions">
            <button class="btn btn-secondary" id="replaceBtn" type="button">Thay anh</button>
            <button class="btn btn-ghost" id="clearBtn" type="button">Xoa anh</button>
            <button class="btn btn-primary btn-analyze" id="analyzeBtn" type="button" disabled>
              <span class="btn-text" id="analyzeBtnLabel">Phan tich anh</span>
              <span class="btn-spinner" id="analyzeBtnSpinner" hidden></span>
            </button>
          </div>
        </section>

        <section class="flow-card results-card" id="resultsPanel">
          <div class="section-heading">
            <p class="section-kicker">Step 2 · Analysis output</p>
            <h3>Ket qua du doan va dinh huong tiep theo</h3>
          </div>

          <div class="placeholder" id="placeholder">
            <p class="placeholder-title">Chua co ket qua</p>
            <p class="placeholder-sub">Sau khi tai anh va bam "Phan tich anh", ket qua se hien thi tai day.</p>
          </div>

          <div class="loading-state" id="loadingState" hidden>
            <div class="loading-badge">Analyzing lesion image</div>
            <p class="loading-text">Mo hinh dang uoc luong xac suat cho 7 nhom ton thuong.</p>
          </div>

          <div class="results-content" id="resultsContent" hidden>
            <div class="prediction-card">
              <div>
                <p class="prediction-label">Chan doan chinh</p>
                <h4 class="prediction-class" id="predClass">-</h4>
                <p class="prediction-fullname" id="predFullname">-</p>
              </div>

              <div class="confidence-ring-wrap">
                <svg class="confidence-ring" viewBox="0 0 80 80">
                  <circle cx="40" cy="40" r="32" class="ring-bg"></circle>
                  <circle cx="40" cy="40" r="32" class="ring-fill" id="ringFill"></circle>
                </svg>
                <div class="ring-label">
                  <span id="confPercent">0%</span>
                  <small>Do tin cay</small>
                </div>
              </div>
            </div>

            <div class="risk-row">
              <span class="risk-badge" id="riskBadge">-</span>
              <span class="risk-description" id="riskDesc">-</span>
            </div>

            <div class="info-card">
              <h5 class="section-title">Thong tin va khuyen nghi</h5>
              <p class="info-desc" id="infoDesc">-</p>
              <div class="recommendation-box">
                <p id="recText">-</p>
              </div>
            </div>

            <div class="prob-section">
              <h5 class="section-title">Xac suat tung loai</h5>
              <div class="prob-bars" id="probBars"></div>
            </div>

            <button class="btn btn-secondary btn-reset" id="resetBtn" type="button">
              Phan tich anh khac
            </button>
          </div>
        </section>
      </div>
    </section>

    <section class="trust-section" id="trustSection">
      <div class="trust-card">
        <p class="trust-kicker">For research and learning use only</p>
        <h3>Ket qua AI chi co gia tri tham khao.</h3>
        <p>
          Ung dung nay khong thay the cho danh gia cua bac si da lieu. Neu ton thuong
          thay doi nhanh, gay dau, chay mau hoac co dau hieu bat thuong, hay di kham som.
        </p>
      </div>
    </section>

    <section class="classes-section">
      <div class="section-heading section-heading--center">
        <p class="section-kicker">Reference</p>
        <h3>7 nhom ton thuong duoc phan loai</h3>
      </div>
      <div class="classes-grid" id="classesGrid"></div>
    </section>
  </main>

  <footer class="footer">
    <p>DermAI · EfficientNet-B3 · HAM10000 · Research demo only</p>
  </footer>

  <script src="/static/js/main.js"></script>
</body>
```

- [ ] **Step 3: Run the homepage structure test again**

Run:

```powershell
python -m unittest tests.test_web_ui.HomePageUiTest.test_homepage_contains_guided_flow_shell -v
```

Expected:

```text
ok
```

- [ ] **Step 4: Commit the structural template rewrite**

```powershell
git add web/templates/index.html tests/test_web_ui.py
git commit -m "feat: add guided ui layout"
```

### Task 3: Replace the Stylesheet with a Light-First Theme System

**Files:**
- Modify: `web/static/css/style.css`
- Test: `tests/test_web_ui.py`

- [ ] **Step 1: Keep the CSS contract test failing before the rewrite**

Run:

```powershell
python -m unittest tests.test_web_ui.HomePageUiTest.test_stylesheet_defines_theme_and_accessibility_hooks -v
```

Expected:

```text
FAIL: test_stylesheet_defines_theme_and_accessibility_hooks
AssertionError: '[data-theme="dark"]' not found in ...
```

- [ ] **Step 2: Replace the stylesheet with the new theme tokens, layout, and accessibility rules**

Replace `web/static/css/style.css` with these sections:

```css
:root {
  --page-bg: #f3f7f6;
  --page-surface: #ffffff;
  --page-surface-muted: #eef4f2;
  --page-border: #d7e4df;
  --page-border-strong: #b8cbc3;
  --text-strong: #17313b;
  --text-muted: #56717b;
  --text-soft: #7e96a0;
  --accent: #1d8f7a;
  --accent-strong: #0f7667;
  --accent-soft: #d9f0ea;
  --info: #3f6db3;
  --danger: #c65757;
  --danger-soft: #fde7e7;
  --warning: #b9852d;
  --shadow-soft: 0 18px 40px rgba(20, 53, 66, 0.08);
  --shadow-card: 0 12px 24px rgba(20, 53, 66, 0.06);
  --radius-lg: 28px;
  --radius-md: 18px;
  --radius-sm: 12px;
  --focus-ring: rgba(29, 143, 122, 0.32);
  --font-ui: "Manrope", "Segoe UI", sans-serif;
  --font-display: "Fraunces", Georgia, serif;
}

[data-theme="dark"] {
  --page-bg: #0f1a20;
  --page-surface: #16252d;
  --page-surface-muted: #1b2f38;
  --page-border: #29414d;
  --page-border-strong: #3a5664;
  --text-strong: #ecf5f4;
  --text-muted: #b8c9c8;
  --text-soft: #8ea3aa;
  --accent: #6ec7b2;
  --accent-strong: #8dddc9;
  --accent-soft: rgba(110, 199, 178, 0.14);
  --info: #8cb1ff;
  --danger: #f08a8a;
  --danger-soft: rgba(240, 138, 138, 0.14);
  --warning: #efc978;
  --shadow-soft: 0 18px 40px rgba(0, 0, 0, 0.28);
  --shadow-card: 0 12px 24px rgba(0, 0, 0, 0.22);
  --focus-ring: rgba(141, 221, 201, 0.28);
}

*,
*::before,
*::after {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(63, 109, 179, 0.08), transparent 28%),
    radial-gradient(circle at top right, rgba(29, 143, 122, 0.1), transparent 32%),
    var(--page-bg);
  color: var(--text-strong);
  font: 500 15px/1.6 var(--font-ui);
}

img {
  display: block;
  max-width: 100%;
}

button,
input {
  font: inherit;
}

:focus-visible {
  outline: 3px solid var(--focus-ring);
  outline-offset: 3px;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  backdrop-filter: blur(18px);
  background: color-mix(in srgb, var(--page-bg) 84%, transparent);
  border-bottom: 1px solid var(--page-border);
}

.topbar-inner,
.page-shell,
.footer {
  width: min(1180px, calc(100% - 32px));
  margin: 0 auto;
}

.topbar-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 18px 0;
}

.brand-block,
.topbar-actions,
.status-pill,
.flow-step,
.review-actions,
.risk-row {
  display: flex;
  align-items: center;
}

.brand-block {
  gap: 14px;
}

.brand-mark {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  background: linear-gradient(135deg, var(--accent-soft), color-mix(in srgb, var(--page-surface) 86%, var(--accent)));
  color: var(--accent-strong);
  box-shadow: var(--shadow-card);
}

.brand-kicker,
.section-kicker,
.hero-eyebrow,
.prediction-label,
.meta-label,
.trust-kicker {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 12px;
  color: var(--text-soft);
}

.brand-name,
.hero-title,
.section-heading h3,
.trust-card h3 {
  margin: 0;
  font-family: var(--font-display);
  line-height: 1.1;
}

.brand-name {
  font-size: clamp(18px, 2vw, 24px);
}

.topbar-actions {
  gap: 12px;
}

.status-pill,
.theme-toggle,
.flow-step,
.file-meta,
.trust-card,
.class-card,
.info-card,
.prediction-card,
.prob-section,
.flow-card {
  border: 1px solid var(--page-border);
  background: var(--page-surface);
  box-shadow: var(--shadow-card);
}

.status-pill {
  gap: 10px;
  padding: 10px 14px;
  border-radius: 999px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: var(--text-soft);
}

.status-dot.online {
  background: var(--accent);
}

.status-dot.offline {
  background: var(--danger);
}

.theme-toggle {
  display: inline-flex;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 999px;
  color: var(--text-muted);
  cursor: pointer;
}

.theme-toggle__sun,
.theme-toggle__moon {
  padding: 6px 10px;
  border-radius: 999px;
}

body[data-theme="light"] .theme-toggle__sun,
body[data-theme="dark"] .theme-toggle__moon {
  background: var(--accent-soft);
  color: var(--accent-strong);
}

.page-shell {
  padding: 40px 0 72px;
}

.hero {
  margin-bottom: 28px;
  padding: 28px 32px;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, color-mix(in srgb, var(--page-surface) 84%, var(--accent-soft)), var(--page-surface));
  border: 1px solid var(--page-border);
  box-shadow: var(--shadow-soft);
}

.hero-copy {
  max-width: 760px;
}

.hero-title {
  font-size: clamp(36px, 5vw, 56px);
  margin: 10px 0 12px;
}

.hero-subtitle {
  max-width: 620px;
  margin: 0;
  color: var(--text-muted);
  font-size: 17px;
}

.analyzer-shell {
  display: grid;
  gap: 20px;
}

.flow-steps {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.flow-step {
  gap: 14px;
  padding: 18px 20px;
  border-radius: var(--radius-md);
}

.flow-step__number {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  background: var(--page-surface-muted);
  color: var(--text-muted);
  font-weight: 800;
}

.flow-step.is-active {
  border-color: var(--page-border-strong);
  background: linear-gradient(135deg, var(--page-surface), var(--accent-soft));
}

.flow-step.is-active .flow-step__number,
.flow-step.is-complete .flow-step__number {
  background: var(--accent);
  color: #ffffff;
}

.flow-step__label {
  margin: 0 0 2px;
  font-weight: 800;
}

.flow-step__copy {
  margin: 0;
  color: var(--text-muted);
  font-size: 13px;
}

.tool-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
  gap: 20px;
}

.flow-card {
  border-radius: var(--radius-lg);
  padding: 24px;
}

.section-heading {
  margin-bottom: 20px;
}

.section-heading h3 {
  font-size: clamp(24px, 3vw, 32px);
}

.section-heading--center {
  text-align: center;
}

.inline-error {
  margin-bottom: 16px;
  padding: 14px 16px;
  border-radius: var(--radius-sm);
  border: 1px solid color-mix(in srgb, var(--danger) 32%, var(--page-border));
  background: var(--danger-soft);
  color: color-mix(in srgb, var(--danger) 82%, var(--text-strong));
}

.drop-zone {
  min-height: 320px;
  display: grid;
  place-items: center;
  border: 1.5px dashed var(--page-border-strong);
  border-radius: var(--radius-md);
  background: linear-gradient(180deg, var(--page-surface), var(--page-surface-muted));
  transition: border-color 160ms ease, transform 160ms ease, background 160ms ease;
}

.drop-zone.drag-over {
  border-color: var(--accent-strong);
  transform: translateY(-2px);
  background: linear-gradient(180deg, var(--page-surface), var(--accent-soft));
}

.drop-content,
.loading-state,
.placeholder {
  text-align: center;
}

.drop-content {
  width: min(100%, 420px);
}

.drop-icon {
  width: 72px;
  height: 72px;
  margin: 0 auto 16px;
  color: var(--accent-strong);
}

.drop-title {
  margin: 0 0 8px;
  font-size: 22px;
  font-weight: 800;
}

.drop-copy,
.placeholder-sub,
.loading-text,
.info-desc,
.risk-description,
.class-name,
.footer p {
  color: var(--text-muted);
}

.drop-actions {
  display: grid;
  gap: 12px;
  justify-items: center;
}

.drop-hint {
  margin: 0;
  font-size: 13px;
  color: var(--text-soft);
}

.preview-shell {
  width: 100%;
}

.preview-shell img {
  width: 100%;
  aspect-ratio: 4 / 3;
  object-fit: cover;
  border-radius: calc(var(--radius-md) - 2px);
}

.file-meta {
  justify-content: space-between;
  gap: 12px;
  margin-top: 16px;
  padding: 16px 18px;
  border-radius: var(--radius-md);
}

.meta-value,
.placeholder-title {
  margin: 4px 0 0;
  font-size: 18px;
  font-weight: 800;
}

.file-size-badge {
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--page-surface-muted);
  color: var(--text-muted);
  font-weight: 700;
}

.review-actions {
  gap: 12px;
  margin-top: 18px;
  flex-wrap: wrap;
}

.btn {
  border: 1px solid transparent;
  border-radius: 999px;
  padding: 12px 18px;
  font-weight: 800;
  cursor: pointer;
  transition: transform 160ms ease, background 160ms ease, border-color 160ms ease, color 160ms ease;
}

.btn:hover {
  transform: translateY(-1px);
}

.btn-primary {
  background: var(--accent);
  color: #ffffff;
}

.btn-primary:hover {
  background: var(--accent-strong);
}

.btn-secondary {
  background: var(--page-surface);
  border-color: var(--page-border-strong);
  color: var(--text-strong);
}

.btn-ghost {
  background: transparent;
  border-color: var(--page-border);
  color: var(--text-muted);
}

.btn-analyze {
  margin-left: auto;
}

.btn-analyze:disabled {
  opacity: 0.52;
  cursor: not-allowed;
  transform: none;
}

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: #ffffff;
  border-radius: 999px;
  animation: spin 900ms linear infinite;
}

.results-card {
  min-height: 540px;
}

.placeholder,
.loading-state {
  min-height: 280px;
  display: grid;
  place-content: center;
  gap: 12px;
}

.loading-badge {
  display: inline-flex;
  justify-content: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent-strong);
  font-weight: 800;
}

.results-content {
  display: grid;
  gap: 16px;
}

.prediction-card {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  padding: 22px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--page-surface), var(--accent-soft));
}

.prediction-class {
  margin: 8px 0 4px;
  font-size: clamp(30px, 5vw, 42px);
  color: var(--text-strong);
}

.prediction-fullname {
  margin: 0;
  color: var(--text-muted);
}

.confidence-ring-wrap {
  position: relative;
  width: 88px;
  height: 88px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.confidence-ring {
  width: 88px;
  height: 88px;
  transform: rotate(-90deg);
}

.ring-bg {
  fill: none;
  stroke: color-mix(in srgb, var(--page-border) 72%, transparent);
  stroke-width: 7;
}

.ring-fill {
  fill: none;
  stroke: var(--accent);
  stroke-width: 7;
  stroke-linecap: round;
  stroke-dasharray: 201;
  stroke-dashoffset: 201;
  transition: stroke-dashoffset 500ms ease, stroke 220ms ease;
}

.ring-label {
  position: absolute;
  inset: 0;
  display: grid;
  place-content: center;
  text-align: center;
}

.ring-label span {
  font-size: 17px;
  font-weight: 800;
}

.ring-label small {
  color: var(--text-soft);
}

.risk-row {
  gap: 12px;
  flex-wrap: wrap;
}

.risk-badge {
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
}

.risk-badge.low {
  background: color-mix(in srgb, var(--accent) 16%, var(--page-surface));
  color: var(--accent-strong);
}

.risk-badge.medium {
  background: color-mix(in srgb, var(--warning) 18%, var(--page-surface));
  color: #8c6219;
}

.risk-badge.high,
.risk-badge.critical {
  background: var(--danger-soft);
  color: var(--danger);
}

.info-card,
.prob-section,
.trust-card,
.class-card {
  border-radius: var(--radius-md);
  padding: 20px;
}

.section-title {
  margin: 0 0 10px;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-soft);
}

.recommendation-box {
  padding: 14px 16px;
  border-radius: var(--radius-sm);
  background: var(--page-surface-muted);
  color: var(--text-strong);
}

.prob-bars {
  display: grid;
  gap: 10px;
}

.prob-row {
  display: grid;
  grid-template-columns: 56px minmax(0, 1fr) 52px;
  gap: 10px;
  align-items: center;
}

.prob-name,
.prob-val {
  font-size: 12px;
  font-weight: 800;
}

.prob-bar-wrap {
  height: 10px;
  border-radius: 999px;
  overflow: hidden;
  background: var(--page-surface-muted);
}

.prob-bar-fill {
  width: 0;
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--info), var(--accent));
  transition: width 420ms ease;
}

.prob-bar-fill.predicted {
  background: linear-gradient(90deg, var(--accent), var(--accent-strong));
}

.btn-reset {
  justify-self: start;
}

.trust-section,
.classes-section {
  margin-top: 28px;
}

.classes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
  margin-top: 18px;
}

.class-card {
  min-height: 152px;
}

.class-code {
  display: inline-block;
  margin-bottom: 8px;
  color: var(--accent-strong);
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.class-name {
  margin: 0;
}

.class-risk {
  display: inline-flex;
  margin-top: 12px;
  padding: 5px 10px;
  border-radius: 999px;
  background: var(--page-surface-muted);
  font-size: 12px;
  font-weight: 800;
}

.footer {
  padding: 0 0 32px;
}

.footer p {
  margin: 0;
  text-align: center;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 860px) {
  .topbar-inner,
  .topbar-actions,
  .tool-grid,
  .flow-steps,
  .prediction-card {
    grid-template-columns: 1fr;
    flex-direction: column;
  }

  .topbar-actions,
  .review-actions {
    align-items: stretch;
  }

  .btn-analyze {
    margin-left: 0;
  }

  .flow-card,
  .hero {
    padding: 20px;
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
  }
}
```

- [ ] **Step 3: Run the CSS contract test again**

Run:

```powershell
python -m unittest tests.test_web_ui.HomePageUiTest.test_stylesheet_defines_theme_and_accessibility_hooks -v
```

Expected:

```text
ok
```

- [ ] **Step 4: Commit the stylesheet rewrite**

```powershell
git add web/static/css/style.css tests/test_web_ui.py
git commit -m "feat: add clinical theme system"
```

### Task 4: Refactor `main.js` for Theme Persistence and Guided State Transitions

**Files:**
- Modify: `web/static/js/main.js`
- Test: `tests/test_web_ui.py`

- [ ] **Step 1: Keep the JS contract test failing before the refactor**

Run:

```powershell
python -m unittest tests.test_web_ui.HomePageUiTest.test_script_defines_theme_and_flow_helpers -v
```

Expected:

```text
FAIL: test_script_defines_theme_and_flow_helpers
AssertionError: "const THEME_KEY = 'dermai-theme';" not found in ...
```

- [ ] **Step 2: Rewrite the frontend script around theme and flow helpers**

Replace `web/static/js/main.js` with this implementation:

```javascript
'use strict';

const THEME_KEY = 'dermai-theme';
const CLASS_META = {
  akiec: { name: 'Actinic Keratoses', risk: 'medium' },
  bcc: { name: 'Basal Cell Carcinoma', risk: 'high' },
  bkl: { name: 'Benign Keratosis', risk: 'low' },
  df: { name: 'Dermatofibroma', risk: 'low' },
  mel: { name: 'Melanoma', risk: 'critical' },
  nv: { name: 'Melanocytic Nevi', risk: 'low' },
  vasc: { name: 'Vascular Lesions', risk: 'low' },
};

const RISK_LABEL = {
  low: 'Lanh tinh',
  medium: 'Can theo doi',
  high: 'Nguy hiem',
  critical: 'Rui ro cao',
};

const themeToggle = document.getElementById('themeToggle');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const stepUpload = document.getElementById('stepUpload');
const stepReview = document.getElementById('stepReview');
const stepResults = document.getElementById('stepResults');
const reviewPanel = document.getElementById('reviewPanel');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const replaceBtn = document.getElementById('replaceBtn');
const clearBtn = document.getElementById('clearBtn');
const analyzeBtn = document.getElementById('analyzeBtn');
const analyzeBtnLabel = document.getElementById('analyzeBtnLabel');
const analyzeBtnSpinner = document.getElementById('analyzeBtnSpinner');
const dropZone = document.getElementById('dropZone');
const dropContent = document.getElementById('dropContent');
const previewContent = document.getElementById('previewContent');
const previewImg = document.getElementById('previewImg');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const inlineError = document.getElementById('inlineError');
const placeholder = document.getElementById('placeholder');
const loadingState = document.getElementById('loadingState');
const resultsContent = document.getElementById('resultsContent');
const predClass = document.getElementById('predClass');
const predFullname = document.getElementById('predFullname');
const confPercent = document.getElementById('confPercent');
const ringFill = document.getElementById('ringFill');
const riskBadge = document.getElementById('riskBadge');
const riskDesc = document.getElementById('riskDesc');
const infoDesc = document.getElementById('infoDesc');
const recText = document.getElementById('recText');
const probBars = document.getElementById('probBars');
const resetBtn = document.getElementById('resetBtn');
const classesGrid = document.getElementById('classesGrid');

let selectedFile = null;
let previewUrl = null;

function getStoredTheme() {
  return localStorage.getItem(THEME_KEY) || 'light';
}

function applyTheme(theme) {
  document.body.dataset.theme = theme;
  themeToggle.setAttribute('aria-pressed', String(theme === 'dark'));
  localStorage.setItem(THEME_KEY, theme);
}

function setFlowState(state) {
  const states = {
    upload: { upload: true, review: false, results: false },
    review: { upload: true, review: true, results: false },
    loading: { upload: true, review: true, results: false },
    results: { upload: true, review: true, results: true },
  };

  const current = states[state];
  stepUpload.classList.toggle('is-active', state === 'upload');
  stepReview.classList.toggle('is-active', state === 'review' || state === 'loading');
  stepResults.classList.toggle('is-active', state === 'results');
  stepUpload.classList.toggle('is-complete', current.review || current.results);
  stepReview.classList.toggle('is-complete', current.results);
}

function setResultsState(name) {
  placeholder.hidden = name !== 'placeholder';
  loadingState.hidden = name !== 'loading';
  resultsContent.hidden = name !== 'results';
}

function clearInlineError() {
  inlineError.hidden = true;
  inlineError.textContent = '';
}

function showInlineError(message) {
  inlineError.hidden = false;
  inlineError.textContent = message;
  setResultsState('placeholder');
  setFlowState(selectedFile ? 'review' : 'upload');
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function revokePreviewUrl() {
  if (previewUrl) {
    URL.revokeObjectURL(previewUrl);
    previewUrl = null;
  }
}

function renderSelectedFile(file) {
  selectedFile = file;
  revokePreviewUrl();
  previewUrl = URL.createObjectURL(file);
  previewImg.src = previewUrl;
  previewContent.hidden = false;
  dropContent.hidden = true;
  fileInfo.hidden = false;
  fileName.textContent = file.name;
  fileSize.textContent = formatBytes(file.size);
  analyzeBtn.disabled = false;
  clearInlineError();
  setResultsState('placeholder');
  setFlowState('review');
  reviewPanel.dataset.state = 'selected';
}

function clearFile() {
  selectedFile = null;
  fileInput.value = '';
  revokePreviewUrl();
  previewImg.removeAttribute('src');
  previewContent.hidden = true;
  dropContent.hidden = false;
  fileInfo.hidden = true;
  analyzeBtn.disabled = true;
  clearInlineError();
  setResultsState('placeholder');
  setFlowState('upload');
  reviewPanel.dataset.state = 'empty';
}

function validateFile(file) {
  if (!file) return 'Khong tim thay file de phan tich.';
  const allowedTypes = ['image/jpeg', 'image/png', 'image/bmp', 'image/webp'];
  if (!allowedTypes.includes(file.type)) {
    return 'Dinh dang khong ho tro. Hay chon JPG, PNG, BMP hoac WEBP.';
  }
  if (file.size > 16 * 1024 * 1024) {
    return 'File qua lon. Gioi han toi da la 16 MB.';
  }
  return '';
}

function handleFile(file) {
  const validationError = validateFile(file);
  if (validationError) {
    showInlineError(validationError);
    return;
  }
  renderSelectedFile(file);
}

function setAnalyzeBusy(isBusy) {
  analyzeBtn.disabled = isBusy || !selectedFile;
  analyzeBtnLabel.hidden = isBusy;
  analyzeBtnSpinner.hidden = !isBusy;
}

async function checkHealth() {
  try {
    const response = await fetch('/api/health', { signal: AbortSignal.timeout(4000) });
    const data = await response.json();

    if (data.model_loaded) {
      statusDot.className = 'status-dot online';
      statusText.textContent = 'Model san sang';
    } else {
      statusDot.className = 'status-dot offline';
      statusText.textContent = 'Model chua duoc load';
    }
  } catch {
    statusDot.className = 'status-dot offline';
    statusText.textContent = 'Khong ket noi duoc server';
  }
}

function getRiskSubtext(risk) {
  return {
    low: 'Khong co dau hieu nguy hiem ro rang trong du doan hien tai.',
    medium: 'Nen theo doi thay doi cua ton thuong va tham khao y kien bac si.',
    high: 'Nen di kham da lieu som de duoc danh gia chinh xac.',
    critical: 'Can duoc kiem tra boi co so y te trong thoi gian som nhat.',
  }[risk] || '';
}

function displayResults(data) {
  const { prediction, confidence, probabilities, description_vi, recommendation, risk_level, risk_label_vi } = data;
  const risk = risk_level || CLASS_META[prediction]?.risk || 'low';
  const percent = Math.round(confidence * 100);

  predClass.textContent = prediction.toUpperCase();
  predFullname.textContent = CLASS_META[prediction]?.name || prediction;
  confPercent.textContent = `${percent}%`;
  ringFill.style.strokeDashoffset = 201 - 201 * confidence;
  ringFill.style.stroke = confidence >= 0.8 ? 'var(--accent)' : confidence >= 0.6 ? '#c28b2c' : 'var(--danger)';

  riskBadge.className = `risk-badge ${risk}`;
  riskBadge.textContent = risk_label_vi || RISK_LABEL[risk];
  riskDesc.textContent = getRiskSubtext(risk);
  infoDesc.textContent = description_vi || '-';
  recText.textContent = recommendation || '-';

  probBars.innerHTML = '';
  Object.entries(probabilities)
    .sort((a, b) => b[1] - a[1])
    .forEach(([label, value]) => {
      const row = document.createElement('div');
      const isPredicted = label === prediction;
      row.className = 'prob-row';
      row.innerHTML = `
        <span class="prob-name">${label.toUpperCase()}</span>
        <div class="prob-bar-wrap">
          <div class="prob-bar-fill ${isPredicted ? 'predicted' : ''}" style="width:${Math.max(value * 100, 0.5)}%"></div>
        </div>
        <span class="prob-val">${(value * 100).toFixed(1)}%</span>
      `;
      probBars.appendChild(row);
    });

  clearInlineError();
  setResultsState('results');
  setFlowState('results');
}

function buildClassCards() {
  classesGrid.innerHTML = '';
  Object.entries(CLASS_META).forEach(([code, meta]) => {
    const card = document.createElement('article');
    card.className = 'class-card';
    card.innerHTML = `
      <span class="class-code">${code.toUpperCase()}</span>
      <p class="class-name">${meta.name}</p>
      <span class="class-risk">${RISK_LABEL[meta.risk]}</span>
    `;
    classesGrid.appendChild(card);
  });
}

themeToggle.addEventListener('click', () => {
  const nextTheme = document.body.dataset.theme === 'dark' ? 'light' : 'dark';
  applyTheme(nextTheme);
});

browseBtn.addEventListener('click', () => fileInput.click());
replaceBtn.addEventListener('click', () => fileInput.click());
clearBtn.addEventListener('click', clearFile);
resetBtn.addEventListener('click', clearFile);

fileInput.addEventListener('change', event => {
  handleFile(event.target.files[0]);
});

dropZone.addEventListener('dragover', event => {
  event.preventDefault();
  dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', event => {
  event.preventDefault();
  dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', event => {
  event.preventDefault();
  dropZone.classList.remove('drag-over');
  handleFile(event.dataTransfer.files[0]);
});

dropZone.addEventListener('click', event => {
  if (event.target === dropZone || event.target.closest('#dropContent')) {
    fileInput.click();
  }
});

analyzeBtn.addEventListener('click', async () => {
  if (!selectedFile) {
    showInlineError('Hay chon anh truoc khi phan tich.');
    return;
  }

  setAnalyzeBusy(true);
  setResultsState('loading');
  setFlowState('loading');

  try {
    const formData = new FormData();
    formData.append('file', selectedFile);

    const response = await fetch('/api/predict', {
      method: 'POST',
      body: formData,
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || `Server error ${response.status}`);
    }

    displayResults(data);
  } catch (error) {
    showInlineError(error.message || 'Khong the ket noi toi server Flask.');
  } finally {
    setAnalyzeBusy(false);
  }
});

document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && selectedFile) {
    clearFile();
  }
});

document.addEventListener('paste', event => {
  const items = event.clipboardData?.items || [];
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      handleFile(item.getAsFile());
      break;
    }
  }
});

applyTheme(getStoredTheme());
setFlowState('upload');
setResultsState('placeholder');
buildClassCards();
checkHealth();
```

- [ ] **Step 3: Run the JS contract test again**

Run:

```powershell
python -m unittest tests.test_web_ui.HomePageUiTest.test_script_defines_theme_and_flow_helpers -v
```

Expected:

```text
ok
```

- [ ] **Step 4: Commit the frontend behavior refactor**

```powershell
git add web/static/js/main.js tests/test_web_ui.py
git commit -m "feat: add guided ui interactions"
```

### Task 5: Verify the Full Redesign End to End

**Files:**
- Validate: `tests/test_web_ui.py`
- Validate: `web/templates/index.html`
- Validate: `web/static/css/style.css`
- Validate: `web/static/js/main.js`

- [ ] **Step 1: Run the automated regression suite**

Run:

```powershell
python -m unittest tests.test_web_ui -v
```

Expected:

```text
Ran 3 tests in ...
OK
```

- [ ] **Step 2: Run the Python syntax smoke check**

Run:

```powershell
python -m compileall src web
```

Expected:

```text
Listing 'src'...
Listing 'web'...
```

- [ ] **Step 3: Run the Flask app and perform the manual smoke test**

Run:

```powershell
python web/app.py
```

Manual checks:

```text
1. Open http://localhost:5000 and confirm light mode loads first.
2. Toggle dark mode, refresh, and confirm the selected theme persists.
3. Drag a valid image into the upload card and verify the review state appears.
4. Click "Thay anh" and confirm the file picker opens.
5. Upload an invalid file type and confirm the inline error appears in the review card.
6. Upload a valid image under 16 MB and confirm "Phan tich anh" becomes enabled.
7. Click "Phan tich anh" and confirm the results panel switches to the calm loading state.
8. If the model is available, confirm prediction, confidence, risk badge, recommendation, and probability bars render.
9. If the model is unavailable, confirm the inline workflow error explains the issue without breaking layout.
10. Resize to mobile width and confirm the step cards stack cleanly with readable spacing.
```

- [ ] **Step 4: Commit the verified redesign**

```powershell
git add tests/test_web_ui.py web/templates/index.html web/static/css/style.css web/static/js/main.js
git commit -m "feat: redesign dermai frontend"
```
