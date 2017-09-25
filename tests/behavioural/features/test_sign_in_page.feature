Feature: Open the sign in page

  Scenario: User signs in
    Given I go to the sign-in page
    And I enter my credentials
    When I click sign-in
    Then I should see the surveys page

  Scenario: User signs out
    Given I am already logged in
    When I click sign-out
    Then I should return to the sign in page

  Scenario: User signs in with incorrect credentials
    Given I go to the sign-in page
    And I enter the incorrect credentials
    When I click sign-in
    Then I should receive a sign-in error