"""Login page object for Nova Shop.

Each page object simply holds the Playwright `page` and its locators, and
exposes small action methods. Locators use `get_by_test_id` (the app's
`data-testid` attributes), which is the most stable selector strategy.
"""

from playwright.sync_api import Page

from config import BASE_URL


class LoginPage:
    def __init__(self, page: Page):
        # Store the Playwright tab so every method acts on the same page.
        self.page = page
        # Locators for the three login-form elements, found by data-testid.
        self.username = page.get_by_test_id("username")
        self.password = page.get_by_test_id("password")
        self.login_button = page.get_by_test_id("login-button")

    def load(self):
        """Open the shop landing page, which shows the login form."""
        # goto(...) navigates the tab to an absolute URL built from config.
        self.page.goto(f"{BASE_URL}/shop")

    def login(self, username: str, password: str):
        """Fill credentials, submit, and wait for the products page to load."""
        # .fill(...) types the value into each input (auto-waits for it first).
        self.username.fill(username)
        self.password.fill(password)
        # .click() submits the form.
        self.login_button.click()
        # Playwright auto-waits for the SPA to route to the products page,
        # so the next action only runs once login has actually succeeded.
        self.page.wait_for_url("**/shop/products")
