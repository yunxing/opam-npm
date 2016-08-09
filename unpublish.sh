#!/usr/bin/env bash

while read p; do
    npm unpublish --force @yunxing-test2/"${p}"
done < publishedPackages.txt
