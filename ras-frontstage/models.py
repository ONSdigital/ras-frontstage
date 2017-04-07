"""
This module contains the data model for the collection instrument
"""

import datetime

from flask_wtf import Form
from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import TEXT, JSON, UUID
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import TextField, DecimalField, SelectField, PasswordField, StringField
from wtforms.validators import InputRequired, EqualTo

from app import db


class User(db.Model):
    """User model."""

    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    pwdhash = db.Column(db.String())
    token = db.Column(db.String())
    token_created_on = db.Column(DateTime)
    token_duration = db.Column(db.Integer)
    created_on = db.Column(DateTime, default=datetime.datetime.utcnow)

    def __init__(self, username, password, token, token_created_on, token_duration, id=None):
        """Init method."""
        self.id = id
        self.username = username
        self.pwdhash = generate_password_hash(password)
        self.token = token
        self.token_created_on = token_created_on
        self.token_duration = token_duration

    def check_password(self, password):
        """Method to check password validity."""
        return check_password_hash(self.pwdhash, password)

    def check_password_simple(self, password):
        """Check password simplicity."""
        if password == self.pwdhash:
            print "Password checks out. Password in {}, password I have: {}".format(password, self.pwdhash)
            return True
        return False


class UserScope(db.Model):
    """Userscope model."""

    __tablename__ = 'user_scopes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    scope = db.Column(db.String(100))
    created_on = db.Column(DateTime, default=datetime.datetime.utcnow)

    def __init__(self, user_id, scope, id=None):
        """Init method."""
        self.id = id
        self.user_id = user_id
        self.scope = scope


class RegistrationForm(Form):
    """Registration form."""

    username = StringField('Username', [InputRequired])
    password = PasswordField( 'Password',[InputRequired(), EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Confirm Password', [InputRequired()])


class LoginForm(Form):
    """Login form."""

    username = StringField('Email Address', [InputRequired()])
    password = PasswordField('Password', [InputRequired()])


class SignIn(Form):
    """Sign in form."""

    username = StringField('Username', [InputRequired()])
    password = PasswordField('Password', [InputRequired()])


class Register(Form):
    """
    This is our Register form. It's used for the user to pass the 'Activation Code'. The activation code will be sent to
    the party service, in turn get resolved in the 'case service'. If succesfull we can progress with registration. The
    'Activation Code' is a string in our case.
    """
    activation_code = StringField('ActivationCode', [InputRequired()])



