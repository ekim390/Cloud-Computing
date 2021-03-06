import json
import boto3  
from boto3.dynamodb.conditions import Key

REGION="us-east-1"
dynamodb = boto3.resource('dynamodb',region_name=REGION)
table = dynamodb.Table('PhotoGallery')

def lambda_handler(event, context):
    photoID=event['body-json']['photoid']
    timestamp=int(photoID)
    
    response = table.delete_item(
        Key={                        
            'PhotoID': photoID,
            'CreationTime': timestamp
        }
    )
                
    return {
        "statusCode": 200,
        "body": json.dumps(timestamp),
    }