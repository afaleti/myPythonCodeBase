import requests
import os
from requests.auth import HTTPBasicAuth
import base64
import shutil
import sys
import subprocess
import json
import time

commit_id = os.environ["GIT_COMMIT"]

artifact_id = "single-module"

repo_url = "http://git.tech-77.net/rest/api/latest/projects/CIC/repos/single-module/archive?at=%s&format=zip" % commit_id

file_name = artifact_id + "-master@" + commit_id + ".zip"

check_repo_request = requests.get(repo_url, verify=False, auth=HTTPBasicAuth("basil", base64.b64decode("QkBzaWwzMjE=")),
                                  stream=True)

if check_repo_request.status_code == 200:
    with open(file_name, 'wb') as handle:
        check_repo_request.raw.decode_content = True
        shutil.copyfileobj(check_repo_request.raw, handle)
else:
    print ("Request for gathering build job names failed with error")
    sys.exit(check_repo_request.status_code)

os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"

aws_call_2 = subprocess.Popen(
    'aws s3api put-object --acl bucket-owner-read --key %s --body %s --bucket "temp-code-source-test"' % (
    file_name, file_name), shell=True, stdout=subprocess.PIPE)

json_output = aws_call_2.stdout.read()

print json_output

aws_call = subprocess.Popen(
    'aws sts assume-role --role-arn "arn:aws:iam::446661844902:role/external-codeBuildaccess-app-test-deploy" --role-session-name "ecsInstanceRole"',
    shell=True, stdout=subprocess.PIPE)

json_output = aws_call.stdout.read()

json_parsed = json.loads(json_output)

os.environ["AWS_ACCESS_KEY_ID"] = json_parsed["Credentials"]["AccessKeyId"]
os.environ["AWS_SECRET_ACCESS_KEY"] = json_parsed["Credentials"]["SecretAccessKey"]
os.environ["AWS_SESSION_TOKEN"] = json_parsed["Credentials"]["SessionToken"]

aws_call_temp = subprocess.Popen(
    'aws codebuild update-project --name "app-test-deploy" --source type="S3",location="arn:aws:s3:::temp-code-source-test/%s" ' % file_name,
    shell=True, stdout=subprocess.PIPE)

aws_call_2 = subprocess.Popen('aws codebuild start-build --project-name "app-test-deploy"', shell=True,
                              stdout=subprocess.PIPE)

json_output_2 = aws_call_2.stdout.read()

print json_output_2

json_parsed_2 = json.loads(json_output_2)

build_id = json_parsed_2["build"]["id"]

completed = "False"

while completed.strip() != "True":
    time.sleep(5)
    #   aws_call = subprocess.Popen(" aws codebuild batch-get-builds --ids '%s' --query 'builds[0].phases[0]'" % build_id ,shell=True, stdout=subprocess.PIPE)
    aws_call = subprocess.Popen(
        " aws codebuild batch-get-builds --ids '%s' --query 'builds[0].{status:buildComplete}' --output text" % build_id,
        shell=True, stdout=subprocess.PIPE)
    completed = aws_call.stdout.read()

aws_build_log = subprocess.Popen(" aws codebuild batch-get-builds --ids '%s'" % build_id, shell=True,
                                 stdout=subprocess.PIPE)

build_output_json = aws_build_log.stdout.read()

print build_output_json

status_parsed = json.loads(build_output_json)

build_status = status_parsed["builds"][0]["buildStatus"]

if build_status.strip() != "SUCCEEDED":
    sys.exit("Build failed.")
