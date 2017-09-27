Feature: Test send message

  Background: User logged in
    Given I am already logged in

  Scenario: User visits the secure-message page
    Given I go to the secure-message page
    When I click create message
    Then The create message page will open

  Scenario: User sends a message
    Given I am on the create message page
    And I have a message to send
    When I send a message
    Then The confirmation sent page opens

  Scenario: User sends a message with non alpha characters
    Given I am on the create message page
    And I have a message with non alpha characters
    When I send a message
    Then The confirmation sent page opens

  Scenario: User sends a message with empty subject and body
    Given I am on the create message page
    And I have a message with empty fields
    When I send a message
    Then I should receive subject and body empty errors

  Scenario: User sends a message with empty subject
    Given I am on the create message page
    And I have a message with an empty subject
    When I send a message
    Then I should receive a subject empty error

  Scenario: User sends a message with empty body
    Given I am on the create message page
    And I have a message with an empty body
    When I send a message
    Then I should receive a body empty error

  Scenario: User sends a message with subject too long
    Given I am on the create message page
    And I have a message with subject too long
    When I send a message
    Then the confirmation sent page opens

  Scenario: User sends a message with body too long
    Given I am on the create message page
    And I have a message with body too long
    When I send a message
    Then I should receive a body too long error

  Scenario: User sends a message with subject and body too long
    Given I am on the create message page
    And I have a message with subject and body too long
    When I send a message
    Then I should receive subject and body too long errors

  Scenario: User receives a message from BRES
    Given I have received a message from BRES
    And I go to the inbox tab
    When I open the internal message
    Then I should see a reply message


