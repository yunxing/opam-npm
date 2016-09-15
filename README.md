# opam-npm
convert opam packages to npm

## Mechanism
A CI machine is constantly reading this repo, and rebuild packages that are new to it
## How to convert a new pacakge to npm (automatically)
Just add a new line to publishedPackages.txt and send a pull request, once the PR is merged, CI will pick it up. 
