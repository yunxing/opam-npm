import re

def getVersionFromStr(str):
    g = re.search(r"([a-zA-Z0-9_\-]\.)?(\d+\.\d+\.\d+).*", str)
    if g:
        return g.group(2)

    g = re.search(r"([a-zA-Z0-9_\-]\.)?(\d+\.\d+).*", str)

    if g:
        return g.group(2) + ".0"

    g = re.search(r"([a-zA-Z0-9_\-]\.)?(\d+).*", str)
    if g:
        return g.group(2) + ".0.0"
    return "0.0.0"

def getPrereleaseTag(name):
    g = re.search(r".*\+(.*)", name)

    if not g:
        return ""
    return "".join(re.findall(r"\d+", g.group(1)))
