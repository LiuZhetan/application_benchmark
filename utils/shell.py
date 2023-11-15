import getpass
import subprocess
import os
import signal
from subprocess import CompletedProcess, Popen, run, check_output, check_call

# run command and print results to stdout
def shell_run(cmd:str) -> CompletedProcess[bytes]:
    return run(['bash', '-c', f'{cmd}'])

# run command and fetch the result in bytes
def shell_out(cmd:str) -> bytes:
    return check_output(['bash', '-c', f'{cmd}'])

# run command and check if successfully run
def shell_call(cmd:str) -> int:
    return check_call(['bash', '-c', f'{cmd}'])

# run command in background
def shell_background(cmd:str) -> Popen:
    return Popen(['bash', '-c', f'{cmd}'])

# try to get root privilege
def sudo():
    run(['sudo','ls','/root'], stdout=subprocess.DEVNULL)

# force to type in password to run under root privilege in background
def sudo_force_run_background(cmd:str) -> Popen:
    try:
        password = getpass.getpass("[sudo] enter your password: ")
        proc =  subprocess.Popen(
            ['bash', '-c', f'{cmd}'], 
            stdin=subprocess.PIPE)
        proc.communicate(password.encode(),timeout=0.01)
    except subprocess.TimeoutExpired:
        return proc

if __name__=="__main__":
    # sudo()
    os.kill(sudo_force_run_background('sudo sleep 100').pid, signal.SIGKILL)