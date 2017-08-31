Feature: Open the surveys page



  Scenario: User visits the history page
    Given I am already logged in
    When I go to the history tab
    Then I should see the Access survey button

  @ignore
  Scenario: User opens the history tab
    Given I am already logged in
    When I am on the history page
    When I click the Access survey button
    Then I should see the access survey page


