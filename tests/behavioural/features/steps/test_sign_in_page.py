from behave import given, when, then

from tests.behavioural.features.steps.common import is_element_present_by_id


@given('I go to the sign-in page')
def step_impl_go_to_sign_in_page(context):
    context.browser.visit('/sign-in/')


@when('I enter my credentials')
def step_impl_enter_credentials(context):
    context.browser.find_by_id('username').send_keys('madpenguinxxx@linux.co.uk')
    context.browser.find_by_id('password').send_keys('Gizmo007!')


@when('I click sign-in')
def step_impl_click_sign_in(context):
    context.browser.find_by_id('SIGN_IN_BUTTON').click()


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
