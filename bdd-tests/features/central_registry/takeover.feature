@allure.label.epic:RTP
@allure.label.feature:Debtor_Activation_Takeover
Feature: A Debtor Service Provider performs takeover of an existing activation

  @allure.label.story:Successful_Takeover
  @happy_path @authentication @activation @takeover
  Scenario: A debtor Service Provider successfully takes over an activation from another provider
    Given the debtor Service Provider is authenticated
    And the debtor Service Provider B is authenticated
    And the debtor A has fiscal code random
    And the debtor Service Provider activated the debtor A
    When the debtor Service Provider B attempts to activate the debtor A
    Then the activation fails because debtor A is already activated
    When the debtor Service Provider B performs takeover for debtor A
    Then the debtor A is now managed by Service Provider B

  @allure.label.story:Invalid_OTP
  @unhappy_path @authentication @activation @takeover
  Scenario: Takeover fails with invalid OTP
    Given the debtor Service Provider is authenticated
    And the debtor Service Provider B is authenticated
    And the debtor A has fiscal code random
    And the debtor Service Provider activated the debtor A
    When the debtor Service Provider B tries takeover with invalid OTP for debtor A
    Then the takeover fails because of invalid OTP

  @allure.label.story:Unauthenticated_Provider
  @unhappy_path @authentication @activation @takeover
  Scenario: Takeover fails without authentication
    Given the debtor Service Provider is authenticated
    And the debtor A has fiscal code random
    And the debtor Service Provider activated the debtor A
    And the debtor Service Provider B is unauthenticated
    When the unauthenticated debtor Service Provider B attempts takeover for debtor A
    Then the takeover fails because the Service Provider has wrong credentials
