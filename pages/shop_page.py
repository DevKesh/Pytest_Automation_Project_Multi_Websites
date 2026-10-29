"""Products (shop) page object — browse, search and add to cart."""

from playwright.sync_api import Page

from config import BASE_URL


class ShopPage:
    def __init__(self, page: Page):
        # Store the Playwright tab so every method acts on the same page.
        self.page = page
        # `product_cards` matches ALL product cards (a multi-element locator).
        self.product_cards = page.get_by_test_id("product-card")
        self.search_input = page.get_by_test_id("search-input")
        self.sort_select = page.get_by_test_id("sort-select")
        self.cart_link = page.get_by_test_id("cart-link")
        # Header badge showing the number of items in the cart.
        self.cart_badge = page.get_by_test_id("cart-badge")

    def load(self):
        """Open the products page directly (requires an active session)."""
        # goto(...) navigates straight to the catalogue URL.
        self.page.goto(f"{BASE_URL}/shop/products")

    def product_card(self, name: str):
        """Return the product card that contains the given product name."""
        # .filter(has_text=...) narrows the many cards down to the one whose
        # text contains `name`, returning a single-element locator.
        return self.product_cards.filter(has_text=name)

    def total_products(self) -> int:
        """Return how many product cards are currently shown."""
        # .count() returns the number of elements the locator matches right now.
        return self.product_cards.count()

    def search(self, term: str):
        """Filter the catalogue by typing in the search box."""
        # Typing filters the list client-side (React re-renders the cards).
        self.search_input.fill(term)

    def add_to_cart(self, index: int):
        """Add the product at position `index` (1-based) via its test id."""
        # Each add button is tagged add-to-cart-p1, add-to-cart-p2, ... so we
        # build the test id from the index and click it.
        self.page.get_by_test_id(f"add-to-cart-p{index}").click()

    def open_cart(self):
        """Go to the cart page via the header cart link."""
        self.cart_link.click()
        # Wait for the cart route so the CartPage reads a fully-loaded list.
        self.page.wait_for_url("**/shop/cart")
