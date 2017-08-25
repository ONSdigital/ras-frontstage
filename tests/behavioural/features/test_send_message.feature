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

  Scenario: User receives a message from BRES
    Given I am already logged in
    And I have received a message from BRES
    When I go to the inbox tab
    When I open the internal message
    Then I should see a reply message

  Scenario: User replies to a message from BRES
    Given I am already logged in
    And I have received a message from BRES
    When I go to the inbox tab
    When I open the internal message
    When I reply to a BRES message
    Then The confirmation sent page opens