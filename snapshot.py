#!/usr/bin/env python3

import os
import shutil
import stat
import subprocess
import sys
import tempfile
from collections import namedtuple, defaultdict
from pathlib import Path
from argparse import ArgumentParser, RawTextHelpFormatter, \
        ArgumentDefaultsHelpFormatter

DEFAULT_CASES = ['test']

TestResult = namedtuple('TestResult', ['name', 'color'])
Passed = TestResult('PASSED', 2)
Skipped = TestResult('SKIPPED', 15)
Failed = TestResult('FAILED', 9)
Updated = TestResult('UPDATED', 6)

class SuiteResult:
    def __init__(self):
        self.results = defaultdict(int)

    def add(self, result):
        self.results[result] += 1

    def summary(self):
        return ', '.join(f'{num} {s.name.lower()}' for s, num in self.results.items())

    def exit_code(self):
        return bool(self.results[Failed])

class ArgumentDefaultsRawTextHelpFormatter(
        ArgumentDefaultsHelpFormatter,
        RawTextHelpFormatter): pass

def is_executable(path):
    return bool(os.stat(path).st_mode & (stat.S_IXGRP | stat.S_IXOTH))

def parse_paths(paths):
    out = []
    for p in paths:
        if p.is_file() and is_executable(p):
            out.append(p)
        elif p.is_dir():
            out.extend(parse_paths(p.iterdir()))
    return out

def get_diff(path1, path2):
    pr = subprocess.run(['diff', path1, path2], capture_output=True, encoding='utf-8')
    return pr.stdout

def color(string, num):
    if sys.stdout.isatty():
        return f"\033[38;5;{num}m{string}\033[0;0m"
    else:
        return string

def print_status(path, status, maxwidth=None):
    name = str(path)
    if maxwidth is None:
        maxwidth = len(name)
    print(name + ' ' * (maxwidth - len(name) + 8) + color(status.name, status.color))

def run_test_case(path, update=False, maxwidth=None):
    snap_path = path.parent / (path.name + '.snapshot')
    status = Skipped
    diff = ''
    if snap_path.exists() or update:
        result = subprocess.run([path], capture_output=True, encoding='utf-8')
        if result.returncode == 0:
            with tempfile.TemporaryDirectory() as tmpdir:
                snap_path_tmp = Path(tmpdir) / snap_path.name
                with open(snap_path_tmp, 'w') as f:
                    f.write(result.stdout)
                if update:
                    shutil.move(snap_path_tmp, snap_path)
                    status = Updated
                else:
                    diff = get_diff(snap_path, snap_path_tmp)
                    status = Failed if diff else Passed
        else:
            status = Failed
    print_status(path, status, maxwidth)
    if status == Failed:
        if diff:
            print(diff, end='')
        if result and result.stderr:
            print(result.stderr)
    return status

def run_test_cases(paths, update=False):
    paths = parse_paths(paths)
    suite_result = SuiteResult()
    maxwidth = max(len(str(p)) for p in paths)
    for p in sorted(paths):
        suite_result.add(run_test_case(p, update=update, maxwidth=maxwidth))
    return suite_result

def main(args):
    description = f'''
Runs snapshot-based test suite. Diffs from stored snapshots count as failures.
Test cases are executable files. If any test case fails, this tool exits with a
non-zero exit code. By default, runs all test cases in {DEFAULT_CASES}.'''
    ap = ArgumentParser(description=description, add_help=False,
            formatter_class=ArgumentDefaultsRawTextHelpFormatter)
    ap.add_argument('-u', '--update', action='store_true', help='Update snapshots')
    ap.add_argument('-?', '-h', action='help', help='Print help')
    ap.add_argument('cases', nargs='*')
    args = ap.parse_args()
    if not args.cases:
        args.cases = DEFAULT_CASES
    if not args.update:
        args.update = bool(os.environ.get('UPDATE'))
    suite_result = run_test_cases(map(Path, args.cases), update=args.update)
    print(suite_result.summary())
    sys.exit(suite_result.exit_code())

if __name__ == '__main__':
    main(sys.argv[1:])
