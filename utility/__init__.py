# UTILITY/__INIT__.PY

# ## PYTHON IMPORTS
import os
import threading
import traceback


# ## CLASS

class RepeatTimer(threading.Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            try:
                self.function(*self.args, **self.kwargs)
            except Exception as e:
                print(repr(e))
                traceback.print_tb(e.__traceback__)


# ## FUNCTIONS

def get_environment_variable(key, default, parser=str):
    value = os.environ.get(key)
    return default if value is None else parser(value)
