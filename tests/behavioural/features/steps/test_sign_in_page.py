from behave import given, when, then


@given('I go to the sign-in page')
def step_impl_go_to_sign_in_page(context):
    context.browser.visit('/sign-in/')


@then('the title should be something')
def step_impl_verify_title(context):
    assert context.browser.find_by_id('sign-in-details')


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


@when('I click sign-out')
def step_impl_click_sign_out(context):
    context.browser.find_by_link_text('Sign out').click()


@then('I should return to the sign in page')
def step_impl_signed_out(context):
    context.browser.visit('/sign-in/')