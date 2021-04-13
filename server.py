# PREBOORU.PY

# ## PYTHON IMPORTS
import os
import psutil
from argparse import ArgumentParser

# ## LOCAL IMPORTS
from app.logical.file import LoadDefault, PutGetJSON
from app.config import WORKING_DIRECTORY, DATA_FILEPATH, HAS_EXTERNAL_IMAGE_SERVER


# ## GLOBAL VARIABLES

PID_FILENAME_FORMAT = WORKING_DIRECTORY + DATA_FILEPATH + '%s-server-pid.json'
SERVER_NAMES = ['prebooru', 'worker', 'similarity', 'images']  # NGINX, ...

SERVER_ARGS = {
    'prebooru': "server",
    'worker': "",
    'similarity': "server",
    'images': "",
}


# ## FUNCTIONS

# #### Auxiliary functions

def StartServer(name, keepopen):
    if name == 'images' and HAS_EXTERNAL_IMAGE_SERVER:
        return
    print("Starting %s" % name)
    if keepopen:
        os.system('start cmd.exe /K "python %s.py --title %s"' % (name, SERVER_ARGS[name]))
    else:
        os.system('start python %s.py --title %s' % (name, SERVER_ARGS[name]))


def StopServer(name, *args):
    if name == 'images' and HAS_EXTERNAL_IMAGE_SERVER:
        return
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
    parser.add_argument('--type', type=str, required=False, help="prebooru, worker, similarity, images")
    args = parser.parse_args()
    Main(args)
