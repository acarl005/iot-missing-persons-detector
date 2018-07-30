# IoT and Facial Recognition at Scale:</br>Using Amazon DeepLens to search for matches from the United States Missing Persons Database

Andrew Carlson, Vicki Foss, Gerard Kelly, Michelle Liu  
[MIDS W251: "Scaling Up! Really Big Data](https://datascience.berkeley.edu/)  
University of California, Berkeley  
August 2018

# Contents
1. [Introduction](#introduction)
2. [Data Source](#datasource)  
3. [Technology Stack](#technology)
4. [Tools](#tools)
5. [Processes](#processes)
    1. [Data ingestion from NamUs](#ingestion)
    2. [Face comparison via Rekognition](#comparison)
    3. [Alert user if match is found](#alert)
6. [Discussion of Results and Future Work](#discussion)
7. [References](#references)

## Introduction <a name="introduction"></a>

In the United States alone, at least 14,500 people are missing today[\[1\]](#footnote1).  By definition, these missing people could be anywhere, which makes “crowd sourcing” the search an important tactic in the effort to locate them.  Historically, this has meant the television broadcasting of photos of the missing, disseminating posters or even printing missing children’s faces on milk cartons—all in the hope that someone who encounters a missing person in a public space will recognize them for who they are. While there are some cases of these sorts of campaigns being successful, they are generally the minority.  Furthermore, several psychology experiments have found that even when a poster of a “missing person” (really an actor) is placed close to where that real person is, only
a small percentage of passersby even recognize the person from the poster (generally less than 5%), and if they do, they often do not speak up out of fear of getting involved [\[2\]](#footnote2). A separate experiment found that the more “missing person” announcements a person sees, the less likely they are to pay attention and identify those people when encountered in real life [\[3\]](#footnote3). Other research has shown that there is a race and gender disparity in the missing persons cases that receive the most media attention, with white people and women and girls getting a disproportionate amount [\[4\]](#footnote4). For all of these reasons, our fellow human beings tend to make poor partners in the search for missing persons.

Fortunately, computers have now surpassed humans in recognizing and identifying a human face [\[5\]](#footnote5). Computers do not fail to identify a person because of their gender or race, for fear of getting involved or lack of paying attention.  As such, well-placed cameras in public spaces equipped with facial recognition software and trained to recognize people from the images scraped from The National Missing and Unidentified Persons System (NamUs) database could be a better method for identifying missing people “in the wild” and alerting authorities in real-time. In this paper, we describe a cloud-based architecture that uses Amazon’s DeepLens to correctly identify test subjects and pictures of people in the NamUs database, and which sends a text message with the person’s information upon finding a match.  While there are monetary, logistic, and privacy concerns that might prevent such a system to be adopted nationwide, we are still able to demonstrate its remarkable effectiveness.

## Data Source <a name="datasource"></a>

The National Missing and Unidentified Persons System ([NamUs](https://www.namus.gov/About)) has a database with records of approximately 14,400 missing people[\[1\]](#footnote1). About 12,300 of those records contain at least one image, with an average of two images per person, resulting in a total of more than 24,600 images. The size of the images range from 100s of kB to 10s of MB. Due to the real-time requirements of the application, the entire corpus of images cannot be processed on each query. Achieving low latency and horizontal scalability with this type of data will be the design goals, and dictate the choice of technologies.

## Technology Stack <a name="technology"></a>

The architecture is comprised of a cloud-based, serverless[\*](#asterisk) backend that interfaces with edge devices via object storage uploads. In this case, our cloud provider is [Amazon Web Services (AWS)](https://aws.amazon.com/). AWS was chosen primarily for the abundance of documentation/tutorials, pleasant developer experience, and out-of-the-box integration with the [Amazon DeepLens](https://aws.amazon.com/deeplens/), an edge device which one of us happens to possess.</br></br>  

![system diagram](system-diagram.png)  

</br>Arbitrary edge devices which recognize faces will upload to object storage that triggers downstream processing. The processing entails running a facial recognition model, and sending a notification when a match on a missing person is found. These operations will be collectively called the **detection pipeline**. It assumes that a collection of missing persons’ faces is built and ready to query.

This collection is built by a set of processes termed the **ingest pipeline**. As mentioned above, this collection of faces must not be processed on each query, but rather preemptively indexed to meet our application’s low-latency requirements. Each missing person’s information and photos were enumerated from the NamUs servers and uploaded to object storage. This triggered the indexing operation, so that the model can recognize the photo in future queries.

<sub>\*<a name="asterisk"></sub> Serverless insofar as we did not need to write, or even manage our own servers. The only servers involved are owned by AWS and NamUs.</small>

## Tools <a name="tools"></a>

We relied heavily on Amazon Web Services in order to implement our system. This section details the specific AWS tools we used and how they were set up and incorporated into pipelines.

* [**S3.**](https://aws.amazon.com/s3/) S3 object storage is used to store each image.
There are two buckets, one for **ingestion** and one for **detection**. In the ingestion pipeline, the bucket stores the database of missing persons. On the detection side, there is a bucket that stores every face detected which is a candidate for a missing person query. This serves as the interface for the edge devices to submit the faces they detect.


* [**Lambda.**](https://aws.amazon.com/lambda/features/) AWS's implementation of serverless compute breaks application logic into function-based units called Lambdas. These are triggered either by user-defined, custom triggers such as changes in data or by other AWS services such as S3 and DynamoDB. Lambda makes it easy to build a real-time serverless data processing system that is scalable and fully managed on AWS’s infrastructure. It is very cost-effective as we only pay for the compute time actually used, instead of having an always-on server.
</br></br>
All the application logic is implemented in two lambdas. The first is triggered during the scraping process. When a new photo is added to S3, a lambda adds the new face to an index in AWS Rekognition. The other lambda triggers on uploads to the other bucket. This takes any detected face and submits it to Rekognition in a search operation to see if it can find matches in our index. If it can, it calls AWS Simple Notification Service (SNS) to send a text message to the team.

* [**Rekognition.**](https://aws.amazon.com/rekognition/) Amazon Rekognition is a collection of pre-trained machine learning models exposed as a service. The model we used is a facial recognition model which can perform object detection to first find faces in photos, and then encode faces into a vector known as “embeddings”. These embeddings are a very compact numerical encoding for a face which is “learned” during the training process. During indexing, it is actually the embeddings which are stored in an index. On each query, the photo is converted to its embeddings and searched against the known embeddings of all the missing persons’ faces. This is how over 20,000 images can be searched in real-time.

* [**DynamoDB.**](https://aws.amazon.com/dynamodb/) DynamoDB is Amazon’s configurable, scalable document store. We use it to store history of when notifications are sent. This is primarily to address the problem of notification “bursts”. When a subject remains in the viewport of the DeepLens for a sustained period of time, many uploads are sent in rapid succession. If that person is a match and texts are sent every time, it leads to an irritating experience. This is prevented by persisting this information in DynamoDB, so the lambda can avoid sending too many repeat notifications.

* [**SNS.**](https://aws.amazon.com/sns/) AWS Simple Notification Service (SNS) is Amazon’s publish-subscribe messaging service that can be called to send text messages.

* [**IAM Roles.**](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html) IAM roles are a set of credentials and permissions given to AWS services that specify access control to other services. For example, our Lambdas are given access to S3, Rekognition, and CloudWatch (for monitoring and logging). If these pieces of compute can only access other services that are actually needed, the surface area for security breaches is minimized. If an attacker somehow gets remote access and is able to execute malicious code on one of our Lambdas, they would not be able to provision EC2 instances and start a botnet/bitcoin mining operation.

* [**DeepLens.**](https://aws.amazon.com/deeplens/) AWS DeepLens is a wireless deep learning enabled video camera that is integrated with the AWS Cloud. The DeepLens camera uses [deep convolutional neural networks](https://gluon.mxnet.io/chapter04_convolutional-neural-networks/cnn-scratch.html) to analyze visual imagery in real time. DeepLens runs Ubuntu OS and is preloaded with the [Greengrass Core](https://aws.amazon.com/greengrass/), where you can deploy either a pre-trained or custom deep learning models that can detect faces, objects, activities, texts, and much more.
</br></br>
Our project leverages the pre-trained model template for face-detection functionality. In the AWS DeepLens console, we created a project with the face detection template. The AWS console provides the default model with a Lambda function that come with the project template. We updated the lambda function so that when the device detects human faces, the project stream containing the frame is extracted, and the face is cropped out and sent as a JSON message IoT. Next, we created a rule in IoT to upload the image to an S3 bucket through another Lambda call if the confidence level of a face detection is over 80%.
</br></br>
Once the project is deployed to the DeepLens device, the project output can be viewed on screen. Below is an example of the project stream:

<!--INSERT IMAGE HERE-->

## Processes<a name="processes"></a>

The `src` directory of the repository contains code used for ingestion, detection and alerting processes.
Scripts for ingesting and indexing NamUs data are contained in the `src/ingest/` directory
while detection and alerts are managed with the `src/lambda_rekognition.py` program.

### Data ingestion from NamUs<a name="ingestion"></a>

For the typical user, NamUs is typically interacted with via the web page. After making an account, the user is directed to an AngularJS application which allows them to search missing persons based on several criteria and see other information about them, including photos. Searching by image cannot be done. This dashboard is not a useable format for our application.

A virtual server was provisioned (AWS EC2) for the scraping. An Ubuntu 16.04 image was given an IAM role with write access to the S3 bucket, and used to run a Python 3 program. The program enumerated data about each missing person via an undocumented API. The URL for this API was found by reverse-engineering the Angular app with the Chrome DevTools. Inspecting the “Network” tab in the DevTools, and filtering on the XHR requests, we looked through all the requests made from the results page for a missing person. We identified this URL, which returns information about the case:

`https://www.namus.gov/api/CaseSets/NamUs/MissingPersons/Cases/<primary_key>`

Once the appropriate URL was found, it was clear that it was parameterized by a primary key, which is an incrementing integer. The Python program loops up through the space of primary keys starting from 1, gathering information about each person. Among this information, there are URLs to a static file server which hosts the person’s photos. These image files are subsequently downloaded and submitted to the S3 bucket, triggering the indexing process.

The indexer was able to find a face in about 94% of the images. Photos work best when the face is in color, and the subject is facing the camera.

|![facedetected1](100-0.jpg)|![facedetected2](10206-0.jpg)|![nofacedetected](rekognition-fail.jpg)|
|:---:|:---:|:---:|
|Face detected | Face detected | **No** face detected | 

### Face comparison via Rekognition<a name="comparison"></a>

Lambda call to match face detected to

Add to DynamoDB database

### Alert user if match is found<a name="alert"></a>

Get person’s info from NamUs

Text user

## Discussion of Results and Future Work<a name="discussion"></a>

***Measure how long between pointing DeepLens at subject and getting text message***

***Scalability***

The success of our person recognition and alert system--as well as its rather elegant, efficient, and effective technology stack--naturally raises the question of how we could build upon it.  

Incorporating additional sources of images we can use to search for matches in the Rekognition index (in addition to the DeepLens).  Ex: Twitter stream or other social media sites, Backpage, etc.

Additional datasets for persons of interest (e.g. wanted criminals)

Non-technological barriers (need for political allies, etc. … maybe include a real-world example of a similar system and any controversy (or lack thereof) associated with it?


## References <a name="references"></a>

[1]<a name="footnote1"></a> National Institute of Justice,
*National Missing and Unidentified Persons System*, 2018. https://www.namus.gov/.

[2]<a name="footnote2"></a> J. M. Lampinen and K. N. Moore,
“Prospective Person Memory in the Search for Missing Persons,”
in *Handbook of Missing Persons*,
S. J. Morewitz and C. S. Colls, Eds. Cham, Switzerland: Springer, 2016, pp. 145-162.

[3]<a name="footnote3"></a>J. M. Lampinen, and K. N. Moore,
“Missing person alerts: does repeated exposure decrease their effectiveness?”,
*Journal of Experimental Criminology*, vol. 12, no. 4, pp 587-598,  Dec. 2016. https://doi.org/10.1007/s11292-016-9263-1.</a>

[4]<a name="footnote4"></a>Z. Sommers,
“Missing White Woman Syndrome: An Empirical Analysis of Race and Gender Disparities in Online News Coverage of Missing Persons”,
*Journal of Criminal Law and Criminology*, vol. 106, no. 2, pp. 275-314, 2016. https://scholarlycommons.law.northwestern.edu/jclc/vol106/iss2/4.</a>

[5]<a name="footnote5"></a>C. Lu and X. Tang,
“Surpassing Human-Level Face Verification Performance on LFW with GaussianFace,” arXiv:1404.3840v3 [cs.CV], Dec. 20, 2014.</a>
