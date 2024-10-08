from playwright.sync_api import sync_playwright


def test_navigation():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto('http://example.com')
        page.click('text=More information...')
        assert page.url == 'https://www.iana.org/help/example-domains'
        browser.close()
