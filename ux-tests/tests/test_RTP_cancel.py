import allure
from playwright.sync_api import expect
from test_RTP_submission import test_rtp_form_submission

_CANCEL_MODT_BUTTON = 'button:has-text("Cancella MODT v3.2")'
_CANCEL_PAID_BUTTON = 'button:has-text("Cancella PAID v3.2")'
_CONFIRM_CANCEL_BUTTON = 'button:has-text("Cancella richiesta")'
_DIALOG_NAME = "Vuoi cancellare la richiesta?"
_DIALOG_DESCRIPTION = "Proseguendo, la richiesta di pagamento appena creata verrà cancellata."
_SUCCESS_MESSAGE = "La richiesta è stata cancellata"


def _assert_cancel_modal_and_confirm(page, trigger_button_selector: str):
    """Open the cancellation modal via the given button, assert its content and confirm."""
    page.click(trigger_button_selector)

    modal = page.get_by_role("dialog", name=_DIALOG_NAME)
    expect(modal).to_be_visible()
    expect(modal.locator(f"text={_DIALOG_NAME}")).to_be_visible()
    expect(modal.locator(f"text={_DIALOG_DESCRIPTION}")).to_be_visible()

    modal.locator(_CONFIRM_CANCEL_BUTTON).click()

    expect(page.locator(f"text={_SUCCESS_MESSAGE}")).to_be_visible()


@allure.feature("RTP Cancellation")
@allure.story("RTP cancellation through web page")
@allure.title("RTP form cancellation with reason MODT")
def test_rtp_form_cancellation_modt(page):
    test_rtp_form_submission(page)
    _assert_cancel_modal_and_confirm(page, _CANCEL_MODT_BUTTON)


@allure.feature("RTP Cancellation")
@allure.story("RTP cancellation through web page")
@allure.title("RTP form cancellation with reason PAID")
def test_rtp_form_cancellation_paid(page):
    test_rtp_form_submission(page)
    _assert_cancel_modal_and_confirm(page, _CANCEL_PAID_BUTTON)
