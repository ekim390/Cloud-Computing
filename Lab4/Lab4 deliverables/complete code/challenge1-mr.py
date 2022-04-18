"""
use this line in Hadoop to run challenge1 mapreduce program:

python challenge1-mr.py -r hadoop hdfs:///user/ekim390/googlebooks-eng-us-all-2gram-20090715-50-subset.csv --output-dir=hdfs:///user/ekim390/challenge1output --conf-path=mrjob.conf

"""

from mrjob.job import MRJob

class MRmyjob(MRJob):
	def mapper(self, _, line):
		bigram, year, match_count, page_count, volume_count = line.split("\t")
		year = int(year)
		yield bigram,year

	def reducer(self, bigram, list_of_values):
		for value in list_of_values:
			if value > 1992:
				yield bigram,value

if __name__ == '__main__':
    MRmyjob.run()