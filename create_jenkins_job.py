from __future__ import print_function
import os
import requests
from requests.auth import HTTPBasicAuth
import base64
import shutil
import fileinput


def check_job(l_application_name):
    repo_url = "https://10.78.19.6/job/%s" %l_application_name

    check_jenkins_request = requests.get(repo_url, verify=False, auth=HTTPBasicAuth("cicdadmin", base64.b64decode("UXdlckFzZGYxMjM0")), stream=True)

    if check_jenkins_request.status_code == 200:
        return True
    else:
        return False


def create_job(p_job_name, p_view):
    create_api = "https://10.78.19.6/view/%s/createItem?name=%s" %(p_view, p_job_name)
    config_file = open('config.xml', 'rb')
    headers = {'content-type': 'application/xml'}

    post_request = requests.post(create_api, verify=False, data=config_file, headers=headers, auth=HTTPBasicAuth("cicdadmin", base64.b64decode("UXdlckFzZGYxMjM0")))

    if post_request.status_code == 200:
        print("Jenkins job has been created")
    else:
        print("Error in creating job")


def generate_config_file_build(p_application_name, p_artifact_id):
    shutil.copyfile("Templates/build_config.xml", "config.xml")

    print("copied build")

    file = fileinput.input("config.xml", inplace=True)
    for line in file:
        if "tobeupdatedreponame" in line:
            print(line.replace("tobeupdatedreponame", p_application_name + ".git"), end='')
        else:
            print(line.replace("ToBeUpdatedArtifactID", p_artifact_id), end='')
    file.close()


def generate_config_file_sonar(p_application_name):
    shutil.copyfile("Templates/sonar_config.xml", "config.xml")

    print("copied sonar")

    file = fileinput.input("config.xml", inplace=True)
    for line in file:
        print(line.replace("tobeupdatedreponame", p_application_name + ".git"), end='')
    file.close()


application_name = os.environ["Application_Name"]
build_job = application_name
sonar_job = build_job + "_Sonar"
artifact_id = os.environ["Artifact_ID"]

if not check_job(application_name):
    generate_config_file_build(application_name, artifact_id)
    create_job(build_job, "testApp Build Jobs")
    os.remove("config.xml")
else:
    print("Build job already present")

if not check_job(application_name + "_Sonar"):
    generate_config_file_sonar(application_name)
    create_job(sonar_job, "testApp-Sonar-Jobs")
    os.remove("config.xml")
else:
    print("Sonar Job already present")