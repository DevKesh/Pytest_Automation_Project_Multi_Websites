"""E2E Test 5: Complete a full checkout and place a real order."""

import pytest
from playwright.sync_api import expect

from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage
from pages.shop_page import ShopPage


@pytest.mark.checkout
@pytest.mark.regression
def test_complete_checkout_places_order(
    shop_page: ShopPage,
    cart_page: CartPage,
    checkout_page: CheckoutPage,
    billing_details,
    product_data,
):
    index = product_data["checkout_product_index"]

    shop_page.add_to_cart(index)
    expect(shop_page.cart_badge).to_have_text("1")
    shop_page.open_cart()

    cart_page.checkout()
    checkout_page.fill_billing(billing_details)
    checkout_page.fill_payment()
    checkout_page.place_order()

    # The order-success banner shows a generated order id like "NS-4680871".
    expect(checkout_page.order_success).to_be_visible()
    expect(checkout_page.order_id).to_contain_text("NS-")
