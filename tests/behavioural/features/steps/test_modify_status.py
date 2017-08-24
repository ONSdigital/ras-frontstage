import json

from behave import given, when, then

from frontstage import app


@given('I am logged in')
def step_impl_go_to_sign_in_page(context):
    context.browser.visit('/sign-in/')
    context.browser.find_by_id('username').send_keys('testuser@email.com')
    context.browser.find_by_id('password').send_keys('password')
    context.browser.find_by_id('SIGN_IN_BUTTON').click()


@when('I receive a message')
def step_impl_post_message_to_inbox(context):
    context.browser.visit('/secure-message/messages')

    headers = {'Content-Type': 'application/json', 'Authorization': 'eyJ0eXAiOiJqd3QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX3V1aWQiOi'
                                                                    'JCUkVTIiwicm9sZSI6ImludGVybmFsIn0.TeamX2lWfucai40rfI2Fe'
                                                                    'GmKPkwnrsn2YrcEaCGPK-A'}
    data = {
        "msg_to": ["ce12b958-2a5f-44f4-a6da-861e59070a32"],
        "msg_from": "BRES",
        "subject": "Subject Text",
        "body": "Body Text",
        "thread_id": "",
        "collection_case": "ACollectionCase",
        "collection_exercise": "ACollectionExercise",
        "ru_id": "f1a5e99c-8edf-489a-9c72-6cabe6c387fc",
        "survey": "BRES"
    }

    # TODO assert that inbox changes from (0) to (1)
    testData = app.test_client().post('http://127.0.0.1:5050/message/send', data=json.dumps(data), headers=headers)
    context.browser.visit('/secure-message/messages/INBOX')


@then('my inbox will change')
def step_impl_receive_message_inbox(context):
    context.browser.visit('/secure-message/messages')
    context.browser.find_by_id('SURVEY_MESSAGES_TAB')
