# coding: utf-8
import flask

filter_blueprint = flask.Blueprint("filters", __name__)


@filter_blueprint.app_template_filter()
def setAttribute(dictionary, key, value):
    dictionary[key] = value
    return dictionary


@filter_blueprint.app_template_filter()
def setAttributes(dictionary, attributes):
    for key in attributes:
        dictionary[key] = attributes[key]
    return dictionary
