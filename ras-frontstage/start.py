from flask import Flask
app = Flask(__name__)
#app.run(debug=True)

@app.route('/')
def hello_world():
    return 'Hello, World!'

from flask import render_template

@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)

@app.route('/login/')
def log_in():
    return render_template('login.html')

@app.route('/success/')
def login_success():
    return render_template('success.html')

