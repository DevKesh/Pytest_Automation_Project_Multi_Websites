# Framework Architecture & Flow — How Everything Connects

This document explains **how the pieces of the framework talk to each other** —
`config`, `pages`, `conftest` fixtures, test data, and the tests themselves —
and then shows you a **repeatable recipe to automate an entirely new web app
in minutes** using the same pattern.

Read this once and you'll understand *why* a plain `pytest` command ends up
driving a real browser through a real user journey.

---

## 1. The big picture (bird's-eye view)

```
┌──────────────────────────────────────────────────────────────────────┐
│                              pytest run                                │
│                                                                        │
│   pytest.ini  ──► applies default flags, pythonpath, markers           │
│       │                                                                │
│       ▼                                                                │
│   pytest-playwright plugin  ──► provides the `page` fixture            │
│       │                         (fresh browser tab per test)           │
│       ▼                                                                │
│   tests/conftest.py  ──► builds fixtures ON TOP of `page`:             │
│       │                   logged_in_page → shop_page / cart_page / ... │
│       │                   + product_data + billing_details             │
│       ▼                                                                │
│   tests/e2e/test_*.py  ──► a test asks for fixtures by name,           │
│       │                     calls page-object methods, asserts         │
│       ▼                                                                │
│   pages/*.py  ──► translate intent ("add_to_cart") into               │
│       │           Playwright locator actions on the real DOM          │
│       ▼                                                                │
│   config.py  ──► supplies URL + credentials used by pages/fixtures    │
└──────────────────────────────────────────────────────────────────────┘
```

**The golden rule of the layers:**
- **Tests** describe *what* a user does and *what* should be true.
- **Page objects** know *how* to do it (locators + Playwright calls).
- **Fixtures** prepare *everything a test needs* before it runs.
- **config** holds *values that change* (URL, credentials).

A test never touches a raw selector; a page object never contains an assertion
about business outcome; config never contains logic. Clean separation.

---

## 2. The actors (what each file is responsible for)

| File | Role | Knows about | Never does |
|------|------|-------------|------------|
| `config.py` | Constants: `BASE_URL`, `USERNAME`, `PASSWORD` | Nothing | Logic, locators |
| `pages/*.py` | Page Object Model — locators + actions | The DOM / `data-testid`s | Assertions on business rules |
| `tests/conftest.py` | Fixtures — setup/teardown & wiring | Pages + config | Test steps |
| `tests/e2e/test_*.py` | The actual scenarios | Fixtures + `expect` | Raw selectors |
| `tests/data/*.json` | Static test data | Nothing | Logic |
| `pytest.ini` | Defaults & plugin config | Paths, flags, markers | — |

---

## 3. The dependency chain, step by step

When you run `pytest tests/e2e/test_add_to_cart.py`, here is the **exact chain
of events** for one test case:

### Step 1 — pytest reads `pytest.ini`
It applies `addopts` (HTML report, screenshot/video/trace on failure),
`pythonpath = .` (so `import config` and `from pages... ` resolve), and
registers the markers.

### Step 2 — pytest collects the test
It finds `test_add_single_product_to_cart` and sees its parameters:

```python
def test_add_single_product_to_cart(shop_page, cart_page, index, product_name):
```

Those parameter **names are fixture requests**. pytest must satisfy them.

### Step 3 — the plugin creates `page`
`shop_page` needs `logged_in_page`, which needs `page`. The `page` fixture
comes from **pytest-playwright**: it launches the browser, opens an isolated
context, and hands over a fresh tab.

### Step 4 — `logged_in_page` logs in
```python
@pytest.fixture
def logged_in_page(page):
    login = LoginPage(page)      # wrap the raw tab in a page object
    login.load()                 # goto BASE_URL/shop
    login.login(USERNAME, PASSWORD)  # fill + submit + wait for /shop/products
    return page                  # now authenticated
```
It uses `config.USERNAME/PASSWORD` and the `LoginPage` object. After this, the
tab is signed in and sitting on the products page.

### Step 5 — `shop_page` / `cart_page` are built on the logged-in tab
```python
@pytest.fixture
def shop_page(logged_in_page):
    return ShopPage(logged_in_page)
```
Both page objects share the **same authenticated tab**, so actions flow
naturally from shop → cart.

### Step 6 — the test body runs
```python
shop_page.add_to_cart(index)                 # ShopPage clicks add-to-cart-pN
expect(shop_page.cart_badge).to_have_text("1")   # web-first assertion
shop_page.open_cart()                        # navigate to /shop/cart
expect(cart_page.cart_items).to_have_count(1)    # auto-waits for the list
expect(cart_page.cart_item(product_name)).to_be_visible()
```
The test reads like a user story. All the "how" lives in the page objects.

### Step 7 — teardown & artifacts
After the test returns, pytest-playwright closes the context. If the test
**failed**, the screenshot/video/trace are retained under
`reports/test-results/`. The HTML report row is written either way.

---

## 4. A concrete trace of the checkout test

To see every layer cooperate, follow `test_complete_checkout_places_order`:

