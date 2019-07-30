import subprocess

import config


NFG_FORMAT_BASE = """NFG 1 R ""
{ "Player 1" "Player 2" } { %s %s }

"""


def format_string_for_options(num_rows, num_cols):

    return NFG_FORMAT_BASE % (num_rows, num_cols)


def append_items_to_string(matrix, string):
    import numpy as np

    item_to_add = "%s %s"
    this_string = ""
    for row in np.transpose(matrix):
        for value in row:
            this_string += "%s %s " % (value, value*-1)
    return item_to_add % (string, this_string)


def convert_from_list(l, num_rows):
    l = [float(i) for i in l]
    return [l[:num_rows], l[num_rows:]]


def find_all_equilibria(matrix):
    import numpy as np
    matrix = matrix.round(0)

    matrix = np.array(matrix)

    num_rows = len(matrix)
    num_cols = len(matrix[0])

    string = format_string_for_options(num_rows, num_cols)
    string = append_items_to_string(matrix, string).encode()

    cmd = [config.gambit_exe_path, '-q', '-d', '2']
    sp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    stdout = sp.communicate(string)[0].decode('utf-8').replace('\r', '')

    lines = stdout.split('\n')

    equilibria = []
    for line in lines:
        if line.startswith("NE"):
            ne = line[3:].split(',')
            ne = convert_from_list(ne, num_rows)
            equilibria.append(ne)

    return np.array(equilibria)
