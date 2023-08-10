"""Simple test

Anything that starts with the given prefix is a valid test and should be
callable without any arguments.  It should throw an exception on failure.
"""
from __future__ import print_function, division
__all__ = ['run']
from importlib import import_module
import os
import sys
import traceback

def _import(name):
    """Import a name.

    filepath/dirname: import it as a module
    a .name: import via importlib
    """
    if os.path.isfile(name) or os.path.isdir(name):
        basename = os.path.basename(name)
        if not basename:
            basename = os.path.basename(basename)
            dname = os.path.dirname(basename)
        else:
            dname = os.path.dirname(name)
        sys.path.insert(0, dname)
        try:
            return import_module(os.path.splitext(basename)[0])
        except ImportError:
            pass
        finally:
            try:
                sys.path.remove(dname)
            except ValueError:
                pass
    return import_module(name)

def run(name, runall=False, prefix='test_', list_tests=False):
    """Run the tests in name.

    name: str
        A path to a file or .module name.  Optionally followed by a :
        and a name of a particular test to run.  This should be the
        portion of the name that follows `prefix`.
    runall: bool
        Continue running tests even if an error occurs.
    prefix: str
        The prefix on names of tests to run.
    """
    if ':' in name:
        name, targets = name.split(':', 1)
        targets = set(targets.split(','))
    else:
        targets = ()
    if name.endswith('.py'):
        name = os.path.normpath(name[:-3]).replace(os.sep, '.')
    item = _import(name)
    if list_tests:
        print(name, ':', file=sys.stderr, sep='')
    ntried = 0
    npass = 0
    for k in dir(item):
        if not k.startswith(prefix):
            continue
        tname = k[len(prefix):]
        if list_tests:
            print('  ', tname, file=sys.stderr, sep='')
            continue
        if not targets or tname in targets:
            ntried += 1
            print(
                '------------------------------\n',
                'running test: ', tname, '\n',
                file=sys.stderr, sep='')
            try:
                getattr(item, k)()
            except Exception:
                if runall:
                    traceback.print_exc()
                else:
                    raise
                print('\ntest', tname, ': failed', file=sys.stderr)
            else:
                print('\ntest', tname, ': passed', file=sys.stderr)
                npass += 1
    if ntried:
        print(
            '------------------------------\nPassed {}/{} = {:.2f}%.'.format(
                npass, ntried, 100 * npass/ntried))

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('tests', nargs='+', help='tests to run, module[:test1,test2,test3,...]')
    p.add_argument(
        '-a', '--all', action='store_true',
        help='run all regardless of error')
    p.add_argument(
        '--prefix', default='test_', help='Prefix on name for tests to run.')
    p.add_argument('-l', '--list', help='list discovered tests', action='store_true')
    args = p.parse_args()
    for t in args.tests:
        run(t, args.all, args.prefix, args.list)
