import subprocess as sp
import os
import re

def set_esg_env(script = "/etc/esg.env"):
    """
    Launch a bash shell to read in the esg.env script, see what environment 
    variables get set in the shell, and copy them into the python session.
    This will also include any environment variables loaded automatically 
    from .bashrc or similar.
    """
    
    command = [". %s; env" % script]

    output = sp.Popen(command, shell=True, stdout=sp.PIPE).communicate()[0]

    match = re.compile("(.*?)=(.*)$").match

    for line in output.split("\n"):
        m = match(line)
        if m:
            key = m.group(1)
            val = m.group(2)
            os.environ[key] = val


if __name__ == '__main__':
    os.system("echo $PATH")
    set_esg_env()
    os.system("echo $PATH")
