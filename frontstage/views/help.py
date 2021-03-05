import logging

from flask import Blueprint, render_template, request, url_for, flash
from requests import session
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage.models import HelpForm, HelpInfoOnsForm

logger = wrap_logger(logging.getLogger(__name__))

help_bp = Blueprint('help_bp', __name__,
                    static_folder='static', template_folder='templates')

form_redirect_mapper = {
    'info-ons': 'help_bp.info_ons_get'
}
form_render_page_mapper = {
    'ons': 'help/help-who-is-ons.html',
    'data': 'help/help-info-how-safe-data.html',
    'info-something-else': 'help/help-info-something-else.html'
}


@help_bp.route('/vulnerability-reporting', methods=['GET'])
def help():
    return render_template('vunerability_disclosure.html')


@help_bp.route('/', methods=['GET'])
def help_get():
    return render_template('help/help.html', form=HelpForm())


@help_bp.route('/', methods=['POST'])
def help_submit():
    form = HelpForm(request.values)
    if request.method == 'POST' and form.validate():
        return redirect(url_for(form_redirect_mapper.get(form.data['option'])))
    else:
        flash('At least one option should be selected.')
        return redirect(url_for('help_bp.help_get'))


@help_bp.route('/info-ons', methods=['GET'])
def info_ons_get():
    return render_template('help/help-info-ons.html', form=HelpInfoOnsForm())


@help_bp.route('/info-ons', methods=['POST'])
def info_ons_submit():
    form = HelpInfoOnsForm(request.values)
    if request.method == 'POST' and form.validate():
        return render_template(form_render_page_mapper.get(form.data['option']))
    else:
        flash('At least one option should be selected.')
        return redirect(url_for('help_bp.info_ons_get'))
