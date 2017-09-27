Feature: Test the drafts

  Background: User logged in
    Given I am already logged in

  Scenario: User opens up a draft
    Given there is a draft
    When I open a draft with the read message link
    Then the draft contains some text

  Scenario: User opens up a draft using subject link
    Given there is a draft
    When I open a draft
    Then the draft contains some text

  Scenario: User opens up a draft with no subject
    Given there is a draft with no subject
    When I open a draft with the read message link
    Then the draft contains some text

  Scenario: User opens up a draft with no body
    Given there is a draft with no body
    When I open a draft with no body
    Then the draft contains some text

  Scenario: User opens up a draft with empty fields
    Given there is a draft with empty fields
    When I open a draft with the read message link
    Then the draft contains some text
