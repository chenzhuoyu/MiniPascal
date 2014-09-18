'''
	Created on 2013-2-6

	@author: desperedo

	miniPascal Compiler Bytecode Assembler
'''

import struct

class AssemblyError(Exception): pass

class Bytecode(object):
	def __init__(self, Code, Descriptor):
		self.Code = Code;
		self.Operand = None;
		self.ExtraData = None;
		self.Descriptor = Descriptor;

class CodeStack(object):
	def __init__(self):
		self.IP = 0;
		self.CodeMap = {};
		self.Bytecodes = [];

		self.AddBytecode('nop'		, 0xFF, 1, []);
		self.AddBytecode('drop'		, 0x00, 1, []);
		self.AddBytecode('dup'		, 0x01, 1, []);
		self.AddBytecode('push'		, 0x02, 5, ['Integer']);
		self.AddBytecode('pusha'	, 0x03, 9, ['Integer', 'Integer']);
		self.AddBytecode('pop'		, 0x04, 5, ['Integer']);
		self.AddBytecode('popa'		, 0x05, 9, ['Integer', 'Integer']);
		self.AddBytecode('ldtrue'	, 0x06, 1, []);
		self.AddBytecode('ldfalse'	, 0x07, 1, []);
		self.AddBytecode('ldc'		, 0x08, 2, ['Char']);
		self.AddBytecode('ldf'		, 0x09, 9, ['Float']);
		self.AddBytecode('ldi'		, 0x0A, 5, ['Integer']);
		self.AddBytecode('lds'		, 0x0B, 0, ['String']);
		self.AddBytecode('chr'		, 0x0C, 1, []);
		self.AddBytecode('real'		, 0x0D, 1, []);
		self.AddBytecode('str'		, 0x0E, 1, []);
		self.AddBytecode('int'		, 0x0F, 1, []);
		self.AddBytecode('bool'		, 0x10, 1, []);
		self.AddBytecode('lens'		, 0x11, 1, []);
		self.AddBytecode('cats'		, 0x12, 1, []);
		self.AddBytecode('cpys'		, 0x13, 1, []);
		self.AddBytecode('ints'		, 0x14, 1, []);
		self.AddBytecode('dels'		, 0x15, 1, []);
		self.AddBytecode('inv'		, 0x16, 1, []);
		self.AddBytecode('add'		, 0x17, 1, []);
		self.AddBytecode('sub'		, 0x18, 1, []);
		self.AddBytecode('mul'		, 0x19, 1, []);
		self.AddBytecode('div'		, 0x1A, 1, []);
		self.AddBytecode('idiv'		, 0x1B, 1, []);
		self.AddBytecode('mod'		, 0x1C, 1, []);
		self.AddBytecode('sin'		, 0x1D, 1, []);
		self.AddBytecode('cos'		, 0x1E, 1, []);
		self.AddBytecode('tan'		, 0x1F, 1, []);
		self.AddBytecode('sqrt'		, 0x20, 1, []);
		self.AddBytecode('and'		, 0x21, 1, []);
		self.AddBytecode('or'		, 0x22, 1, []);
		self.AddBytecode('not'		, 0x23, 1, []);
		self.AddBytecode('xor'		, 0x24, 1, []);
		self.AddBytecode('shl'		, 0x25, 1, []);
		self.AddBytecode('shr'		, 0x26, 1, []);
		self.AddBytecode('equ'		, 0x27, 1, []);
		self.AddBytecode('neq'		, 0x28, 1, []);
		self.AddBytecode('gt'		, 0x29, 1, []);
		self.AddBytecode('lt'		, 0x2A, 1, []);
		self.AddBytecode('geq'		, 0x2B, 1, []);
		self.AddBytecode('leq'		, 0x2C, 1, []);
		self.AddBytecode('br'		, 0x2D, 5, ['Integer']);
		self.AddBytecode('brt'		, 0x2E, 5, ['Integer']);
		self.AddBytecode('brf'		, 0x2F, 5, ['Integer']);
		self.AddBytecode('call'		, 0x30, 5, ['Integer']);
		self.AddBytecode('ret'		, 0x31, 1, []);
		self.AddBytecode('dchar'	, 0x32, 5, ['Integer']);
		self.AddBytecode('dint'		, 0x33, 5, ['Integer']);
		self.AddBytecode('dfloat'	, 0x34, 5, ['Integer']);
		self.AddBytecode('dstr'		, 0x35, 5, ['Integer']);
		self.AddBytecode('dbool'	, 0x36, 5, ['Integer']);
		self.AddBytecode('mkarr'	, 0x37, 9, ['Integer', 'Integer']);
		self.AddBytecode('undef'	, 0x38, 5, ['Integer']);
		self.AddBytecode('read'		, 0x39, 5, ['Integer']);
		self.AddBytecode('readln'	, 0x3A, 5, ['Integer']);
		self.AddBytecode('write'	, 0x3B, 5, ['Integer']);
		self.AddBytecode('writeln'	, 0x3C, 5, ['Integer']);

	def AddBytecode(self, Mnemonic, Opcode, Size, Operands):
		self.CodeMap[Mnemonic.lower()] = {};
		self.CodeMap[Mnemonic.lower()]['Size'] = Size;
		self.CodeMap[Mnemonic.lower()]['Opcode'] = Opcode;
		self.CodeMap[Mnemonic.lower()]['Operands'] = Operands;
		self.CodeMap[Mnemonic.lower()]['Mnemonic'] = Mnemonic.lower();

	def PushBytecode(self, Mnemonic, *Operands):
		if Mnemonic.lower() not in self.CodeMap.keys():
			raise AssemblyError('Invalid Opcode.');
		Instr = self.CodeMap[Mnemonic.lower()];
		if len(Operands) != len(Instr['Operands']):
			raise AssemblyError('Operand count mismatch.');
		if Instr['Size'] > 0:
			self.IP += Instr['Size'];
		else:
			self.IP += len(Operands[0]) + 2;
		Code = Bytecode(Instr['Opcode'], Instr);
		if len(Instr['Operands']) > 0: Code.Operand = Operands[0];
		if len(Instr['Operands']) > 1: Code.ExtraData = Operands[1];
		self.Bytecodes.append(Code);
		return Code;

	def MakeOperand(self, Type, Operand):
		if Type == 'String':		return Operand.encode() + b'\0';
		elif Type == 'Char':		return struct.pack('b', Operand.encode()[0]);
		elif Type == 'Float':		return struct.pack('d', Operand);
		elif Type == 'Integer':		return struct.pack('i', Operand);

	def Assemble(self):
		Buffer = b'';
		for Instr in self.Bytecodes:
			Buffer += struct.pack('B', Instr.Code);
			if len(Instr.Descriptor['Operands']) > 0: Buffer += self.MakeOperand(Instr.Descriptor['Operands'][0], Instr.Operand);
			if len(Instr.Descriptor['Operands']) > 1: Buffer += self.MakeOperand(Instr.Descriptor['Operands'][1], Instr.ExtraData);
		return Buffer;
