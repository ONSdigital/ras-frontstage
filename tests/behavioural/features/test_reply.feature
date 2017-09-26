Feature: Test the replies

  Background: User logged in
    Given I am already logged in

  Scenario: User replies to a message from BRES
    Given I have received a message from BRES
    And I go to the inbox tab
    When I open the internal message
    Then I reply to a BRES message
    And The confirmation sent page opens

  Scenario: User sends an empty reply
    Given I have received a message from BRES
    And I go to the inbox tab
    When I open the internal message
    Then I send an empty reply
    And I should receive an empty reply error

  Scenario: User sends reply to long
    Given I have received a message from BRES
    And I go to the inbox tab
    When I open the internal message
    Then I send a reply that's too long
    And I should receive a reply too long error