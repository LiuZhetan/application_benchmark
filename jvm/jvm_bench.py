import argparse
import subprocess
import os
import signal
import sys
import logging
from logging import info, debug
import time
from monitor.state import monitor_cpu, monitor_io, monitor_net
from utils.logging import set_log

from utils.shell import file_exists, shell_call, shell_run, sudo

def parse_args():
    parser = argparse.ArgumentParser(description='运行一组renaissance benchmark')
    parser.add_argument('--benchs', default='als,akka-uct,db-shootout,neo4j-analytics,finagle-http,future-genetic,scala-kmeans', metavar='bench1,bench2', type=str, help='测试的项目')
    parser.add_argument('--output', default="local_results", metavar="dir", type=str, help='输出数据的目录')
    parser.add_argument('--monitor_cpu', default="all", metavar='cpu1,...,cpuN', type=str, help='监控的cpu')
    parser.add_argument('--monitor_iface', default="lo", metavar='interface1,...,interfaceN', type=str, help='监控的interface')
    parser.add_argument('--monitor_disk', default="sda,sdb,sdc", metavar='dev1,...,devN', type=str, help='监控的磁盘')
    parser.add_argument('--log', default='info', type=str, help='日志层级,分别为info、debug、error')
    parser.add_argument('--disable_monitor', action='store_true', help='禁用性能监控')
    return parser.parse_args()

# kill process and all its children
def kill_all(p:subprocess.Popen):
    try:
        shell_run(f'pkill -P  {p.pid}')
    except subprocess.CalledProcessError:
        logging.error(f'pid:{p} is not killed')

def handler(signum, frame):
    sudo()
    shell_run('sudo pkill sar')
    exit(0)

signal.signal(signal.SIGINT, handler)

def main(args):
    out_dir = args.output
    shell_run(f'mkdir -p {out_dir}')
    if not file_exists('renaissance-gpl-0.15.0.jar'):
        info('Download renaissance-gpl-0.15.0.jar......')
        shell_call('curl -O https://github.com/renaissance-benchmarks/renaissance/releases/download/v0.15.0/renaissance-gpl-0.15.0.jar')
    run_bench="java -jar renaissance-gpl-0.15.0.jar"

    # 创建监控文件存放的路径
    path = f'{out_dir}/monitor'
    shell_call(f'mkdir -p {path}')
    shell_call(f'mkdir -p {path}/cpu')
    shell_call(f'mkdir -p {path}/net')
    shell_call(f'mkdir -p {path}/io')

    info("......Running benchmark......")
    info("=============================")

    for bench in args.benchs.split(','):
        info(f"Running project {bench}......")
        # 启动监控程序
        if not args.disable_monitor:
            cpu = monitor_cpu(args.monitor_cpu ,f'{path}/cpu/{bench}_cpu.log')
            net = monitor_net(args.monitor_iface ,f'{path}/net/{bench}_net.log')
            io = monitor_io(args.monitor_disk ,f'{path}/io/{bench}_io.log')
            time.sleep(2)
        shell_call(f'{run_bench} {bench} --csv {out_dir}/{bench}.csv | sudo tee {out_dir}/{bench}.log')
        # 关闭监控程序
        if not args.disable_monitor:
            time.sleep(4)
            kill_all(cpu)
            kill_all(net)
            kill_all(io)
            time.sleep(0.5)

    info("......Finished Benchmark.....")
    info("=============================")


if __name__=='__main__':
    args = parse_args()

    # 启用日志
    set_log(args.log)
    # 切换到脚本所在的目录
    p_dir = os.path.dirname(sys.argv[0])
    debug(f"change to directory {p_dir}")
    os.chdir(p_dir)

    main(args)