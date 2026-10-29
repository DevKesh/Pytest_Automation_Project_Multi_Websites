"""Shared fixtures.

We use the `pytest-playwright` plugin, which already provides the `page`
fixture (a fresh, isolated browser tab per test) and the `--browser`,
`--headed`, `--tracing`, `--screenshot` and `--video` command-line options.
That keeps this file small: we only add login + page-object fixtures.

-------------------------------------------------------------------------------
WHERE DOES THE BROWSER COME FROM?
-------------------------------------------------------------------------------
We never launch a browser or open a tab ourselves. Our fixtures depend on ONE
plugin fixture — `page` — and naming it triggers this chain INSIDE the plugin
file `.venv/Lib/site-packages/pytest_playwright/pytest_playwright.py`:

    browser_name   -> "chromium" (from --browser)
    playwright     -> sync_playwright().start()        # start the driver   [session]
    browser_type   -> getattr(playwright, browser_name)
    browser        -> browser_type.launch(...)         # LAUNCH BROWSER     [session]
    context        -> browser.new_context(...)         # isolated session   [per test]
    page           -> context.new_page()               # OPEN TAB           [per test]
      |
      v
    logged_in_page(page)  -> OUR code starts here (browser already running,
                             tab already open; we just drive it)

Scopes: `playwright`/`browser` are session-scoped (launched once, reused);
`context`/`page` are function-scoped (fresh per test for isolation). The
plugin's `playwright`/`browser` fixtures use `yield` for teardown
(`pw.stop()` / `browser.close()`), which is why OUR fixtures can simply
`return` — there is nothing left for us to clean up.
-------------------------------------------------------------------------------

"""

import json
import time
from pathlib import Path

import pytest

from config import PASSWORD, USERNAME
from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage
from pages.login_page import LoginPage
from pages.shop_page import ShopPage


@pytest.fixture
def logged_in_page(page):
    """Log in as the demo user and return the authenticated page.

    Every commerce page is behind login, so page-object fixtures below build on
    this one — tests therefore start already signed in on /shop/products.

    `page` is provided by the pytest-playwright plugin: a fresh, isolated
    browser tab for this single test. We log in once here and hand it back.
    """
    login = LoginPage(page)  # wrap the raw tab in a LoginPage object
    login.load()  # open /shop (the login form)
    login.login(USERNAME, PASSWORD)  # fill creds + submit + wait for products
    return page  # the tab is now authenticated


@pytest.fixture
def shop_page(logged_in_page):
    """Give the test a ready-to-use ShopPage on the logged-in tab."""
    # Depending on `logged_in_page` guarantees we are already signed in.
    return ShopPage(logged_in_page)


@pytest.fixture
def cart_page(logged_in_page):
    """Give the test a ready-to-use CartPage on the logged-in tab."""
    # Same authenticated tab as shop_page, so actions flow shop -> cart.
    return CartPage(logged_in_page)


@pytest.fixture
def checkout_page(logged_in_page):
    """Give the test a ready-to-use CheckoutPage on the logged-in tab."""
    return CheckoutPage(logged_in_page)


@pytest.fixture(scope="session")
def product_data():
    """Load product test data from tests/data/products.json.

    `scope="session"` means the JSON is read just once per test run and shared
    by every test, instead of being re-read for each one.
    """
    # Build an OS-independent path to the data file next to this conftest.
    data_file = Path(__file__).parent / "data" / "products.json"
    # Read the file and parse the JSON text into a Python dict.
    return json.loads(data_file.read_text(encoding="utf-8"))


@pytest.fixture
def billing_details():
    """Return unique, valid billing data (unique email per run).

    Function scope (the default) means every test gets a FRESH dict. The epoch
    timestamp makes the email unique so repeated real checkouts never collide.
    """
    unique = int(time.time())  # seconds since 1970 — different on each run
    # A dict (key -> value); the test passes it to CheckoutPage.fill_billing().
    return {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": f"jane.doe.{unique}@example.com",
        "phone": "5551234567",
        "address": "123 Test Street",
        "city": "Testville",
        "state": "California",
        "zip": "90210",
    }
