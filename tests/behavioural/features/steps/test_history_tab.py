from behave import when, then, given
from tests.behavioural.features.steps.common import is_element_present_by_id


@when('I go to the history tab')
def step_impl_open_history_tab(context):
    context.browser.find_by_id('SURVEY_HISTORY_TAB').click()


@then('I should see the Access survey button')
def step_impl_find_button_in_history_tab(context):
    assert is_element_present_by_id(context, 'ACCESS_SURVEY_BUTTON_1')


@given('I am on the history page')
def step_impl_open_history_page(context):
    context.browser.visit('/surveys/history')


@when('I click the Access survey button')
def step_impl_click_access_survey_button(context):
    context.browser.find_by_id('ACCESS_SURVEY_BUTTON_1').click()


@then('I should see the access survey page')
def step_impl_open_access_surveys_page(context):
    assert is_element_present_by_id(context, 'download-survey-button')
    assert is_element_present_by_id(context, 'upload-survey-button')
