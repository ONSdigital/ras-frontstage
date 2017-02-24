from __future__ import print_function
from functools import wraps, update_wrapper
from datetime import datetime
from flask import Flask, make_response, render_template, request

app = Flask(__name__)
app.debug = True

@app.route('/')
def hello_world():
    return 'Hello, World!'

#@app.route('/hello/')
#@app.route('/hello/<name>')
#def hello(name=None):
    #return render('hello.html', name=name)

@app.route('/sign-in/')
def sign_in():
    querystring = request.args

    #data variables configured: [error: <undefined, failed, last-attempt>]
    return render_template('sign-in.html', _theme='default', data = querystring, method = 'get')

@app.route('/troubleshoot-sign-in/')
def troubleshoot_sign_in():
    return render('sign-in-trouble.html')

@app.route('/account-locked/')
def account_locked():
    return render('sign-in-locked-account.html')

@app.route('/forgot-password/')
def forgot_password():
    return render('forgot-password.html')

@app.route('/register/')
def register():
    return render('register.html')

@app.route('/enter-your-details/')
def enter_your_details():
    return render('enter-your-details.html')

@app.route('/confirm-organisation-survey/')
def confirm_organisation_survey():
    return render('confirm-organisation-survey.html')

@app.route('/almost-done/')
def almost_done():
    return render('almost-done.html')


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

if __name__ == '__main__':
    app.run( host='0.0.0.0', port=5000)
