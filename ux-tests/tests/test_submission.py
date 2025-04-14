import re
from datetime import datetime

import allure
from playwright.sync_api import expect

from config.configuration import config
from config.configuration import secrets
from utils.dataset import generate_rtp_data

page_url = config.landing_page_path

@allure.feature('RTP Submission')
@allure.story('RTP submission though web page')
@allure.title('RTP form is filled and submitted')
def test_rtp_form_submission(page):
    rtp_data = generate_rtp_data()
    rtp_data['payer']['payerId'] = 'CPPRML60T46X000R'

    page.goto(page_url)
    expect(page).to_have_url(config.login_page_path)

    page.fill('input[name="username"]', secrets.webpage.username)
    page.fill('input[name="password"]', secrets.webpage.password)
    page.click('button[id=":r2:"]')

    expect(page).to_have_url(page_url)

    page.fill('input[name="payee.name"]', rtp_data['payee']['name'])
    page.fill('input[name="payee.payeeId"]', rtp_data['payee']['payeeId'])
    page.fill('input[name="payee.payTrxRef"]', rtp_data['paymentNotice']['noticeNumber'])

    page.fill('input[name="payer.name"]', rtp_data['payer']['payerId'])
    page.fill('input[name="payer.payerId"]', rtp_data['payer']['payerId'])

    page.fill('input[name="paymentNotice.noticeNumber"]', rtp_data['paymentNotice']['noticeNumber'])
    page.fill('input[name="paymentNotice.amount"]', str(rtp_data['paymentNotice']['amount']))
    page.fill('input[placeholder="DD/MM/YYYY"]',
              str(datetime.strptime(rtp_data['paymentNotice']['expiryDate'], '%Y-%m-%d').strftime('%d/%m/%Y')))
    page.fill('input[name="paymentNotice.subject"]', rtp_data['paymentNotice']['description'])
    page.fill('input[name="paymentNotice.description"]', rtp_data['paymentNotice']['description'])
    page.click('[type=submit]')

    # Check success message and URL
    message = page.locator('text=La richiesta è stata inviata con successo!')
    expect(message).to_be_visible()
    base_url = re.escape(config.landing_page_path.split('/')[0] + '//' + config.landing_page_path.split('/')[2])
    uuidv4_pattern = f'[0-9a-f]{{8}}-[0-9a-f]{{4}}-4[0-9a-f]{{3}}-[89ab][0-9a-f]{{3}}-[0-9a-f]{{12}}'
    assert (re.search(f'{base_url}/{uuidv4_pattern}/ok', page.url))
    resource_id_from_url = re.search(uuidv4_pattern, page.url).group(0)
    resource_id = page.locator(f'text={resource_id_from_url}')
    expect(resource_id).to_be_visible()


@allure.feature('RTP Submission')
@allure.story('Input validation')
@allure.title('Whitespaces is allowed in description and company name field')
def test_whitespace_and_capitalization_in_description_and_payee_company_name(page):
    page.goto(page_url)
    expect(page).to_have_url(config.login_page_path)

    page.fill('input[name="username"]', secrets.webpage.username)
    page.fill('input[name="password"]', secrets.webpage.password)
    page.click('button[id=":r2:"]')

    expect(page).to_have_url(page_url)

    description = 'Description with spaces'
    payee_company_name = 'Payee company name with spaces'

    page.fill('input[name="paymentNotice.description"]', description)
    filled_description = page.locator('input[name="paymentNotice.description"]')
    assert filled_description.input_value() == description.upper()

    page.fill('input[name="payee.name"]', payee_company_name)
    filled_description = page.locator('input[name="payee.name"]')
    assert filled_description.input_value() == payee_company_name.upper()
