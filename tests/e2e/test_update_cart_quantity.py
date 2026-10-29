"""E2E Test 3: Increase an item's quantity using the +/- steppers."""

import pytest
from playwright.sync_api import expect

from pages.shop_page import ShopPage
from pages.cart_page import CartPage


@pytest.mark.regression
def test_increase_product_quantity(shop_page: ShopPage, cart_page: CartPage):
    product_name = "Aurora Wireless Headphones"

    shop_page.add_to_cart(1)
    expect(shop_page.cart_badge).to_have_text("1")
    shop_page.open_cart()

    # Quantity starts at 1; two increments -> 3.
    cart_page.increase_quantity(product_name, times=2)

    expect(cart_page.quantity_of(product_name)).to_have_text("3")

