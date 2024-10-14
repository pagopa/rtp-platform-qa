import pytest
from playwright.sync_api import sync_playwright

from config.configuration import config


@pytest.mark.landing_page
def test_landing_page():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(config.landing_page_path)
        expected_text = 'Welcome to React'

        assert expected_text in page.content(), f"'{expected_text}' not found on the page!"
        browser.close()
