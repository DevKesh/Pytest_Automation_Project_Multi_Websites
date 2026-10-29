"""E2E Test 1: Browse and search the Nova Shop catalogue."""

import pytest
from playwright.sync_api import expect

from config import BASE_URL
from pages.shop_page import ShopPage


@pytest.mark.smoke
def test_shop_lists_all_products(shop_page: ShopPage, product_data):
    # After login we are already on the products page.
    expect(shop_page.page).to_have_url(f"{BASE_URL}/shop/products")
    assert shop_page.total_products() == product_data["total_products"]


@pytest.mark.regression
def test_search_filters_catalogue(shop_page: ShopPage, product_data):
    target = product_data["products"][0]["name"]  # Aurora Wireless Headphones
    shop_page.search("Aurora")
    expect(shop_page.product_card(target)).to_be_visible()
    assert shop_page.total_products() == 1
