from __future__ import print_function
from functools import wraps, update_wrapper
from datetime import datetime
from flask import Flask, make_response, render_template, request

app = Flask(__name__)
app.debug = True


@app.route('/')
def hello_world():
    return render_template('_temp.html', _theme='default')

#@app.route('/hello/')
#@app.route('/hello/<name>')
#def hello(name=None):
    #return render('hello.html', name=name)


# ===== Sign in =====
@app.route('/sign-in/', methods=['GET','POST'])
def sign_in():

    password= request.form.get('pass')
    password= request.form.get('emailaddress')
    
    templateData = {
        "error": {
            "type": request.args.get("error")
        }
    }

    #data variables configured: {"error": <undefined, failed, last-attempt>}
    return render_template('sign-in.html', _theme='default', data=templateData)

@app.route('/sign-in/troubleshoot')
def sign_in_troubleshoot():
    return render('sign-in.trouble.html')

@app.route('/account-locked/')
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
@app.route('/register/')
def register():
    return render('register.html')

@app.route('/register/enter-your-details/')
def register_enter_your_details():
    return render('register.enter-your-details.html')

@app.route('/register/confirm-organisation-survey/')
def register_confirm_organisation_survey():
    return render('register.confirm-organisation-survey.html')

@app.route('/register/almost-done/')
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

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 5000))
    app.run( host='0.0.0.0', port=PORT)
