Feature: Test The drafts



  Scenario: User opens up a draft
    Given I am already logged in
    And there is a draft
    When I open a draft
    Then the draft contains some text

  Scenario: User opens up a draft with no subject
    Given I am already logged in
    And there is a draft with no subject
    When I open a draft
    Then the draft contains some text

  Scenario: User opens up a draft with no body
    Given I am already logged in
    And there is a draft with no body
    When I open a draft
    Then the draft contains some text

  Scenario: User opens up a draft with empty fields
    Given I am already logged in
    And there is a draft with empty fields
    When I open a draft
    Then the draft contains some text
