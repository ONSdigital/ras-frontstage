from behave import given, when, then
from tests.behavioural.features.steps.common import is_element_present_by_id


@given('I go to the sign-in page')
def step_impl_go_to_sign_in_page(context):
    context.browser.visit('/sign-in/')


@then('I should see the surveys page')
def step_impl_see_sign_in_message(context):
    context.browser.visit('/surveys/')
    assert is_element_present_by_id(context, 'SURVEY_TODO_TAB')


@when('I click sign-out')
def step_impl_click_sign_out(context):
    context.browser.find_by_link_text('Sign out').click()


@then('I should return to the sign in page')
def step_impl_signed_out(context):
    context.browser.visit('/sign-in/')
    assert is_element_present_by_id(context, 'SIGN_IN_BUTTON')


@given('I enter the incorrect password')
def step_impl_incorrect_credentials(context):
    context.browser.find_by_id('username').send_keys('tejas.patel@ons.gov.uk')
    context.browser.find_by_id('password').send_keys('Gizmo7')


@given('I enter the incorrect email')
def step_impl_incorrect_credentials(context):
    context.browser.find_by_id('username').send_keys('tas.patel@ons.gov.uk')
    context.browser.find_by_id('password').send_keys('Gizmo007!')


@given('I enter the incorrect email and password')
def step_impl_incorrect_credentials(context):
    context.browser.find_by_id('username').send_keys('tas.patel@ons.gov.uk')
    context.browser.find_by_id('password').send_keys('Gizmo7')


@then('I should receive a sign-in error')
def step_impl_sign_in_error(context):
    context.browser.find_by_link_text('Please try again')
