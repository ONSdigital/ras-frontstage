import logging

from flask import current_app as app
from flask import request
from structlog import wrap_logger

from frontstage.common.authorisation import jwt_authorization
from frontstage.common.cryptographer import Cryptographer
from frontstage.controllers import (
    case_controller,
    collection_exercise_controller,
    iac_controller,
    party_controller,
    survey_controller,
)
from frontstage.exceptions.exceptions import ApiError
from frontstage.views.surveys import surveys_bp
from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))


@surveys_bp.route("/add-survey/confirm-organisation-survey", methods=["GET"])
@jwt_authorization(request)
def survey_confirm_organisation(session):
    # Get and decrypt enrolment code
    cryptographer = Cryptographer()
    encrypted_enrolment_code = request.args.get("encrypted_enrolment_code", None)
    enrolment_code = cryptographer.decrypt(encrypted_enrolment_code.encode()).decode()

    # Validate enrolment code before retrieving organisation data
    iac_controller.validate_enrolment_code(enrolment_code)

    logger.info("Attempting to retrieve data for confirm add organisation/survey page", enrolment_code=enrolment_code)
    try:
        # Get organisation name
        case = case_controller.get_case_by_enrolment_code(enrolment_code)
        business_party_id = case["caseGroup"]["partyId"]
        business_party = party_controller.get_party_by_business_id(
            business_party_id, app.config["PARTY_URL"], app.config["BASIC_AUTH"]
        )

        # Get survey name
        collection_exercise_id = case["caseGroup"]["collectionExerciseId"]
        collection_exercise = collection_exercise_controller.get_collection_exercise(collection_exercise_id)
        survey_id = collection_exercise["surveyId"]
        survey_name = survey_controller.get_survey(app.config["SURVEY_URL"], app.config["BASIC_AUTH"], survey_id).get(
            "longName"
        )
    except ApiError as exc:
        logger.error(
            "Failed to retrieve data for confirm add organisation/survey page",
            api_url=exc.url,
            api_status_code=exc.status_code,
            enrolment_code=enrolment_code,
        )
        raise

    business_context = {
        "encrypted_enrolment_code": encrypted_enrolment_code,
        "enrolment_code": enrolment_code,
        "case": case,
        "trading_as": business_party.get("trading_as"),
        "organisation": business_party.get("name"),
        "collection_exercise_id": collection_exercise_id,
        "survey_id": collection_exercise,
        "survey_name": survey_name,
    }

    logger.info(
        "Successfully retrieved data for confirm add organisation/survey page",
        collection_exercise_id=collection_exercise_id,
        business_party_id=business_party_id,
        survey_id=survey_id,
        enrolment_code=enrolment_code,
    )

    return render_template(
        "surveys/surveys-confirm-organisation.html",
        session=session,
        context=business_context,
    )
