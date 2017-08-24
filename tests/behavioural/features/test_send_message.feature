Feature: Test send message




  Scenario: User visits the secure-message page
    Given I am already logged in
    When I go to the secure-message page
    When I click create message
    Then The create message page will open

  Scenario: User sends a message
    Given I am already logged in
    When I am on the create message page
    When I have a message to send
    Then The confirmation sent page opens

