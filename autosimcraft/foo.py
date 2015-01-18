#!/usr/bin/env python

import sys
import argparse
import os

from config import DEFAULT_CONFDIR
from autosimcraft import AutoSimcraft
import getpass
import platform

script = AutoSimcraft(dry_run=False, verbose=2, confdir='/home/jantman/.autosimcraft')

from_addr = getpass.getuser() + '@' + platform.node()
dest_addr = 'jason@jasonantman.com'
subj = 'AutoSimcraft mail test'
c_name = 'cname@rname'
c_diff = "MULTIPLE\nLINES\nOF\nDIFF\nHERE\n"
html_path = '/home/jantman/.autosimcraft/jantman@area52.html'
duration = '1:02:03'
output = "MULTIPLE\nLINES\nOF\nOUTPUT\nHERE\n\n"

msg = script.format_message(from_addr, dest_addr, subj, c_name, c_diff, html_path, duration, output)
script.send_gmail(from_addr, dest_addr, msg.as_string())
