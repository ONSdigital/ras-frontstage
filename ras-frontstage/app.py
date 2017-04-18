"""
Main file that is ran
"""

#from __future__ import print_function
from functools import wraps, update_wrapper
from datetime import datetime
from flask import Flask, make_response, render_template, request
import os
import requests

from flask import Flask, make_response, render_template, request, flash, redirect, url_for, session, Response
from flask_sqlalchemy import SQLAlchemy
from oauthlib.oauth2 import LegacyApplicationClient, MissingTokenError, MissingClientIdError, MismatchingStateError
from requests_oauthlib import OAuth2Session

from sqlalchemy import exc

from jwt import encode, decode
from models import *
from config import OAuthConfig

app = Flask(__name__)
app.debug = True

if 'APP_SETTINGS' in os.environ:
    app.config.from_object(os.environ['APP_SETTINGS'])

db = SQLAlchemy(app)

def get_user_scopes(username):
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


@app.route('/')
@app.route('/home', methods=['GET', 'POST'])
def hello_world():
    return render_template('_temp.html', _theme='default')

@app.route('/')
@app.route('/logged-in', methods=['GET', 'POST'])
def logged_in():
    """Logged in page for users only."""
    if session.get('jwt_token'):
        return render_template('signed-in.html', _theme='default', data={"error": {"type": "success"}})

    return render_template('signed-in.html', _theme='default', data={"error": {"type": "failed"}})
    #res = Response(response="Not authorised", status=403, mimetype="text/html")
    #return res


@app.route('/protected/collectioninstrument', methods=['GET'])
def protected_collection():
    """Protected method to return full list of collectioninstrument json."""
    if session.get('jwt_token'):
        jwttoken = session.get('jwt_token')

        decodedJWT = decode(jwttoken)
        userID = decodedJWT['user_id']

        try:
            user_object = User.query.filter_by(username=userID).first()
            # Check the tokens are the same
            # TODO Check the token has not expired
            if user_object.token == jwttoken:

                headers = {'authorization': jwttoken}
                url = 'localhost:5000/collectioninstrument'
                req = requests.get(url,  headers=headers)
                data = req.json()
                print(data)
                res = Response(response=data, status=200, mimetype="application/json")
                return res

            res = Response(response="""Your session is stale, try logging in again to
                                     refresh your session variables""", status=404, mimetype="text/html")
            return res
        except:
            res = Response(response="""Looks like you are not a valid user,
                           try logging in again and refresh your session""", status=404, mimetype="text/html")
            return res


@app.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username')
    if 'jwt_token' in session:
        session.pop('jwt_token')

    flash('You have successfully logged out.', 'success')
    return redirect(url_for('login_OAuth'))


# ===== Sign in =====
@app.route('/sign-in/', methods=['GET', 'POST'])
def login():
    print("*** Hitting login() function.... ***")
    """Login Page."""
    form = LoginForm(request.form)

    if request.method == 'POST' and form.validate():
        username = request.form.get('username')
        password = request.form.get('password')
        print("Username is: {}".format(username))
        print("Password is: {}".format(password))

        existing_user = User.query.filter_by(username=username).first()

        if not (existing_user and existing_user.check_password_simple(password)):
            flash('Invalid username or password. Please try again.', 'danger')
            print("Failed validation")
            return render_template('sign-in.html', _theme='default', form=form, data={"error": {"type": "failed"}})

        session['username'] = username

        usr_scopes = get_user_scopes(username)

        data_dict_for_jwt_token = {"username": username, "user_scopes": usr_scopes }

        encoded_jwt_token = encode(data_dict_for_jwt_token)
        session['jwt_token'] = encoded_jwt_token

        flash('You have successfully logged in.', 'success')
        print("validation OK")
        return redirect(url_for('logged_in'))

    if form.errors:
        flash(form.errors, 'danger')

    templateData = {
        "error": {
            "type": request.args.get("error")
        }
    }

    return render_template('sign-in.html', _theme='default', form=form, data=templateData)

