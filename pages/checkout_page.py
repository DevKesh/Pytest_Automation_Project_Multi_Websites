"""Checkout page object — fill billing/payment and place the order."""

from playwright.sync_api import Page


class CheckoutPage:
    def __init__(self, page: Page):
        # Store the Playwright tab so every method can act on the same page.
        self.page = page
        # Locators for elements we assert on later. Defined once here so the
        # test ids live in a single place (easy to update if the app changes).
        self.place_order_button = page.get_by_test_id("place-order")
        self.order_success = page.get_by_test_id("order-success")
        self.order_id = page.get_by_test_id("order-id")

    def fill_billing(self, details: dict):
        """Fill the contact and shipping address fields from a dict.

        `details` is a dictionary (key → value). Each `details["..."]` reads the
        value for that key and types it into the matching field. The data comes
        from the `billing_details` fixture in conftest.py.
        """
        # get_by_test_id(...) finds the input by its data-testid attribute;
        # .fill(...) clears the field and types the value (auto-waits first).
        self.page.get_by_test_id("first-name").fill(details["first_name"])
        self.page.get_by_test_id("last-name").fill(details["last_name"])
        self.page.get_by_test_id("email").fill(details["email"])
        self.page.get_by_test_id("phone").fill(details["phone"])
        self.page.get_by_test_id("address").fill(details["address"])
        self.page.get_by_test_id("city").fill(details["city"])
        # `state` is a <select> dropdown, so we pick an option instead of typing.
        self.page.get_by_test_id("state").select_option(details["state"])
        self.page.get_by_test_id("zip").fill(details["zip"])

    def fill_payment(self):
        """Pick standard delivery + card payment and enter the test card."""
        # .check() ticks a radio button / checkbox (selects standard shipping).
        self.page.get_by_test_id("shipping-standard").check()
        # Selecting card payment reveals the card-detail fields below.
        self.page.get_by_test_id("payment-card").check()
        # Enter the approved Stripe-style test card the demo app accepts.
        self.page.get_by_test_id("card-name").fill("Test Cardholder")
        self.page.get_by_test_id("card-number").fill("4242 4242 4242 4242")
        self.page.get_by_test_id("card-expiry").fill("12/30")
        self.page.get_by_test_id("card-cvv").fill("123")
        # The terms checkbox is required before the order can be placed.
        self.page.get_by_test_id("accept-terms").check()

    def place_order(self):
        """Submit the order and wait for the confirmation page."""
        # Click submit, then wait for the SPA to route to the success page so
        # the next assertion runs only after navigation completes.
        self.place_order_button.click()
        self.page.wait_for_url("**/checkout/complete")
