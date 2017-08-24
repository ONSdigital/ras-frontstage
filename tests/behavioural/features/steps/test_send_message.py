from behave import given, when, then


@when('I go to the secure-message page')
def step_impl_go_to_secure_message_create_page(context):
    context.browser.visit('/secure-message/messages/')


@when('I click create message')
def step_impl_click_create_message(context):
    context.browser.find_by_link_text('Create a message').click()


@then('The create message page will open')
def step_impl_open_create_message_page(context):
    context.browser.find_by_id('send-message')


@when('I am on the create message page')
def step_impl_open_create_message_page(context):
    context.browser.visit('/secure-message/create-message/')


@when('I have a message to send')
def step_impl_add_text_to_subject_and_body(context):
    context.browser.find_by_id('secure-message-subject').send_keys('Test Subject')
    context.browser.find_by_id('secure-message-body').send_keys('Test Body')
    context.browser.find_by_id('send-message').click()


@then('The confirmation sent page opens')
def step_impl_open_confirmation_page(context):
    context.browser.find_by_id('message-sent')