# ===== Sign in using OAuth2 =====
@app.route('/sign-in/OAuth', methods=['GET', 'POST'])
def login_OAuth():
    print("*** Hitting login for OAuth() function.... ***")
    """ Login OAuth Page.
    This function uses the OAuth 2 server to receive a token upon successful sign in. If the user presents the correct
    password and username and is accepted by the OAuth 2 server we receive an access token, a refresh token and a TTL.
    Otherwise we fail.
    This uses the flow Resource Owner Password Credentials Grant. See: https://tools.ietf.org/html/rfc6749#section-4.3

    To make this work the server application (thats us!) needs a client ID and a client secret. This has to exist on the
    OAuth server. We then use Basic Auth to access the OAuth2 server and provide the user ID, and user password in the
    POST Body message. In the real world this would be done over https - for now all this works over http since it is
    behind our firewall.

    Parms_to_OAuth:
        client_id
        client_secret
        user_id
        user_password
        oauth2_url

    Returned_from_OAuth:
        access_token
        refresh_token
        ttl

    """
    form = LoginForm(request.form)

    if request.method == 'POST' and form.validate():
        username = request.form.get('username')
        password = request.form.get('password')
        print("Username is: {}".format(username))
        print("Password is: {}".format(password))

        # Creates a 'session client' to interact with OAuth2. This provides a client ID to our client that is used to
        # interact with the server.
        client = LegacyApplicationClient(client_id=OAuthConfig.RAS_FRONTSTAGE_CLIENT_ID)

        # Populates the request body with username and password from the user
        client.prepare_request_body(username=username, password=password, scope=['ci.write', 'ci.read'])

        # passes our 'client' to the session management object. this deals with the transactions between the OAuth2 server
        oauth = OAuth2Session(client=client)

        token_url = OAuthConfig.ONS_OAUTH_PROTOCOL + OAuthConfig.ONS_OAUTH_SERVER + OAuthConfig.ONS_TOKEN_ENDPOINT
        print "Our Token Endpoint is: ", token_url

        try:
            token = oauth.fetch_token(token_url=token_url, username=username, password=password, client_id=OAuthConfig.RAS_FRONTSTAGE_CLIENT_ID, client_secret=OAuthConfig.RAS_FRONTSTAGE_CLIENT_SECRET)
            print " *** Access Token Granted *** "
            print " Values are: "
            for key in token:
                print key, " Value is: ", token[key]
        except MissingTokenError as e:
            print "Missing token error, error is: {}".format(e)
            print("Failed validation")
            return render_template('sign-in-oauth.html', _theme='default', form=form, data={"error": {"type": "failed"}})

        session['username'] = username
        usr_scopes = token['scope']
        data_dict_for_jwt_token = {"username": username, "user_scopes": usr_scopes, 'access_token':token['access_token'] }

        #data_dict_for_jwt_token = {"username": username, "user_scopes": usr_scopes }
        #encoded_jwt_token = encode(data_dict_for_jwt_token)

        session['jwt_token'] = token['access_token']

        print("validation OK")
        return redirect(url_for('logged_in'))

    templateData = {
        "error": {
            "type": request.args.get("error")
        }
    }

    return render_template('sign-in-oauth.html', _theme='default', form=form, data=templateData)



@app.route('/sign-in/error', methods=['GET'])
def sign_in_error():

    password= request.form.get('pass')
    password= request.form.get('emailaddress')

    templateData = {
        "error": {
            "type": "failed"
        }
    }

    #data variables configured: {"error": <undefined, failed, last-attempt>}
    return render_template('sign-in.html', _theme='default', data=templateData)

@app.route('/sign-in/troubleshoot')
def sign_in_troubleshoot():
    return render('sign-in.trouble.html')

@app.route('/sign-in/final-sign-in')
def sign_in_last_attempt():
    return render('sign-in.last-attempt.html')

@app.route('/sign-in/account-locked/')
def sign_in_account_locked():
    return render('sign-in.locked-account.html')


# ===== Forgot password =====
@app.route('/forgot-password/')
def forgot_password():
    templateData = {
        "error": {
            "type": request.args.get("error")
        }
    }

    #data variables configured: {"error": <undefined, failed>}
    return render_template('forgot-password.html', _theme='default', data=templateData)

@app.route('/forgot-password/check-email/')
def forgot_password_check_email():
    return render('forgot-password.check-email.html')


# ===== Reset password =====
@app.route('/reset-password/')
def reset_password():
    templateData = {
        "error": {
            "type": request.args.get("error")
        }
    }

    print(request.args.get("error"))

    #data variables configured: {"error": <undefined, password-mismatch>}
    return render_template('reset-password.html', _theme='default', data=templateData)

@app.route('/reset-password/confirmation/')
def reset_password_confirmation():
    return render('reset-password.confirmation.html')


# ===== Registration =====
@app.route('/create-account/', methods=['GET', 'POST'])
def register():

    form = ActivationCodeForm(request.form)

    if request.method == 'POST' and form.validate():
        activation_code = request.form.get('activation_code')
        print "Activation code is: {}".format(activation_code)

    if form.errors:
        flash(form.errors, 'danger')

    templateData = {
        "error": {
            "type": request.args.get("error")
        }
    }

    return render_template('register.html', _theme='default', form=form, data=templateData)

