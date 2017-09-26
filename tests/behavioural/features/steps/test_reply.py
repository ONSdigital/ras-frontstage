from behave import given, when, then
from tests.behavioural.features.steps.common import maxtext10000


@then('I send an empty reply')
def step_impl_reply_to_bres_message(context):
    context.browser.find_by_id('secure-message-body').send_keys()
    context.browser.find_by_id('submit-btn').click()


@then('I should receive an empty reply error')
def step_impl_subject_and_body_error(context):
    context.browser.find_by_link_text('Please enter a message')


@then('I send an empty reply')
def step_impl_reply_to_bres_message(context):
    context.browser.find_by_id('secure-message-body').send_keys(maxtext10000)
    context.browser.find_by_id('submit-btn').click()


@then('I should receive an empty reply error')
def step_impl_subject_and_body_error(context):
    context.browser.find_by_link_text('Please enter a message')
