from behave import given, when, then


@when('I go to the history tab')
def step_impl_open_history_tab(context):
    context.browser.find_by_id('SURVEY_HISTORY_TAB').click()


@then('I should see the Access survey button')
def step_impl_find_button_in_history_tab(context):
    context.browser.find_by_id('ACCESS_SURVEY_BUTTON_1')


@when('I am on the history page')
def step_impl_open_history_page(context):
    context.browser.visit('/surveys/history/')


@when('I click the Access survey button')
def step_impl_click_access_survey_button(context):
    context.browser.find_by_id('ACCESS_SURVEY_BUTTON_1').click()


@then('I should see the access survey page')
def step_impl_open_access_surveys_page(context):
    context.browser.find_by_id('download-survey-button')
    context.browser.find_by_id('upload-survey-button')
