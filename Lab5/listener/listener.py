import tweepy
import pickle
import boto3
import json
import time
import sys
import config
from botocore.exceptions import ClientError
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

REGION="us-east-1"

# create secret client connection
secrets_client = boto3.client("secretsmanager", region_name=REGION)

# create kinesis client connection
kinesis_client = boto3.client('kinesis', region_name=REGION)

# list of keys for the Twitter API
credential_keys = ["TwitterAPIKey", "TwitterAPISecretKey", "TwitterAccessToken", "TwitterAccessSecret"]

# check if CloudFormation
CF = config.CF

# add kinesis data stream
STREAM = config.KINESIS_STREAM

def get_credentials():

    credential_values = []

    for key in credential_keys:

        try:
            keyName = key if not CF else f'''{key}-cf'''
            get_secret_value_response = secrets_client.get_secret_value(SecretId=keyName)

        except ClientError as e:
            print(f'''Error from secret manager: {e}''')
        else:
            # Decrypts secret using the associated KMS CMK.
            # Depending on whether the secret is a string or binary, one of these fields will be populated.
            if 'SecretString' in get_secret_value_response:
                secret = get_secret_value_response['SecretString']
                credential_values.append(secret)
            else:
                # decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
                secret = base64.b64decode(get_secret_value_response['SecretBinary'])
                credential_values.append(secret)

    if len(credential_values) == 4:
        return (credential_values[0], credential_values[1], credential_values[2], credential_values[3])
    else:
        sys.exit(1)

class TweetStreamListener(StreamListener):
    # on success
    def on_data(self, data):
        try:
            dataObject = json.loads(data)
            
            print(dataObject)
            print('\n')
            
            response = kinesis_client.put_record(
                StreamName=STREAM, 
                Data=json.dumps(dataObject), 
                PartitionKey=dataObject['id_str']
            )

        except (AttributeError, Exception) as e:
            print(e)

        return True

    # on failure
    def on_error(self, status):
        print(status)

def setConnection(auth, listener):
    # create instance of the tweepy stream
    stream = Stream(auth, listener)

    # search twitter for tags or keywords
    stream.filter(track=keywords)

if __name__ == '__main__':

    # get credentials for Twitter API
    (consumer_key, consumer_secret, access_token, access_token_secret) = get_credentials()
    # list of instresting keywords/hashtag
    keywords=['cricket']
    # create instance of the tweepy tweet stream listener
    listener = TweetStreamListener()
    # set Twitter authorization keys
    auth = OAuthHandler(consumer_key, consumer_secret)    
    auth.set_access_token(access_token, access_token_secret)

    try:
        setConnection(auth, listener)

    except ValueError:
        print("connection error: Retrying...")
        setConnection(auth, listener)


