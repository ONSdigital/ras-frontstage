import json

from frontstage import app


with open('tests/test_data/party/business_party.json') as json_data:
    business_party = json.load(json_data)

with open('tests/test_data/case/case.json') as json_data:
    case = json.load(json_data)

with open('tests/test_data/case/categories.json') as json_data:
    categories = json.load(json_data)

with open('tests/test_data/collection_exercise/collection_exercise.json') as json_data:
    collection_exercise = json.load(json_data)

with open('tests/test_data/party/party.json') as json_data:
    party = json.load(json_data)

with open('tests/test_data/survey/survey.json') as json_data:
    survey = json.load(json_data)

enrolment_code = 'ABCDEF123456'
encrypted_enrolment_code = 'WfwJghohWOZTIYnutlTcVucqnuED5Lm9q8t0L4ASHPo='
token = 'test_token'

url_create_account = f"{app.config['PARTY_URL']}/party-api/v1/respondents"
url_validate_enrolment = f"{app.config['IAC_URL']}/iacs/{enrolment_code}"
url_verify_email = f"{app.config['PARTY_URL']}/party-api/v1/emailverification/{token}"
url_case_by_enrolment_code = f"{app.config['CASE_URL']}/cases/iac/{enrolment_code}"
url_get_cases_by_party = f"{app.config['CASE_URL']}/cases/partyid/{case['partyId']}"
url_get_business_party = f"{app.config['PARTY_URL']}/party-api/v1/businesses/id/{business_party['id']}"
url_get_case_categories = f"{app.config['CASE_URL']}/categories"
url_get_collection_exercise = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/{collection_exercise['id']}"
url_get_survey = f"{app.config['SURVEY_URL']}/surveys/{survey['id']}"
url_post_case_event_uuid = f"{app.config['CASE_URL']}/cases/{case['id']}/events"
url_post_add_survey = f"{app.config['PARTY_URL']}/party-api/v1/respondents/add_survey"
