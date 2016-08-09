#!/usr/bin/python
import re
import sys
import json
from config import *

name = sys.argv[1]
version = sys.argv[2]
packageJSON = {}
packageJSON["name"] = prefixWithScope(name)
packageJSON["version"] = version
packageJSON["dependencies"] = {
    "%s-actual" % name: "git://github.com/%s/%s.git#%s" % (githubOrgName, name, version)
}

print(json.dumps(packageJSON, indent=4, separators=(',', ': ')))
