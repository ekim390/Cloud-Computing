import sys, os
from time import sleep
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import csv
import boto3
from boto3.dynamodb.conditions import Key, Attr

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
AWS_ACCESS_KEY="AKIA2ZGOWDKUERXHLP6X"
AWS_SECRET_ACCESS_KEY="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"
AWS_REGION="us-east-1"

dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                            region_name=AWS_REGION)

table = dynamodb.Table('AirQualityData')

# for stationID: ST102
timestamp_2 = []
pm25_2 = []
pm10_2 = []
co_2 = []
so2_2 = []

# for stationID: ST105
timestamp_5 = []
pm25_5 = []
pm10_5 = []
co_5 = []
so2_5 = []

# for stationID: ST102
plt.figure(1)
plt.suptitle('ST102 Raw Data Graph')
plt.xlabel('Timestamp')

ax1 = plt.subplot(2, 1, 1)
ax1.set_yticks(np.arange(0, 600, 100))
ax2 = plt.subplot(2, 1, 2)

# for stationID: ST105
plt.figure(2)
plt.suptitle('ST105 Raw Data Graph')
plt.xlabel('Timestamp')

ax3 = plt.subplot(2, 1, 1)
ax3.set_yticks(np.arange(0, 600, 100))
ax4 = plt.subplot(2, 1, 2)

now=int(time.time())
timestampold=now-3600

response = table.scan(
	    FilterExpression=Key('stationID').eq('ST102') & Attr('timestamp').gt(timestampold)
	)
items_2 = response['Items']

response = table.scan(
	    FilterExpression=Key('stationID').eq('ST105') & Attr('timestamp').gt(timestampold)
	)
items_5 = response['Items']

while len(items_2) == 0:
	now=int(time.time())
	timestampold=now-3600
	response = table.scan(
	    FilterExpression=Key('stationID').eq('ST102') & Attr('timestamp').gt(timestampold)
	)
	items_2 = response['Items']

def animate_2(i):
	# for stationID: ST102
	timestamp_2 = []
	pm25_2 = []
	pm10_2 = []
	co_2 = []
	so2_2 = []

	now=int(time.time())
	timestampold=now-3600

	response = table.scan(
	    FilterExpression=Key('stationID').eq('ST102') & Attr('timestamp').gt(timestampold)
	)

	items = response['Items']

	for i in items:
		timestamp_2.append(int(i['timestamp']))
		pm25_2.append(float(i['data']['pm2_5']))
		pm10_2.append(float(i['data']['pm10']))
		co_2.append(float(i['data']['co']))
		so2_2.append(float(i['data']['so2']))


	# ST102 graph
	plt.figure(1)
	ax1.clear()
	ax2.clear()

	#ax1 = plt.subplot(2, 1, 1)
	ax1.plot(timestamp_2, pm25_2, color='green', label='PM2.5')
	ax1.plot(timestamp_2, pm10_2, color='red', label='PM10')
	ax1.set_xticks(np.arange(min(timestamp_2), max(timestamp_2), 100))
	ax1.legend(loc="upper right")

	#ax2 = plt.subplot(2, 1, 2)
	ax2.plot(timestamp_2, co_2, color='orange', label='CO')
	ax2.plot(timestamp_2, so2_2, color='purple', label='SO2')
	ax2.set_xticks(np.arange(min(timestamp_2), max(timestamp_2), 100))
	ax2.set_yticks(np.arange(0, max(co_2), .5))
	ax2.legend(loc="upper right")

while len(items_5) == 0:
	now=int(time.time())
	timestampold=now-3600
	response = table.scan(
		    FilterExpression=Key('stationID').eq('ST105') & Attr('timestamp').gt(timestampold)
		)
	items_5 = response['Items']

def animate_5(i):
	# for stationID: ST105
	timestamp_5 = []
	pm25_5 = []
	pm10_5 = []
	co_5 = []
	so2_5 = []

	now=int(time.time())
	timestampold=now-3600

	response = table.scan(
	    FilterExpression=Key('stationID').eq('ST105') & Attr('timestamp').gt(timestampold)
	)

	items = response['Items']

	for i in items:
		timestamp_5.append(int(i['timestamp']))
		pm25_5.append(float(i['data']['pm2_5']))
		pm10_5.append(float(i['data']['pm10']))
		co_5.append(float(i['data']['co']))
		so2_5.append(float(i['data']['so2']))

	#ST105 graph
	plt.figure(2)
	ax3.clear()
	ax4.clear()

	#ax3 = plt.subplot(2, 1, 1)
	ax3.plot(timestamp_5, pm25_5, color='green', label='PM2.5')
	ax3.plot(timestamp_5, pm10_5, color='red', label='PM10')
	ax3.set_xticks(np.arange(min(timestamp_5), max(timestamp_5), 100))
	ax3.legend(loc="upper right")
	
	#ax4 = plt.subplot(2, 1, 2)
	ax4.plot(timestamp_5, co_5, color='orange', label='CO')
	ax4.plot(timestamp_5, so2_5, color='purple', label='SO2')
	ax4.set_xticks(np.arange(min(timestamp_5), max(timestamp_5), 100))
	ax4.set_yticks(np.arange(0, max(co_5), .5))
	ax4.legend(loc="upper right")

ani_2 = animation.FuncAnimation(plt.figure(1), animate_2, 800)
ani_5 = animation.FuncAnimation(plt.figure(2), animate_5, 800)
plt.show()