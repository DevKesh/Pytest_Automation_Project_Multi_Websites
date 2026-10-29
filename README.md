# Nova Shop — Playwright + Pytest E2E Framework

[![Playwright E2E Tests](https://github.com/DevKesh/Pytest_Automation_Project_Multi_Websites/actions/workflows/playwright-tests.yml/badge.svg)](https://github.com/DevKesh/Pytest_Automation_Project_Multi_Websites/actions/workflows/playwright-tests.yml)

A clean, production-style end-to-end test framework for the **Nova Shop**
practice app at [practiceqaautomation.com/shop](https://www.practiceqaautomation.com/shop),
built with **Python + Playwright + pytest** using the Page Object Model.

It keeps things simple and idiomatic: it relies on the official
`pytest-playwright` plugin for the browser lifecycle, cross-browser execution,
tracing, screenshots and video — so there is no hand-rolled plumbing to
maintain.

---

## Features

- **Page Object Model** — one small class per page (`pages/`).
- **Cross-browser** — Chromium, Firefox and WebKit via `--browser`.
- **Fixtures** — login + page objects injected via `tests/conftest.py`.
- **Reporting** — self-contained HTML report + trace/screenshot/video on failure.
- **Data-driven** — `@pytest.mark.parametrize` and JSON test data.
- **CI-ready** — GitHub Actions matrix workflow included.

## Project structure

```
PythonPyTestProject/
├─ config.py                 # Base URL + demo credentials (plain constants)
├─ pytest.ini                # pytest + plugin options, markers
├─ requirements.txt
├─ pages/                    # Page Object Model
│  ├─ login_page.py
│  ├─ shop_page.py
│  ├─ cart_page.py
│  └─ checkout_page.py
├─ tests/
│  ├─ conftest.py            # Fixtures: login, page objects, test data
│  ├─ data/products.json     # Static product data
│  └─ e2e/                   # The five E2E tests
│     ├─ test_browse_products.py
│     ├─ test_add_to_cart.py
│     ├─ test_update_cart_quantity.py
│     ├─ test_remove_from_cart.py
│     └─ test_checkout.py
├─ reports/                  # HTML report + artifacts (git-ignored)
└─ .github/workflows/playwright-tests.yml
```

## Setup

```powershell
# 1. Create / activate a Python 3.12 virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install the browser binaries
playwright install
```

> **Note:** Use Python 3.12. At the time of writing, Playwright has no
> prebuilt wheels for Python 3.14, which forces a C++ source build.

## Running tests

```powershell
# All tests on Chromium (default)
pytest

# Pick a browser
pytest --browser firefox

# Cross-browser (repeat the flag)
pytest --browser chromium --browser firefox --browser webkit

# Watch the browser (local debugging) + slow motion
pytest --headed --slowmo 500

# Run by marker
pytest -m smoke
pytest -m "regression and not checkout"
```

The HTML report is written to `reports/report.html`. On failure, a trace
(`reports/test-results/.../trace.zip`), screenshot and video are kept.
Open a trace with:

```powershell
playwright show-trace reports/test-results/<test>/trace.zip
```

> **Full command reference** (headless, headed, browser-specific, markers,
> parallel, debugging, reporting): see
> [`docs/running-tests.md`](docs/running-tests.md).

## The five E2E tests

| Test file | What it verifies |
|---|---|
| `test_browse_products.py` | Catalogue loads after login; search filters products |
| `test_add_to_cart.py` | Adding a product (parametrized) updates the cart |
| `test_update_cart_quantity.py` | `+` stepper raises the line quantity |
| `test_remove_from_cart.py` | Removing the only item empties the cart |
| `test_checkout.py` | Full checkout places a real order (NS- id) |

## Credentials

The practice site exposes shared demo accounts (see the login page hint).
This framework uses `demo_user` / `Demo@123`, set in `config.py`.

## Quality gate (CI)

Every push / PR runs a quality gate in GitHub Actions
([`.github/workflows/playwright-tests.yml`](.github/workflows/playwright-tests.yml)):

1. **Lint** — `ruff check` + `ruff format --check` (config in `ruff.toml`).
2. **E2E** — the suite runs on a matrix of Chromium, Firefox and WebKit.
3. **Quality Gate** — a final job that **fails the workflow unless lint *and*
   every browser job succeeded**. Set this job as the required status check in
   branch protection to block merges on red.

Run the same checks locally before pushing:

```powershell
pip install -r requirements-dev.txt
ruff check .            # lint
ruff format .           # auto-format
pytest                  # tests
```


See [`docs/framework-creation-guide.md`](docs/framework-creation-guide.md) for a
full, step-by-step explanation of how the framework was built, including a
concept glossary.

## Documentation

- [`docs/architecture-and-flow.md`](docs/architecture-and-flow.md) — how pages, tests, conftest and fixtures interact, plus a recipe to automate a new app fast.
- [`docs/running-tests.md`](docs/running-tests.md) — every way to trigger the suite (headless, headed, browser-specific, markers, parallel, debugging).
- [`docs/framework-creation-guide.md`](docs/framework-creation-guide.md) — how the framework was built + concept glossary.
