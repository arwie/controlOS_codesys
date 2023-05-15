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


import posix_ipc, mmap, os, re
from ctypes import *
import asyncio
from pathlib import Path


types = {
	'BOOL':		c_bool,
	'BYTE':		c_byte,
	'SINT':		c_int8,
	'INT':		c_int16,
	'DINT':		c_int32,
	'LINT':		c_int64,
	'USINT':	c_uint8,
	'UINT':		c_uint16,
	'UDINT':	c_uint32,
	'ULINT':	c_uint64,
	'REAL':		c_float,
	'LREAL':	c_double,
}

def parse_struct(file):
	file_text = Path('/usr/share/codesys', file).read_text()
	
	def ctype(codesys_type):
		if array := re.search(r'ARRAY \[(\d+)\.\.(\d+)\] OF (\w+)', codesys_type):
			return types[array.group(3)] * (int(array.group(2)) - int(array.group(1)) + 1)
		else:
			return types[codesys_type]
	
	class Struct(Structure):
		_fields_ = [(f[0], ctype(f[1])) for f in re.findall(r'^\s*(\w+)\s*:\s*(.+)\s*;', file_text, re.MULTILINE)]
		print('codesys:', file, _fields_)
	
	return Struct


GetStruct = parse_struct('set.struct')
SetStruct = parse_struct('get.struct')

get = GetStruct()
set = SetStruct()
ack = SetStruct()


_get_addr, _get_size = addressof(get), sizeof(get)
_set_addr, _set_size = addressof(set), sizeof(set)
_ack_addr, _ack_size = addressof(ack), sizeof(ack)

def _mmap_shm(name):
	shm = posix_ipc.SharedMemory(name)
	mapfile = mmap.mmap(shm.fd, shm.size)
	addr = addressof((c_char*shm.size).from_buffer(mapfile))
	os.close(shm.fd)
	return mapfile, addr

_shm_get_map, _shm_get_addr = _mmap_shm('/codesys_shm_set')
_shm_set_map, _shm_set_addr = _mmap_shm('/codesys_shm_get')
_shm_ack_map, _shm_ack_addr = _mmap_shm('/codesys_shm_ack')
_sem = posix_ipc.Semaphore('/codesys_sem')


def exchange():
	with _sem:
		memmove(_get_addr, _shm_get_addr, _get_size)
		memmove(_shm_set_addr, _set_addr, _set_size)
		memmove(_ack_addr, _shm_ack_addr, _ack_size)


async def exchange_task(cycle_time):
	while (True):
		await asyncio.sleep(cycle_time)
		exchange()


def start():
	asyncio.create_task(exchange_task(0.01))
