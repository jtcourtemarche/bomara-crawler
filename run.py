#!/usr/bin/python

import argparse

from apc.crawler import APCCrawler
from apc.gui import run
from apc.tools import clear_output

# Load args ------------------------->

parser = argparse.ArgumentParser()
parser.add_argument('tool', nargs='?')
parser.add_argument('tool_args', nargs='?')

args = parser.parse_args()

if args.tool == 'clear':
	if args.tool_args != None:
		clear_output(output_dir=args.tool_args)
	else:
		# Assume default dir ('output/')
		clear_output()
	exit()

# ----------------------------------->

# Optional: breadcrumbs
# breadcrumbs => list of tuples for every breadcrumb
# reader = APCCrawler('http://www.apc.com/shop/us/en/products/APC-Smart-UPS-SRT-1000VA-RM-120V/P-SRT1000RMXLA', [('APC Rocks', 'http')])

# Optional: write
# write => outputs parsing results to a json file (output.json)
# reader.parse()

# Optional: template, output_dir
# path => template file location
# output_dir => directory to generate files to
# reader.apply_template()

# Run GUI
if __name__ == '__main__':
	run()