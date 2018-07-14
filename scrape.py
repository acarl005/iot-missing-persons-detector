import requests
import csv
import boto3
import os
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ids = []

with open('namus-female.csv', 'r') as csvfile:
    female = csv.DictReader(csvfile, delimiter = ',')
    for row in female:
        ids.append(int(row['\ufeff"Case Number"'][2:]))

with open('namus-male.csv', 'r') as csvfile:
    male = csv.DictReader(csvfile, delimiter = ',')
    for row in male:
        ids.append(int(row['\ufeff"Case Number"'][2:]))

ids = sorted(ids)

s3 = boto3.resource("s3")
bucket = s3.Bucket("missingpeopledb")

base_url = "https://www.namus.gov"
case_metadata_path = base_url + "/api/CaseSets/NamUs/MissingPersons/Cases/"

if os.path.exists('namus_progress'):
    with open('namus_progress', 'r') as progress:
        last_finished_id = int(progress.read())
    index_to_resume = ids.index(last_finished_id)
    ids_to_download = ids[index_to_resume:]    
else:
    ids_to_download = ids
    
    
for id in ids_to_download:
    print(id)
    case_url = case_metadata_path + str(id)
    metadata_resp = requests.get(case_url, verify = False)
    metadata = metadata_resp.json()
    
    for ind, image in enumerate(metadata['images']):
        image_path = image['files']['original']['href']

        image_url = base_url + image_path
        image_resp = requests.get(image_url, verify = False, stream = True)
        
        image_filename = str(id) + '-' + str(ind) +'.jpg'
        with open('namus/' +  image_filename, 'wb') as image_file:
            for chunk in image_resp:
                image_file.write(chunk)
        bucket.upload_file('namus/' + image_filename,
                           image_filename)
    
    with open('namus_progress', 'w') as progress:
        progress.write(str(id))

