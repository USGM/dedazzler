#!/usr/bin/env python
"""
Dedazzler-- undoes the atrocities of 'from module import *', with some
limitations.

This module must be run in an environment that can import the same modules
that the original module would and result in the same names.

It also depends on the names imported by a modules __all__ all exist within
dir(module) and do not start with an underscore.

These conditions should be satisfiable in 99% of cases.

Once this program is finished modifying a module, a linter should be used to
remove unnecessary imports and find names that aren't defined.
"""
import re
import sys
import time

from argparse import ArgumentParser
from shutil import copyfile
# Some men just want to watch the world burn.
__all__ = [ 'replace_imports', 'import_generator']

star_match = re.compile('from\s(?P<module>[\.\w]+)\simport\s[*]')
now = str(time.time())
error = lambda x: sys.stderr.write(x + '\n')

def replace_imports(lines):
    """
    Iterates through lines in a Python file, looks for 'from module import *'
    statements, and attempts to fix them.
    """
    for line_num, line in enumerate(lines):
        match = star_match.search(line)
        if match:
            newline = import_generator(match.groupdict()['module'])
            if newline:
                lines[line_num] = newline
    return lines

def import_generator(modulename):
    try:
        prop_depth = modulename.split('.')[1:]
        namespace = __import__(modulename)
        for prop in prop_depth:
            namespace = getattr(namespace, prop)
    except ImportError:
        error("Couldn't import module '%s'!" % modulename)
        return
    directory = [ name for name in dir(namespace) if not name.startswith('_') ]
    return "from %s import %s\n"% (modulename, ', '.join(directory))

def do_full_run(file_list, backup):
    for arg in file_list:
        try:
            if backup:
                backup = "%s.%s" % (arg, now)
                copyfile(arg, backup)
            target = open(arg)
            new_lines = replace_imports(target.readlines())
            target.close()
            target = open(arg, 'w')
            target.writelines(new_lines)
            message = "Processed '%s'." % arg
            if backup:
                message += " Backed up to '%s'" % backup
            print message
        except IOError as e:
            print "Could not work with %s. %s" % (arg, e)
            continue

if __name__ == '__main__':
    parser = ArgumentParser(description="Expand 'from module import *' lines in Python.")
    parser.add_argument("file", help="File to expand imports on", nargs="+")
    parser.add_argument("-b", "--backup", help="Backup the file first.", action='store_true')
    args = parser.parse_args()
    do_full_run(args.file, args.backup)
