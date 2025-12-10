@allure.label.epic:RTP
@allure.label.feature:Debtor Activation
Feature: A Debtor Service Providers activates a debtor

  @allure.label.story:Happy Path
  @happy_path @authentication @activation
  Scenario: A debtor Service Provider activates a debtor
    Given the debtor Service Provider is authenticated
    And the debtor A has fiscal code random
    When the debtor Service Provider activates the debtor A
    Then the debtor A is activated

  @allure.label.story:Already Activated
  @unhappy_path @authentication @activation
  Scenario: A debtor Service Provider tries to activates a debtor 2 times, failing the second attempt
    Given the debtor Service Provider is authenticated
    And the debtor A has fiscal code random
    And the debtor Service Provider activated the debtor A
    When the debtor Service Provider tries to activate the debtor A
    Then the activation fails because debtor A is already activated

  @allure.label.story:Wrong Credentials
  @unhappy_path @authentication @activation
  Scenario: A Service Provider tries to activates a debtor without having the correct credentials
    Given the debtor A has fiscal code random
    And the debtor Service Provider is unauthenticated
    When the debtor Service Provider tries to activate the debtor A
    Then the activation fails because the Service Provider has wrong credentials
