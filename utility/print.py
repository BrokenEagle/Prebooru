# UTILITY/PRINT.PY

# ## PYTHON IMPORTS
import uuid
import colorama
import traceback


# ## FUNCTIONS

def safe_print(*args, **kwargs):
    print(_coalesce_arguments(args).encode('ascii', 'backslashreplace').decode(), **kwargs)


def print_info(*args, **kwargs):
    print(colorama.Fore.GREEN + colorama.Style.BRIGHT + _coalesce_arguments(args) + colorama.Style.RESET_ALL, **kwargs)


def print_warn(*args, **kwargs):
    print(colorama.Fore.YELLOW + colorama.Style.BRIGHT + _coalesce_arguments(args) + colorama.Style.RESET_ALL, **kwargs)


def print_error(*args, **kwargs):
    print(colorama.Fore.RED + colorama.Style.BRIGHT + _coalesce_arguments(args) + colorama.Style.RESET_ALL, **kwargs)


def buffered_print(name, safe=False, header=True, sep=" ", end="\n"):
    buffer_key = name + " - " + uuid.uuid1().hex
    if header:
        print("\n++++++++++ %s ++++++++++\n" % buffer_key, flush=True)
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
        print_func(print_str, flush=True)

    setattr(accumulator, 'print', printer)
    return accumulator


def exception_print(error):
    print(repr(error))
    traceback.print_tb(error.__traceback__)


# #### Private

def _coalesce_arguments(args):
    temp = ''
    for arg in args:
        if type(arg) is str:
            temp += arg + ' '
        else:
            temp += repr(arg) + ' '
    return temp.strip()
