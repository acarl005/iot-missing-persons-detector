for key in $(aws s3api list-objects --bucket missingpeopledb --query 'Contents[].Key' --output text); do
    echo $key;
    aws rekognition index-faces --image '{"S3Object":{"Bucket":"missingpeopledb","Name":"'"$key"'"}}' --collection-id missingpeople --detection-attributes ALL --external-image-id echo ${key%-*}
done
