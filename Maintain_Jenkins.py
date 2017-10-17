import requests
from requests.auth import HTTPBasicAuth
import base64
import shutil
import xml.etree.ElementTree as ET
import xml.dom.minidom
import sys

class MaintainJenkins:

   def capture_job_list(self):
      repo_name = []
      list_repo_url = "https://10.78.19.6/api/xml"

      list_repo_req = requests.get(list_repo_url, verify=False,auth=HTTPBasicAuth("cicdadmin", base64.b64decode("UXdlckFzZGYxMjM0"))).text

      xmldoc = xml.dom.minidom.parseString(list_repo_req)
      itemlist = xmldoc.getElementsByTagName('name')

      print(self.job_pattern)
      print(self.repo_prefix)

      for s in itemlist:
         if ((self.job_pattern == s.firstChild.nodeValue.split('_')[-1]) or (self.job_pattern == "All")) and (self.repo_prefix in s.firstChild.nodeValue):
             print(s.firstChild.nodeValue)
             print (s.firstChild.nodeValue.split('_')[-1])
             repo_name.append(s.firstChild.nodeValue)

      return repo_name

   def get_config(self, p_repo_name):

       repo_url = "https://10.78.19.6/job/%s/config.xml" %p_repo_name

       update_req = requests.get(repo_url, verify=False,auth=HTTPBasicAuth("cicdadmin", base64.b64decode("UXdlckFzZGYxMjM0")), stream=True)
       print (update_req)
       if update_req.status_code == 200:
           with open('temp_config.xml', 'wb') as handle:
             update_req.raw.decode_content = True
             shutil.copyfileobj(update_req.raw, handle)
       else:
           print ("Request for gathering build job names failed with error")
           sys.exit(update_req.status_code)


   def update_config_file(self):
       tree = ET.parse('temp_config.xml')
       root = tree.getroot()
       branch_present = "false"
       branch_update = "false"

       for git in root.iter('scm'):
           for branch in git.iter('branches'):
             l_number_branches = len(branch)
             for l_branch_count in range (0, l_number_branches):
                  print (branch[l_branch_count][0].text)
                  if branch[l_branch_count][0].text == "*/" + self.branch_name + "/*":
                      branch_present = "true"
             if branch_present != "true":
                  b = ET.SubElement(branch, 'hudson.plugins.git.BranchSpec')
                  c = ET.SubElement(b, 'name')
                  c.text = '*/' + self.branch_name + '/*'
                  tree.write('config.xml')
                  branch_update = "true"
       return branch_update

   def push_config_changes(self, p_repo_name):
       config_file = open('config.xml', 'rb')
       headers = {'content-type': 'application/xml'}

       repo_url = "https://10.78.19.6/job/%s/config.xml" %p_repo_name

       update_req = requests.post(repo_url, verify=False, data=config_file, headers=headers, auth=HTTPBasicAuth("cicdadmin", base64.b64decode("UXdlckFzZGYxMjM0")))

       print (update_req)

   def update_jenkins_branch_list(self):
       l_job_list = self.capture_job_list()
       value_len = len(l_job_list)

       for i in range(0, value_len):
           print(l_job_list[i])
           self.get_config(l_job_list[i])
           l_udpate_status = self.update_config_file()

           if l_udpate_status == "true":
              self.push_config_changes (l_job_list[i])


   def __init__(self,job_group, job, branch_name):
       self.job_group = job_group
       self.job = job
       self.branch_name = branch_name
       if self.job_group == "Test":
           self.repo_prefix = "4748"
       elif self.job_group == "testApp":
           self.repo_prefix = "6578"
       if self.job == "Build":
           self.job_pattern = "application"
       elif self.job == "Sonar":
           self.job_pattern = "Sonar"
       elif self.job == "All":
           self.job_pattern = "All"
