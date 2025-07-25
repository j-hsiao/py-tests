"""Simple benchmark code."""
from __future__ import print_function
import argparse
import math
import collections
import timeit
import textwrap
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
        '--ttest', type=float, nargs='*', default=None,
        help='perform pair-wise ttests to this significance. significance is optional(default0.05).')
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
    eq: callable
        Use this to check whether the results are equivalent.
    vname: str
        The variable name to check.  If not defined, then ignore the
        corresponding script.

    Returns
    sets: dict of {index: [names]}
        Index is an index into results.  All names in the list gave an
        equivalent result to results[index]
    results: list
        List of results from each script.
    unchecked: list[str]
        List of script names that did not define `vname` so could not
        be checked.
    """
    gdict = {}
    if callable(setup):
        gdict['__bench_setupfunc'] = setup
        setup = '__bench_setupfunc()'
    exec(setup, gdict)
    results = []
    valid = []
    invalid = []
    names = []
    for i, (name, script) in enumerate(scripts.items()):
        names.append(name)
        l = gdict.copy()
        if callable(script):
            l['__bench_scriptfunc'] = script
            script = '{} = __bench_scriptfunc()'.format(vname)
        exec(script, l)
        try:
            results.append(l[vname])
            valid.append(i)
        except KeyError:
            print(
                ('WARNING: Test "{}" does not define variable for'
                 ' checking: "{}".').format(name, vname))
            results.append(None)
            invalid.append(name)
    sets = {}
    for idx in range(len(valid)):
        key = valid[idx]
        if key is None:
            continue
        sets[key] = [names[key]]
        for jdx in range(idx+1, len(valid)):
            j = valid[jdx]
            if j is None:
                continue
            if eq(results[key], results[j]):
                valid[jdx] = None
                sets[key].append(names[j])
    return sets, results, invalid


def pairwise_ttest(results, significance=0.05):
    """Perform pairwise ttest, print matrix.

    results: dict of {testname: [timings]}
    significance: the significance threshold for testing.  Greater
                  than significance, assume the timings are equal
                  (blank).
    """
    try:
        import scipy
    except ImportError:
        import sys
        import subprocess as sp
        sp.Popen([sys.executable, '-m', 'pip', 'install', 'scipy']).wait()
        import scipy

    names = []
    data = []
    means = []
    for k, v in results.items():
        names.append(k)
        data.append(v)
        means.append(sum(v) / len(v))

    fmtstr = f'{{:{len(str(len(names)-1))}}}: {{}}'
    headindent = len(fmtstr.format(0, names[0]))
    print(' '*headindent, end='')
    for idx in range(len(names)):
        print('\t', idx, end='')
    print()

    pmatrix = []
    for i in range(len(data)):
        print(fmtstr.format(i, names[i]), end='')
        pmatrix.append([])
        for j in range(i):
            pmatrix[-1].append(pmatrix[j][i])
            print('\t', end='')
            if pmatrix[j][i] < significance:
                print('{:.2f}'.format(means[j] / means[i]), end='')
            else:
                print('...', end='')
        print('\t...', end='')
        pmatrix[-1].append(1)
        for j in range(i+1, len(data)):
            pmatrix[-1].append(scipy.stats.ttest_ind(data[i], data[j], equal_var=False).pvalue)
            print('\t', end='')
            if pmatrix[-1][-1] < significance:
                print('{:.2f}'.format(means[j] / means[i]), end='')
            else:
                print('...', end='')
        print()

def run(scripts={}, setup='', args=None, eq=None, vname='result', title=None, **kwargs):
    """Run scripts and time.

    scripts: dict of str: str
        The key is the name of the test.  The value is the script or a
        function to run.
    args: argparse.Namespace or list of args for parser().parse_args()
        If None, then parse from sys.argv.
        relevant attrs:
            number: number of runs per measurement.
            repeat: number of measurements.
            gui: display hist, otherwise print min, mean, max
            tfmt: running time format str
            nosort: don't sort resulting output
    eq: callable to check if `vname` is equivalent for each script.
    kwargs:
        specify scripts via kwargs instead.
    """
    if title:
        print('-'*len(title))
        print(title)
    kwargs.update(scripts)
    for k, v in kwargs.items():
        if isinstance(v, str):
            kwargs[k] = textwrap.dedent(v)
    if isinstance(setup, str):
        setup = textwrap.dedent(setup)
    if eq is not None:
        sets, outputs, invalid = check_values(kwargs, setup, eq, vname)
        if invalid:
            print('Unchecked:', invalid)
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
            if args.gui or args.ttest is not None:
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
        if len(results) > 3:
            plt.hist(list(results.values()), label=list(results))
        else:
            for name, result in results.items():
                plt.hist(result, label=name, alpha=.5)
        plt.legend()
        plt.show()

    if args.ttest is not None:
        if not args.ttest:
            args.ttest = [0.05]
        pairwise_ttest(results, args.ttest[0])
