@allure.label.epic:RTP
@allure.label.feature:RTP_Sending
Feature: A Creditor Service Provider sends an RTP through API

  Background:
    Given the debtor A has fiscal code random
    And the debtor Service Provider is authenticated

  @allure.label.story:Successful_Send
  @happy_path @authentication @send
  Scenario: An authenticated creditor Service Provider can send an RTP to an activated debtor
    Given the creditor Service Provider is authenticated
    And the debtor Service Provider activated the debtor A
    When the creditor Service Provider sends an RTP to the debtor A
    Then the RTP is created correctly
    And the debtor A receives the RTP

  @allure.label.story:Unauthenticated_Creditor
  @unhappy_path @authentication @send
  Scenario: An authenticated Service Provider cannot send an RTP to an activated debtor
    Given the creditor Service Provider is authenticated
    And the debtor Service Provider activated the debtor A
    When the creditor Service Provider is unauthenticated
    And the creditor Service Provider sends an RTP to the debtor A
    Then the RTP is not created because the Service Provider is not authenticated

  @allure.label.story:Debtor_Not_Activated
  @unhappy_path @authentication @send
  Scenario: An authenticated Service Provider cannot send an RTP to an unactivated debtor
    Given the creditor Service Provider is authenticated
    When the creditor Service Provider sends an RTP to the debtor A
    Then the RTP is not created because the debtor is not activated

  @allure.label.story:Debtor_Provider_Forbidden
  @unhappy_path @authentication @send
  Scenario: A debtor Service Provider cannot send an RTP
    Given the debtor Service Provider activated the debtor A
    When the debtor Service Provider sends an RTP to the debtor A
    Then the RTP is not created because the debtor Service Provider cannot send an RTP
