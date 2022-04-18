# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.express as px
import plotly.graph_objects as go 
import numpy as np 
import pandas as pd
from time import sleep
import time
import sys, os
import boto3
from boto3.dynamodb.conditions import Key, Attr

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
AWS_ACCESS_KEY="AKIA2ZGOWDKUERXHLP6X"
AWS_SECRET_ACCESS_KEY="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"
AWS_REGION="us-east-1"
dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                            region_name=AWS_REGION)
tweet = dynamodb.Table('Tweet')

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

now=int(time.time())
timestampold=now-3600

response = tweet.scan(
	    FilterExpression=Attr('timestamp').gt(timestampold)
	)
items = response['Items']

while len(items) == 0:
	now=int(time.time())
	timestampold=now-3600
	response = table.scan(
	    FilterExpression=Attr('timestamp').gt(timestampold)
	)
	items = response['Items']

timestamp = []
latitude = []
longitude = []
count = []
sentiment = []
sentimentValues = []
tweet_name = []
tweet_text = []
tweet_user_id = []
sentiment_names = ['POSITIVE', 'NEGATIVE', 'NEUTRAL', 'MIXED']
sentiment_count = []

for i in items:
	timestamp.append(int(i['timestamp']))
	splitlocation = i['location'].split(',')
	latitude.append(float(splitlocation[0]))
	longitude.append(float(splitlocation[1]))
	count.append(1)
	sentValue = int(i['sentiment'])
	sentName = 'NEUTRAL'
	if sentValue < 0:
		sentName = 'NEGATIVE'
	if sentValue == 0:
		sentName == 'NEUTRAL'
	if sentValue == 1:
		sentName = 'MIXED'
	if sentValue > 1:
		sentName = 'POSITIVE'
	sentiment.append(sentName)
	sentimentValues.append(int(i['sentiment']))
	tweet_name.append(i['tweet_name'])
	tweet_text.append(i['tweet_text'])
	tweet_user_id.append(i['tweet_user_id'])

for name in sentiment_names:
	sumCount = 0
	for i in sentiment:
		if i == name:
			sumCount = sumCount + 1
	sentiment_count.append(sumCount)

piedf = pd.DataFrame({
	"sentiment_names": sentiment_names,
	"sentiment_count": sentiment_count
})

linedf = pd.DataFrame({
	"timestamp": timestamp,
	"sentimentValues": sentimentValues,
})

linedf = linedf.groupby('timestamp').mean()

mapdf = pd.DataFrame({
	"latitude": latitude,
	"longitude": longitude,
	"count": count
})

mapdf = mapdf.groupby(['latitude','longitude']).agg({'count':sum})

tabledf = pd.DataFrame({
	"timestamp": timestamp,
	"sentiment": sentiment,
	"tweet_text": tweet_text,
	"tweet_user_id": tweet_user_id
})

pie = px.pie(piedf, values='sentiment_count', names='sentiment_names', title='Pie Chart of Sentiment for Tweets')

line = px.line(linedf, x=linedf.index, y='sentimentValues', title='Sentiment Values Per Timestamp')


scale = 1.5
mapfig = go.Figure(data=go.Scattergeo(
	lat=mapdf.reset_index()['latitude'], lon=mapdf.reset_index()['longitude'], text='<br>Count: ' + mapdf['count'].astype(str), geojson='natural earth', marker=dict(size=mapdf['count']*scale)
))

mapfig.update_layout(title_text = 'Map of Tweet Locations')

app.layout = html.Div(children=[
    html.H1(children='Dashboard for TwitterStream'),

    html.Div(children='A variety of visualizations to display processed data from Twitter.'),

    dcc.Graph(
        id='pie',
        figure=pie
    ),

    dcc.Graph(
    	id='line',
    	figure=line
    ),

    dcc.Graph(
    	id='map',
    	figure=mapfig
    ),

    dash_table.DataTable(
    	id='table',
    	columns=[{'id': i, 'name': i} for i in tabledf.columns],
    	style_cell={'textAlign':'left'},
    	data=tabledf.to_dict('records')
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)