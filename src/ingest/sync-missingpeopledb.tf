provider "aws" {
  region = "us-east-1"
}

data "aws_s3_bucket" "missingpeopledb" {
  bucket = "missingpeopledb"
}

resource "aws_iam_role" "iam_for_index_lambda" {
  name = "iam_for_index_lambda"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "test_policy" {
  name = "enable_index_lambda"
  role = "${aws_iam_role.iam_for_index_lambda.id}"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid" : "yaycloudwatchloggingherewego",
      "Effect": "Allow",
      "Action": [ "logs:*" ],
      "Resource": [ "*" ]
    },
    {
      "Sid": "yayrekognitionindexingherewego",
      "Effect": "Allow",
      "Action": [ "rekognition:IndexFaces" ],
      "Resource": [ "*" ]
    },
    {
      "Sid": "yays3bucketherewego",
      "Effect": "Allow",
      "Action": [ "*" ],
      "Resource": [ "${data.aws_s3_bucket.missingpeopledb.arn}" ]
    }
  ]
}
EOF
}

resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.index_face.arn}"
  principal     = "s3.amazonaws.com"
  source_arn    = "${data.aws_s3_bucket.missingpeopledb.arn}"
}

resource "aws_lambda_function" "index_face" {
  filename         = "index_face.zip"
  function_name    = "index_face"
  role             = "${aws_iam_role.iam_for_index_lambda.arn}"
  handler          = "index_face.handler"
  runtime          = "python2.7"
  source_code_hash = "${base64sha256(file("index_face.zip"))}"
  description      = "Adds a new picture to the missingpeople rekognition index when uploaded to the missingpeopledb bucket"
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = "${data.aws_s3_bucket.missingpeopledb.id}"

  lambda_function {
    lambda_function_arn = "${aws_lambda_function.index_face.arn}"
    events              = ["s3:ObjectCreated:*"]
  }
}
