Feature: Send RTP feature

  Background: the Ente Creditore is on the web page

  @happy_path
  Scenario: Successful login
    Given the Ente Creditore insert RTP data
    When the Ente Creditore presses send button
    Then a confirmation messages shows confirming the operation
