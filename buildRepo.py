#!/usr/bin/python
import re
import sys
import os
import json
import subprocess
import urllib
import base64
import urllib2
from config import *
from common import *

if len(sys.argv) < 2:
    print "USAGE: buildRepo.py packageName1 packageName2..."
    exit(-1)

packages = "./_build/opam-repository/packages/"

def git_createTime(dir):
    return "git log --diff-filter=A --follow --format=%at -1 -- " + dir

def bash(cmd):
    print "#" + cmd
    p = subprocess.Popen(['/bin/bash', '-c', cmd], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    return p.communicate()

def getSortedSubDirs(dir):
    subs = os.listdir(dir)
    max_time = 0
    max_subDir = ""
    def gitTime(sub):
        cmd = ("cd %s;" % dir ) + git_createTime(sub)
        out, err = bash(cmd)
        if out == "": return 0
        return int(out)
    return list(reversed(sorted(subs, key=gitTime)))

def getURLFromURLFile(urlFile):
    return re.search(r"(archive:\s*|http:\s*)\"(.*)\"", open(urlFile).read()).group(2)


def buildCURLCMD(url):
    return "curl -OL --insecure " + url

def buildUnzipCMD(tarName):
    return "tar xzvf " + tarName + " -C unzipped"

def createRepo(packageName):
    data = {
        'name': packageName
    }
    req = urllib2.Request('https://api.github.com/orgs/%s/repos' % githubOrgName)
    req.add_header('Content-Type', 'application/json')

    base64string = base64.encodestring('%s:%s' % (githubUsername,
                                                  githubToken)).replace('\n', '')
    req.add_header("Authorization", "Basic %s" % base64string)
    try:
        result = urllib2.urlopen(req, data=json.dumps(data))
    except urllib2.HTTPError as e:
        if e.code != 422:
            raise e

def buildTarget(packageDir, pkg, target):
    '''
    build a package with target version
    '''

    version = getVersionFromStr(target) + getPrereleaseTag(target)

    bash("cd %s; mkdir -p npmdirect; " % packageDir)

    npmdirectPath = os.path.join(packageDir, "npmdirect")

    pkgJSONFile = os.path.join(npmdirectPath, "package.json")

    bash("./nameToNPMDirect.py %s %s > %s" % (pkg, version, pkgJSONFile))

    out, err = bash("cd %s; npm publish --access public" % (npmdirectPath))

    if err:
        print "error: %s" % err

    if err and not forceUpdate:
        return

    targetDir = os.path.join(packageDir, target)

    targetOpamFile = os.path.join(targetDir, "opam")
    targetURLFile = os.path.join(targetDir, "url")
    targetFilesDir = os.path.join(targetDir, "files")
    try:
        targetURL = getURLFromURLFile(targetURLFile)
        packageName = targetURL.rsplit('/', 1)[-1]
        print "downloading %s to %s" % (targetURL, packageDir)

        bash("cd %s; " % packageDir + buildCURLCMD(targetURL))
        tarName = targetURL.split("/")[-1]
        tarPath = os.path.join(packageDir, tarName)
        bash("cd %s; rm -rf unzipped; mkdir unzipped; " % packageDir + buildUnzipCMD(tarName))
        print "unzipping %s " % tarPath
    except:
        import traceback
        print "Failed at downloading package:"
        traceback.print_stack()
        print "Creating empty package:"
        bash("cd %s; mkdir unzipped; " % packageDir)


    createRepo(pkg)
    unzippedPath = os.path.join(packageDir, "unzipped")

    if len(os.listdir(unzippedPath)) == 1:
        unzippedPath = os.path.join(unzippedPath, os.listdir(unzippedPath)[0])

    pkgJSONFile = os.path.join(unzippedPath, "package.json")

    bash("cp -a %s/. %s" % (targetFilesDir, unzippedPath))

    bash("cd %s; for f in *.patch; do patch -p1 < $f; done;" % unzippedPath)

    bash("cd %s; rm .gitignore; git init; git add .; git commit -m 'init commit' " % unzippedPath)

    bash("./OPAMToNPM.py %s %s %s > %s" % (targetOpamFile, pkg, version, pkgJSONFile))

    bash("cd %s; git add .; git commit -m 'add package.json' " % unzippedPath)

    bash("cd %s; git tag -f %s" % (unzippedPath, version))

    print(bash("cat %s" % pkgJSONFile)[0])

    bash("cd %s; git remote add origin git@github.com:npm-opam/%s.git; git push -f --tags" % (unzippedPath, pkg))

def buildPackage(pkg):
    split = pkg.split("/")
    pkg = split[0]
    numPkgToBuild = 1
    if len(split) > 1:
        numPkgToBuild = int(split[1])
    packageDir = os.path.join(packages, pkg)
    dirs = getSortedSubDirs(packageDir)
    dirs = [dir for dir in dirs if dir not in blacklistedPkgs]
    for target in dirs[:numPkgToBuild]:
        buildTarget(packageDir, pkg, target)


if __name__ == "__main__":
    from multiprocessing import Process
    ps = []
    for pkg in sys.argv[1:]:
        p = Process(target=buildPackage, args=(pkg,))
        p.start()
        ps.append(p)
    for p in ps:
        p.join()
