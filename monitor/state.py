import subprocess
import logging
from utils.shell import shell_background, sudo

# if sucess return Popen object of running monitor process, else return None
def monitor_cpu(cpu_list:str, out_file:str):
    try:
        return shell_background(f'sar -u -P {cpu_list} 1 > {out_file}')
    except subprocess.CalledProcessError as e:
        logging.error('Fail to start CPU monitor')
        logging.error(e)
        return None

# if sucess return Popen object of running monitor process, else return None
def monitor_net(interface_list:str, out_file:str):
    try:
        return shell_background(f'sar -n DEV --iface={interface_list} 1 > {out_file}')
    except subprocess.CalledProcessError as e:
        logging.error('Fail to start network monitor')
        logging.error(e)
        return None

# if sucess return Popen object of running monitor process, else return None
def monitor_io(dev_list:str, out_file:str):
    try:
        return shell_background(f'sar -d --dev={dev_list} 1 > {out_file}')
    except subprocess.CalledProcessError as e:
        logging.error('Fail to start I/O monitor')
        logging.error(e)
        return None

if __name__ == "__main__":
    proc = monitor_cpu("all", "cpu.log")
    print(proc.pid)