#!/usr/bin/env python3

# This file is licensed under BSD 3-Clause.
# All license information is available in the included COPYING file.

#
# utils.py
#
# Author       : Finn Rayment <finn@rayment.fr>
# Date created : 12/08/2023
#

import argparse
import platform
import sys


def os_detect(usrinput=None, suppress=False):
    my_os = platform.system()
    if my_os == 'Windows' or usrinput == 'windows':
        my_os = 'windows'
    elif my_os == 'Linux' or usrinput == 'linux':
        my_os = 'linux'
    elif my_os == 'Darwin' or usrinput == 'mac':
        my_os = 'osx'
    else:
        my_os = usrinput if usrinput is not None else my_os
        if not suppress:
            print(f'Unsupported platform {my_os}!')
        sys.exit(1)
    return my_os


def keydic(key, dic, default=None):
    if key in dic:
        return dic[key]
    return default


# https://stackoverflow.com/a/1094933
def sizeof_fmt(num, suffix='B'):
    for unit in ('', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi'):
        if abs(num) < 1024.0:
            return f'{num:3.1f}{unit}{suffix}'
        num /= 1024.0
    return f'{num:.1f}Yi{suffix}'


# https://stackoverflow.com/a/14117511
def check_positive(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f'{value} is not a valid positive int value')
    return ivalue
