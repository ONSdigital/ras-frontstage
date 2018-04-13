from behave import given, when, then
from tests.behavioural.features.steps.common import is_element_present_by_id


@given('there is a draft')
def step_impl_create_draft(context):
    context.browser.visit('/secure-message/create-message')
    context.browser.find_by_id('secure-message-subject').send_keys('Test Subject')
    context.browser.find_by_id('secure-message-body').send_keys('Test Body')
    context.browser.find_by_id('draft').click()


@given('there is a draft with no subject')
def step_impl_create_draft_no_subject(context):
    context.browser.visit('/secure-message/create-message')
    context.browser.find_by_id('secure-message-body').send_keys('Test Body')
    context.browser.find_by_id('draft').click()


@given('there is a draft with no body')
def step_impl_create_draft_no_body(context):
    context.browser.visit('/secure-message/create-message')
    context.browser.find_by_id('secure-message-subject').send_keys('Test Subject No Body')
    context.browser.find_by_id('draft').click()


@given('there is a draft with empty fields')
def step_impl_create_draft_empty_fields(context):
    context.browser.visit('/secure-message/create-message')
    context.browser.find_by_id('draft').click()


@when('I open a draft')
def step_impl_go_to_draft_message(context):
    context.browser.visit('/secure-message/messages/DRAFT')
    context.browser.find_by_link_text('Test Subject').click()


@when('I open a draft with no body')
def step_impl_go_to_draft_message_no_body(context):
    context.browser.visit('/secure-message/messages/DRAFT')
    context.browser.find_by_link_text('Test Subject No Body').click()


@when('I open a draft with the read message link')
def step_impl_go_to_draft_message_via_message_link(context):
    context.browser.visit('/secure-message/messages/DRAFT')
    context.browser.find_by_id('read-message-link-1').click()


@when('I save a message')
def step_impl_send_a_message(context):
    context.browser.find_by_id('draft').click()


@then('the draft contains some text')
def step_impl_draft_page(context):
    assert is_element_present_by_id(context, 'secure-message-subject')
    assert is_element_present_by_id(context, 'secure-message-body')


@then('The confirmation save page opens')
def step_impl_open_confirmation_page(context):
    assert is_element_present_by_id(context, 'inbox-link')
