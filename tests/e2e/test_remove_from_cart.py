"""E2E Test 4: Remove an item and verify the cart is empty."""

import pytest
from playwright.sync_api import expect

from pages.shop_page import ShopPage
from pages.cart_page import CartPage


@pytest.mark.regression
def test_remove_item_empties_cart(shop_page: ShopPage, cart_page: CartPage):
    product_name = "Aurora Wireless Headphones"

    shop_page.add_to_cart(1)
    expect(shop_page.cart_badge).to_have_text("1")
    shop_page.open_cart()
    expect(cart_page.cart_items).to_have_count(1)

    cart_page.remove_item(product_name)

    expect(cart_page.cart_items).to_have_count(0)

