"""Common code for quick profiling tests of implementation methods."""
from __future__ import print_function
__all__ = ['simpletest', 'simpleparser', 'Stopwatch']
import argparse
import timeit
import sys
import operator
import traceback
import time
if sys.version_info.major > 2:
    tstamp = time.perf_counter
else:
    tstamp = time.time

from ..utils.strutils import longest_fmt

simpleparser = argparse.ArgumentParser(
    add_help=False, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
simpleparser.add_argument(
    '-n', '--number', type=int, help='number of reps per test', default=100)
simpleparser.add_argument(
    '-r', '--repeat', type=int, help='number of times to repeat the test',
    default=10)
simpleparser.add_argument(
    '-a', '--all', action='store_true', help='run all tests regardless of errors')

_CACHE = []
def simpletest(
    tests, cfg, args=(), kwargs={},
    checkmatch=operator.eq):
    """Assume the tests exist in __main__.

    tests: dict of tests, name:func (or corresponding tuple)
    cfg: an item with repeat and number attributes

    Call the function with args and kwargs.
    Compare outputs if checkmatch is callable, (
        default: use == (operator.eq))
    NOT thread safe (func, args, kwargs are stored in module-level
    global for easy acccess in the test script.)
    """
    if not isinstance(tests, dict):
        tests = dict(tests)
    nfmt = longest_fmt(tests)
    command = 'func('
    if args:
        command += '*args'
        if kwargs:
            command += ', **kwargs)'
        else:
            command += ')'
    elif kwargs:
        command += '**kwargs)'
    else:
        command += ')'
    setup = (
        'from {} import _CACHE;'
        ' func, args, kwargs = _CACHE').format(__name__)
    _CACHE[:] = None, args, kwargs
    results = []
    sep = '------------------------------'
    print(sep, 'running timing tests', sep, sep='\n', file=sys.stderr)
    for name, func in sorted(tests.items()):
        print(nfmt(name), end=' : ', file=sys.stderr)
        sys.stderr.flush()
        _CACHE[0] = func
        try:
            best = min(timeit.repeat(
                command.format(name),
                setup.format(name),
                repeat=cfg.repeat, number=cfg.number))
        except Exception:
            print('error!')
            traceback.print_exc()
        else:
            print('{:.8f}'.format(best), file=sys.stderr)
            results.append((name, func(*args, **kwargs)))
    if callable(checkmatch):
        it = iter(results)
        first, val = next(it)
        print(sep, file=sys.stderr)
        print('checking output against', first, file=sys.stderr)
        print(sep, file=sys.stderr)
        for oname, result in it:
            if checkmatch(val, result):
                print(nfmt(oname), 'ok', file=sys.stderr)
            else:
                print(sep, file=sys.stderr)
                print(nfmt(oname), 'error', file=sys.stderr)
                print('first :', file=sys.stderr)
                print(val, file=sys.stderr)
                print('\tvs', oname, ':', file=sys.stderr)
                print(result, file=sys.stderr)

class Stopwatch(object):
    def __init__(self):
        self.times = [tstamp()]
    def __call__(self):
        self.times.append(tstamp())
    def p(self, *names, total=True, file=sys.stderr):
        times = self.times
        dototal = total and not (len(self.times) == 2 and names)
        if dototal:
            fmt = longest_fmt(names+('total',))
        elif names:
            fmt = longest_fmt(names)
        else:
            return
        print('------------------------------', file=file)
        for i, nm in enumerate(names):
            print(fmt(nm), times[i+1] - times[i], file=file)
        if dototal:
            print(fmt('total'), times[-1] - times[0], file=file)