```
test_checkout.py
  requests: shop_page, cart_page, checkout_page, billing_details, product_data
      │
      ├─ product_data  ← conftest reads tests/data/products.json
      ├─ billing_details ← conftest generates a UNIQUE email per run
      ├─ shop_page/cart_page/checkout_page ← all share logged_in_page
      │
      ▼ test body
  shop_page.add_to_cart(1)                 → ShopPage → click add-to-cart-p1
  shop_page.open_cart()                    → ShopPage → click cart-link + wait
  cart_page.checkout()                     → CartPage → click checkout-button + wait
  checkout_page.fill_billing(details)      → CheckoutPage → fill 8 fields + select state
  checkout_page.fill_payment()             → CheckoutPage → card + accept terms
  checkout_page.place_order()              → CheckoutPage → submit + wait /complete
  expect(order_success).to_be_visible()    → assert banner
  expect(order_id).to_contain_text("NS-")  → assert real order id
```

Notice: the **test** orchestrates; the **page objects** execute; the
**fixtures** supplied the session + data; **config** supplied the URL.

---

## 5. Why fixtures instead of setup code in each test?

Without fixtures, every test would repeat:

```python
# ❌ the painful way — duplicated in every test
page.goto(BASE_URL + "/shop")
page.get_by_test_id("username").fill("demo_user")
page.get_by_test_id("password").fill("Demo@123")
page.get_by_test_id("login-button").click()
page.wait_for_url("**/shop/products")
shop = ShopPage(page)
```

With fixtures, the test just asks for `shop_page` and it's **already logged in
and ready**. Benefits:
- **DRY** — login written once.
- **Isolation** — each test gets its own fresh context (no shared cookies).
- **Composability** — `shop_page` depends on `logged_in_page` depends on
  `page`; pytest resolves the whole chain automatically.
- **Readability** — the test shows intent, not plumbing.

---

## 6. How data flows (parametrize + JSON + generated data)

Three data sources, three purposes:

1. **`@pytest.mark.parametrize`** — inline variations of the *same* test
   (e.g. add product 1, then product 2). One function → many reported cases.
2. **`tests/data/products.json`** — static reference data (names, indexes)
   loaded once via the session-scoped `product_data` fixture.
3. **`billing_details` fixture** — dynamically generated, **unique per run**
   (epoch-stamped email) so repeated real checkouts never collide.

Rule of thumb:
- Values that define *which scenarios* to run → **parametrize**.
- Known reference facts about the app → **JSON**.
- Values that must be unique/fresh each run → **generated in a fixture**.

---

## 7. ⭐ Recipe: automate a brand-new web app in minutes

The same skeleton works for *any* site. Here's the repeatable process.

### Step 0 — Inspect the target app
Open the app and find stable selectors. Prefer, in order:
1. `data-testid` / `data-test` attributes → `page.get_by_test_id(...)`
2. Accessible roles/labels → `page.get_by_role("button", name="Sign in")`
3. Text → `page.get_by_text(...)`
4. CSS/XPath (last resort).

> Tip: run a throwaway script that logs in and dumps `data-testid`s, exactly
> like we did for Nova Shop, to map the DOM fast.

### Step 1 — Set config
```python
# config.py
BASE_URL = "https://your-new-app.com"
USERNAME = "..."
PASSWORD = "..."
```

### Step 2 — Create a page object per screen
```python
# pages/dashboard_page.py
from playwright.sync_api import Page

class DashboardPage:
    def __init__(self, page: Page):
        self.page = page
        self.new_button = page.get_by_test_id("new-item")
        self.rows = page.get_by_test_id("row")

    def create_item(self, name: str):
        self.new_button.click()
        self.page.get_by_test_id("name").fill(name)
        self.page.get_by_test_id("save").click()
```
Keep the pattern: **locators in `__init__`, intent methods below.**

### Step 3 — Add a fixture (wire it to the session)
```python
# tests/conftest.py
@pytest.fixture
def dashboard_page(logged_in_page):
    return DashboardPage(logged_in_page)
```
If the new app has a different login, just adapt `logged_in_page`.

### Step 4 — Write the test (Arrange / Act / Assert)
```python
# tests/e2e/test_dashboard.py
import pytest
from playwright.sync_api import expect
from pages.dashboard_page import DashboardPage

@pytest.mark.smoke
def test_create_item(dashboard_page: DashboardPage):
    dashboard_page.create_item("My Item")                     # Act
    expect(dashboard_page.rows.filter(has_text="My Item")).to_be_visible()  # Assert
```

### Step 5 — Run it
```powershell
pytest tests/e2e/test_dashboard.py --headed
```

That's it. **Config → Page object → Fixture → Test → Run.** Because the
lifecycle, cross-browser, reporting and artifacts are all handled by
`pytest-playwright` + `pytest.ini`, you only ever write those four small pieces.

---

## 8. Mental checklist for every new test

- [ ] Are my selectors stable (`data-testid` / role) — not brittle CSS?
- [ ] Did I put locators in the **page object**, not the test?
- [ ] Did I put assertions in the **test**, not the page object?
- [ ] Am I reusing `logged_in_page` (or a similar fixture) for setup?
- [ ] Am I using **`expect(...)`** web-first assertions (auto-wait), not
      bare `assert` on immediate snapshots?
- [ ] Is unique data generated in a fixture, static data in JSON, and
      scenario variation in `parametrize`?
- [ ] Did I tag the test with a marker (`smoke`/`regression`)?

Tick all seven and your test will be clean, stable, and cross-browser ready.

---

## 9. Where to look next

- **How to run everything:** [`running-tests.md`](running-tests.md)
- **Why the framework is built this way + glossary:**
  [`framework-creation-guide.md`](framework-creation-guide.md)
- **pytest.ini explained:** comments inside `pytest.ini`
