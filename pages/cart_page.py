"""Cart page object — view items, change quantity, remove, and checkout."""

from playwright.sync_api import Page

from config import BASE_URL


class CartPage:
    def __init__(self, page: Page):
        # Store the Playwright tab so every method acts on the same page.
        self.page = page
        # `cart_items` matches ALL line-item rows (a multi-element locator).
        self.cart_items = page.get_by_test_id("cart-item")
        self.checkout_button = page.get_by_test_id("checkout-button")

    def load(self):
        """Open the cart page directly."""
        # goto(...) navigates straight to the cart URL.
        self.page.goto(f"{BASE_URL}/shop/cart")

    def cart_item(self, name: str):
        """Return the cart line item that contains the given product name."""
        # .filter(has_text=...) picks the single row matching this product.
        return self.cart_items.filter(has_text=name)

    def item_count(self) -> int:
        """Return the number of line items in the cart."""
        # .count() = how many rows the locator matches right now.
        return self.cart_items.count()

    def quantity_of(self, name: str):
        """Return the quantity locator for a named line item."""
        # First find the row, then the qty element inside it (nested locator).
        return self.cart_item(name).get_by_test_id("item-qty")

    def increase_quantity(self, name: str, times: int = 1):
        """Click the '+' stepper `times` times for a line item."""
        # Loop so the caller can bump the quantity by any amount in one call.
        for _ in range(times):
            self.cart_item(name).get_by_test_id("increase-qty").click()

    def remove_item(self, name: str):
        """Remove a line item from the cart."""
        # Click the row's remove ('x') button; the row disappears from the DOM.
        self.cart_item(name).get_by_test_id("remove-item").click()

    def checkout(self):
        """Proceed to the checkout page."""
        self.checkout_button.click()
        # Wait for the checkout route so the CheckoutPage form is ready.
        self.page.wait_for_url("**/checkout")
