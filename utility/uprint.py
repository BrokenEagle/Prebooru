# UTILITY/UPRINT.PY

# ## PYTHON IMPORTS
import uuid
import colorama
import traceback


# ## FUNCTIONS

def checkcolorama(func):
    def wrapper(*args, **kwargs):
        if colorama.initialise.orig_stdout is None:
            normal_print(*args, **kwargs)
        else:
            func(*args, **kwargs)
    return wrapper


def normal_print(*args, trim=False, **kwargs):
    print(_coalesce_arguments(args, trim), **kwargs)


def safe_print(*args, trim=False, **kwargs):
    print(_coalesce_arguments(args, trim).encode('ascii', 'backslashreplace').decode(), **kwargs)


@checkcolorama
def print_info(*args, trim=False, **kwargs):
    print(_convert(_coalesce_arguments(args, trim), 'GREEN'), **kwargs)


@checkcolorama
def print_warning(*args, trim=False, **kwargs):
    print(_convert(_coalesce_arguments(args, trim), 'YELLOW'), **kwargs)


@checkcolorama
def print_error(*args, trim=False, **kwargs):
    print(_convert(_coalesce_arguments(args, trim), 'RED'), **kwargs)


@checkcolorama
def print_sql(*args, trim=False, **kwargs):
    print(_convert(_coalesce_arguments(args, trim), 'CYAN'), **kwargs)


def buffered_print(name, safe=False, header=True, trim=False, sep=" ", end="\n"):
    buffer_key = name + " - " + uuid.uuid1().hex
    if header:
        print("\n++++++++++ %s ++++++++++\n" % buffer_key, flush=True)
    print_func = safe_print if safe else normal_print
    print_buffer = []

    def accumulator(*args):
        nonlocal print_buffer
        print_buffer += [*args, end]

    def printer():
        nonlocal print_buffer
        top_header = "========== %s ==========" % buffer_key
        print_buffer = ["\n", top_header, "\n"] + print_buffer
        print_buffer += [("=" * len(top_header)), "\n"]
        print_str = sep.join(map(str, print_buffer))
        print_func(print_str, trim=trim, flush=True)

    setattr(accumulator, 'print', printer)
    return accumulator


def exception_print(error):
    print(repr(error))
    traceback.print_tb(error.__traceback__)


# #### Private

def _coalesce_arguments(args, trim):
    temp = ''
    for arg in args:
        if type(arg) is str:
            temp += arg + ' '
        else:
            temp += repr(arg) + ' '
    return temp.strip() if trim else temp


def _convert(string, color):
    string = getattr(colorama.Fore, color) + colorama.Style.BRIGHT + string
    string += colorama.Style.RESET_ALL
    return string
