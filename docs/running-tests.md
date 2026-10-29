# Running the Tests — Complete Command Reference

This guide lists **every practical way to trigger the Nova Shop E2E suite**:
headless vs headed, specific browsers, cross-browser, by marker, by
name, debugging, parallelism, reporting, and more.

> All commands assume you are in the project root with the virtual environment
> active. On Windows PowerShell:
> ```powershell
> .\.venv\Scripts\Activate.ps1
> ```
> If the venv is **not** activated, prefix every command with the venv's python:
> ```powershell
> .\.venv\Scripts\python.exe -m pytest ...
> ```

---

## 0. One-time setup

```powershell
# Install Python dependencies
pip install -r requirements.txt

# Install the Playwright browser binaries (Chromium, Firefox, WebKit)
playwright install
```

---

## 1. The simplest run

```powershell
pytest
```

What this does (because of `pytest.ini`):
- Collects tests from the `tests/` folder.
- Runs **headless** on **Chromium** (the default browser).
- Captures a **screenshot, video, and trace on failure**.
- Writes an HTML report to `reports/report.html`.
- Prints a summary of non-passing tests (`-ra`).

---

## 2. Headless vs Headed

**Headless** (no visible window) is the default — fastest, used in CI.

```powershell
pytest                 # headless (default)
```

**Headed** (watch the browser drive the UI) — great for local debugging.

```powershell
pytest --headed
```

**Slow motion** — pause N milliseconds between each action so you can follow
along visually. Combine with `--headed`.

```powershell
pytest --headed --slowmo 1000       # 1 second between actions
```

---

## 3. Browser-specific runs

The `--browser` flag comes from the `pytest-playwright` plugin.

```powershell
pytest --browser chromium       # Chromium only (default engine)
pytest --browser firefox        # Firefox only
pytest --browser webkit         # WebKit (Safari engine) only
```

### Cross-browser (run on several engines)

Repeat the `--browser` flag. Each test runs once **per** browser.

```powershell
# Two browsers
pytest --browser chromium --browser firefox

# All three engines
pytest --browser chromium --browser firefox --browser webkit
```

Test IDs then include the browser name, e.g.:

```
test_add_to_cart.py::test_add_single_product_to_cart[firefox-1-Aurora Wireless Headphones]
```

### Headed + specific browser + slow motion (full debug combo)

```powershell
pytest --browser webkit --headed --slowmo 500
```

---

## 4. Running specific tests

### A single file
```powershell
pytest tests/e2e/test_checkout.py
```

### A single test function
```powershell
pytest tests/e2e/test_checkout.py::test_complete_checkout_places_order
```

### One parametrized case (quote the brackets in PowerShell)
```powershell
pytest "tests/e2e/test_add_to_cart.py::test_add_single_product_to_cart[chromium-1-Aurora Wireless Headphones]"
```

### By keyword (matches names, substring)
```powershell
pytest -k "checkout"                 # any test whose name contains "checkout"
pytest -k "add or remove"            # boolean expressions allowed
pytest -k "cart and not remove"
```

---

## 5. Running by marker

Markers are labels defined in `pytest.ini` (`smoke`, `regression`, `checkout`).

```powershell
pytest -m smoke                      # only smoke tests
pytest -m regression                 # only regression tests
pytest -m checkout                   # only the real-order checkout test
pytest -m "regression and not checkout"
pytest -m "smoke or checkout"
```

---

## 6. Parallel execution (faster runs)

Parallelism needs the `pytest-xdist` plugin.

```powershell
pip install pytest-xdist
```

```powershell
pytest -n auto                       # use all CPU cores
pytest -n 4                          # use 4 workers
pytest -n auto --browser chromium --browser firefox   # cross-browser in parallel
```

> Note: live logs interleave when running in parallel. Use a serial run
> (`-n0` or omit `-n`) when you need clean, ordered log output.

---

## 7. Controlling output & verbosity

