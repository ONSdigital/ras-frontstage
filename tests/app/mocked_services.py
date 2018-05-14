import json

from frontstage import app


with open('tests/test_data/party/business_party.json') as fp:
    business_party = json.load(fp)

with open('tests/test_data/case/case.json') as fp:
    case = json.load(fp)

with open('tests/test_data/case/categories.json') as json_data:
    categories = json.load(json_data)

with open('tests/test_data/collection_exercise/collection_exercise.json') as fp:
    collection_exercise = json.load(fp)

with open('tests/test_data/collection_exercise/collection_exercise_before_go_live.json') as json_data:
    collection_exercise_before_go_live = json.load(json_data)

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

with open('tests/test_data/case/completed_case.json') as json_data:
    completed_case = json.load(json_data)

with open('tests/test_data/party/party.json') as fp:
    party = json.load(fp)

with open('tests/test_data/survey/survey.json') as fp:
    survey = json.load(fp)

url_get_business_party = f"{app.config['PARTY_URL']}/party-api/v1/businesses/id/{business_party['id']}"
url_get_case = f"{app.config['CASE_URL']}/cases/{case['id']}"
url_get_case_categories = f"{app.config['CASE_URL']}/categories"
url_get_ci = f"{app.config['COLLECTION_INSTRUMENT_URL']}/collection-instrument-api/1.0.2/collectioninstrument/id/{collection_instrument_seft['id']}"
url_get_collection_exercise = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/{collection_exercise['id']}"
url_get_collection_exercise_events = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/{collection_exercise['id']}/events"
url_get_collection_exercise_go_live = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/{collection_exercise['id']}/events/go_live"
url_get_survey = f"{app.config['SURVEY_URL']}/surveys/{survey['id']}"
url_post_case_event_uuid = f"{app.config['CASE_URL']}/cases/{case['id']}/events"
