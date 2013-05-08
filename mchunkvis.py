from pymongo import MongoClient
import argparse
import pprint
import json

class NestedDict(dict):
	def __getitem__(self,key):
		if key in self: return self.get(key)
		return self.setdefault(key, NestedDict())

class MongoChunkVis(object):
	def __init__(self):
		self.parse_args()

		self.collect_data(self.args['configdb'], self.args['host'], self.args['port'])

	def parse_args(self):
		parser = argparse.ArgumentParser(description='A script to generate chunk information and visualise it '\
			'in D3.js.  Requires pymongo')
		#if sys.stdin.isatty():

		parser.add_argument('--configdb', action='store', nargs='*', help='config datbase to analyse', default='config')
		parser.add_argument('--host', action='store', nargs='*', help='host to connect to', default='localhost')
		parser.add_argument('--port', action='store', nargs='*', help='port to connect to', default=27017)

		self.args = vars(parser.parse_args())

	def collect_data(self, configdb, host, port):

		outputdata = { 'name' : 'databases', 'children' : [] }

		mc = MongoClient(host, port)

		db = mc["".join(configdb)]
		#TODO - add checking that this is actually a configdb/sharded

		cshards = db['shards']
		cchunks = db['chunks']
		cdatabases = db['databases']
		ccoll = db['collections']

		for databases in cdatabases.find():
			databasedata = { 'name' : databases['_id'], 'children' : [], 'size' : 100 }
			if databases['partitioned']:
				for coll in ccoll.find( { '_id' : { '$regex' : '^%s'%databases['_id']}, 'dropped' : False } ):
					colldata = { 'name' : coll['_id'].replace(databases['_id'],'',1), 'children' : [], 'size' : 1 }
					for shards in cshards.find():
						sharddata = { 'name' : shards['_id'], 'children' : [] }
						for chunks in cchunks.find( { 'shard' : shards['_id'], 'ns' : coll['_id'] } ):
							colldata['size'] +=1
							chunkdata = { 'name' : chunks['_id'].replace(chunks['ns'],'',1), 'size' : 1 }
							sharddata['children'].append(chunkdata)
						colldata['children'].append(sharddata)

					databasedata['children'].append(colldata)
			outputdata['children'].append(databasedata)

		print json.dumps(outputdata)


if __name__ == '__main__':
	mchunkvis = MongoChunkVis()