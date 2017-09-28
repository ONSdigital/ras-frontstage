Feature: Open the surveys page

  Background: User logged in
    Given I am already logged in

  Scenario: User visits the history page
    When I go to the history tab
    Then I should see the Access survey button

  Scenario: User opens the history tab
    Given I am on the history page
    When I click the Access survey button
    Then I should see the access survey page


