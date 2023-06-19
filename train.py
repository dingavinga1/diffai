import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import sys
from flask_socketio import SocketIO

# model training function
def train_model(good_file_path, bad_file_path):
	# reading from dataset
	with open(good_file_path, "r", encoding="utf-8") as goodFile, open(bad_file_path, "r", encoding="utf-8") as badFile:
	    good=goodFile.readlines()
	    bad=badFile.readlines()

	# adding labels to good data and bad data
	goodData={
	    "url":good,
	    "Label": [0 for _ in range(len(good))]
	}

	badData={
	    "url":bad,
	    "Label": [1 for _ in range(len(bad))]
	}

	# creating a dataframe from datasets
	goodDf=pd.DataFrame(goodData)
	badDf=pd.DataFrame(badData)

	df=pd.concat([goodDf, badDf])

	# binary encoding of string features
	vectorizer=TfidfVectorizer()
	X=vectorizer.fit_transform(df['url'])

	y=df['Label']

	# Splitting our dataset into train and test to get accuracy
	X_train, X_test, y_train, y_test=train_test_split(X, y, test_size=0.2, random_state=42)

	# Creating, training and saving our newly created model
	model=LogisticRegression(max_iter=1000)
	model.fit(X_train, y_train)
	import joblib
	joblib.dump((model, vectorizer), 'model.joblib')

	# Printing and returning accuracy
	score=model.score(X_test, y_test)
	print(f"Score: {score}")
	return score