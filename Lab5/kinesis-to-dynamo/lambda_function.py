import base64
import os
import json
import boto3
from botocore.exceptions import ClientError

REGION="us-east-1"

def flattenData(tweet):
    output_json={}    
    output_json["id_str"] = tweet['id_str']
    output_json["timestamp"] = int(tweet['timestamp_ms'])
    output_json["tweet"] = tweet['text']
    output_json["location"] = tweet['user']['location']
    output_json['tweet_name'] = tweet['user']['name']
    output_json['tweet_text'] = tweet['text']        
    output_json['tweet_user_id'] = tweet['user']['screen_name']

    return output_json

def store_data(table, item):
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    client = dynamodb.Table(table)

    client.put_item(Item=item)

def lambda_handler(event, context):

    DYNAMO_TABLE = os.environ['TWEET_TABLE']  

    if not DYNAMO_TABLE:
        return "TABLE NOT FOUND"

    if 'Records' in event:
        
        for record in event['Records']:

            if record['eventSource'] == 'aws:kinesis':
                try:
                    # Kinesis data is base64 encoded so decode here
                    payload = base64.b64decode(record['kinesis']['data'])
                    print(f'''Decoded payload: {payload}''')
                    output_payload = json.loads(payload)

                    dataFlatten = flattenData(output_payload)
    
                    try:
                        store_data(DYNAMO_TABLE, dataFlatten)
                        
                    except ClientError as e:
                        print(e.response['Error']['Message'])
    
                    print("Kinesis Record: " + json.dumps(dataFlatten, indent=2))
    
                except BaseException as e:
                    print(f'''Processing failed with exception: {str(e)}''')

        return 'Successfully processed {} records.'.format(len(event['Records']))

