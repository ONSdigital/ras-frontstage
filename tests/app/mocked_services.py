import json
from frontstage import app


with open('tests/test_data/case/case.json') as json_data:
    case = json.load(json_data)

with open('tests/test_data/case/categories.json') as json_data:
    categories = json.load(json_data)


url_download_ci = f"{app.config['COLLECTION_INSTRUMENT_SERVICE_URL']}/collection-instrument-api/1.0.2/download/{case['collectionInstrumentId']}"
url_upload_ci = f"{app.config['COLLECTION_INSTRUMENT_SERVICE_URL']}/survey_response-api/v1/survey_responses/{case['id']}"
url_get_case = f"{app.config['CASE_SERVICE_URL']}/cases/{case['id']}"
url_get_case_categories = f"{app.config['CASE_SERVICE_URL']}/categories"
url_post_case_event = f"{app.config['CASE_SERVICE_URL']}/cases/test_case_id/events"
url_post_case_event_uuid = f"{app.config['CASE_SERVICE_URL']}/cases/{case['id']}/events"
