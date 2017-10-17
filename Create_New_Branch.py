from requests.auth import HTTPBasicAuth
import requests
import base64
import json
import sys
import shutil
import xml.etree.ElementTree as ET
import os

g_build_status = "True"

def silentremove(filename):
    try:
        os.remove(filename)
    except OSError:
        pass


def check_repo(l_application_name):
    repo_url = "https://gitrepo.no/git/rest/api/1.0/projects/test/repos/%s" %l_application_name

    check_repo_request = requests.get(repo_url, verify=False, auth=HTTPBasicAuth("ab24716", base64.b64decode("QnJvbnplMDU=")), stream=True)

    if check_repo_request.status_code == 404:
        return False
    elif check_repo_request.status_code == 200:
        return True
    else:
        sys.exit("Connection issue with BitBucket")


def check_branch(p_repo, p_branch_name):
    req_url = "https://gitrepo.no/git/rest/api/1.0/projects/test/repos/%s/branches?filterText=%s" %(p_repo, p_branch_name)
    check_branch_request = requests.get(req_url, verify=False, auth=HTTPBasicAuth("ab24716", base64.b64decode("QnJvbnplMDU=")), stream=True)

    if check_branch_request.status_code == 404:
        return False
    elif check_branch_request.status_code == 200:
        json_reader = json.loads(check_branch_request.text)
        branch_count = len(json_reader["values"])
        for l_branch_counter in range(0, branch_count):
            if json_reader["values"][l_branch_counter]["displayId"] == p_branch_name:
                return True
            else:
                return False
    else:
        sys.exit("Connection issue with BitBucket")


def get_ref_branchid(p_repo, p_ref_branch):

    req_url = "https://gitrepo.no/git/rest/api/1.0/projects/test/repos/%s/branches?filterText=%s" % (p_repo, p_ref_branch)
    check_branch_request = requests.get(req_url, verify=False,auth=HTTPBasicAuth("ab24716", base64.b64decode("QnJvbnplMDU=")), stream=True)

    if check_branch_request.status_code == 404:
        return "False"
    elif check_branch_request.status_code == 200:
        json_reader = json.loads(check_branch_request.text)
        branch_count = len(json_reader["values"])
        for l_branch_counter in range(0, branch_count):
            if json_reader["values"][l_branch_counter]["displayId"] == p_ref_branch:
                return json_reader["values"][l_branch_counter]["latestCommit"]
        return "False"
    else:
        sys.exit("Connection issue with BitBucket")


def submit_json_request(p_json_request,p_req_url):
    headers = {'X-Atlassian-Token': 'no-check', 'Content-Type': 'application/json'}

    post_request = requests.post(p_req_url, data=p_json_request, headers=headers, auth=HTTPBasicAuth("ab24716", base64.b64decode("QnJvbnplMDU=")))

    if post_request.status_code == 200:
        return True
    else:
        print( post_request.status_code )
        return False


def create_branch(l_branch_name, ref_branch_id, p_repo):

    req_url = "https://gitrepo.no/git/rest/api/1.0/projects/test/repos/%s/branches" % p_repo

    request_json = '{"name": "%s","startPoint": "%s","message": "This is my branch"}' %(l_branch_name,ref_branch_id)

    status = submit_json_request(request_json, req_url)

    if status:
        print("Branch " + l_branch_name + " has been created in the repository " + p_repo + "." )
    else:
        print("Creation of branch " + l_branch_name + " in the repository " + p_repo + " failed")
        g_build_status = "False"

def define_branch_permission(l_repo_name,p_branch_name):
    json_request = []
    json_request.append('{ "type": "pull-request-only","matcher": {"id": "refs/heads/%s","type": {"id": "BRANCH","name": "Branch"}},"groups": ["6578-testApp_admins"]}' %p_branch_name)
    json_request.append('{ "type": "no-deletes","matcher": {"id": "refs/heads/%s","type": {"id": "BRANCH","name": "Branch"}}}' %p_branch_name)
    json_request.append('{ "type": "read-only","matcher": {"id": "refs/heads/%s","type": {"id": "BRANCH","name": "Branch"}},"groups": ["6578-testApp_admins", "6578-testApp_AM_Team"]}' %p_branch_name)
    json_request.append('{ "type": "fast-forward-only","matcher": {"id": "refs/heads/%s","type": {"id": "BRANCH","name": "Branch"}}}' %p_branch_name)

    repo_url = "https://gitrepo.no/git/rest/branch-permissions/2.0/projects/test/repos/%s/restrictions/" % l_repo_name

    l_permission = ["pull-request-only","no-deletes","read-only","fast-forward-only"]

    for l_req_count in range(0,len(json_request)):
        request_status = submit_json_request(json_request[l_req_count], repo_url)
        if request_status:
           print("Permission " + l_permission[l_req_count]  + " have been defined for the branch " + p_branch_name + " in the repository " + l_repo_name)
        else:
           print("Error in defining permission " + l_permission[l_req_count] + " for the branch " + p_branch_name + " in the repository " + l_repo_name)
           g_build_status = "False"

