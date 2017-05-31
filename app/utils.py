"""Utils module."""

from __future__ import print_function

from datetime import datetime
from functools import wraps, update_wrapper
import os

from flask import Flask, make_response, render_template, request, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc

from models import User, db, UserScope


def get_user_scopes_util(username):
    """
    Get the user scopes for the user.

    :param username: String
    :return: Http Response
    """
    user_data = (db.session.query(User, UserScope)
                 .filter(User.id == UserScope.user_id)
                 .filter(User.username == username)
                 .all())

    user_scopes = [us.scope for u, us in user_data]

    if not user_scopes:
        return []

    return user_scopes
