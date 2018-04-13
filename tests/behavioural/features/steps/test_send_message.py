from behave import given, when, then
from tests.behavioural.features.steps.common import is_element_present_by_id, step_impl_body_too_long, step_impl_subject_too_long, \
    step_impl_subject_empty, step_impl_body_empty


@given('I go to the secure-message page')
def step_impl_go_to_secure_message_create_page(context):
    context.browser.visit('/secure-message/messages/')


@when('I click create message')
def step_impl_click_create_message(context):
    context.browser.find_by_link_text('Create a message').click()


@then('The create message page will open')
def step_impl_open_create_message_page(context):
    assert is_element_present_by_id(context, 'submit-btn')


@given('I have a message to send')
def step_impl_add_text_to_subject_and_body(context):
    context.browser.find_by_id('secure-message-subject').send_keys('Test Subject')
    context.browser.find_by_id('secure-message-body').send_keys('Test Body')


@given('I have a message with non alpha characters')
def step_impl_add_non_alpha_text_to_subject_and_body(context):
    context.browser.find_by_id('secure-message-subject').send_keys('[]!@%^&*()')
    context.browser.find_by_id('secure-message-body').send_keys('"?><:}{+_')


@given('I have a message with empty fields')
def step_impl_empty_subject_and_body(context):
    step_impl_subject_empty(context)
    step_impl_body_empty(context)


@given('I have a message with an empty subject')
def step_impl_create_msg_with_empty_subject(context):
    step_impl_subject_empty(context)
    context.browser.find_by_id('secure-message-body').send_keys('Subject empty')


@given('I have a message with an empty body')
def step_impl_create_msg_empty_body(context):
    context.browser.find_by_id('secure-message-subject').send_keys('Test body empty')
    step_impl_body_empty(context)


@given('I have a message with body too long')
def step_impl_add_text_to_body_too_long(context):
    context.browser.find_by_id('secure-message-subject').send_keys('Test')
    step_impl_body_too_long(context)


@given('I have a message with subject and body too long')
def step_impl_add_text_to_body_and_subject_too_long(context):
    step_impl_subject_too_long(context)
    step_impl_body_too_long(context)


@when('I send a message')
def step_impl_send_a_message(context):
    context.browser.find_by_id('submit-btn').click()


@then('The confirmation sent page opens')
def step_impl_open_confirmation_page(context):
    assert is_element_present_by_id(context, 'message-sent')


@then('The draft saved text should appear')
def step_impl_draft_saved_text_appears(context):
    assert is_element_present_by_id(context, 'message-sent')
