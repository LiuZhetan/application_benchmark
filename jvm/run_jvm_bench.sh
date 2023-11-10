#!/bin/bash

if [ ! -f renaissance-gpl-0.15.0.jar ]; then
    curl -O https://github.com/renaissance-benchmarks/renaissance/releases/download/v0.15.0/renaissance-gpl-0.15.0.jar
fi

out=results
mkdir -p $out

test_set=(als dec-tree fj-kmeans db-shootout scala-kmeans dummy-teardown-failing)
benchmark="java -jar renaissance-gpl-0.15.0.jar"

for i in "${test_set[@]}"
do
   $benchmark $i --csv $out/$i.csv | sudo tee $out/$i.log
done