def get_config( p_repo_name):

       repo_url = "https://10.78.19.6/job/%s/config.xml" %p_repo_name

       update_req = requests.get(repo_url, verify=False,auth=HTTPBasicAuth("cicdadmin", base64.b64decode("UXdlckFzZGYxMjM0")), stream=True)
       if update_req.status_code == 200:
           with open('temp_config.xml', 'wb') as handle:
             update_req.raw.decode_content = True
             shutil.copyfileobj(update_req.raw, handle)
             return True
       else:
           print ("Request for gathering config.xml for the job " + p_repo_name + " failed with error")
           g_build_status = "False"
           return False

def update_config_file(p_branch_name):
       tree = ET.parse('temp_config.xml')
       root = tree.getroot()
       branch_present = "false"
       branch_update = "false"

       for git in root.iter('scm'):
           for branch in git.iter('branches'):
             l_number_branches = len(branch)
             for l_branch_count in range (0, l_number_branches):
                  if branch[l_branch_count][0].text == "*/" + p_branch_name:
                      branch_present = "true"
             if branch_present != "true":
                  b = ET.SubElement(branch, 'hudson.plugins.git.BranchSpec')
                  c = ET.SubElement(b, 'name')
                  c.text = '*/' + p_branch_name
                  tree.write('config.xml')
                  branch_update = "true"
       return branch_update


def update_jenkins_branch(p_repo_name, p_branch_name):
    config_file = open('temp_config.xml', 'w+')
    config_file = open('config.xml', 'w+')
    if get_config(p_repo_name):
       l_update_status = update_config_file(p_branch_name)
       if l_update_status == "true":
           config_file = open('config.xml', 'rb')
           headers = {'content-type': 'application/xml'}

           repo_url = "https://10.78.19.6/job/%s/config.xml" % p_repo_name

           update_req = requests.post(repo_url, verify=False, data=config_file, headers=headers,
                                          auth=HTTPBasicAuth("cicdadmin", base64.b64decode("UXdlckFzZGYxMjM0")))

           if update_req.status_code != 200:
               print("Addition of branch " + p_branch_name + " in the job " + p_repo_name + " failed.")
               g_build_status = "False"
           else:
               print("A new branch " + p_branch_name + " has been added to the job " + p_repo_name + ".")
    silentremove("temp_config.xml")
    silentremove("config.xml")


def get_repo_list():
    repo_url = "https://gitrepo.no/git/rest/api/1.0/projects/test/repos?limit=100"
    repo_list = []

    check_repo_request = requests.get(repo_url, verify=False,
                                      auth=HTTPBasicAuth("ab24716", base64.b64decode("QnJvbnplMDU=")), stream=True)

    if check_repo_request.status_code == 200:
        json_reader = json.loads(check_repo_request.text)
        for element_count in range(0,len(json_reader["values"])):
            print(json_reader["values"][element_count]["name"])
            repo_list.append(json_reader["values"][element_count]["name"])
        return repo_list
    else:
        sys.exit("Connection issue with BitBucket")


branch_name = os.environ["New_Branch"]
ref_branch = os.environ["Source_Branch"]
repo_list_input = os.environ["Repositories"]

#repo_list_input = "4748-Vaap_Sample_Parent;4748-testApp_notification_application"

repo_selection = []

repo_count = repo_list_input.count(';') + 1

for l_repo_count in range(0, repo_count):
    repo_selection.append(repo_list_input.split(';')[l_repo_count])

if repo_selection[0] == "All":
   l_repo_list = get_repo_list()
   for l_repo_count in range(0,len(l_repo_list)):
       if not check_branch(l_repo_list[l_repo_count], branch_name):
           l_ref_branch_id = get_ref_branchid(l_repo_list[l_repo_count], ref_branch)
           if l_ref_branch_id == "False":
               print("Reference branch is not present for " + l_repo_list[l_repo_count] )
               print("Branch not created for the repository " + l_repo_list[l_repo_count])
               g_build_status = "False"
           else:
               create_branch(branch_name, l_ref_branch_id,l_repo_list[l_repo_count])
               define_branch_permission(l_repo_list[l_repo_count], branch_name)
               update_jenkins_branch(l_repo_list[l_repo_count], branch_name)
       else:
           print("Branch " + branch_name + " already present in BitBucket for the repository " + l_repo_list[l_repo_count])
           g_build_status = "False"
else:
   for l_repo_count in range(0, len(repo_selection)):
       print(repo_selection[l_repo_count])
       if check_repo(repo_selection[l_repo_count]):
           if not check_branch(repo_selection[l_repo_count], branch_name):
               l_ref_branch_id = get_ref_branchid(repo_selection[l_repo_count], ref_branch)
               print(l_ref_branch_id)
               create_branch(branch_name, l_ref_branch_id, repo_selection[l_repo_count])
               define_branch_permission(repo_selection[l_repo_count], branch_name)
               update_jenkins_branch(repo_selection[l_repo_count], branch_name)
           else:
               print("Branch " + branch_name + " already present in BitBucket for the repository " + repo_selection[l_repo_count])
               g_build_status = "False"
       else:
           print("Repository " + repo_selection[l_repo_count] + " not present in BitBucket")
           g_build_status = "False"

if g_build_status == "False":
    sys.exit("There are issues in creating/configuring all/certain branches. Please see the above logs.")