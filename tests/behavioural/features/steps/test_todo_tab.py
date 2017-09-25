from behave import when, then

from tests.behavioural.features.steps.common import is_element_present_by_id


@when('I go to the todo tab')
def step_impl_open_todo_tab(context):
    context.browser.find_by_id('SURVEY_TODO_TAB').click()


@then('I should see the Access survey button')
def step_impl_find_button_in_todo_tab(context):
    assert is_element_present_by_id(context, 'ACCESS_SURVEY_BUTTON_1')


@when('I am on the todo page')
def step_impl_open_todo_page(context):
    context.browser.visit('/surveys/')


@when('I click the Access survey button')
def step_impl_click_access_survey_button(context):
    context.browser.find_by_id('ACCESS_SURVEY_BUTTON_1').click()


@then('I should see the access survey page')
def step_impl_open_access_surveys_page(context):
    assert is_element_present_by_id(context, 'download-survey-button')
    assert is_element_present_by_id(context, 'upload-survey-button')