# This take all the user credentials and then creates an account on the OAuth2 server
@app.route('/create-account/enter-account-details/', methods=['GET', 'POST'])
def register_enter_your_details():

    form = RegistrationForm(request.form)

    if request.method == 'POST' and form.validate():

        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email_address = request.form.get('email_address')
        email_address_confirm = request.form.get('email_address_confirm')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        phone_number = request.form.get('phone_number')
        terms_and_conditions = request.form.get('terms_and_conditions')

        print ("User name is: {} {}".format(first_name, last_name))
        print ("Email is: {}".format(email_address))
        print ("Confirmation email is: {}".format(email_address_confirm))
        print ("password is: {}".format(password))
        print ("Confirmation password is: {}".format(password_confirm))
        print ("phone number is: {}".format(phone_number))
        print ("T's&C's is: {}".format(terms_and_conditions))

        # Lets try and create this user on the OAuth2 server
        data = {"username": email_address, "password": password, "client_id": OAuthConfig.RAS_FRONTSTAGE_CLIENT_ID, "client_secret": OAuthConfig.RAS_FRONTSTAGE_CLIENT_SECRET }
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        authorisation=(OAuthConfig.RAS_FRONTSTAGE_CLIENT_ID, OAuthConfig.RAS_FRONTSTAGE_CLIENT_SECRET)

        try:

            OAuthurl = OAuthConfig.ONS_OAUTH_PROTOCOL + OAuthConfig.ONS_OAUTH_SERVER + OAuthConfig.ONS_ADMIN_ENDPOINT
            OAuth_response = requests.post(OAuthurl, auth=authorisation, headers=headers, data=data)

            print "OAuth response is: {}".format(OAuth_response.content)
            # TODO A utility function to allow us to route to a page for 'user is registered already'. We need a html page for this.

        except requests.exceptions.ConnectionError:
            print  "There seems to be no server listening on this connection?"
            # TODO A redirect to a page that helps the user

        except requests.exceptions.Timeout:
            print "Timeout error. Is the OAuth Server overloaded?"
            # TODO A redirect to a page that helps the user
        except requests.exceptions.RequestException as e:
            # TODO catastrophic error. bail. A page that tells the user something horrid has happeded and who to inform
            print e

        OAuth_response.raise_for_status()                       # A stop gap until we know all the correct error pages
        return render_template('register.almost-done.html', _theme='default', email=email_address)

    else:
        print "either this is not a POST, or form validation failed"
        print "Form failed validation, errors are: {}".format(form.errors)

    return render_template('register.enter-your-details.html', _theme='default', form=form, errors=form.errors)


@app.route('/create-account/confirm-organisation-survey/')
def register_confirm_organisation_survey():
    return render('register.confirm-organisation-survey.html')


@app.route('/create-account/check-email/')
def register_almost_done():
    return render('register.almost-done.html')


#Disable cache for development
def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    return update_wrapper(no_cache, view)

def render(template):
    return render_template(template, _theme='default')


@app.route('/protected/collectioninstrument/id/<string:_id>', methods=['GET', 'POST'])
def get_id(_id):
    """
    Method to return collection instrument json by ID.
    """
    # app.logger.info('get_id with value: {} '.format(_id))

    # First check we have a jwt token.
    if (session.get(('jwt_token') and session.get('username'))):
        jwttoken = session.get('jwt_token')

        # If we can decode the the token we need to get the user ID out and
        # ensure it's a valid token for that user in our database
        decodedJWT = decode(jwttoken)
        userID = decodedJWT['user_id']

        # lets find a user with this ID and check the token

        try:
            user_object = User.query.filter_by(username=userID).first()
            # Check the tokens are the same
            # TODO Check the token has not expired
            if user_object.token == jwttoken:
                # OK Tokens match we can forward this on to our collection instrument
                headers = {'authorization': jwttoken}
                # TODO make the calling of this URL a utility function
                url = 'localhost:5000/collectioninstrument/id/' + '_id'             # OK construct the URL now we know it's a valid token
                # Depending on wheather this is a put or a get will change how we forward on this message
                if request.method['GET']:
                    req = requests.get(url,  headers=headers)
                if request.method['PUT']:
                    req = requests.post(url,  headers=headers)
                data = req.json()
                print(data)
                res = Response(response=data, status=200, mimetype="application/json")
                return res

            # Anything else but a token match means we reject the call
            print("tokens don't match")
            res = Response(response="""Your session is stale, try logging in again to
                                     refresh your session variables""", status=404, mimetype="text/html")
            return res
        except:
            print("failure to find a user with this ID")
            res = Response(response="""Looks like you are not a valid user,
                           try logging in again and refresh your session""", status=404, mimetype="text/html")
            return res

    # If we hit here then the request did not have a token or username set
    res = Response(response="Not authorised", status=403, mimetype="text/html")
    return res

if __name__ == '__main__':
    #PORT = int(os.environ.get('PORT', 5001))
    app.run( host='0.0.0.0', port=5001)

