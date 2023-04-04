"""Simple test

Anything that starts with the given prefix is a valid test and should be
callable without any arguments.  It should throw an exception on failure.
"""
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

def run(name, runall=False, prefix='test_'):
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
        name, target = name.split(':', 1)
    else:
        target = None
    item = _import(name)
    for k in dir(item):
        if not k.startswith(prefix):
            continue
        tname = k.split('_', 1)[-1]
        if target is None or tname == target:
            print('running', tname)
            try:
                getattr(item, k)()
            except Exception:
                if runall:
                    traceback.print_exc()
                else:
                    raise

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('tests', nargs='+', help='tests to run')
    p.add_argument(
        '-a', '--all', action='store_true',
        help='run all regardless of error')
    p.add_argument(
        '--prefix', default='test_', help='Prefix on name for tests to run.')
    args = p.parse_args()
    for t in args.tests:
        run(t, args.all, args.prefix)
