"""E2E Test 2: Add products to the cart (data-driven with parametrize)."""

import pytest
from playwright.sync_api import expect

from pages.cart_page import CartPage
from pages.shop_page import ShopPage


@pytest.mark.smoke
@pytest.mark.parametrize(
    "index, product_name",
    [
        (1, "Aurora Wireless Headphones"),
        (2, "Pulse Smartwatch"),
    ],
)
def test_add_single_product_to_cart(shop_page: ShopPage, cart_page: CartPage, index, product_name):
    shop_page.add_to_cart(index)
    expect(shop_page.cart_badge).to_have_text("1")
    shop_page.open_cart()

    expect(cart_page.cart_items).to_have_count(1)
    expect(cart_page.cart_item(product_name)).to_be_visible()
