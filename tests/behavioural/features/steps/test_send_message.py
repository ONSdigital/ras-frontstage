import requests
from behave import given, when, then
from flask import json

from frontstage.views.secure_messaging import headers
from tests.behavioural.features.steps.common import is_element_present_by_id


@when('I go to the secure-message page')
def step_impl_go_to_secure_message_create_page(context):
    context.browser.visit('/secure-message/messages/')


@when('I click create message')
def step_impl_click_create_message(context):
    context.browser.find_by_link_text('Create a message').click()


@then('The create message page will open')
def step_impl_open_create_message_page(context):
    assert is_element_present_by_id(context, 'send-message')


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
    assert is_element_present_by_id(context, 'message-sent')


@given('I have received a message from BRES')
def step_impl_received_message_from_bres(context):
    url = 'http://localhost:5050/message/send'
    headers['Authorization'] = "eyJ0eXAiOiJqd3QiLCJhbGciOiJIUzI1NiJ9.eyJwYXJ0eV9pZCI6IkJSRVMiLCJy" \
                               "b2xlIjoiaW50ZXJuYWwifQ.y_B0MsBwFbwUBadYvtn5ZppWRrw4Z-3JW9_ZXDprLug"
    headers['Content-Type'] = 'application/json'
    message = {
        "msg_to": ["ef0a2bd7-1da2-4197-a64a-bf2e6deebabf"],
        "msg_from": "BRES",
        "subject": "Test internal message",
        "body": "Test internal message",
        "thread_id": "",
        "ru_id": "f1a5e99c-8edf-489a-9c72-6cabe6c387fc",
        "collection_case": "ACollectionCase",
        "survey": "BRES"
    }
    requests.post(url, data=json.dumps(message), headers=headers)


@when('I go to the inbox tab')
def step_impl_go_to_inbox_tab(context):
    context.browser.visit('/secure-message/messages/INBOX')


@when('I open the internal message')
def step_impl_open_internal_message(context):
    context.browser.find_by_link_text('Test internal message').click()


@then('I should see a reply message')
def step_impl_see_message_from_bres(context):
    assert is_element_present_by_id(context, 'secure-message-subject')  # TODO find some values inside
    assert is_element_present_by_id(context, 'secure-message-body')


@when('I reply to a BRES message')
def step_impl_reply_to_bres_message(context):
    context.browser.find_by_id('secure-message-body').send_keys('I am replying to BRES')
    context.browser.find_by_id('submit-btn').click()

