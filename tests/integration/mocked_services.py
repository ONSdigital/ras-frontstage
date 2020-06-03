import io
import json

from frontstage import app

survey_file = dict(file=(io.BytesIO(b'my file contents'), "testfile.xlsx"))
with open('tests/test_data/party/business_party.json') as fp:
    business_party = json.load(fp)

with open('tests/test_data/party/business_party_no_trading_as.json') as fp:
    business_party_no_trading_as = json.load(fp)

with open('tests/test_data/party/party.json') as fp:
    respondent_party = json.load(fp)

with open('tests/test_data/case/case.json') as fp:
    case = json.load(fp)

with open('tests/test_data/case/case_diff_surveyId.json') as fp:
    case_diff_surveyId = json.load(fp)

with open('tests/test_data/case/case_list.json') as fp:
    case_list = json.load(fp)

with open('tests/test_data/case/case_list_without_iac_and_with_case_events.json') as fp:
    case_list_with_iac_and_case_events = json.load(fp)

with open('tests/test_data/case/categories.json') as fp:
    categories = json.load(fp)

with open('tests/test_data/collection_exercise/collection_exercise.json') as fp:
    collection_exercise = json.load(fp)

with open('tests/test_data/collection_exercise/collection_exercise_list_by_survey.json') as fp:
    collection_exercise_by_survey = json.load(fp)

with open('tests/test_data/collection_exercise/collection_exercise_before_go_live.json') as fp:
    collection_exercise_before_go_live = json.load(fp)

with open('tests/test_data/collection_exercise/collection_exercise_events.json') as json_data:
    collection_exercise_events = json.load(json_data)

with open('tests/test_data/collection_exercise/go_live_event.json') as fp:
    collection_exercise_go_live_event = json.load(fp)

with open('tests/test_data/collection_exercise/go_live_event_before.json') as fp:
    collection_exercise_go_live_event_before = json.load(fp)

with open('tests/test_data/collection_instrument/collection_instrument_eq.json') as fp:
    collection_instrument_eq = json.load(fp)

with open('tests/test_data/collection_instrument/collection_instrument_seft.json') as fp:
    collection_instrument_seft = json.load(fp)

with open('tests/test_data/case/completed_case.json') as fp:
    completed_case = json.load(fp)

with open('tests/test_data/case/completed_by_phone_case.json') as fp:
    completed_by_phone_case = [json.load(fp)]

with open('tests/test_data/conversation.json') as fp:
    conversation_json = json.load(fp)

with open('tests/test_data/conversation_list.json') as fp:
    conversation_list_json = json.load(fp)

with open('tests/test_data/eq_payload.json') as fp:
    eq_payload = json.load(fp)

with open('tests/test_data/iac/iac_active.json') as fp:
    active_iac = json.load(fp)

with open('tests/test_data/iac/iac-inactive.json') as fp:
    inactive_iac = json.load(fp)

with open('tests/test_data/secure_messaging/message.json') as fp:
    message = json.load(fp)

with open('tests/test_data/secure_messaging/count.json') as fp:
    message_count = json.load(fp)

with open('tests/test_data/party/party.json') as fp:
    party = json.load(fp)

with open('tests/test_data/survey/bricks_survey.json') as fp:
    survey = json.load(fp)

with open('tests/test_data/survey/qbs_survey.json') as fp:
    survey_eq = json.load(fp)

with open('tests/test_data/survey/rsi_survey.json') as fp:
    survey_rsi = json.load(fp)

with open('tests/test_data/survey/survey_list_todo.json') as fp:
    survey_list_todo = json.load(fp)

with open('tests/test_data/survey/survey_list_history.json') as fp:
    survey_list_history = json.load(fp)

encoded_jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoicmVzcG9uZGVu" \
                    "dCIsImFjY2Vzc190b2tlbiI6ImI5OWIyMjA0LWYxMDAtNDcxZS1iOTQ1LTIyN" \
                    "2EyNmVhNjljZCIsInJlZnJlc2hfdG9rZW4iOiIxZTQyY2E2MS02ZDBkLTQxYj" \
                    "MtODU2Yy02YjhhMDhlYmIyZTMiLCJleHBpcmVzX2F0IjoxNzM4MTU4MzI4LjA" \
                    "sInBhcnR5X2lkIjoiZjk1NmU4YWUtNmUwZi00NDE0LWIwY2YtYTA3YzFhYTNl" \
                    "MzdiIiwidW5yZWFkX21lc3NhZ2VfY291bnQiOnsidmFsdWUiOjAsInJlZnJlc" \
                    "2hfaW4iOjMyNTAzNjgwMDAwLjB9fQ.d9KA3ltbNbcgqYmknQwiR2SEEOZ25ja2cZlQ4yC-dy8"
