# UTILITY/PRINT.PY

# ## PYTHON IMPORTS
import uuid
import traceback


# ## FUNCTIONS

def safe_print(*args, **kwargs):
    temp = ''
    for arg in args:
        if type(arg) is str:
            temp += arg + ' '
        else:
            temp += repr(arg) + ' '
    temp.strip()
    print(temp.encode('ascii', 'backslashreplace').decode(), **kwargs)


def buffered_print(name, safe=False, sep=" ", end="\n"):
    header = name + " - " + uuid.uuid1().hex
    print("\n++++++++++ %s ++++++++++\n" % header, flush=True)
    print_func = safe_print if safe else print
    print_buffer = []

    def accumulator(*args):
        nonlocal print_buffer
        print_buffer += [*args, end]

    def printer():
        nonlocal print_buffer
        top_header = "========== %s ==========" % header
        print_buffer = ["\n", top_header, "\n"] + print_buffer
        print_buffer += [("=" * len(top_header)), "\n"]
        print_str = sep.join(map(str, print_buffer))
        print_func(print_str, flush=True)

    setattr(accumulator, 'print', printer)
    return accumulator


def error_print(error):
    print(repr(error))
    traceback.print_tb(error.__traceback__)
