"""

   Frontstage (my)Surveys Module
   License: MIT
   Copyright (c) 2017 Crown Copyright (Office for National Statistics)

"""
import json
from flask import Blueprint, render_template, request, redirect, url_for
from app.config import Config
from ons_ras_common.ons_decorators import jwt_session
from ons_ras_common import ons_env

surveys_bp = Blueprint('surveys_bp', __name__, static_folder='static', template_folder='templates')


@surveys_bp.route('/', methods=['GET', 'POST'])
@jwt_session(request)
def logged_in(session):
    """
    Display the todo tab for the 'my surveys' page

    :param session: The user's current session details
    :return: A rendered version of the my surveys page
    """
    return my_surveys_page(session, page='surveys-todo.html', in_progress=True, not_started=True)


@surveys_bp.route('/history')
@jwt_session(request)
def surveys_history(session):
    """
    Display the history tab for the 'my surveys' page

    :param session: The user's current session details
    :return: A rendered version of the my surveys page
    """
    return my_surveys_page(session, page='surveys-history.html', complete=True)


@surveys_bp.route('/access_survey', methods=['GET', 'POST'])
@jwt_session(request)
def access_survey(session):
    """
    Come here when a user clicks on the 'access survey' button.

    :param session: The user's current session details
    :return: The survey-access page for the selected survey
    """
    instrument_id = request.form.get('collection_instrument_id', None)
    case_id = request.form.get('case_id', None)
    code, instrument = ons_env.collection_instrument.get_by_id(instrument_id)
    if code != 200:
        return redirect(url_for('error_page'))
    return render_template('surveys-access.html', _theme='default', case_id=case_id,
                           form=request.form, ci_data=instrument['instrument'])


@surveys_bp.route('/upload_survey', methods=['POST'])
@jwt_session(request)
def upload_survey(session):
    """
    Handle a user upload of a returning instrument.

    :param session: The user's current session details
    :return: Renders a success or failure page
    """
    party_id = session.get('party_id', 'no-party-id')
    case_id = request.args.get('case_id', None)
    try:
        file_obj = request.files['file']
    except Exception as e:
        print(e)
        raise Exception

    code, msg = ons_env.collection_instrument.upload(case_id, party_id, file_obj)
    if code == 200:
        return render_template('surveys-upload-success.html', _theme='default', upload_filename=file_obj.filename)

    return render_template('surveys-upload-failure.html',  _theme='default', error_info=msg, case_id=case_id)


def my_surveys_page(session, page=None, not_started=False, in_progress=False, complete=False):
    """
    Call the aggregated call to build an appropriate data array, then feed it into
    the "my-surveys" template.

    :param session: The users's current session record
    :param page: The page to render
    :param not_started: Are we interested in jobs that haven't started
    :param in_progress: Are we interested in jobs that are in progress
    :param complete: Are we interested in jobs that are complete
    :return: a rendered response
    """
    filter = []
    if not_started:
        filter.append("not started")
    if in_progress:
        filter.append("in progress")
    if complete:
        filter.append("complete")
    try:
        status_filter = {'status_filter': json.dumps(filter)}
        data = ons_env.case_service.my_surveys(session.get('party_id', None), status_filter)
        return render_template(page, _theme='default', data_array=data)
    except Exception as e:
        ons_env.logger.error('unexpected error "{}"'.format(e))
        return redirect(url_for('error_page'))

