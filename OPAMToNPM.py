#!/usr/bin/python
import re
import sys
import json
from config import *
from common import *

def splitKV(txt):
    g = txt.split(":")
    return (g[0], ":".join(g[1:]).strip())

def yieldKVPair(f):
    current = ""
    for l in open(f):
        if l.startswith("#"):
            continue
        l = l.split("#")[0]
        g = re.search(r"^([a-zA-Z\-]+):", l)
        if not g:
            current += l
        else:
            if current != "":
                yield splitKV(current)
            current = l
    if current != "":
        yield splitKV(current)

def unescapeTerm(term):
    if term.startswith("{"):
        return ""
    g = re.search(r'\"(.*)\"', term)
    if g:
        return term
    else:
        return builtInVars[term]

def buildFlatList(txt):
    if txt.startswith("["):
        txt = txt[1:-1]
    txt = txt.strip()
    if txt == "":
        return []
    g = re.findall(r'\"(.*?)\"\s*(\{.*\})?', txt)
    return list(g)

def breakList(txt):
    if txt.startswith("["):
        txt = txt[1:-1]
    txt = txt.strip()
    if txt == "":
        return []

    # Look for lists
    g = re.findall(r'\[([^\[\]]*)\]\s*\{?([^\{\}\[\]]*)\}?', txt, re.S)
    if not g:
        terms = [unescapeTerm(term) for term in re.split(r"[\s\n]+", txt)]

        return [(" ".join(terms), "")]
        # results = []
        # for line in re.split(r"\s+", txt):
        #     results.append((txt, ""))
            # g = re.search(r'"[a-zA-Z0-9\-]*"', line)
            # if not g:
            #     results.append((line, ""))
            #     continue
            # key = g.group(0)
            # g = re.search(r'\{(.*)\}', line)

            # if g:
            #     constraint = g.group(1)
            # else:
            #     constraint = ""
            # results.append((key, constraint))
        # return results
    return g

if len(sys.argv) < 4:
    print "USAGE: OPAMToNPM.py opam_file_path project_name project_version"
    exit -1


def cmdToStrings(cmd):
    return re.findall(r"\"[^\"]+\"|\S+", cmd)

builtInVars = {
    "make": "make",
    "jobs": "4",
    "bin": "$opam_bin",
    "prefix": "$opam_prefix",
    "lib": "$opam_lib",
    "sbin": "$opam_sbin",
    "doc": "$opam_doc",
    "man": "$opam_man",
    "ocaml-native": "true",
    "ocaml-native-dynlink": "true",
}

def unescapeBuiltinVariables(s):
    def escape(matched):
        var = matched.group(1)
        if var in builtInVars:
            return builtInVars[var]
        g = re.search(r"(.*):enable", var)
        if g:
            return "${%s_enable:-disable}" % g.group(1).replace("-", "_")
        g = re.search(r"(.*):installed", var)
        if g:
            return "${%s_installed:-false}" % g.group(1).replace("-", "_")
        raise Exception("Cannot expand variable %s" % var)
    return re.sub(r"%\{(.*?)\}%", escape, s)

# TODO unhack this
def filterCommands(filter):
    if filter == "ocaml-native":
        return False
    if filter == "!ocaml-native":
        return True
    if filter == "preinstalled":
        return True
    return False

def createPostInstallCommand(substs, cmds):
    finalCMD = "eval $(dependencyEnv) && nopam"

    for (subst, _) in substs:
        finalCMD += " && substs %s" % (subst + ".in")

    for cmd in cmds:
        if filterCommands(cmd[1]):
            continue
        subCMDs = cmdToStrings(cmd[0])
        newCMDs = []
        for subCMD in subCMDs:
            g = re.search(r'\"(.*)\"', subCMD)
            if g:
                newCMDs.append(g.group(1))
            else:
                if not subCMD.startswith("{"):
                    newCMDs.append(builtInVars[subCMD])
        finalCMD += " && " + " ".join(newCMDs)
    finalCMD += " && (opam-installer --prefix=$opam_prefix || true)"
    return unescapeBuiltinVariables(finalCMD)

