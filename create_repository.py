import requests
import os
from requests.auth import HTTPBasicAuth
import base64
import subprocess
import sys


def check_repo(l_application_name):
    repo_url = "https://test.no/git/rest/api/1.0/projects/VAAPC/repos/%s" %l_application_name

    check_repo_request = requests.get(repo_url, verify=False, auth=HTTPBasicAuth("ab24716", base64.b64decode("QnJvbnplMDU=")), stream=True)

    if check_repo_request.status_code == 404:
        return True
    elif check_repo_request.status_code == 200:
        return False
    else:
        sys.exit("Connection issue with BitBucket")


def create_repo(l_application_name):
    json_request = '{"name": "' + l_application_name + '","scmId": "git","forkable": true }'
    json_headers = {'X-Atlassian-Token': 'no-check', 'Content-Type': 'application/json'}
    base_url = "https://test.no/git/rest/api/1.0/projects/VAAPC/repos"

    update_req = requests.post(base_url, data=json_request, headers=json_headers, auth=HTTPBasicAuth("ab24716", base64.b64decode("QnJvbnplMDU=")))
    print(update_req)
    print(update_req.status_code)
    if update_req.status_code == 201:
        print("New repository has been created")
    else:
        sys.exit("Repo creation failed")


def execute_shell(l_command):
    subprocess.call(l_command, shell=True)


def create_gitignore(l_repo_name):
    l_command = []
    os.makedirs("temp_location")
    os.chdir("temp_location")
    file = open(".gitignore", 'w')
    file.close()
    os.chmod(".gitignore", 0o777)

    l_command.append("git init")
    l_command.append("git remote add temp_origin https://AB24716:Bronze05@test.no/git/scm/vaapc/%s.git" %l_repo_name.lower())
    l_command.append("git add .gitignore")
    l_command.append("git commit -m \"Initial commit\" ")
    l_command.append("git push temp_origin master")

    print(l_command)

    for l_command_count in range(0, len(l_command)):
        execute_shell(l_command[l_command_count])


def submit_request(l_json_request,l_repo_name):
    headers = {'X-Atlassian-Token': 'no-check', 'Content-Type': 'application/json'}
    repo_url = "https://test.no/git/rest/branch-permissions/2.0/projects/vaapc/repos/%s/restrictions/" %l_repo_name

    post_request = requests.post(repo_url, data=l_json_request, headers=headers, auth=HTTPBasicAuth("ab24716", base64.b64decode("QnJvbnplMDU=")))

    if post_request.status_code == 200:
        print("Permissions have been defined")
    else:
        print("Error in defining permissions")


def define_branch_permission(l_repo_name):
    json_request = []
    json_request.append('{ "type": "pull-request-only","matcher": {"id": "refs/heads/master","type": {"id": "BRANCH","name": "Branch"}},"groups": ["6578-testApp_admins"]}')
    json_request.append('{ "type": "no-deletes","matcher": {"id": "refs/heads/master","type": {"id": "BRANCH","name": "Branch"}}}')
    json_request.append('{ "type": "read-only","matcher": {"id": "refs/heads/master","type": {"id": "BRANCH","name": "Branch"}},"groups": ["6578-testApp_admins", "6578-testApp_AM_Team"]}')
    json_request.append('{ "type": "fast-forward-only","matcher": {"id": "refs/heads/master","type": {"id": "BRANCH","name": "Branch"}}}')

    for l_req_count in range(0,len(json_request)):
        print(json_request[l_req_count])
        submit_request(json_request[l_req_count], l_repo_name)


def hook_enable(l_repo_name):
    headers = {'X-Atlassian-Token': 'no-check', 'Content-Type': 'application/json'}
    json_input = '{ "cloneType": "http", "jenkinsBase": "https://devops-build.tech-02.net", "gitRepoUrl": "https://test.no/git/scm/vaapc/%s.git", "enabled": true, "ignoreCerts": true}' %l_repo_name.lower()
    hook_enable_url = "https://test.no/git/rest/api/1.0/projects/VAAPC/repos/%s/settings/hooks/com.nerdwin15.stash-stash-webhook-jenkins:jenkinsPostReceiveHook/enabled" %l_repo_name

    post_hook_enable = requests.put(hook_enable_url, data=json_input, headers=headers, auth=HTTPBasicAuth("ab24716", base64.b64decode("QnJvbnplMDU=")))

    if post_hook_enable.status_code == 200:
        print("Webhook successfully enabled")
    else:
        print("Webhook couldnt be enabled because of failure")


if check_repo(os.environ["Application_Name"]):
    create_repo(os.environ["Application_Name"])
    create_gitignore(os.environ["Application_Name"])
    define_branch_permission(os.environ["Application_Name"])
    hook_enable(os.environ["Application_Name"])
else:
    print("Repository already present. Branch permissions and webhooks will be re-configured.")
    define_branch_permission(os.environ["Application_Name"])
    hook_enable(os.environ["Application_Name"])