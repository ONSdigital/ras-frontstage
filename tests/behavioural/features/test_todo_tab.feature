Feature: Open the surveys page



  Scenario: User visits the todo page
    Given I am already logged in
    When I go to the todo tab
    Then I should see the Access survey button

  Scenario: User opens the todo tab
    Given I am already logged in
    When I am on the todo page
    When I click the Access survey button
    Then I should see the access survey page


