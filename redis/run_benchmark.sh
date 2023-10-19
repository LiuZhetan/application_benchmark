#!/bin/bash

# 初始化变量
test_num=8
prefix="local"
ouput_dir="results"
limit_cpu="none"
linear_growth=1
growth_rate=1
init_clients=50
init_query=10000
pipelines=16
data_size=32
extra_args=""

help_info="run_benchmark [options]

  -h 帮助
  -n [iter_num] 测试轮次(测试迭代次数)
  -o [ouput_directory] 输出的文件夹,默认为output
  -p [prefix] 输出文件的前缀
  -C [limit_cpus] 使用cset限制测试运行在limit_cpu上,limit_cpu可以是一个列表,例如-l 0,1将测试限制在cpu0和cpu1上
  -e 指数级别增长测试规模(默认线性增长,即:每次规模迭代,测试规模翻倍)
  -r [growth_rate] 每次迭代后测试规模增长的比例,默认为1
  -c [client_num] 初始的客户数目
  -q [total_query_num] 初始的总请求数目
  -P redis-benchmark pipeline
  -d redis-benchmark data size
  -A [args] 其他redis-benchmark参数
  "


# 使用 getopts 处理参数
while getopts "hn:p:o:C:lc:q:P:d:A" opt; do
  case ${opt} in
    h)
      echo -e "$help_info"
      exit 1
      ;;
    n)
      test_num=$OPTARG
      ;;
    p)
      prefix=$OPTARG
      ;;
    o)
      ouput_dir=$OPTARG
      ;;
    C)
      limit_cpu=$OPTARG
      ;;
    l)
      linear_growth=1
      ;;
    c)
      init_clients=$OPTARG
      ;;
    q)
      init_query=$OPTARG
      ;;
    P)
      pipelines=$OPTARG
      ;;
    d)
      data_size=$OPTARG
      ;;
    A)
      extra_args=$OPTARG
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
mkdir -p "$ouput_dir"

RUN_SERVER="redis-server"
RUN_CLI="redis-cli"
RUN_BENCHMARK="redis-benchmark"
CUT_HEAD=""

if [ "$limit_cpu" != "none" ]; then
  echo "limited cpus is $limit_cpu"
  sudo cset shield --cpu="$limit_cpu"
  EXEC="sudo cset shield --exec"
  RUN_SERVER="$EXEC redis-server --"
  RUN_CLI="$EXEC redis-cli --"
  RUN_BENCHMARK="$EXEC redis-benchmark --"
  CUT_HEAD="| tail -n +2"
fi

if sudo lsof -Pi :6379 -sTCP:LISTEN -t >/dev/null ; then
    echo "Redis is running"
else
    echo "Redis is not running, starting Redis"
    $RUN_SERVER > redis_server_info.txt 2>&1 &
fi

sleep 4 

echo "Measuring latency:"
$RUN_CLI --latency -i 5 "$CUT_HEAD" | sudo tee results/latency.txt

#echo "Measuring intrinsic latency, it takes 80 seconds......"
#$RUN_CLI --csv --intrinsic-latency 80  "$CUT_HEAD" | tee results/intrinsic-latency.txt

echo "$CUT_HEAD"

echo "......Running benchmark......"
echo "============================="

for ((i=1; i <= test_num; i++))
do
    if [ $linear_growth == 0 ]; then
      num=$((2**(i-1)))
    else
      num=i
    fi
    num=$((growth_rate*num))
    echo Clinet and query num X$num
    clinet_num=$((num*init_clients))
    query_total=$((num*init_query))
    echo "$RUN_BENCHMARK -P $pipelines -d $data_size -c $clinet_num -n $query_total --csv $CUT_HEAD $extra_args"
    $RUN_BENCHMARK -P $pipelines -d $data_size -c $clinet_num -n $query_total --csv ${CUT_HEAD} $extra_args \
    | sudo tee $ouput_dir/"$prefix"-redis-benchmark-client:$clinet_num-query:$query_total.csv
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