import json
import boto3  
from boto3.dynamodb.conditions import Key, Attr

REGION="us-east-1"
dynamodb = boto3.resource('dynamodb',region_name=REGION)
table = dynamodb.Table('PhotoGallery')

def lambda_handler(event, context):
    photoID=event['body-json']['photoid']
    timestamp=int(photoID)
    title=event['body-json']['title']
    description=event['body-json']['description']
    tags=event['body-json']['tags']
    
    table.update_item(
        TableName= 'PhotoGallery',
        Key={                        
            'PhotoID': photoID,
            'CreationTime': timestamp
        },
        UpdateExpression='set Title = :title, Description = :description, Tags = :tags',
        ExpressionAttributeValues={
            ':title': title,
            ':description': description,
            ':tags': tags
        },
        ReturnValues="UPDATED_NEW"
    )
                
    return {
        "statusCode": 200,
        "body": json.dumps(timestamp)
    }