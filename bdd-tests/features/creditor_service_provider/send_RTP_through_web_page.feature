@allure.label.parentSuite:bdd-tests
@allure.label.suite:RTP
@allure.label.subSuite:RTP_Web_Sending

@allure.label.epic:RTP
@allure.label.feature:RTP_Web_Sending
Feature: A Creditor Service Provider sends an RTP through web page

  Background: the Creditor is on the web page

  @allure.label.story:Successful_Send
  @happy_path
  Scenario: Successful login
    Given the Creditor insert RTP data
    When the Creditor presses send button
    Then a confirmation messages shows confirming the operation
