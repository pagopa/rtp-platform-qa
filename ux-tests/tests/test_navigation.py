import pytest
from playwright.sync_api import sync_playwright

from utils.dataset import generate_rtp_data


@pytest.fixture(scope='session')
def playwright_browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(playwright_browser):
    page = playwright_browser.new_page()
    yield page
    page.close()


def test_rtp_form_submission(page):
    rtp_data = generate_rtp_data()

    page.goto('https://rtp.dev.cstar.pagopa.it/')

    page.fill('input[id="noticeNumber"]', rtp_data['noticeNumber'])
    page.fill('input[id="amount"]', rtp_data['amount'])
    page.fill('textarea[id="description"]', rtp_data['description'])
    page.fill('input[id="expiryDate"]', rtp_data['expiryDate'])
    page.fill('input[id="payee.name"]', rtp_data['payeeCompanyName'])
    page.fill('input[id="payee.id"]', rtp_data['payeeId'])
    page.fill('input[id="payerId"]', rtp_data['payerId'])

    page.click('button[id="submit"]')

    response_message = page.locator('#response')
    assert not response_message.text_content() == 'An error occurred: Failed to fetch'
    assert not response_message.text_content() == 'Error creating the request to pay.'
    assert response_message.text_content() == 'Request to pay created successfully!'
