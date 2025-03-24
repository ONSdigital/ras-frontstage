import io
import json

from frontstage import app

survey_file = dict(file=(io.BytesIO(b"my file contents"), "testfile.xlsx"))
with open("tests/test_data/party/business_party.json") as fp:
    business_party = json.load(fp)

with open("tests/test_data/party/party.json") as fp:
    respondent_party = json.load(fp)

with open("tests/test_data/case/case.json") as fp:
    case = json.load(fp)

with open("tests/test_data/case/case_diff_surveyId.json") as fp:
    case_diff_surveyId = json.load(fp)

with open("tests/test_data/case/case_list.json") as fp:
    case_list = json.load(fp)

with open("tests/test_data/case/case_list_without_iac_and_with_case_events.json") as fp:
    case_list_with_iac_and_case_events = json.load(fp)

with open("tests/test_data/case/case_without_case_group.json") as fp:
    case_without_case_group = json.load(fp)

with open("tests/test_data/case/categories.json") as fp:
    categories = json.load(fp)

with open("tests/test_data/collection_exercise/collection_exercise.json") as fp:
    collection_exercise = json.load(fp)

with open("tests/test_data/collection_exercise/collection_exercise_v3.json") as fp:
    collection_exercise_v3 = json.load(fp)

with open("tests/test_data/collection_exercise/collection_exercise_with_supplementary_dataset.json") as fp:
    collection_exercise_with_supplementary_dataset = json.load(fp)

with open("tests/test_data/collection_exercise/collection_exercise_list_by_survey.json") as fp:
    collection_exercise_by_survey = json.load(fp)

with open("tests/test_data/collection_exercise/collection_exercises_for_survey_ids.json") as fp:
    collection_exercises_for_survey_ids = json.load(fp)

with open("tests/test_data/collection_exercise/collection_exercise_events.json") as json_data:
    collection_exercise_events = json.load(json_data)

with open("tests/test_data/collection_exercise/go_live_event.json") as fp:
    collection_exercise_go_live_event = json.load(fp)

with open("tests/test_data/collection_instrument/collection_instrument_eq.json") as fp:
    collection_instrument_eq = json.load(fp)

with open("tests/test_data/collection_instrument/collection_instrument_seft.json") as fp:
    collection_instrument_seft = json.load(fp)

with open("tests/test_data/case/completed_case.json") as fp:
    completed_case = json.load(fp)

with open("tests/test_data/message.json") as fp:
    message_json = json.load(fp)

with open("tests/test_data/eq_payload.json") as fp:
    eq_payload = json.load(fp)

with open("tests/test_data/iac/iac_active.json") as fp:
    active_iac = json.load(fp)

with open("tests/test_data/iac/iac-inactive.json") as fp:
    inactive_iac = json.load(fp)

with open("tests/test_data/secure_messaging/message.json") as fp:
    message = json.load(fp)

with open("tests/test_data/secure_messaging/count.json") as fp:
    message_count = json.load(fp)

with open("tests/test_data/party/party.json") as fp:
    party = json.load(fp)

with open("tests/test_data/survey/bricks_survey.json") as fp:
    survey = json.load(fp)

with open("tests/test_data/party/pending_surveys.json") as fp:
    pending_surveys = json.load(fp)

with open("tests/test_data/survey/qbs_survey.json") as fp:
    survey_eq = json.load(fp)

with open("tests/test_data/survey/survey_list_todo.json") as fp:
    survey_list_todo = json.load(fp)

with open("tests/test_data/survey/survey_list_history.json") as fp:
    survey_list_history = json.load(fp)

with open("tests/test_data/party/respondent_enrolments.json") as fp:
    respondent_enrolments = json.load(fp)

encoded_jwt_token = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwYXJ0eV9pZCI6ImY5NTZlOGFlLTZ"
    "lMGYtNDQxNC1iMGNmLWEwN2MxYWEzZTM3YiIsImV4cGlyZXNfYXQiOiIxMDAxMjM0NTY"
    "3ODkiLCJyb2xlIjoicmVzcG9uZGVudCIsInVucmVhZF9tZXNzYWdlX2NvdW50Ijp7InZh"
    "bHVlIjowLCJyZWZyZXNoX2luIjozMjUyNzY3NDAwMC4wfSwiZXhwaXJlc19pbiI6MzI1M"
    "jc2NzQwMDAuMH0.m94R50EPIKTJmE6gf6PvCmCq8ZpYwwV8PHSqsJh5fnI"
)
enrolment_code = "ABCDEF123456"
encrypted_enrolment_code = "WfwJghohWOZTIYnutlTcVucqnuED5Lm9q8t0L4ASHPo="
token = "test_token"

