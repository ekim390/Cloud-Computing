"""
use this line in Hadoop to run challenge2 mapreduce program:

python challenge2-mr.py -r hadoop hdfs:///user/ekim390/googlebooks-eng-us-all-2gram-20090715-50-subset.csv --output-dir=hdfs:///user/ekim390/challenge2output --conf-path=mrjob.conf

"""

from mrjob.job import MRJob

class MRmyjob(MRJob):
	def mapper(self, _, line):
		bigram, year, match_count, page_count, volume_count = line.split("\t")
		match_count = int(match_count)
		volume_count = int(volume_count)
		countList = [match_count, volume_count]
		yield bigram,countList

	def reducer(self, bigram, list_of_values):
		totalcount = 0
		totalbooks = 0
		for value in list_of_values:
			totalcount = totalcount + value[0]
			totalbooks = totalbooks + value[1]
		average = int(totalcount / totalbooks)
		yield bigram,average

if __name__ == '__main__':
    MRmyjob.run()