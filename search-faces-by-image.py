import boto3

rekog = boto3.client("rekognition")

img_files = [ "andy3.jpg", "tony1.jpeg" ]

for img_path in img_files:
    with open(img_path, 'rb') as img:
        result = rekog.search_faces_by_image(
            CollectionId="missingpeople",
            Image={ "Bytes": img.read() },
            MaxFaces=1
        )
        print(result)

