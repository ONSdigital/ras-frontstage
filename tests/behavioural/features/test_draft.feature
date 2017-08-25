Feature: Test The drafts



  Scenario: User opens up a draft
    Given I am already logged in
    And there is a draft
    When I open a draft
    Then the draft contains some text

