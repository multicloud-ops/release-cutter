# Release cutter

Initial cut of release cutter

Based on cloud founctions

## How to use

Add bot URL as webhook to repo you want to be served by the release cutter bot. You get the URL from someone who knows it (believe it or not)

## How the bot was built
The bot was built using IBM Cloud Functions with additional 
https://cloud.ibm.com/docs/openwhisk?topic=cloud-functions-prep#prep_python_virtenv


Alternatively, it could be built with custom docker container image
1. Built using python and gidgethub https://github-bot-tutorial.readthedocs.io/en/latest/gidgethub-for-webhooks.html
2. Hosted on IBM Cloud Functions using custom docker container https://cloud.ibm.com/docs/openwhisk?topic=cloud-functions-prep#prep_python_docker

## Deploying the application
1. Setup your virtualenv and pip install dependencies
2. zip -r releasecutter.zip \_\_main\_\_.py virtualenv
3. ibmcloud fn action create releasecutter creleasecutter.zip --kind python:3.7  --web true


### Settings
Update the function after creating
ibmcloud fn action update createrelease -p ghtoken _TOKEN_ -p tag_author _AUTHOR_ -p tag_author_email _AUTHOR_EMAIL_


### Getting the URL for the webhook
1. ibmcloud fn action get releasecutter --url

The returned URL goes into github as the webhook
