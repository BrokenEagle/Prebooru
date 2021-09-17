# PREBOORU.PY

# ## PYTHON IMPORTS
import os
import subprocess

import psutil
from argparse import ArgumentParser
from sys import platform

# ## LOCAL IMPORTS
from app.logical.file import LoadDefault, PutGetJSON
from app.config import WORKING_DIRECTORY, DATA_FILEPATH


# ## GLOBAL VARIABLES

PID_FILENAME_FORMAT = WORKING_DIRECTORY + DATA_FILEPATH + '%s-server-pid.json'
SERVER_NAMES = ['prebooru', 'similarity']

SERVER_ARGS = {
    'prebooru': "server",
    'worker': "",
    'similarity': "server",
}


# ## FUNCTIONS

# #### Auxiliary functions

def StartServer(name, keepopen):
    print("Starting %s" % name)
    if platform == "win32":
        if keepopen:
            os.system('start cmd.exe /K "python %s.py --title %s"' % (name, SERVER_ARGS[name]))
        else:
            os.system('start python %s.py --title %s' % (name, SERVER_ARGS[name]))
    else:
        try:
            subprocess.call(['gnome-terminal', f'--title="{name}"', '-e', f'bash -c "python {name}.py {SERVER_ARGS[name]}; bash"'])
        except Exception:
            subprocess.call(['xterm', '-e', f'bash -c "python {name}.py; bash"'])


def StopServer(name, *args):
    filename = PID_FILENAME_FORMAT % name
    pid = next(iter(LoadDefault(filename, [])), None)
    if pid is not None:
        print("Stopping %s: %d" % (name, pid))
        p = psutil.Process(pid)
        p.terminate()
        try:
            p.wait(timeout=5)
        except psutil.TimeoutExpired:
            print("Killing %s: %d" % (name, pid))
            p.kill()
        PutGetJSON(filename, 'w', [])
    else:
        print("Server %s not running." % name)


# #### Main execution functions

def StartAll(*args):
    for name in SERVER_NAMES:
        StartServer(name, False)


def StopAll(*args):
    for name in SERVER_NAMES:
        StopServer(name)


# #### Main function

def Main(args):
    if (args.operation in ['start', 'stop']) and (args.type not in SERVER_NAMES):
        print("Must select a valid server name to %s: %s" % (args.operation, ', '.join(SERVER_NAMES)))
        exit(-1)
    switcher = {
        'startall': StartAll,
        'stopall': StopAll,
        'start': StartServer,
        'stop': StopServer,
    }
    switcher[args.operation](args.type, args.keepopen)


# ## EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Helper application to start/stop servers.")
    parser.add_argument('operation', choices=['startall', 'stopall', 'start', 'stop'])
    parser.add_argument('--keepopen', required=False, default=False, action="store_true", help="Keeps the window open even after the process has been killed.")
    parser.add_argument('--type', type=str, required=False, help="prebooru, worker, similarity")
    args = parser.parse_args()
    Main(args)
