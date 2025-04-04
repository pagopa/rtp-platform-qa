Feature: A Creditor Service Provider can cancel a Request to Pay

  Background:
    Given the debtor A has fiscal code random
    And the debtor Service Provider is authenticated
    And the debtor Service Provider activated the debtor A
    And the creditor Service Provider is authenticated

  @happy_path @authentication @send @cancel
  Scenario: Successfully cancel a Request to Pay
    Given the creditor Service Provider sent an RTP to the debtor A
    When the creditor Service send a cancellation request for the RTP
    Then the RTP is cancelled

  @unhappy_path @authentication @send @cancel
  Scenario: Attempt to cancel an already cancelled RTP
    Given the creditor Service Provider sent an RTP to the debtor A
    And the creditor Service sent a cancellation request for the RTP
    When the creditor Service send another cancellation request for the RTP
    Then the RTP is already cancelled

  @unhappy_path @authentication @send @cancel
  Scenario: Attempt to cancel a non-existing RTP
    Given the creditor Service Provider sent an RTP to the debtor A
    When the creditor Service Provider send a cancellation request for a non-existing RTP
    Then the RTP is not found
