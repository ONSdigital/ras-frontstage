Feature: Open the sign in page



  Scenario: User visits the sign-in page
    Given I go to the sign-in page
    Then the title should be something


  Scenario: User signs in
    Given I go to the sign-in page
    When I enter my credentials
    When I click sign-in
    Then I should see the surveys page


  Scenario: User signs out
    Given I am already logged in
    When I click sign-out
    Then I should return to the sign in page

