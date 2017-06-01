"""
This module contains the data model for the collection instrument
"""
import datetime
from flask_wtf import Form
from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import TEXT, JSON, UUID
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import DecimalField, SelectField, PasswordField, StringField, IntegerField, BooleanField
from wtforms.validators import InputRequired, EqualTo, Length, DataRequired, NumberRange, Email, ValidationError
import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException
from flask_sqlalchemy import SQLAlchemy
import logging

db = SQLAlchemy()

logger = logging.getLogger(__name__)


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
            logger.debug("Password checks out. Password in {}, password I have: {}".format(password, self.pwdhash))
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
    """
    Registration form.
    This is our Register form and part 3 of registration. It allows the user to pass all details to create an account.
    The form data will be used to create the account on the OAuth2 server and to provide the Case Service with a valid
    account name that is not verified.
    """

    first_name = StringField('First name', validators=[InputRequired(), Length(max=254, message='Your first name must be less than 254 characters')])
    last_name = StringField('Last name', validators=[InputRequired(), Length(max=254, message='Your last name must be less than 254 characters')])
    email_address = StringField('Enter your email address', validators=[InputRequired(), Email(message="Your email shoud be of the form 'myname@email.com' "), Length(max=254, message='Your email must be less than 254 characters')])
    email_address_confirm = StringField('Re-type your email address', validators=[DataRequired(), EqualTo('email_address', message='Emails must match'), Length(max=254, message='Your email must be less than 254 characters')])
    password = PasswordField( 'Create a password', validators=[DataRequired(), Length(min=8, max=254, message='Your password must be more than 8 characters')])
    password_confirm = PasswordField('Re-type your password', validators=[DataRequired(), EqualTo('password', message='Passwords must match'), Length(min=8, max=254, message='Your password must be more than 8 characters')])
    phone_number = StringField('Enter your phone number', validators=[DataRequired(), Length(min=9, max=15, message="This should be a valid phone number between 9 and 15 digits")], default=None)

    terms_and_conditions = BooleanField('Please confirm you accept our terms and conditions ' )

    def validate_phone_number(form, field):
        if len(field.data) > 16:
            raise ValidationError('This should be a valid phone number between 9 and 15 digits')
        try:
            logger.debug("Checking this is a valid GB Number")
            input_number = phonenumbers.parse(field.data, "GB")                 # Tell the parser we are looking for a GB number

            if not (phonenumbers.is_possible_number(input_number)):
                raise ValidationError('This should be a valid phone number between 9 and 15 digits')

            if not (phonenumbers.is_valid_number(input_number)):
                raise ValidationError('Please use a valid UK number e.g. 01632 496 0018.')
        except NumberParseException:
            logger.debug(" There is a number parse exception in the phonenumber field")
            raise ValidationError('This should be a valid UK number e.g. 01632 496 0018. ')


class LoginForm(Form):
    """Login form."""

    username = StringField('Email Address', [InputRequired()])
    password = PasswordField('Password', [InputRequired()])


class SignIn(Form):
    """Sign in form."""

    username = StringField('Username', [InputRequired()])
    password = PasswordField('Password', [InputRequired()])


class ActivationCodeForm(Form):
    """
    This is our Register form and part 1 of registration. It's used for the user to pass the 'Activation Code'. The
    activation code will be sent to the party service, in turn get resolved in the 'case service'. If successful we can
    progress with registration. The 'Activation Code' is a string in our case.
    """
    activation_code = StringField('Activation Code', [InputRequired()])