import collections
d = collections.defaultdict(str)
for (k, v) in yieldKVPair(sys.argv[1]):
    d[k] = v

name = sys.argv[2]

packageJSON = {}
packageJSON["name"] = name + "-actual"
packageJSON["version"] = sys.argv[3]
packageJSON["scripts"] = {}
packageJSON["peerDependencies"] = {}
packageJSON["scripts"]["postinstall"] = createPostInstallCommand(buildFlatList(d["substs"]), breakList(d["build"]) + breakList(d["install"]))
packageJSON["dependencies"] = {
    "nopam": "https://github.com/yunxing/nopam.git",
    "substs": "https://github.com/yunxing/substs.git",
    # "ocaml": "https://github.com/npm-opam/ocaml.git#npm-4.02.3",
    "opam-installer-bin": "https://github.com/yunxing/opam-installer-bin.git",
    "dependency-env": "https://github.com/npm-ml/dependency-env.git"
}

def opamVersionToNpmVersion(v):
    v = v.group(0).strip("\"")
    return getVersionFromStr(v) + getPrereleaseTag(name)

def opamRangeToNpmRange(range):
    if range == "" : return "*"
    range = range.strip("{}")
    assert ("|" not in range)
    ranges = [re.sub("\".*\"", opamVersionToNpmVersion, r) for r in [r.strip() for r in range.split("&")] if r != "build" and r != "test"]
    if len(ranges) == 0:
        return "*"
    return " ".join(ranges)

for (dep, range) in buildFlatList(d["depends"]):
    if dep.startswith("base-"):
        continue
    dep = dep.strip("\" ")
    if dep == "": continue
    packageJSON["dependencies"][prefixWithScope(dep)] = opamRangeToNpmRange(range)

if name in extraDepPerPkg:
    for dep in extraDepPerPkg(name):
        packageJSON["dependencies"][dep] = ("https://github.com/npm-opam/" + dep)

for (dep, range) in buildFlatList(d["depopts"]):
    dep = dep.strip("\" ")
    if dep == "" or dep in depoptBlackList: continue
    if name in depoptBlackListPerPkg and dep in depoptBlackListPerPkg[name]: continue
    packageJSON["dependencies"][prefixWithScope(dep)] = opamRangeToNpmRange(range)

g = re.findall(r"ocaml-version ([!=<>]+.*?\".*?\")", d["available"])
if g:
    g = " ".join(g)
    packageJSON["dependencies"][prefixWithScope("ocaml")] = re.sub("\".*?\"", opamVersionToNpmVersion, g)
else:
    packageJSON["dependencies"][prefixWithScope("ocaml")] = ">= 4.2.3"

packageJSON["exportedEnvVars"] = {
    "PATH": {
        "val": "./_build/ocamlfind/bin",
        "resolveAsRelativePath": True,
        "global": True,
        "globalCollisionBehavior": "joinPath"
    },
    "FINDLIB": {
        "val": "./_build/ocamlfind/lib",
        "resolveAsRelativePath": True,
        "global": True,
        "globalCollisionBehavior": "joinPath"
    },
    "version": {
        "val": packageJSON["version"],
        "global": True,
        "globalCollisionBehavior": "clobber"
    },
    "%s_version" % sys.argv[2].replace("-", "_"): {
        "val": packageJSON["version"],
        "global": True,
        "globalCollisionBehavior": "clobber"
    },
    "%s_enable" % sys.argv[2].replace("-", "_"): {
        "val": "enable",
        "global": True,
        "globalCollisionBehavior": "clobber"
    },
    "%s_installed" % sys.argv[2].replace("-", "_"): {
        "val": "true",
        "global": True,
        "globalCollisionBehavior": "clobber"
    }
}

print(json.dumps(packageJSON, indent=4, separators=(',', ': ')))
