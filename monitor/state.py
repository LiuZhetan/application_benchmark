import subprocess
import logging
from utils.shell import shell_background, sudo

# if sucess return Popen object of running monitor process, else return None
def monitor_cpu(cpu_list:str, out_file:str):
    try:
        '''return subprocess.Popen(
            ["sar", "-u", "-P", f"{cpu_list}", f"{1}"], 
            stdout=out_fd,
            stderr=subprocess.DEVNULL)'''
        return shell_background(f'sar -u -P {cpu_list} 1 > {out_file}')
    except subprocess.CalledProcessError as e:
        logging.error('Fail to start CPU monitor')
        logging.error(e)
        return None

# if sucess return Popen object of running monitor process, else return None
def monitor_net(interface:str, out_file:str):
    try:
        '''return subprocess.Popen(
            ['ifstat','-t', '-n','-i', f'{interface}'], 
            stdout=out_fd,
            stderr=subprocess.DEVNULL)'''
        return shell_background(f'ifstat -t -n -i {interface} > {out_file}')
    except subprocess.CalledProcessError as e:
        logging.error('Fail to start network monitor')
        logging.error(e)
        return None

# if sucess return Popen object of running monitor process, else return None
def monitor_io(pid:int, out_file:str):
    try:
        '''return subprocess.Popen(
            ['sudo','iotop','-o','-p',f'{pid}','-b','-t','-q'], 
            stderr=subprocess.DEVNULL,
            stdout=out_fd)'''
        sudo()
        return shell_background(f'sudo iotop -o -p {pid} -b -t -q > {out_file}')
    except subprocess.CalledProcessError as e:
        logging.error('Fail to start I/O monitor')
        logging.error(e)
        return None

if __name__ == "__main__":
    proc = monitor_cpu("all", "cpu.log")
    print(proc.pid)