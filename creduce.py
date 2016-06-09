#!/usr/bin/env python3

import argparse
import logging
import multiprocessing
import os
import time

from creduce.creduce import CReduce

from creduce.tests.test0 import *
from creduce.tests.test1 import *
from creduce.tests.test2 import *
from creduce.tests.test3 import *
from creduce.tests.test6 import *
from creduce.tests.test7 import *

try:
    core_count = multiprocessing.cpu_count()
except NotImplementedError:
    core_count = 1

parser = argparse.ArgumentParser(description="C-Reduce")
parser.add_argument("--n", "-n", type=int, default=core_count, help="Number of cores to use; C-Reduce tries to automatically pick a good setting but its choice may be too low or high for your situation")
parser.add_argument("--tidy", action="store_true", default=False, help="Do not make a backup copy of each file to reduce as file.orig")
parser.add_argument("--shaddap", action="store_true", default=False, help="Suppress output about non-fatal internal errors")
parser.add_argument("--die-on-pass-bug", action="store_true", default=False, help="Terminate C-Reduce if a pass encounters an otherwise non-fatal problem")
parser.add_argument("--sanitize", action="store_true", default=False, help="Attempt to obscure details from the original source file")
parser.add_argument("--sllooww", action="store_true", default=False, help="Try harder to reduce, but perhaps take a long time to do so")
parser.add_argument("--also-interesting", metavar="EXIT_CODE", type=int, nargs=1, help="A process exit code (somewhere in the range 64-113 would be usual) that, when returned by the interestingness test, will cause C-Reduce to save a copy of the variant")
parser.add_argument("--debug", action="store_true", default=False, help="Print debug information")
parser.add_argument("--log", type=str, choices=["INFO", "DEBUG", "WARNING", "ERROR"], default="INFO", help="Define what kind of events should be displayed")
parser.add_argument("--no-kill", action="store_true", default=False, help="Wait for parallel instances to terminate on their own instead of killing them (only useful for debugging)")
parser.add_argument("--no-give-up", action="store_true", default=False, help="Don't give up on a pass that hasn't made progress for {} iterations".format(CReduce.GIVEUP_CONSTANT))
parser.add_argument("--print-diff", action="store_true", default=False, help="Show changes made by transformations, for debugging")
parser.add_argument("--save-temps", action="store_true", default=False, help="Don't delete /tmp/creduce-xxxxxx directories on termination")
parser.add_argument("--skip-initial-passes", action="store_true", default=False, help="Skip initial passes (useful if input is already partially reduced)")
parser.add_argument("--timing", action="store_true", default=False, help="Print timestamps about reduction progress")
parser.add_argument("--no-default-passes", action="store_true", default=False, help="Start with an empty pass schedule")
parser.add_argument("--add-pass", metavar=("PASS", "SUBPASS", "PRIORITY"), nargs=3, help="Add the specified pass to the schedule")
parser.add_argument("--skip-key-off", action="store_true", default=False, help="Disable skipping the rest of the current pass when \"s\" is pressed")
parser.add_argument("--max-improvement", metavar="BYTES", type=int, nargs=1, help="Largest improvement in file size from a single transformation that C-Reduce should accept (useful only to slow C-Reduce down)")
parser.add_argument("--pass-group", type=str, choices=list(map(str, CReduce.PassGroup)), default="all", help="Set of passes used during the reduction")
parser.add_argument("interestingness_test", metavar="INTERESTINGNESS_TEST", help="Executable to check interestingness of test cases")
parser.add_argument("test_cases", metavar="TEST_CASE", nargs="+", help="Test cases")

args = parser.parse_args()

if args.timing:
    log_format = "%(asctime)s@%(levelname)s@%(name)s@%(message)s"
else:
    log_format = "@%(levelname)s@%(name)s@%(message)s"

log_level = getattr(logging, args.log.upper(), None)

if args.debug:
    log_level = logging.DEBUG

logging.basicConfig(level=log_level, format=log_format)

pass_options = set()

if args.sanitize:
    pass_options.add(CReduce.PassOption.sanitize)

if args.sllooww:
    pass_options.add(CReduce.PassOption.slow)

tests = {"test0": Test0InterestingnessTest,
         "test1": Test1InterestingnessTest,
         "test2": Test2InterestingnessTest,
         "test3": Test3InterestingnessTest,
         "test6": Test6InterestingnessTest,
         "test7": Test7InterestingnessTest}

interestingness_test = tests[args.interestingness_test](map(os.path.basename, args.test_cases))

reducer = CReduce(interestingness_test, args.test_cases)

reducer.silent_pass_bug = args.shaddap
reducer.die_on_pass_bug = args.die_on_pass_bug
reducer.also_interesting = args.also_interesting

# Track runtime
if args.timing:
    time_start = time.monotonic()

reducer.reduce(args.n,
               skip_initial=args.skip_initial_passes,
               pass_group=CReduce.PassGroup(args.pass_group),
               pass_options=pass_options)

if args.timing:
    time_stop = time.monotonic()
    logging.info("Runtime: {} seconds".format(round((time_stop - time_start))))

logging.shutdown()