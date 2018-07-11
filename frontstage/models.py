import logging
import enum
import phonenumbers

from flask_wtf import FlaskForm
from phonenumbers.phonenumberutil import NumberParseException
from structlog import wrap_logger
from wtforms import HiddenField, PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import InputRequired, EqualTo, Length, DataRequired, Email, ValidationError

from frontstage import app

logger = wrap_logger(logging.getLogger(__name__))


class EnrolmentCodeForm(FlaskForm):
    enrolment_code = StringField('Enrolment Code', [InputRequired(), Length(min=12,
                                                                            max=12,
                                                                            message='Please re-enter '
                                                                                    'the code and try again')])


class RegistrationForm(FlaskForm):
    first_name = StringField('First name',
                             validators=[InputRequired('First name is required'),
                                         Length(max=254,
                                                message='Your first name must be less than 254 characters')])
    last_name = StringField('Last name',
                            validators=[InputRequired('Last name is required'),
                                        Length(max=254, message='Your last name must be less than 254 characters')])
    email_address = StringField('Enter your email address',
                                validators=[InputRequired('Email address is required'),
                                            Email(message="Your email should be of the form 'myname@email.com' "),
                                            Length(max=254,
                                                   message='Your email must be less than 254 characters')])
    password = PasswordField('Create a password',
                             validators=[DataRequired('Password is required'),
                                         EqualTo('password_confirm', message=app.config['PASSWORD_MATCH_ERROR_TEXT']),
                                         Length(min=app.config['PASSWORD_MIN_LENGTH'],
                                                max=app.config['PASSWORD_MAX_LENGTH'],
                                                message=app.config['PASSWORD_CRITERIA_ERROR_TEXT'])])
    password_confirm = PasswordField('Re-type your password')
    phone_number = StringField('Enter your phone number',
                               validators=[DataRequired('Phone number is required'),
                                           Length(min=9,
                                                  max=15,
                                                  message='This should be a valid phone number between 9 and 15 digits')],
                               default=None)
    enrolment_code = HiddenField('Enrolment Code')

    @staticmethod
    def validate_phone_number(form, field):
        try:
            logger.debug('Checking this is a valid GB phone number')
            input_number = phonenumbers.parse(field.data, 'GB')  # Tell the parser we are looking for a GB number

            if not phonenumbers.is_possible_number(input_number):
                raise ValidationError('This should be a valid phone number between 9 and 15 digits')

            if not phonenumbers.is_valid_number(input_number):
                raise ValidationError('Please use a valid UK number e.g. 01632 496 0018.')
        except NumberParseException:
            logger.debug('There is a number parse exception in the phonenumber field')
            raise ValidationError('This should be a valid UK number e.g. 01632 496 0018. ')

    @staticmethod
    def validate_email_address(form, field):
        logger.debug('Checking if the email address contains a space')
        # this extends the email validator to check if there is whitespace in the email
        if ' ' in field.data:
            logger.debug('Space found in email address')
            raise ValidationError('Your email should be of the form myname@email.com')

    @staticmethod
    def validate_password(form, field):
        password = field.data
        if password.isalnum() or not any(char.isupper() for char in password) or not any(char.isdigit() for char in password):
            raise ValidationError(app.config['PASSWORD_CRITERIA_ERROR_TEXT'])


class LoginForm(FlaskForm):
    username = StringField('Email Address', [InputRequired('Email Address is required'),
                                             Email("Your email should be of the form 'myname@email.com' ")])
    password = PasswordField('Password', [InputRequired('Password is required')])


class ForgotPasswordForm(FlaskForm):
    email_address = StringField('Enter your email address',
                                validators=[InputRequired('Email address is required'),
                                            Email(message="Your email should be of the form 'myname@email.com' "),
                                            Length(max=254,
                                                   message='Your email must be less than 254 characters')])


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New password',
                             validators=[DataRequired('Password is required'),
                                         EqualTo('password_confirm', message=app.config['PASSWORD_MATCH_ERROR_TEXT']),
                                         Length(min=app.config['PASSWORD_MIN_LENGTH'],
                                                max=app.config['PASSWORD_MAX_LENGTH'],
                                                message=app.config['PASSWORD_CRITERIA_ERROR_TEXT'])])
    password_confirm = PasswordField('Re-type new password')

    @staticmethod
    def validate_password(form, field):
        password = field.data
        if password.isalnum() or not any(char.isupper() for char in password) or not any(char.isdigit() for char in password):
            raise ValidationError(app.config['PASSWORD_CRITERIA_ERROR_TEXT'])


class SecureMessagingForm(FlaskForm):
    send = SubmitField(label='Send', id='send-message-btn')
    subject = StringField('Subject')
    body = TextAreaField('Message')
    msg_id = HiddenField('Message id')
    thread_id = HiddenField('Thread id')
    hidden_subject = HiddenField('Hidden Subject')

    @staticmethod
    def validate_subject(form, field):
        subject = form['hidden_subject'].data if form['hidden_subject'].data else field.data

        if len(subject) > 96:
            raise ValidationError('Subject field length must not be greater than 100')
        if form.send.data and not subject or subject.isspace():
            raise ValidationError('Please enter a subject')

    @staticmethod
    def validate_body(form, field):
        body = field.data
        if len(body) > 10000:
            raise ValidationError('Body field length must not be greater than 10000')
        if form.send.data and not body:
            raise ValidationError('Please enter a message')


class RespondentStatus(enum.IntEnum):
    CREATED = 0
    ACTIVE = 1
    SUSPENDED = 2
