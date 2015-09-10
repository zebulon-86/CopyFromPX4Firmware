#!/usr/bin/env python
"""
This converts a binary imagge to an object file
"""
from __future__ import print_function
import subprocess
import argparse
import re
from subprocess import PIPE

#pylint: disable=invalid-name
parser = argparse.ArgumentParser(description='Convert bin to obj.')
parser.add_argument('--c_flags', required=True)
parser.add_argument('--c_compiler', required=True)
parser.add_argument('--nm', required=True)
parser.add_argument('--ld', required=True)
parser.add_argument('--objcopy', required=True)
parser.add_argument('--bin', required=True)
parser.add_argument('--obj', required=True)
parser.add_argument('--var', required=True)
args = parser.parse_args()

in_bin = args.bin
c_flags = args.c_flags
c_compiler = args.c_compiler
nm = args.nm
ld = args.ld
obj = args.obj
var = args.var
objcopy = args.objcopy

sym = "_binary_" + in_bin.replace('/', '_').replace('.', '_').replace('-', '_')
#print("sym: ", sym)

# write empty file
with open('{obj:s}.c'.format(**locals()), 'w') as f:
    f.write("")

def run_cmd(cmd, d):
    cmd = cmd.format(**d)
    #print(cmd)
    proc = subprocess.Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    if stderr != "":
        raise RuntimeError(stderr)
    return stdout

# do compile
run_cmd("{c_compiler:s} {c_flags:s} -c {obj:s}.c -o {obj:s}.c.o",
        locals())

# link
run_cmd("{ld:s} -r -o {obj:s}.bin.o {obj:s}.c.o -b binary {in_bin:s}",
        locals())

# get size of image
stdout = run_cmd("{nm:s} -p --radix=x {obj:s}.bin.o", locals())
re_size = re.compile("(^[0-9A-Fa-f]*) .*{sym:s}_size".format(
    **locals()))
size_match = re.match(re_size, stdout)
size = size_match.group(1)
#print("romfs size: ", size)

# write size to file
with open('{obj:s}.c'.format(**locals()), 'w') as f:
    f.write("const unsigned int {var:s}_len = 0x{size:s};".format(
        **locals()))

# do compile
run_cmd("{c_compiler:s} {c_flags:s} -c {obj:s}.c -o {obj:s}.c.o",
        locals())

# link
run_cmd("{ld:s} -r -o {obj:s} {obj:s}.c.o {obj:s}.bin.o",
        locals())

# obj copy
run_cmd("""
{objcopy:s} {obj:s}
    --redefine-sym {sym:s}_start={var:s}
    --strip-symbol {sym:s}_size
    --strip-symbol {sym:s}_end
    --rename-section .data=.rodata
""", locals())

# vim: set et ft=python fenc= ff=unix sts=4 sw=4 ts=4 :