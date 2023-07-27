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


from __future__ import annotations
import re
from ctypes import *
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


class Field(tuple):
	def __new__(cls, name, ctype, comment):
		self = tuple.__new__(cls, (name, ctype))
		self.name = name
		self.ctype = ctype
		self.comment = comment
		return self


def parse_struct(name:str) -> Structure:
	file_text = Path('/usr/share/codesys', f'{name}.struct').read_text()
	
	def ctype(codesys_type):
		if array := re.search(r'ARRAY \[(\d+)\.\.(\d+)\] OF (\w+)', codesys_type):
			codesys_type = array.group(3)
			array_length = int(array.group(2)) - int(array.group(1)) + 1
		if codesys_type not in types:
			types[codesys_type] = parse_struct(codesys_type)
		return types[codesys_type] * array_length if array else types[codesys_type]
	
	return type(
		name,
		(Structure, ),
		{'_fields_': [Field(f[0], ctype(f[1]), f[2]) for f in re.findall(r'^\s*(\w+)\s*:\s*(.+)\s*;\s*(?://\s*(.*)\s*)?$', file_text, re.MULTILINE)]},
	)
