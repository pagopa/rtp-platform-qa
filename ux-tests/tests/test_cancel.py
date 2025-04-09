import allure
from playwright.sync_api import expect
from test_submission import test_rtp_form_submission


@allure.feature('RTP Submission')
@allure.story('RTP cancellation through web page')
@allure.title('RTP form cancellation test')
def test_rtp_form_cancellation(page):
    test_rtp_form_submission(page)

    page.click('button:has-text("Cancella richiesta")')

    modal = page.get_by_role("dialog", name="Vuoi cancellare la richiesta?")
    expect(modal).to_be_visible()

    modal.locator('button:has-text("Cancella richiesta")').click()

    cancellation_msg = page.locator('text=La richiesta è stata cancellata')
    expect(cancellation_msg).to_be_visible()
