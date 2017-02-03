from functools import wraps, update_wrapper
from datetime import datetime
from flask import Flask, make_response
app = Flask(__name__)
app.debug = True

@app.route('/')
def hello_world():
    return 'Hello, World!'

from flask import render_template

@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)

@app.route('/sign-in/')
def log_in():
    return render_template('sign-in.html', _theme='default')

@app.route('/register/')
def register():
    return render_template('register.html')

@app.route('/success/')
def login_success():
    return render_template('success.html')


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


if __name__ == '__main__':
    app.run( host='0.0.0.0', port=5000)