enrolment_code = 'ABCDEF123456'
encrypted_enrolment_code = 'WfwJghohWOZTIYnutlTcVucqnuED5Lm9q8t0L4ASHPo='
token = 'test_token'

url_create_account = f"{app.config['PARTY_URL']}/party-api/v1/respondents"
url_download_ci = f"{app.config['COLLECTION_INSTRUMENT_URL']}/collection-instrument-api/1.0.2/download/{case['collectionInstrumentId']}"
url_get_respondent_by_email = f"{app.config['PARTY_URL']}/party-api/v1/respondents/email"
url_get_business_party = f"{app.config['PARTY_URL']}/party-api/v1/businesses/id/{business_party['id']}"
url_get_respondent_party = f"{app.config['PARTY_URL']}/party-api/v1/respondents/id/{party['id']}"
url_get_case = f"{app.config['CASE_URL']}/cases/{case['id']}"
url_get_case_by_enrolment_code = f"{app.config['CASE_URL']}/cases/iac/{enrolment_code}"
url_get_case_categories = f"{app.config['CASE_URL']}/categories"
url_get_cases_by_party = f"{app.config['CASE_URL']}/cases/partyid/{case['partyId']}"
url_get_ci = f"{app.config['COLLECTION_INSTRUMENT_URL']}/collection-instrument-api/1.0.2/collectioninstrument/id/{collection_instrument_seft['id']}"
url_get_collection_exercise = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/{collection_exercise['id']}"
url_get_collection_exercises_by_survey = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/survey/{collection_exercise['surveyId']}"
url_get_collection_exercise_events = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/{collection_exercise['id']}/events"
url_get_collection_exercise_go_live = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/{collection_exercise['id']}/events/go_live"
url_get_respondent_email = f"{app.config['PARTY_URL']}/party-api/v1/respondents/email"
url_get_survey = f"{app.config['SURVEY_URL']}/surveys/{survey['id']}"
url_get_survey_by_short_name = f"{app.config['SURVEY_URL']}/surveys/shortname/{survey['shortName']}"
url_get_survey_by_short_name_eq = f"{app.config['SURVEY_URL']}/surveys/shortname/{survey_eq['shortName']}"
url_get_survey_by_short_name_rsi = f"{app.config['SURVEY_URL']}/surveys/shortname/{survey_rsi['shortName']}"
url_get_token = f"{app.config['AUTH_URL']}/api/v1/tokens/"
url_get_thread = app.config['SECURE_MESSAGE_URL'] + '/threads/9e3465c0-9172-4974-a7d1-3a01592d1594'
url_get_thread_old = app.config['SECURE_MESSAGE_URL'] + '/thread/9e3465c0-9172-4974-a7d1-3a01592d1594'
url_get_conversation_count = f"{app.config['SECURE_MESSAGE_URL']}/messages/count?new_respondent_conversations=True"
url_get_threads = app.config['SECURE_MESSAGE_URL'] + '/threads'
url_oauth_token = f"{app.config['AUTH_URL']}/api/v1/tokens/"
url_password_change = f"{app.config['PARTY_URL']}/party-api/v1/respondents/change_password"
url_post_add_survey = f"{app.config['PARTY_URL']}/party-api/v1/respondents/add_survey"
url_post_case_event_uuid = f"{app.config['CASE_URL']}/cases/{case['id']}/events"
url_reset_password_request = f"{app.config['PARTY_URL']}/party-api/v1/respondents/request_password_change"
url_send_message = app.config['SECURE_MESSAGE_URL'] + '/messages'
url_upload_ci = f"{app.config['COLLECTION_INSTRUMENT_URL']}/survey_response-api/v1/survey_responses/{case['id']}"
url_validate_enrolment = f"{app.config['IAC_URL']}/iacs/{enrolment_code}"
url_verify_email = f"{app.config['PARTY_URL']}/party-api/v1/emailverification/{token}"
url_verify_token = f"{app.config['PARTY_URL']}/party-api/v1/tokens/verify/{token}"
url_notify_party_and_respondent_account_locked = f'{app.config["PARTY_URL"]}/party-api/v1/respondents/edit-account-' \
                                                 f'status/{party["id"]}'
