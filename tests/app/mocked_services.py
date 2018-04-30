import json
from frontstage import app

with open('tests/test_data/party/business_party.json') as json_data:
    business_party = json.load(json_data)

with open('tests/test_data/case/case.json') as json_data:
    case = json.load(json_data)

with open('tests/test_data/collection_exercise/collection_exercise.json') as json_data:
    collection_exercise = json.load(json_data)

with open('tests/test_data/collection_exercise/collection_exercise_before_go_live.json') as json_data:
    collection_exercise_before_go_live = json.load(json_data)

with open('tests/test_data/collection_instrument/collection_instrument_eq.json') as json_data:
    collection_instrument_eq = json.load(json_data)

with open('tests/test_data/collection_instrument/collection_instrument_seft.json') as json_data:
    collection_instrument_seft = json.load(json_data)

with open('tests/test_data/survey/survey.json') as json_data:
    survey = json.load(json_data)

url_get_business_party = f"{app.config['PARTY_SERVICE_URL']}/party-api/v1/businesses/id/{business_party['id']}"
url_get_case = f"{app.config['CASE_SERVICE_URL']}/cases/{case['id']}"
url_get_ci = f"{app.config['COLLECTION_INSTRUMENT_SERVICE_URL']}/collection-instrument-api/1.0.2/collectioninstrument/id/{collection_instrument_seft['id']}"
url_get_collection_exercise = f"{app.config['COLLECTION_EXERCISE_SERVICE_URL']}/collectionexercises/{collection_exercise['id']}"
url_get_collection_exercise_go_live = f"{app.config['COLLECTION_EXERCISE_SERVICE_URL']}/collectionexercises/{collection_exercise['id']}/events/go_live"
url_get_survey = f"{app.config['SURVEY_SERVICE_URL']}/surveys/{survey['id']}"
