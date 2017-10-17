import Maintain_Jenkins
import os

uj = Maintain_Jenkins.MaintainJenkins(os.environ["Job_Group"], os.environ["Job"], os.environ["Branch_Name"])

uj.update_jenkins_branch_list()