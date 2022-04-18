import matplotlib.pyplot as plt
import numpy as np
import csv

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

with open('rawdata.csv', 'r') as csv_file:
	csv_reader = csv.reader(csv_file)
	for row in csv_reader:
		if row[0] == 'ST102':
			timestamp_2.append(int(row[1]))
			pm25_2.append(float(row[4]))
			pm10_2.append(float(row[5]))
			co_2.append(float(row[6]))
			so2_2.append(float(row[7]))
		if row[0] == 'ST105':
			timestamp_5.append(int(row[1]))
			pm25_5.append(float(row[4]))
			pm10_5.append(float(row[5]))
			co_5.append(float(row[6]))
			so2_5.append(float(row[7]))


# ST102 graph
plt.figure(1)
plt.suptitle('ST102 Raw Data Graph')
plt.xlabel('Timestamp')

ax1 = plt.subplot(2, 1, 1)
ax1.plot(timestamp_2, pm25_2, color='green', label='PM2.5')
ax1.plot(timestamp_2, pm10_2, color='red', label='PM10')
ax1.set_xticks(np.arange(min(timestamp_2), max(timestamp_2), 40))
ax1.set_yticks(np.arange(0, 600, 100))
ax1.legend(loc="upper right")

ax2 = plt.subplot(2, 1, 2)
ax2.plot(timestamp_2, co_2, color='orange', label='CO')
ax2.plot(timestamp_2, so2_2, color='purple', label='SO2')
ax2.set_xticks(np.arange(min(timestamp_2), max(timestamp_2), 40))
ax2.set_yticks(np.arange(0, max(co_2), .5))
ax2.legend(loc="upper right")

#ST105 graph
plt.figure(2)
plt.suptitle('ST105 Raw Data Graph')
plt.xlabel('Timestamp')

ax1 = plt.subplot(2, 1, 1)
ax1.plot(timestamp_5, pm25_5, color='green', label='PM2.5')
ax1.plot(timestamp_5, pm10_5, color='red', label='PM10')
ax1.set_xticks(np.arange(min(timestamp_5), max(timestamp_5), 40))
ax1.set_yticks(np.arange(0, 600, 100))
ax1.legend(loc="upper right")

ax2 = plt.subplot(2, 1, 2)
ax2.plot(timestamp_5, co_5, color='orange', label='CO')
ax2.plot(timestamp_5, so2_5, color='purple', label='SO2')
ax2.set_xticks(np.arange(min(timestamp_5), max(timestamp_5), 40))
ax2.set_yticks(np.arange(0, max(co_5), .5))
ax2.legend(loc="upper right")

plt.show()