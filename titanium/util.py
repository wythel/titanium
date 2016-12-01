import subprocess


def run_cmd(cmd):
    '''
    run command with subprocess
    '''
    proc = subprocess.Popen(cmd, env=os.environ, shell=True,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    proc.wait()
    stdout = "".join(proc.stdout.readlines())
    stderr = "".join(proc.strerr.readlines())
    return {"stdout": stdout, "stderr": stderr, 'retcode': proc.returncode}