url_create_account = f"{app.config['PARTY_URL']}/party-api/v1/respondents"
url_download_ci = f"{app.config['COLLECTION_INSTRUMENT_URL']}/collection-instrument-api/1.0.2/download/{case['collectionInstrumentId']}"
url_get_respondent_by_email = f"{app.config['PARTY_URL']}/party-api/v1/respondents/email"
url_get_business_party = f"{app.config['PARTY_URL']}/party-api/v1/businesses/id/{business_party['id']}"
url_get_respondent_party = f"{app.config['PARTY_URL']}/party-api/v1/respondents/party_id/{party['id']}"
url_get_respondent_enrolments = f"{app.config['PARTY_URL']}/party-api/v1/enrolments/respondent/{party['id']}"
url_get_existing_pending_surveys = f"{app.config['PARTY_URL']}/party-api/v1/pending-surveys/originator/{party['id']}"
url_get_case = f"{app.config['CASE_URL']}/cases/{case['id']}"
url_get_case_by_enrolment_code = f"{app.config['CASE_URL']}/cases/iac/{enrolment_code}"
url_get_case_categories = f"{app.config['CASE_URL']}/categories"
url_get_cases_by_party = f"{app.config['CASE_URL']}/cases/partyid/{case['partyId']}"
url_get_ci = (
    f"{app.config['COLLECTION_INSTRUMENT_URL']}/collection-instrument-api/1.0.2/{collection_instrument_seft['id']}"
)
url_get_collection_exercise = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/{collection_exercise['id']}"
url_get_collection_exercises_by_surveys = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/surveys"
url_get_collection_exercises_by_survey = (
    f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/survey/{collection_exercise['surveyId']}"
)
url_get_collection_exercise_events = (
    f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/{collection_exercise['id']}/events"
)
url_get_collection_exercise_go_live = (
    f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/{collection_exercise['id']}/events/go_live"
)
url_get_respondent_email = f"{app.config['PARTY_URL']}/party-api/v1/respondents/email"
url_get_survey = f"{app.config['SURVEY_URL']}/surveys/{survey['id']}"
url_get_survey_by_short_name = f"{app.config['SURVEY_URL']}/surveys/shortname/{survey['shortName']}"
url_get_survey_by_short_name_eq = f"{app.config['SURVEY_URL']}/surveys/shortname/{survey_eq['shortName']}"
url_get_survey_by_short_name_rsi = f"{app.config['SURVEY_URL']}/surveys/shortname/rsi"
url_get_survey_long_name = app.config["SURVEY_URL"] + "/surveys/02b9c366-7397-42f7-942a-76dc5876d86d"
url_get_thread = app.config["SECURE_MESSAGE_URL"] + "/threads/9e3465c0-9172-4974-a7d1-3a01592d1594"
url_get_conversation_count = f"{app.config['SECURE_MESSAGE_URL']}/messages/count?unread_conversations=true"
url_get_threads = app.config["SECURE_MESSAGE_URL"] + "/threads"
url_auth_token = f"{app.config['AUTH_URL']}/api/v1/tokens/"
url_password_change = f"{app.config['PARTY_URL']}/party-api/v1/respondents/change_password"
url_post_add_survey = f"{app.config['PARTY_URL']}/party-api/v1/respondents/add_survey"
url_get_post_add_survey = f"{app.config['PARTY_URL']}/party-api/v1/respondents/add_survey"
url_post_case_event_uuid = f"{app.config['CASE_URL']}/cases/{case['id']}/events"
url_reset_password_request = f"{app.config['PARTY_URL']}/party-api/v1/respondents/request_password_change"
url_send_message = app.config["SECURE_MESSAGE_URL"] + "/messages"
url_send_message_v2_messages = app.config["SECURE_MESSAGE_V2_URL"] + "/messages"
url_send_message_v2_threads = app.config["SECURE_MESSAGE_V2_URL"] + "/threads"
url_validate_enrolment = f"{app.config['IAC_URL']}/iacs/{enrolment_code}"
url_verify_email = f"{app.config['PARTY_URL']}/party-api/v1/emailverification/{token}"
url_verify_token = f"{app.config['PARTY_URL']}/party-api/v1/tokens/verify/{token}"
url_resend_expired_account_change_verification = (
    f"{app.config['PARTY_URL']}/party-api/v1/resend-account-email-change" f"-expired-token/{token} "
)
url_notify_party_and_respondent_account_locked = (
    f'{app.config["PARTY_URL"]}/party-api/v1/respondents/edit-account-' f'status/{party["id"]}'
)
url_banner_api = f"{app.config['BANNER_SERVICE_URL']}/banner"
url_auth_delete = f'{app.config["AUTH_URL"]}/api/account/user'