```powershell
pytest -v                            # verbose: show each test name + result
pytest -q                            # quiet: minimal output
pytest -s                            # don't capture stdout/print()
pytest --tb=short                    # shorter tracebacks on failure
pytest --tb=line                     # one line per failure
pytest -x                            # stop at the first failure
pytest --maxfail=2                   # stop after 2 failures
pytest -rA                           # summary of ALL results (incl. passes)
```

---

## 8. Reporting & artifacts

An HTML report is written on **every** run (configured in `pytest.ini`):

```
reports/report.html
```

On **failure**, these are also saved under `reports/test-results/`:
- a **screenshot** (`--screenshot=only-on-failure`)
- a **video** (`--video=retain-on-failure`)
- a **trace** zip (`--tracing=retain-on-failure`)

### Write the report to a custom path
```powershell
pytest --html=reports/my-run.html --self-contained-html
```

### Force artifacts for ALL tests (not just failures)
```powershell
pytest --screenshot=on --video=on --tracing=on
```

### Turn artifacts OFF (fast run, no capture)
```powershell
pytest --screenshot=off --video=off --tracing=off
```

### View a saved trace (DOM snapshots, network, timeline)
```powershell
playwright show-trace reports/test-results/<test-folder>/trace.zip
```

---

## 9. Debugging tools

### Playwright Inspector — step through actions live
```powershell
$env:PWDEBUG=1 ; pytest tests/e2e/test_checkout.py --headed
# To turn it off afterwards:
Remove-Item Env:\PWDEBUG
```

### Drop into the Python debugger on failure
```powershell
pytest --pdb
```

### Re-run only the tests that failed last time
```powershell
pytest --lf                          # "last failed"
pytest --ff                          # "failed first", then the rest
```

---

## 10. Browser channels & devices (optional)

### Use real Google Chrome / Microsoft Edge instead of bundled Chromium
```powershell
pytest --browser-channel chrome
pytest --browser-channel msedge
```

### Custom viewport / device emulation
These are set in test code via Playwright context options, but you can also
emulate a device by configuring the `browser_context_args` fixture. See the
`pytest-playwright` docs for `--device`.

---

## 11. Handy recipes

| Goal | Command |
|------|---------|
| Quick smoke check, headless, Chromium | `pytest -m smoke` |
| Watch the full checkout happen | `pytest tests/e2e/test_checkout.py --headed --slowmo 500` |
| Full cross-browser regression | `pytest -m regression --browser chromium --browser firefox --browser webkit` |
| Fast parallel full run | `pytest -n auto` |
| Debug one failing case | `pytest -k "remove" --headed --pdb` |
| Re-run only failures from last time | `pytest --lf --headed` |
| CI-style run with per-browser report | `pytest --browser firefox --html=reports/report-firefox.html --self-contained-html` |

---

## 12. Quick reference — flag cheat sheet

| Flag | Meaning |
|------|---------|
| `--headed` | Show the browser window |
| `--slowmo N` | Delay N ms between actions |
| `--browser {chromium\|firefox\|webkit}` | Pick engine (repeatable) |
| `--browser-channel {chrome\|msedge}` | Use installed Chrome/Edge |
| `-m "<expr>"` | Select tests by marker |
| `-k "<expr>"` | Select tests by name substring |
| `-n auto` | Run in parallel (needs pytest-xdist) |
| `-v` / `-q` | Verbose / quiet |
| `-s` | Show print()/stdout |
| `-x` / `--maxfail=N` | Stop early on failures |
| `--lf` / `--ff` | Last-failed / failed-first |
| `--pdb` | Debugger on failure |
| `--screenshot/--video/--tracing {on\|off\|...}` | Artifact capture mode |
| `--html=PATH --self-contained-html` | HTML report location |

---

For an explanation of **why** each default lives in `pytest.ini`, see the
comments in that file and [`docs/framework-creation-guide.md`](docs/framework-creation-guide.md).
