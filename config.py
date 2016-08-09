import os
def prefixWithScope(str):
    return "@opam-alpha/" + str

depoptBlackList = ["conf-libev", "lablgtk", "ssl", "mirage-xen-ocaml", "tyxml", "reactiveData", "deriving"]

depoptBlackListPerPkg = {
    "utop": ["camlp4"]
}

extraDepPerPkg = {
    "camomile": ["cppo"]
}

blacklistedPkgs = [
    "camlp4.4.03+system",
    "camlp4.4.02+system",
    "inotify.2.2", # doesn't support mac
    "inotify.2.3",
    "ocaml-data-notation.0.0.9"
]

githubUsername = os.environ["GITHUB_USER"]

githubToken = os.environ["GITHUB_TOKEN"]

githubOrgName = "npm-opam"

try:
  forceUpdate = bool(os.environ["FORCE_UPDATE"])
except KeyError:
  forceUpdate = False
