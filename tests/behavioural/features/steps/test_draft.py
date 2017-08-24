from behave import given, when, then


@given('there is a draft')
def step_impl_create_draft(context):
    context.browser.visit('/secure-message/create-message')
    context.browser.find_by_id('secure-message-subject').send_keys('Test Subject')
    context.browser.find_by_id('secure-message-body').send_keys('Test Body')
    context.browser.find_by_id('draft').click()


@when('I open a draft')
def step_impl_go_to_draft_message(context):
    context.browser.visit('/secure-message/messages/DRAFT')
    context.browser.find_by_link_text('Test Subject').click()


@then('the draft contains some text')
def step_impl_draft_page(context):
    context.browser.find_by_id('secure-message-subject')  # TODO find the value in both
    context.browser.find_by_id('secure-message-body')
