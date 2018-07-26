from __future__ import print_function
import boto3
import urllib
import re


rekognition = boto3.client("rekognition")

# validate that the object key is the right format
key_pattern = re.compile(r"^\d+-\d+(\.\w+)?")

# --------------- Main handler ------------------

def handler(event, context):
    s3_info = event["Records"][0]["s3"]

    # Get the object from the event
    bucket = s3_info["bucket"]["name"]
    key = urllib.unquote_plus(s3_info["object"]["key"].encode("utf8"))
    print('bucket', bucket)
    print('key', key)

    if key_pattern.match(key) is None:
        raise ValueError('The key "%s" is invalid format. For this bucket, it must be the integer ExternalId, a hyphen, and in integer index, followed optionally by an extension. For example 1371-1.jpg')
    external_id = key.split("-")[0]

    # tells rekognition to index the new image
    results = rekognition.index_faces(
        CollectionId="missingpeople",
        Image={
            'S3Object': {
                'Bucket': bucket,
                'Name': key
            }
        },
        ExternalImageId=external_id,
        DetectionAttributes=['ALL']
    ) 
    print(results)

