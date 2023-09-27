#!/bin/bash

# 初始化变量
test_num=5
prefix="local"
limit_cpu="none"

# 使用 getopts 处理参数
while getopts "n:p:l:" opt; do
  case ${opt} in
    n)
      num=$OPTARG
      ;;
    p)
      prefix=$OPTARG
      ;;
    l)
      limit_cpu=$OPTARG
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
CWD=$(pwd)

cd "$DIR" || exit
mkdir -p results

RUN_SERVER="redis-server"
RUN_CLI="redis-cli"
RUN_BENCHMARK="redis-benchmark"

if [ "$limit_cpu" != "none" ]; then
  echo "limited cpus is $limit_cpu"
  sudo cset shield --cpu="$limit_cpu"
  EXEC="sudo cset shield --exec"
  RUN_SERVER="$EXEC redis-server --"
  RUN_CLI="$EXEC redis-cli --"
  RUN_BENCHMARK="$EXEC redis-benchmark --"
fi

if sudo lsof -Pi :6379 -sTCP:LISTEN -t >/dev/null ; then
    echo "Redis is running"
else
    echo "Redis is not running, starting Redis"
    $RUN_SERVER > redis_server_info.txt 2>&1 &
fi

sleep 4 

echo "Measuring latency:"
$RUN_CLI --latency -i 5 | tail -n +2 | tee results/latency.txt

echo "Measuring intrinsic latency, it takes 80 seconds......"
$RUN_CLI --csv --intrinsic-latency 80  | tail -n +2 | tee results/intrinsic-latency.txt

echo "......Running benchmark......"
echo "============================="

for ((i=1; i <= test_num; i++))
do
    num=$((2**(i-1)))
    echo $num
    clinet_num=$((num*50))
    query_total=$((num*10000))
    $RUN_BENCHMARK -P 16 -d 32 -c $clinet_num -n $query_total --csv \
    | tail -n +2 | tee results/"$prefix"-redis-benchmark-client:$clinet_num-query:$query_total.csv
done

echo "......Finished Benchmark....."
echo "============================="

# 收尾工作
# 关闭服务器
redis_pid=$(ps -aux | grep "$RUN_SERVER" | head -n1 | awk '{print $2}')
sudo kill -9 "$redis_pid"
if [ "$limit_cpu" != "none" ]; then
  sudo cset shield --reset
fi
cd "$CWD" || exit