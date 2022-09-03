"""Classes for searching and running test modules.

Tests can be stored in:
    a standalone module (file run directly)
    a module within a package (use the module name to run the tests)
"""
from __future__ import print_function
__all__ = ['Tests', 'Base']
import argparse
import os
import sys
import traceback

class Base(object):
    """Base test: no args, does nothing."""
    def __init__(self, p):
        pass
    def __call__(self, args):
        pass

class Tests(object):
    """Class for managing test.

    Note: tests should be written as client of the modules rather than
    a part of the source code (tested modules should be absolute
    imported, not relative, etc)

    The old mechanism incrementally gave dirs to traverse/search, but
    not necessary.  In this mechanism, just python <test file to run>
    which also allows for tab completion.

    Each test is a class.
    A Tests.PWrap argument parser is passed as the single argument to
    the constructor for the test.  The test should add test arguments
    to the parser in __init__().  It should also implement __call__(args)
    where args is the parsed argument argparse.Namespace object.
    A default all() test is added which runs all registered tests with
    no arguments.  If the test requires arguments or you do not want it
    to be run with the all() test, then add an attribute to the test:
    skip = True.

    example:
        mytests = Tests()
        @mytests
        class test1(object):
            def __init__(self, parser):
                parser('arg1', type=int, help='helpstr', ...)
                parser('--arg2', ...)
            def __call__(self, args):
                print(args)

        mytests.run()
    """
    class PWrap(object):
        """Wrap a parser object with __call__ to add_argument"""
        def __init__(self, sub):
            self.sub = sub
        def __getattr__(self, name):
            atr = getattr(self.sub, name)
            if callable(atr):
                setattr(self, name, atr)
            return atr
        def __call__(self, *args, **kwargs):
            return self.add_argument(*args, **kwargs)

    def __init__(
        self, formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        *args, **kwargs):
        """Initialize TestSuite.

        Have formatter_class default to ArgumentDefaultsHelpFormatter.
        """
        self.parser = argparse.ArgumentParser(
            *args, formatter_class=formatter_class, **kwargs)
        self.sub = self.parser.add_subparsers(
            title='test', help='the test to run')
        self.parser.set_defaults(_action=self.default)
        p = self.PWrap(self.sub.add_parser('all'))
        p(
            '--all', '-a',
            help='run all instead of stopping on first fail',
            action='store_true')
        p.set_defaults(_action=self.all)
        self._alltests = []
        self.ran = False

    def __call__(self, itemorname=None, name=None):
        """Register a test.

        If itemorname is not callable, return a partial with
        name=name or itemorname
        """
        if not callable(itemorname):
            return partial(self, name=name or itemorname)
        name = name or itemorname.__name__
        p = self.sub.add_parser(
            name, formatter_class=self.parser.formatter_class)
        action = itemorname(self.PWrap(p))
        p.set_defaults(_action=action)
        if not getattr(action, 'skip', False):
            self._alltests.append(name)

    def default(self, args):
        """Default: run all without args."""
        self.all(self.parser.parse_args(['all']))

    def all(self, args):
        """Run all tests."""
        success = 0
        for testname in self._alltests:
            p = self.sub.choices[testname]
            print('\n>>> running test {} <<<\n\n'.format(testname))
            try:
                p.get_default('_action')(p.parse_known_args([])[0])
                success += 1
            except Exception:
                if args.all:
                    traceback.print_exc()
                else:
                    raise
        print(
            '\nsummary: passed:{} total:{}'.format(
                success, len(self._alltests)))

    def run(self, args=None):
        """Run the selected test."""
        self.ran = True
        defaultcmd = argparse.ArgumentParser(add_help=False)
        defaultcmd.add_argument('command', default='all', nargs='?')
        res, extra = defaultcmd.parse_known_args(args)
        args, extra = self.parser.parse_known_args([res.command] + extra)
        args._action(args)
