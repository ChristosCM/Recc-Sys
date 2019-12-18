from flask import Flask, render_template, request, redirect, Response
import sys
app = Flask(__name__)


@app.route('/')
def output():
	# serve index template
	return render_template('index.html', name='Joe')


@app.route('/receiver', methods = ['POST'])
def worker():
	# read json + reply
    data = request.get_json()
    result = ''
    for item in data:
        # loop over every row
        result += str(item['make']) + '\n'

    return result

@app.route('/index')
def index():
    return render_template('data.html',results=[
        {
            "UserID":"Chris",
            "BookID":"Good Book",
            "Rating":"5/5"
        }
    ])

if __name__ == '__main__':
    app.run()