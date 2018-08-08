from __future__ import print_function

import boto3
from decimal import Decimal
import json
import urllib
import datetime
from botocore.vendored import requests

print('Loading function')

dynamodb = boto3.client('dynamodb')
s3 = boto3.client('s3')
sns = boto3.client('sns')
rekognition = boto3.client('rekognition')
    
# --------------- Helper Functions ------------------

def update_db(tableName,faceId, timestamp):
    response = dynamodb.put_item(
        TableName=tableName,
        Item={
            'faceID': {'S': faceId},
            'TimeDetected': {'S': timestamp}
            }
        ) 

# --------------- Main handler ------------------

def lambda_handler(event, context):

    # Get the object from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(
        event['Records'][0]['s3']['object']['key'].encode('utf8'))

    try:

        # Calls Amazon Rekognition Search Face API to compare the face detected 
        # in the 'missingpeople' index

        result = rekognition.search_faces_by_image(
            CollectionId="missingpeople",
            Image={ 'S3Object':{
                'Bucket': bucket,
                'Name': key
                } 
            },
            MaxFaces=1
        )
        
        if result['FaceMatches']:
            
            externalid = int(result['FaceMatches'][0]['Face']['ExternalImageId'])
            prob = result['FaceMatches'][0]['Similarity']
            
            # See if the faceID exists in the DynamoDB already
            response = dynamodb.get_item(TableName='person_detected', Key={'faceID':{'S':str(externalid)}})
            update_flag = 0
            
            try:
                if response['Item']: #key exist already
                    item_timestamp = response['Item']['TimeDetected']['S']
                    # only update the DB if at least 1 min has passed since last detected
                    if abs(int(datetime.datetime.now().strftime('%s')) - int(item_timestamp)) > 60: 
                        update_flag = 1
            except:
                print('New person detected!')
                update_flag = 1
            
            if (update_flag == 1):
                #update the database with faceID and the time detected
                update_db('person_detected',str(externalid), datetime.datetime.now().strftime('%s'))
                
                msg = "Positive match identified with {:.3f}% similarity to ".format(prob)
                #hardcode in ID for testing purposes
                if externalid == 66666:
                    msg += "test subject Andrew Carlson."
                elif externalid == 66667:
                    msg += 'test subject Michelle Liu.'
                else:
                    try:
                        #call the NamUs API to get the person's information
                        r = requests.get('https://www.namus.gov/api/CaseSets/NamUs/MissingPersons/Cases/{}'.format(externalid))
                        personinfo = r.json()
                        fullname = ' '.join('{} {} {}'.format(
                            personinfo["subjectIdentification"]["firstName"], 
                            personinfo["subjectIdentification"].get("middleName",""), 
                            personinfo["subjectIdentification"]["lastName"]).split())
                        if personinfo["subjectIdentification"]["currentMinAge"] == personinfo["subjectIdentification"]["currentMaxAge"]:
                            age = personinfo["subjectIdentification"]["currentMinAge"]
                        else:
                            age = '{}-{}'.format(personinfo["subjectIdentification"]["currentMinAge"],
                                     personinfo["subjectIdentification"]["currentMaxAge"])
                        lastseen = datetime.datetime.strptime(personinfo["sighting"]["date"], '%Y-%m-%d').strftime('%m/%d/%Y')
                        sex = personinfo["subjectDescription"]["sex"]["name"]
                        msg += 'missing person {}: {}. {}, age {}. Last seen on {}.'.format(externalid, fullname, sex, age, lastseen)
                    except:
                        msg += 'missing person {}'.format(externalid)
                
                #Send a text message to alert the user of the match 
                number = '+15555555555'  # Replace with actual phone number
                sns.publish(PhoneNumber = number, Message=msg )
            
        else:
                print("No match is found.")

    except Exception as e:
        print(e)
        print("Error processing object {} from bucket {}. ".format(key, bucket))
        raise e
