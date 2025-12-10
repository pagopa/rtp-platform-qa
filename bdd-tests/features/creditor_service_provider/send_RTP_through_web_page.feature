@allure.label.epic:RTP
@allure.label.feature:RTP Web Sending
Feature: A Creditor Service Provider sends an RTP through web page

  Background: the Ente Creditore is on the web page

  @allure.label.story:Successful Send
  @happy_path
  Scenario: Successful login
    Given the Ente Creditore insert RTP data
    When the Ente Creditore presses send button
    Then a confirmation messages shows confirming the operation
