import os
import boto3
import config
from elasticsearch.exceptions import ElasticsearchException
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

REGION = 'us-east-1'
SERVICE = 'es'

credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, REGION, SERVICE, session_token=credentials.token)

ES_INDEX = config.ES_INDEX
ES_URL = config.ES_URL

mappings = {
    "properties": {
        "timestamp": {
            "type":   "date",
            "format": "epoch_millis"
        },
        "sentiment" : { "type" : "float" },
        "id_str" : { "type" : "text" },
        "tweet_name" : { "type" : "text" },
        "tweet_text" : { "type" : "text" },
        "tweet_user_id" : { "type" : "text" },
        "location": {
            "type": "geo_point"
        }
    }
}

def create_index(es, index_name, mapping):
    print('creating index {}...'.format(index_name))
    es.indices.create(index_name, body = mapping)


if __name__ == '__main__':
    print(f'''ES URL: {ES_URL}''')
    print(f'''ES INDEX: {ES_INDEX}''')

    es = Elasticsearch(
        hosts = [{'host': ES_URL, 'port': 443}],
        http_auth = awsauth,
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )

    mapping = { 'mappings': mappings }

    if es.indices.exists(ES_INDEX):
        print ('index {} already exists'.format(ES_INDEX))
    else:
        print('index {} does not exist'.format(ES_INDEX))

        try:
            create_index(es, ES_INDEX, mapping)
            print("Index Created")

        except ElasticsearchException as e:
            print('error putting mapping:\n'+str(e))



