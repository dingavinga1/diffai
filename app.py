from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json

from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import joblib

from urllib.parse import urlparse, unquote

import time
import subprocess
import threading

from train import train_model

# Creating a Socket-IO Wrapper for Flask Application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Reading all user-defined rules and parsing them
with open("rules.json", "r") as rfile:
	rules=json.loads(rfile.read())

# Debug Output for MITMProxy Connection
@socketio.on('connect', namespace="/")
def connect_handle():
    print("Proxy Connected")

# Debug Output for Frontend Connection
@socketio.on('connect', namespace="/web")
def connect_handle_web():
    print("Web Connected")


# Function to make predictions using our AI Model 
def predict(url):
	parsed_url=urlparse(url) #decoding URL
	url=parsed_url.path+parsed_url.params+parsed_url.query+parsed_url.fragment

	url=unquote(url)

	model, vectorizer=joblib.load('model.joblib') #loading saved model
	test=[{
		'url':url
	}]
	df=pd.DataFrame(test)
	X=vectorizer.transform(df['url'])

	# making a prediction on our new data
	y_pred=model.predict(X)

	if y_pred==1:
		return True
	else:
		return False

# Function to match user-defined rules and AI-based detection
def check_alert(data):
	# parsing to match rules with new request recieved
	for rule in rules:
		flag=True
		for key, value in rule.items():
			if key!='alert' and key!='headers':
				if key not in data:
					flag=False
					break
				if value not in data[key]:
					flag=False
					break


		if 'headers' in rule:
			for key, value in rule['headers'].items():
				if key not in data['headers']:
					flag=False
					break
				if value not in data['headers'][key]:
					flag=False
					break

		log={'time': str(int(time.time()))}
		writeFlag=False

		# checking if user-defined alert was triggered
		if flag:
			socketio.emit('new_alert', {'alert':  rule['alert']}, namespace="/web")
			log['alert']=rule['alert']
			writeFlag=True

		# matching with AI-based detection
		else:
			pred=predict(data['url'])
			if pred:
				socketio.emit('new_alert', {'alert':  '[!] AI detected an anomaly with URL '+data['url']}, namespace="/web")
				log['alert']='[!] AI detected an anomaly with URL '+data['url']
				writeFlag=True
		# logging alert
		if writeFlag:
			with open("alert.log", "a") as logfile:
				logfile.write(log['time']+" - "+log['alert']+"\n")

# socket io event handler for new request 
@socketio.on('request', namespace="/")
def handle_request(data):
    check_alert(dict(data))

# socket io event handler  for training model
@socketio.on('train', namespace="/web")
def handle_train(data):
    socketio.emit("train_log", {'log':"Processing... It is advised not to change the page during training. It may result in a crash."}, namespace="/web")
    socketio.start_background_task(train_model, data['goodpath'], data['badpath'])
    socketio.emit("train_log", {'log': ""}, namespace="/web")
    socketio.emit("train_log", {'log': "Model trained successfully"}, namespace="/web")

# default route for web UI
@app.route("/")
def home():
	return render_template("index.html")


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000)
