#!/bin/bash

if [ -z "$1" ]
then
  n=5
else
  n=$1
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
CWD=$(pwd)

cd "$DIR" || exit
mkdir -p results

echo "set cpus"
sudo cset shield --cpu=0-3

EXEC="sudo cset shield --exec"

if sudo lsof -Pi :6379 -sTCP:LISTEN -t >/dev/null ; then
    echo "Redis is running"
else
    echo "Redis is not running, starting Redis"
    $EXEC redis-server > redis_server_info.txt 2>&1 &
fi

echo "Measuring latency:"
$EXEC redis-cli -- --latency -i 5 \
| tail -n +2 | tee results/latency.txt

echo "Measuring intrinsic latency......"
$EXEC redis-cli -- --csv --intrinsic-latency 80  \
| tail -n +2 | tee results/intrinsic-latency.txt

echo "......Running benchmark......"
echo "============================="

for ((i=1; i <= n; i++))
do
    num=$((2**(i-1)))
    echo $num
    $EXEC redis-benchmark -- -P 16 -d 32 -c $((num*50)) -n $((num*10000)) --csv \
    | tail -n +2 | tee results/benchmark-$((num*50)).csv
done

echo "......Finished Benchmark....."
echo "============================="

sudo cset shield --reset
cd "$CWD" || exit