from datetime import datetime

import allure
import pytest
from playwright.sync_api import expect
from playwright.sync_api import sync_playwright

from config.configuration import config
from utils.dataset import generate_rtp_data

page_url = config.landing_page_path


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


@allure.feature('RTP Submission')
@allure.story('RTP submission though web page')
@allure.title('RTP form is filled and submitted')
def test_rtp_form_submission(page):
    rtp_data = generate_rtp_data()

    page.goto(page_url)

    page.fill('input[id="noticeNumber"]', rtp_data['paymentNotice']['noticeNumber'])
    page.fill('input[id="amount"]', str(rtp_data['paymentNotice']['amount']))
    page.fill('input[id="description"]', rtp_data['paymentNotice']['description'])
    page.fill('input[placeholder="DD/MM/YYYY"]', str(datetime.strptime(rtp_data['paymentNotice']['expiryDate'], '%Y-%m-%d').strftime('%d/%m/%Y')))
    page.fill('input[id="payeeCompanyName"]', rtp_data['payee']['name'])
    page.fill('input[id="payee"]', rtp_data['payee']['payeeId'])
    page.fill('input[id="payerId"]', rtp_data['payer']['payerId'])

    page.click('button[id="paymentNoticeButtonContinue"]')

    popup_message = page.locator("div[role='dialog'] p.MuiDialogContentText-root")
    expect(popup_message).to_be_visible()
    expect(popup_message).to_have_text('Request to pay created successfully!')


@allure.feature('RTP Submission')
@allure.story('Input validation')
@allure.title('Comma is not allowed in amount field')
def test_comma_not_allowed(page):
    rtp_data = generate_rtp_data()

    page.goto(page_url)

    page.fill('input[id="noticeNumber"]', rtp_data['paymentNotice']['noticeNumber'])
    page.fill('input[id="amount"]', str(rtp_data['paymentNotice']['amount']).replace('.', ','))
    page.fill('input[id="description"]', rtp_data['paymentNotice']['description'])
    page.fill('input[placeholder="DD/MM/YYYY"]', rtp_data['paymentNotice']['expiryDate'])
    page.fill('input[id="payeeCompanyName"]', rtp_data['payee']['name'])
    page.fill('input[id="payee"]', rtp_data['payee']['payeeId'])
    page.fill('input[id="payerId"]', rtp_data['payer']['payerId'])

    validation_message = page.locator('#amount-helper-text')
    expect(validation_message).to_have_text('Enter a valid number. To separate decimals use the dot (.)')

    page.click('button[id="paymentNoticeButtonContinue"]')
    popup_message = page.locator("div[role='dialog'] p.MuiDialogContentText-root")
    expect(popup_message).not_to_be_visible()


@allure.feature('RTP Submission')
@allure.story('Input validation')
@allure.title('Whitespaces is allowed in description and company name field')
def test_whitespace_allowed_in_description_and_payee_company_name(page):
    page.goto(page_url)

    description = 'Description with spaces'
    payee_company_name = 'Payee company name with spaces'

    page.fill('input[id="description"]', description)
    filled_description = page.locator('input[id="description"]')
    assert filled_description.input_value() == description

    page.fill('input[id="payeeCompanyName"]', payee_company_name)
    filled_description = page.locator('input[id="payeeCompanyName"]')
    assert filled_description.input_value() == payee_company_name
