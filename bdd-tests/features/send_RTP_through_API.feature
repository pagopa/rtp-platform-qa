Feature: Send RTP through API

  Background:
    Given the debtor A has fiscal code random

  @happy_path @authentication @send
  Scenario: An authenticated Service Provider can send an RTP to an activated debtor
    Given the Service Provider is authenticated
    When the Service Provider sends an RTP to the debtor A
    Then the RTP is created correctly
    And the debtor A receives the RTP

  @unhappy_path @authentication @send
  Scenario: An authenticated Service Provider cannot send an RTP to an activated debtor
    Given the Service Provider is unauthenticated
    When the Service Provider sends an RTP to the debtor A
    Then the RTP is not created because the Service Provider is not authenticated
