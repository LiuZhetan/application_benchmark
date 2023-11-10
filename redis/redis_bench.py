import argparse
import subprocess
import os
import signal
import sys
import logging
from logging import info, debug
import time

from monitor.state import monitor_cpu, monitor_net
from utils.shell import shell_out, shell_run, shell_call, sudo, shell_background

def parse_args():
    parser = argparse.ArgumentParser(description='运行一组redis-benchmark测试')
    parser.add_argument('--iter_num', default=8, metavar='num', type=int, help='测试次数')
    parser.add_argument('--ouput', default="results", metavar="dir", type=str, help='输出数据的目录')
    parser.add_argument('--prefix', default="local", metavar='str', type=str, help='输出文件的前缀')
    parser.add_argument('--server_cpu', default="0", metavar='cpu1,...,cpuN', type=str, help='限制redis-server在某些cpu上')
    parser.add_argument('--clinet_cpu', default="1", metavar='cpu1,...,cpuN', type=str, help='限制redis-benchamrk的client在某些cpu上')
    parser.add_argument('--growth_fun', default="linear", type=str, help='每次迭代规模增长的函数，默认线性函数')
    parser.add_argument('--growth_rate', default=1, type=float, help='增长因子,growth_fun计算增长规模后乘以增长因子即为下一次的测试规模')
    parser.add_argument('--initial_clinet', default=50, type=int, help='初始的客户数目')
    parser.add_argument('--initial_request', default=10000, type=int, help='初始的请求总数')
    parser.add_argument('--pipelines', default=16, type=int, help='redis-benchmark 的pipeline参数')
    parser.add_argument('--data_size', default=32, type=int, help='redis-benchmark 的data size参数')
    parser.add_argument('--shutdown', action='store_true', help='运行结束后关闭服务器')
    parser.add_argument('--log', default='info', type=str, help='日志层级,分别为info、debug、error')
    parser.add_argument('--latency', action='store_true', help='是否测试redis latency')
    parser.add_argument('--others', default='', metavar='option val', type=str, help='redis-benchmark 的其他参数，使用空格分隔')
    return parser.parse_args()

def start_server() -> subprocess.Popen[bytes]:
    try:
        server_proc = shell_background(f'redis-server > redis_server_info.txt 2>&1')
        return server_proc.pid
    except subprocess.CalledProcessError as e:
        logging.error(e)
        raise Exception('Fail to start redis server')
    
def set_log(log:str):
    log_dict = {
        'info': logging.INFO,
        'error': logging.ERROR,
        'debug': logging.DEBUG,
    }
    if log in log_dict.keys():
        logging.basicConfig(level=log_dict[log])
    else:
        logging.basicConfig(level=logging.INFO)

def set_growth_fun(fun:str):
    fun_dict = {
    'linear' : lambda x : x,
    'exp' : lambda x : 2 ** (x-1)
    }
    return fun_dict['linear'] if fun not in fun_dict.keys() else fun_dict[fun]

# kill process and all its children
def kill_all(p:subprocess.Popen):
    try:
        shell_run(f'pkill -P  {p.pid}')
    except subprocess.CalledProcessError:
        logging.error(f'pid:{p} is not killed')

def handler(signum, frame):
    sudo()
    shell_run('sudo pkill sar')
    shell_run('sudo pkill ifstat')
    shell_run('sudo pkill iotop')
    exit(0)

signal.signal(signal.SIGINT, handler)

def main(args):
    sudo()
    # 如果redis服务器没有启动，则启动服务器
    try:
        res = shell_out('pgrep redis-server 2>/dev/null').decode('utf-8')
        server_pid = int(res.splitlines()[0])
        info("Redis is already running")
    except subprocess.CalledProcessError:
        # 运行redis-server
        info("Redis is not running, starting Redis")
        server_pid = start_server()
    debug(f"Redis is running, pid:{server_pid}")
    shell_call(f'taskset -p -c {args.server_cpu} {server_pid}')
    time.sleep(2)
    
    out_dir = args.ouput
    if args.latency == 1:
        info("Measuring latency......")
        shell_call(f'redis-cli --latency -i 5 | sudo tee {out_dir}/latency.txt')
        info("Measuring intrinsic latency......")
        shell_call(f'redis-cli --csv --intrinsic-latency 80 | sudo tee {out_dir}/intrinsic-latency.txt')

    info("......Running benchmark......")
    info("=============================")

    growth_fun = set_growth_fun(args.growth_fun)

    # 创建监控文件存放的路径
    path = f'{out_dir}/monitor'
    shell_call(f'mkdir -p {path}')
    shell_call(f'mkdir -p {path}/cpu')
    shell_call(f'mkdir -p {path}/net')
    shell_call(f'mkdir -p {path}/io')

    for i in range(1,args.iter_num + 1):

        num = growth_fun(i)
        num *= args.growth_rate
        info(f'echo Clinet and query num X{num}')
        clinet_num = num * args.initial_clinet
        query_total = num * args.initial_request
        bench_cmd = f'taskset -c {args.clinet_cpu} redis-benchmark ' + \
                    f'-P {args.pipelines} -d {args.data_size} ' + \
                    f'-c {clinet_num} -n {query_total} ' + \
                    f'--csv {args.others} ' + \
                    f'| sudo tee {out_dir}/{args.prefix}-redis-benchmark-client:' + \
                    f'{clinet_num}-query:{query_total}.csv'
        info(f"{bench_cmd}")
        # 启动监控程序
        cpu = monitor_cpu(args.server_cpu+','+args.clinet_cpu ,f'{path}/cpu/iter{i}_cpu.log')
        net = monitor_net('lo' ,f'{path}/net/iter{i}_net.log')
        time.sleep(2)
        shell_call(bench_cmd)
        # 关闭监控程序
        time.sleep(4)
        kill_all(cpu)
        kill_all(net)
        time.sleep(0.5)

    info("......Finished Benchmark.....")
    info("=============================")

    if args.shutdown:
        info('shutdown redis server')
        os.kill(server_pid, signal.SIGKILL)

if __name__=="__main__":
    args = parse_args()

    # 启用日志
    set_log(args.log)
    # 切换到脚本所在的目录
    p_dir = os.path.dirname(sys.argv[0])
    debug(f"change to directory {p_dir}")
    os.chdir(p_dir)
    shell_call(f'mkdir -p {args.ouput}')
    main(args)