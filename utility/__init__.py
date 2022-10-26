# UTILITY/__INIT__.PY

# ## PYTHON IMPORTS
import os
import sys
import random
import threading
import traceback


# ## CLASS

class RepeatTimer(threading.Timer):
    def __init__(self, *args, jitter=False, swing=10, **kwargs):
        self.jitter = jitter
        super().__init__(*args, **kwargs)
        self.swing = self.interval / swing if self.jitter else 0

    @property
    def next_interval(self):
        return self.interval + ((self.swing / 2) - (self.swing * random.random())) if self.jitter else self.interval

    def run(self):
        while not self.finished.wait(self.next_interval):
            try:
                self.function(*self.args, **self.kwargs)
            except Exception as e:
                print(repr(e))
                traceback.print_tb(e.__traceback__)


# ## FUNCTIONS

def get_environment_variable(key, default, parser=str):
    value = os.environ.get(key)
    return default if value is None else parser(value)


def is_interactive_shell():
    return hasattr(sys, 'ps1')
