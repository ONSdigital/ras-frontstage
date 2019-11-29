import json
from collections import defaultdict

from tests.test_data import get_case_by_iac, get_cases_by_party, get_casegroups_by_party, get_ce_by_id, \
    get_ces_by_survey, get_survey_by_id, get_iac


class MockResponse:

    status_code = 200

    def __init__(self, payload, status_code=None):
        self.payload = payload
        self.status_code = status_code or MockResponse.status_code

    def json(self):
        return json.loads(self.payload)

    def raise_for_status(self):
        pass


class MockRequests:

    class Get:

        def __init__(self):
            self._calls = defaultdict(int)

        def __call__(self, uri, *args, **kwargs):
            self._calls[uri] += 1

            try:
                return {
                    'http://mockhost:1111/cases/iac/fb747cq725lj':
                        MockResponse(get_case_by_iac.response),
                    'http://mockhost:1111/cases/partyid/438df969-7c9c-4cd4-a89b-ac88cf0bfdf3':
                        MockResponse(get_cases_by_party.response),
                    'http://mockhost:1111/cases/partyid/3b136c4b-7a14-4904-9e01-13364dd7b972':
                        MockResponse(get_cases_by_party.response),
                    'http://mockhost:1111/casegroups/partyid/3b136c4b-7a14-4904-9e01-13364dd7b972':
                        MockResponse(get_casegroups_by_party.response),
                    'http://mockhost:2222/collectionexercises/dab9db7f-3aa0-4866-be20-54d72ee185fb':
                        MockResponse(get_ce_by_id.response),
                    'http://mockhost:2222/collectionexercises/survey/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87':
                        MockResponse(get_ces_by_survey.response),
                    'http://mockhost:3333/surveys/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87':
                        MockResponse(get_survey_by_id.response),
                    'http://mockhost:6666/iacs/fb747cq725lj':
                        MockResponse(get_iac.response),
                    'http://mockhost:1111/cases/casegroupid/612f5c34-7e11-4740-8e24-cb321a86a917':
                        MockResponse(get_cases_by_party.response)
                }[uri]
            except KeyError:
                raise Exception(f"MockRequests doesn't know about route {uri}")

        def assert_called_once_with(self, arg):
            assert(self._calls.get(arg, 0) == 1)

    class Post:

        def __init__(self):
            self._calls = defaultdict()
            self.response_payload = '{}'

        def __call__(self, uri, *args, **kwargs):
            self._calls[uri] = kwargs
            return MockResponse(self.response_payload, status_code=201)

        def assert_called_with(self, uri, expected_payload):
            assert(self._calls.get(uri) == expected_payload)

    class Put:

        status_code = 200

        def __init__(self, *args, **kwargs):
            pass

        def __call__(self, *args, **kwargs):
            return MockResponse('{}', status_code=201)

        def raise_for_status(self):
            pass

    def __init__(self):
        self.get = self.Get()
        self.post = self.Post()
        self.put = self.Put()
