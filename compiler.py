#!/usr/bin/python3

'''
	Created on 2013-1-24

	@author: desperedo

	miniPascal Compiler written in Python
'''

import sys
import Parser
import Scanner
import Analyzer
import Generator
import TreeDumper

class Compiler(object):
	def __init__(self, Source):
		self.Scanner = Scanner.Scanner(Source);
		self.Program = Parser.Program(self.Scanner);
		self.Analyzer = Analyzer.Analyzer(self.Program);
		self.Generator = Generator.Generator(self.Program);

	def Compile(self, FileName):
		self.Program.Parse();
		self.Analyzer.Analyze();
		self.Generator.Generate();
		File = open(FileName, 'wb');
		File.write(self.Generator.CodeStack.Assemble());
		File.close();

def usage():
	print('usage: mpc -[h|d] filename [-o output]');
	print('    -h        display this message');
	print('    -d        dump AST after compiling');
	print('    -o        specify the output file name');
	print();
	exit();

def main():
	if len(sys.argv) < 2:
		print('error: no input file.');
		exit();
	DumpAST = False;
	InputFileName = None;
	OutputFileName = None;
	for Arg in sys.argv[1:]:
		if Arg == '-h':					usage();
		elif Arg == '-d':				DumpAST = True;
		elif Arg == '-o':				OutputFileName = '';
		elif OutputFileName == '':		OutputFileName = Arg;
		elif InputFileName == None:		InputFileName = Arg;
	if InputFileName == None:
		print('error: no input file.');
		exit();
	elif OutputFileName == '':
		print('error: output file name not specified.');
		exit();
	elif OutputFileName == None:
		OutputFileName = InputFileName;
		Index = OutputFileName.rfind('.');
		if Index >= 0:
			OutputFileName = OutputFileName[:Index - len(OutputFileName)];
		OutputFileName += '.mpo';
	File = open(InputFileName);
	Instance = Compiler(File.read());
	Instance.Compile(OutputFileName);
	if DumpAST:
		TreeDumper.DumpProgram(Instance.Program);
	File.close();
	print("Done.");

if __name__ == '__main__':
	main();
