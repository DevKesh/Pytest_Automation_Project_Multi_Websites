# Framework Creation Guide — Nova Shop E2E (Python + Playwright + pytest)

This guide explains, end to end, how this framework was built and why each
piece exists. It is written to be read top-to-bottom as a learning reference.
Nothing is skipped.

---

## 1. Goal and philosophy

Build a small, realistic E2E suite for the Nova Shop practice app that:

- Uses the **Page Object Model (POM)** so locators live in one place.
- Runs **cross-browser** (Chromium, Firefox, WebKit).
- Produces an **HTML report** plus **trace/screenshot/video** on failure.
- Stays **simple**: lean on the official `pytest-playwright` plugin instead of
  re-implementing browser lifecycle, CLI flags, or artifact capture.

The guiding rule: *don't add an abstraction unless it earns its keep.* We have
no custom `BasePage` wrapper, no bespoke logger, and no settings dataclass —
the plugin and plain Python already cover those needs.

---

## 2. Understanding the application under test

The app is **not** a classic WooCommerce store — it's a React single-page app
("Nova Shop"). Two facts shaped the whole framework:

1. **It requires login.** `/shop` shows a sign-in form. Shared demo accounts are
   listed on the page; we use `demo_user` / `Demo@123`.
2. **Every meaningful element has a `data-testid`.** For example
   `product-card`, `add-to-cart-p1`, `cart-badge`, `checkout-button`,
   `place-order`, `order-success`. These are the most stable selectors
   available, so we target them with Playwright's `get_by_test_id()`.

We discovered the structure by scripting Playwright to log in and dump the
`data-testid` attributes and page routes:

- Login → routes to `/shop/products`
- Add to cart → header `cart-badge` increments; product button becomes
  `remove-from-cart-pN`
- Cart page `/shop/cart` → `cart-item`, `item-qty`, `increase-qty`,
  `decrease-qty`, `remove-item`, `checkout-button`
- Checkout `/shop/checkout` → billing fields, `shipping-standard`,
  `payment-card`, card fields, `accept-terms`, `place-order`
- Success `/shop/checkout/complete` → `order-success`, `order-id` (e.g.
  `NS-4680871`)

> **Lesson:** always inspect the real DOM before writing page objects. Our
> first draft assumed WooCommerce selectors and every test failed.

---

## 3. Tooling and environment

### Dependencies (`requirements.txt`)

- `pytest` — the test runner.
- `playwright` + `pytest-playwright` — the browser driver and its pytest plugin.
  The plugin gives us the `page` fixture and the `--browser`, `--headed`,
  `--slowmo`, `--tracing`, `--screenshot`, `--video`, `--output` options for
  free.
- `pytest-html` — the self-contained HTML report.

### Python version

Use **Python 3.12**. Playwright had no prebuilt wheels for 3.14 at build time,
so pip tried to compile `greenlet` from source and failed without MS C++ Build
Tools. Recreating the venv with 3.12 fixed it instantly.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install
```

---

## 4. Configuration

### `config.py`

Plain module-level constants — no class, no env parsing. This is all the config
a small suite needs:

```python
BASE_URL = "https://www.practiceqaautomation.com"
USERNAME = "demo_user"
PASSWORD = "Demo@123"
```

### `pytest.ini`

- `pythonpath = .` makes `config` and `pages` importable from the project root.
- `addopts` turns on the HTML report and failure artifacts by default:
  `--screenshot=only-on-failure`, `--video=retain-on-failure`,
  `--tracing=retain-on-failure`, `--output=reports/test-results`.
- `markers` registers `smoke`, `regression`, `checkout`.
- `log_cli = true` streams logs during the run.

---

## 5. The Page Object Model (`pages/`)

Each page object is a plain class that:

1. Takes the Playwright `page` in its constructor.
2. Stores its locators as attributes (resolved lazily — Playwright locators are
   just descriptions, not elements).
3. Exposes small action methods that read like user intent.

Example — `pages/shop_page.py`:

```python
class ShopPage:
    def __init__(self, page):
        self.page = page
        self.product_cards = page.get_by_test_id("product-card")
        self.cart_badge = page.get_by_test_id("cart-badge")

    def add_to_cart(self, index):
        self.page.get_by_test_id(f"add-to-cart-p{index}").click()

    def open_cart(self):
        self.page.get_by_test_id("cart-link").click()
        self.page.wait_for_url("**/shop/cart")
