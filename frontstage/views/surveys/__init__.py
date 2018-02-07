from flask import Blueprint


surveys_bp = Blueprint('surveys_bp', __name__,
                       static_folder='static', template_folder='templates/surveys')
