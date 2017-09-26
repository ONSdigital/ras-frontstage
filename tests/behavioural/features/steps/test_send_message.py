import requests

from behave import given, when, then
from flask import json
from tests.behavioural.features.steps.common import is_element_present_by_id, maxtext10000


maxtext100 = 'lA4qe9NwQ5jO90Kkx30xf7Qjwcl8argK5IyJKutxUv6RlraTzwPSb2ka4XJ7TOJMCZyGgk0fCx8lLnOOQC3uJTBtfCiatbwvGNaZV'


@given('I go to the secure-message page')
def step_impl_go_to_secure_message_create_page(context):
    context.browser.visit('/secure-message/messages/')


@when('I click create message')
def step_impl_click_create_message(context):
    context.browser.find_by_link_text('Create a message').click()


@then('The create message page will open')
def step_impl_open_create_message_page(context):
    assert is_element_present_by_id(context, 'send-message')


@given('I am on the create message page')
def step_impl_visit_create_message_page(context):
    context.browser.visit('/secure-message/create-message/')


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
    context.browser.find_by_id('secure-message-subject').send_keys('')
    context.browser.find_by_id('secure-message-body').send_keys('')


@given('I have a message with subject too long')
def step_impl_add_text_to_subject_too_long(context):
    context.browser.find_by_id('secure-message-subject').send_keys(maxtext100)
    context.browser.find_by_id('secure-message-body').send_keys('Test')


# The subject textarea in frontstage has an auto limit of 100 characters
@given('I click send with subject too long')
def step_impl_subject_too_long_send(context):
    length = context.browser.find_by_id('subject').length()
    assert length < 101
    context.browser.find_by_id('send-message').click()


@given('I have a message with body too long')
def step_impl_add_text_to_body_too_long(context):
    context.browser.find_by_id('secure-message-subject').send_keys('Test')
    context.browser.find_by_id('secure-message-body').send_keys(maxtext10000)


@when('I send a message')
def step_impl_send_a_message(context):
    context.browser.find_by_id('send-message').click()


@then('The confirmation sent page opens')
def step_impl_open_confirmation_page(context):
    assert is_element_present_by_id(context, 'message-sent')


@given('I have received a message from BRES')
def step_impl_received_message_from_bres(context):
    url = 'http://localhost:5050/message/send'
    # This authorization needs to be valid for the user or the test will not work
    headers = {
        'Authorization': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyZWZyZXNoX3Rva2VuIjoiNGE3NThlZTUtNDQ2My00ZWZjLTk4MGItOTcyYjcxMjIyN2U5IiwiYW' \
        'NjZXNzX3Rva2VuIjoiNWZhNmZkYTgtYzQ1Zi00YTE5LWEzZDYtNGMzYWUzMTI0NjMxIiwiZXhwaXJlc19hdCI6MTUwNjA3NjY1OC40ODk1OTYsInJvb' \
        'GUiOiJpbnRlcm5hbCIsInBhcnR5X2lkIjoiQlJFUyJ9.gBqxH_HgK7TRUxBtpgiI97QsHBPhfzbNdHyC8Nm8caw',
        'Content-Type': 'application/json'
    }
    message = {
        "msg_to": ["a0e833fe-8a2d-4293-903b-4b826732e079"],
        "msg_from": "BRES",
        "subject": "Test internal message",
        "body": "Test internal message",
        "thread_id": "",
        "ru_id": "f1a5e99c-8edf-489a-9c72-6cabe6c387fc",
        "collection_case": "ACollectionCase",
        "survey": "BRES"
    }
    # requests.post(url, data=json.dumps(message), headers=headers)
    response = requests.post(url, data=json.dumps(message), headers=headers)
    print(response)


@then('I should see a reply message')
def step_impl_see_message_from_bres(context):
    assert is_element_present_by_id(context, 'secure-message-subject')
    assert is_element_present_by_id(context, 'secure-message-body')


@then('I reply to a BRES message')
def step_impl_reply_to_bres_message(context):
    context.browser.find_by_id('secure-message-body').send_keys('I am replying to BRES')
    context.browser.find_by_id('submit-btn').click()


@then('The draft saved text should appear')
def step_impl_draft_saved_text_appears(context):
    assert is_element_present_by_id(context, 'message-sent')


@then('I should receive a subject and body error')
def step_impl_subject_and_body_error(context):
    context.browser.find_by_link_text('Please enter a subject')
    context.browser.find_by_link_text('Please enter a message')


@then('I should receive a body too long error')
def step_impl_subject_and_body_error(context):
    context.browser.find_by_link_text('Body field length must not be greater than 10000')
