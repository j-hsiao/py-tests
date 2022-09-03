from __future__ import print_function
import argparse
import os
import runpy
import sys
import traceback

from jhsiao.tests import Tests

if __name__ == '__main__':
    p = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument(
        'torun', help='directory, filepath, or modulename to run',
        default='.', nargs='?')
    p.add_argument(
        '--all', '-a',
        help='run all instead of stopping on first fail',
        action='store_true')
    p.add_argument(
        '--prefix',
        '-p', help='prefix for test files', default='test_')
    p.add_argument(
        'remaining',
        help='args to pass onto module if applicable', nargs='...')
    args = p.parse_args()

    # In case Tests.run() is called in the file itself, modify
    # sys.argv so it gets the correct arguments.
    orig = sys.argv[1:]
    sys.argv[1:] = args.remaining
    def run(moddict, args):
        """Run the first Tests instance if not ran."""
        for k, v in moddict.items():
            if isinstance(v, Tests):
                if not v.ran:
                    v.run(args.remaining)
                    return

    def search_files(dirname, args):
        """Find test files."""
        ret = []
        for base in os.listdir(dirname):
            f = os.path.join(dirname, base)
            if (
                    os.path.isfile(f)
                    and base.startswith(args.prefix)
                    and base.endswith('.py')):
                ret.append(f)
            elif os.path.isdir(f):
                ret.extend(search_files(f, args))
        return ret

    isdir = os.path.isdir(args.torun)
    isfile = os.path.isfile(args.torun)
    if isdir or isfile:
        if isdir:
            fnames = search_files(args.torun, args)
        else:
            fnames = [args.torun]
        for fname in fnames:
            msg = ' '.join(('running test set:', fname))
            delim = '#'*min(len(msg), 40)
            print(delim, msg, delim, sep='\n')
            try:
                run(runpy.run_path(fname), args)
            except Exception:
                if args.all:
                    traceback.print_exc()
                else:
                    raise
    else:
        run(runpy.run_module(args.torun), args)