```

Key points:

- **No BasePage.** Playwright's `Locator`/`Page` API is already a clean, shared
  base; wrapping `.click()` in `self.click(locator)` adds noise without value.
- **`wait_for_url`** after navigation makes the next action deterministic
  (this fixed a real flake where the cart read 0 items because the assertion
  ran before the route changed).
- The four page objects are `LoginPage`, `ShopPage`, `CartPage`, `CheckoutPage`.

---

## 6. Fixtures (`tests/conftest.py`)

`conftest.py` is auto-discovered by pytest; its fixtures are available to every
test without importing.

- **`page`** — provided by `pytest-playwright` (fresh, isolated tab per test).
- **`logged_in_page`** — logs in once via `LoginPage` and returns the
  authenticated `page`. Because every commerce page is gated, the page-object
  fixtures depend on this, so tests start already signed in.
- **`shop_page` / `cart_page` / `checkout_page`** — construct the matching page
  object bound to the logged-in tab.
- **`product_data`** — loads `tests/data/products.json` (session-scoped).
- **`billing_details`** — returns a dict with a **unique email per run**
  (`jane.doe.<epoch>@example.com`) so repeated checkouts never collide.

This dependency chain — `page → logged_in_page → shop_page → test` — is exactly
how real suites compose setup through fixtures.

---

## 7. The tests (`tests/e2e/`)

All five tests follow a simple **Arrange / Act / Assert** shape and use
Playwright's **web-first assertions** (`expect(...)`) which auto-wait and retry.

1. **`test_browse_products.py`** — catalogue loads after login (URL + count);
   search narrows results.
2. **`test_add_to_cart.py`** — `@pytest.mark.parametrize` adds two products;
   checks the badge and the cart line item.
3. **`test_update_cart_quantity.py`** — clicks `increase-qty` twice and asserts
   the quantity text becomes `3`.
4. **`test_remove_from_cart.py`** — removes the item and asserts
   `cart_items` has count `0`.
5. **`test_checkout.py`** — full flow: add → cart → checkout → fill billing +
   payment (test card `4242 4242 4242 4242`) → place order → assert
   `order-success` is visible and `order-id` contains `NS-`.

> **Why `expect(locator).to_have_count(1)` instead of `assert count() == 1`?**
> `.count()` is an immediate snapshot and can run before the UI updates;
> `expect(...)` retries until the condition holds or times out, removing flakes.

---

## 8. Cross-browser execution

The `pytest-playwright` plugin parametrizes the `page` fixture by browser when
you pass `--browser`. Repeat the flag to fan out:

```powershell
pytest --browser chromium --browser firefox --browser webkit
```

Each test then runs once per engine, with the browser name shown in the test id
(e.g. `test_add_to_cart.py::...[firefox-1-Aurora Wireless Headphones]`). This
suite was verified green on all three engines.

---

## 9. Reporting & diagnostics

- **HTML report:** `reports/report.html` (from `pytest-html`,
  `--self-contained-html` so it's a single shareable file).
- **Trace:** `--tracing=retain-on-failure` keeps a Playwright trace zip for
  failing tests under `reports/test-results/`. View it with
  `playwright show-trace <trace.zip>` — it includes DOM snapshots, a timeline,
  network and console.
- **Screenshot:** `--screenshot=only-on-failure`.
- **Video:** `--video=retain-on-failure`.

Everything above is configured once in `pytest.ini`, so a plain `pytest` run
produces full diagnostics without extra flags.

---

## 10. CI (`.github/workflows/playwright-tests.yml`)

A GitHub Actions workflow runs the suite on a **matrix** of
`{chromium, firefox, webkit}` with `fail-fast: false` so one engine's failure
doesn't cancel the others. Steps:

1. `actions/checkout`
2. `actions/setup-python` (3.12) with pip cache
3. `pip install -r requirements.txt`
4. `playwright install --with-deps <browser>`
5. `pytest --browser <browser> --html=reports/report-<browser>.html`
6. `actions/upload-artifact` (with `if: always()`) uploads `reports/` so the
   HTML report, traces, screenshots and videos are downloadable from the run.

---

## 11. Concept glossary

- **Fixture** — a reusable setup/teardown function marked `@pytest.fixture`.
  Tests request it by naming it as a parameter; pytest injects the value.
- **Fixture scope** — how long a fixture lives: `function` (default, per test),
  `session` (once per run, e.g. `product_data`). Wider scope = less repetition.
- **`conftest.py`** — a special file pytest auto-loads; fixtures/hooks here are
  shared with all tests in that folder tree without importing.
- **Marker** — a label like `@pytest.mark.smoke` used to select subsets with
  `-m`. Register markers in `pytest.ini` to avoid typos.
- **Parametrization** — `@pytest.mark.parametrize` runs one test function many
  times with different inputs; each becomes its own reported case.
- **Locator** — a Playwright object describing how to find element(s). It is
  lazy: it re-resolves on each action, so it survives DOM re-renders.
- **`get_by_test_id`** — a locator that matches a `data-testid` attribute, the
  most change-resistant selector strategy.
- **Auto-waiting** — before acting, Playwright waits for the element to be
  visible, enabled and stable. No manual `sleep` needed.
- **Web-first assertion** — `expect(locator).to_...()` retries until the
  condition is true or times out, eliminating race-condition flakiness.
- **Browser / Context / Page** — Playwright's hierarchy. A *context* is an
  isolated session (like incognito); a *page* is a tab. `pytest-playwright`
  gives each test its own context+page for clean isolation.
- **Trace** — a recorded timeline of a test (snapshots, network, console)
  viewable with `playwright show-trace`; invaluable for debugging CI failures.
