#!/usr/bin/python -Bu

# Copyright (c) 2023 Artur Wiebe <artur@4wiebe.de>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os
import re
from systemd import journal, daemon


master, slave = os.openpty()
os.symlink(os.ttyname(slave), '/run/codesys-log/tty')
daemon.notify('READY=1')

pattern = re.compile(r'.*: Cmp=(.*), Class=(.*), Error=(.*), Info=(.*), pszInfo=\s*(.*)\s*')

def prio(prio_class):
	match prio_class:
		case '1': return 6 #Info
		case '2': return 4 #Warning
		case '4': return 3 #Error
		case '8': return 2 #Critical
		case _:   return 7 #Debug

with os.fdopen(master) as input:
	while True:
		if line := pattern.search(input.readline()):
			journal.sendv(
				f'CMP={line.group(1)}',
				f'PRIORITY={prio(line.group(2))}',
				f'ERROR={line.group(3)}',
				f'INFO={line.group(4)}',
				f'MESSAGE={line.group(5)}',
				'SYSLOG_IDENTIFIER=codesys'
			)
