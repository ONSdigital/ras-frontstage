import json

from frontstage import app


with open('tests/test_data/party/business_party.json') as fp:
    business_party = json.load(fp)

with open('tests/test_data/party/business_party_no_trading_as.json') as fp:
    business_party_no_trading_as = json.load(fp)

with open('tests/test_data/case/case.json') as fp:
    case = json.load(fp)

with open('tests/test_data/collection_exercise/collection_exercise.json') as fp:
    collection_exercise = json.load(fp)

with open('tests/test_data/collection_exercise/collection_exercise_before_go_live.json') as fp:
    collection_exercise_before_go_live = json.load(fp)

with open('tests/test_data/collection_exercise/go_live_event.json') as fp:
    collection_exercise_go_live_event = json.load(fp)

with open('tests/test_data/collection_exercise/go_live_event_before.json') as fp:
    collection_exercise_go_live_event_before = json.load(fp)

with open('tests/test_data/case/completed_case.json') as fp:
    completed_case = json.load(fp)

with open('tests/test_data/case/completed_by_phone_case.json') as fp:
    completed_by_phone_case = [json.load(fp)]

with open('tests/test_data/collection_instrument/collection_instrument_eq.json') as fp:
    collection_instrument_eq = json.load(fp)

with open('tests/test_data/collection_instrument/collection_instrument_seft.json') as fp:
    collection_instrument_seft = json.load(fp)

with open('tests/test_data/survey/survey.json') as fp:
    survey = json.load(fp)

url_get_business_party = f"{app.config['PARTY_URL']}/party-api/v1/businesses/id/{business_party['id']}"
url_get_case = f"{app.config['CASE_URL']}/cases/{case['id']}"
url_get_cases_by_party = f"{app.config['CASE_URL']}/cases/partyid/{case['partyId']}"
url_get_ci = f"{app.config['COLLECTION_INSTRUMENT_URL']}/collection-instrument-api/1.0.2/collectioninstrument/id/{collection_instrument_seft['id']}"
url_get_collection_exercise = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/{collection_exercise['id']}"
url_get_collection_exercise_go_live = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/{collection_exercise['id']}/events/go_live"
url_get_survey = f"{app.config['SURVEY_URL']}/surveys/{survey['id']}"
