"""Simple benchmark code."""
from __future__ import print_function
import argparse
import collections
import timeit
import traceback
from operator import eq


def parser(**kwargs):
    """Return an argparse.ArgumentParser with some bench args."""
    kwargs.setdefault('add_help', True)
    if kwargs['add_help']:
        kwargs.setdefault('formatter_class', argparse.ArgumentDefaultsHelpFormatter)
    kwargs.setdefault('conflict_handler', 'resolve')
    p = argparse.ArgumentParser(**kwargs)
    p.add_argument('-n', '--number', help='number of iters per measure', type=int, default=100)
    p.add_argument('-r', '--repeat', help='number of measurements to make', type=int, default=10)
    p.add_argument('--gui', action='store_true', help='use matplotlib to display results')
    p.add_argument('--tfmt', help='time format str', default='{:7.5f}')
    p.add_argument(
        '--nosort', action='store_true',
        help='display in order instead of sorting by min times.')
    return p

def check_values(scripts, setup, eq, vname):
    """Calculate sets where the values are the same.

    Generally they should all be equal to test different
    implementations doing the same thing so there should
    only be 1 set.

    scripts: dict of name: code/func
    setup: setup code (str) or no-args func.
        If func, then setup is not run.
    """
    gdict = {}
    if callable(setup):
        gdictr['__bench_setupfunc'] = setup
        setup = '__bench_setupfunc()'
    exec(setup, gdict)
    results = []
    for name, script in scripts.items():
        l = gdict.copy()
        if callable(script):
            l['__bench_scriptfunc'] = script
            script = '{} = __bench_scriptfunc()'.format(vname)
        exec(script, l)
        results.append(l[vname])
    merges = list(range(len(results)))
    for i in range(len(results)):
        for j in range(i+1, len(results)):
            if eq(results[i],results[j]):
                merges[i] = j
                break
    sets = collections.defaultdict(list)
    names = list(scripts)
    for i in range(len(merges)):
        dst = i
        while merges[dst] != dst:
            dst = merges[dst]
        sets[dst].append(names[i])
    return sets, results

def run(scripts={}, setup='', args=None, eq=None, vname='result', title=None, **kwargs):
    """Run scripts and time.

    scripts: dict of name: str
        The str is the script to run.
    args: argparse.Namespace or list of args for parser().parse_args()
        If None, then parse from sys.argv.
        relevant attrs:
            number: number of runs per measurement.
            repeat: number of measurements.
            gui: display hist, otherwise print min, mean, max
            tfmt: runtime format str
            nosort: don't sort resulting output
    eq: callable to ensure all scripts are equivalent.
        (only applicable if each script is a function)
    kwargs:
        specify scripts via kwargs instead.
    """
    if title:
        print('-'*len(title))
        print(title)
    kwargs.update(scripts)
    if eq is not None:
        sets, outputs = check_values(kwargs, setup, eq, vname)
        if len(sets) == 1:
            print('All results match!')
        else:
            print('Error! outputs do not match!')
            print('equivalence sets:')
            for idx, s in sets.items():
                print(s, type(outputs[idx]), str(outputs[idx])[:100])
            raise ValueError('Values do not match')
    if args is None:
        args = parser().parse_args()
    elif not isinstance(args, argparse.Namespace):
        args = parser().parse_args(args)
    results = {}
    errored = {}
    fmt = '{{:>{}}}:'.format(max(map(len, kwargs))).format
    tfmt = args.tfmt.format

    headfmt = '{{:^{}}}'.format(len(tfmt(0.0))).format
    print(
        fmt(''),
        headfmt('min'),
        headfmt('mean'),
        headfmt('med'),
        headfmt('max'))
    printout = []
    for name, script in kwargs.items():
        try:
            result = timeit.repeat(script, setup, number=args.number, repeat=args.repeat)
        except Exception:
            errored[name] = traceback.format_exc()
        else:
            if args.gui:
                results[name] = result
            result.sort()
            mid = len(result) // 2
            med = result[mid]
            if len(result) % 2 == 0:
                med += result[mid-1]
                med *= 0.5
            if args.nosort:
                print(
                    fmt(name),
                    tfmt(result[0]),
                    tfmt(sum(result)/len(result)),
                    tfmt(med),
                    tfmt(result[-1]))
            else:
                printout.append((
                    result[0],
                    fmt(name),
                    tfmt(result[0]),
                    tfmt(sum(result)/len(result)),
                    tfmt(med),
                    tfmt(result[-1])))
                print(*printout[-1][1:], end='\r')
    if not args.nosort:
        printout.sort(key=lambda x: x[0])
        for item in printout:
            print(*item[1:])
    if errored:
        print('Errored:')
        for name, result in errored.items():
            print(fmt(name), end='\n\t')
            print(result.replace('\n', '\n\t'))
    if args.gui:
        import matplotlib.pyplot as plt
        for name, result in results.items():
            plt.hist(result, label=name, alpha=.5)
        plt.legend()
        plt.show()
