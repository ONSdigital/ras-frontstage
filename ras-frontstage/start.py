from flask import Flask, send_from_directory
app = Flask(__name__)
app.debug = True

@app.route('/')
def hello_world():
    return 'Hello, World!'

from flask import render_template

@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('pages/hello.html', name=name)

@app.route('/sign-in/')
def log_in():
    return render_template('pages/sign-in.html')

@app.route('/register/')
def register():
    return render_template('pages/register.html')

@app.route('/success/')
def login_success():
    return render_template('pages/success.html')


if __name__ == '__main__':
    app.run( host='0.0.0.0', port=5000)
