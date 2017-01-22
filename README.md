# opam-npm
convert opam packages to npm

## Mechanism
A CI machine is constantly reading this repo and rebuilding packages that are new to it.
## How to convert a new package to npm (automatically)
Just add a new line to publishedPackages.txt and send a pull request. Once the PR is merged, CI will pick it up. 



## Convert A Package Locally

You can convert a package locally without having to wait for a pull request to be merged. Just clone this repo, as well as the one you want to convert, and run this command on it. It requires that all dependencies are also converted to npm packages, and assumes that they've been published to `opam-alpha` on `npm`. But you can hand edit the output to correct any incorrect assumptions. Most of the popular packages are already published to `opam-alpha` on `npm`.

```
env FORCE_UPDATE="" GITHUB_USER="" GITHUB_TOKEN="" \
  path/to/OPAMToNPM.py path/to/converted/package/opam npm-package-name 0.0.1 > output/location/package.json
```
