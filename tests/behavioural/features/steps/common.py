from behave import given, when, then
from selenium.common.exceptions import NoSuchElementException


@given('I am already logged in')
def step_impl_go_to_sign_in_page(context):
    context.browser.visit('/sign-in/')
    context.browser.find_by_id('username').send_keys('madpenguinxxx@linux.co.uk')
    context.browser.find_by_id('password').send_keys('Gizmo007!')
    context.browser.find_by_id('SIGN_IN_BUTTON').click()


def is_element_present_by_id(context, element_id):
    try:
        context.browser.find_by_id(element_id)
    except NoSuchElementException:
        return False
    return True
