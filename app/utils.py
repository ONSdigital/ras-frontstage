"""Utils module."""

from __future__ import print_function
# from models import *


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
