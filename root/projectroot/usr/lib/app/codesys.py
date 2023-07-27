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


import asyncio
import mmap
import os
from ctypes import *
import posix_ipc
from shared.codesys import parse_struct


cmd = parse_struct('Cmd')()
fbk = parse_struct('Fbk')()


def sync():
	global _sync_event
	return _sync_event.wait()


async def _sync_loop(cycle_time):
	global _sync_event
	_sync_event = asyncio.Event()

	cmd_addr, cmd_size = addressof(cmd), sizeof(cmd)
	fbk_addr, fbk_size = addressof(fbk), sizeof(fbk)

	sem = posix_ipc.Semaphore('/codesys')
	shm = posix_ipc.SharedMemory('/codesys')
	mapfile = mmap.mmap(shm.fd, shm.size)
	shm_cmd_addr = addressof((c_char*shm.size).from_buffer(mapfile))
	shm_fbk_addr = shm_cmd_addr + cmd_size
	os.close(shm.fd)

	while (True):
		await asyncio.sleep(cycle_time)

		with sem:
			memmove(shm_cmd_addr, cmd_addr, cmd_size)
			memmove(fbk_addr, shm_fbk_addr, fbk_size)

		_sync_event.set()
		_sync_event = asyncio.Event()


def start():
	_sync_loop.task = asyncio.create_task(_sync_loop(0.008))