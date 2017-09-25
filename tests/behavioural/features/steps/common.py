from behave import given, when
from selenium.common.exceptions import NoSuchElementException


@given('I enter my credentials')
def step_impl_enter_credentials(context):
    context.browser.find_by_id('username').send_keys('tejas.patel@ons.gov.uk')
    context.browser.find_by_id('password').send_keys('Gizmo007!')


@when('I click sign-in')
def step_impl_click_sign_in(context):
    context.browser.find_by_id('SIGN_IN_BUTTON').click()


# Need an authenticated user
@given('I am already logged in')
def step_impl_go_to_sign_in_page(context):
    context.browser.visit('/sign-in/')
    step_impl_enter_credentials(context)
    step_impl_click_sign_in(context)


def is_element_present_by_id(context, element_id):
    try:
        context.browser.find_by_id(element_id)
    except NoSuchElementException:
        return False
    return True
