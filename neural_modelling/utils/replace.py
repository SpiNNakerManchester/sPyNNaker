# Script to replace one string with another, transforming an input file into an
# output file. Note that this code runs with an uncertain version of Python;
# care needs to be taken to ensure that it is both 2.7 and 3.* compatible.

import sys

def change(string, match, replacement):
    return str(replacement).join(str(string).split(str(match)))

if len(sys.argv) != 5:
    sys.stderr.write(
        "wrong # arguments: should be {} fromString toString inFile outFile\n"
        .format(sys.argv[0]))
    sys.exit(1)
was, to, inf, outf = sys.argv[1:]

with open(inf) as i:
    with open(outf, 'w') as o:
        for line in i:
            o.write(change(line, was, to))
