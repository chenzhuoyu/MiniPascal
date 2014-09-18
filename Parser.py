'''
	Created on 2013-1-25

	@author: desperedo

	miniPascal Compiler Parser
'''

class Type(object):
	def __init__(self):
		self.Type = None;
		self.Array = False;
		self.ArrayLow = None;
		self.ArrayHigh = None;

	def Parse(self, Scanner):
		if Scanner.TokenExpected('Type'):
			self.Type = Scanner.NextToken()[1];
		elif Scanner.TokenExpected('Array'):
			self.Array = True;
			Scanner.NextToken();
			if not Scanner.TokenNeeded('['):
				raise SyntaxError('"[" expected');
			self.ArrayLow = Expression().Parse(Scanner);
			if not Scanner.TokenNeeded('..'):
				raise SyntaxError('".." expected');
			self.ArrayHigh = Expression().Parse(Scanner);
			if not Scanner.TokenNeeded(']'):
				raise SyntaxError('"]" expected');
			if not Scanner.TokenNeeded('Of'):
				raise SyntaxError('"Of" expected');
			self.Type = Type().Parse(Scanner);
		else:
			Token = Scanner.NextToken();
			raise SyntaxError('Type-name expected but "%s".' % (Token[1] or Token[0]));
		return self;

class Constant(object):
	def __init__(self):
		self.Name = '';
		self.Value = None;
		self.Type = Type();

	def Parse(self, Scanner):
		self.Name = Scanner.NextToken()[1];
		if Scanner.TokenExpected(':'):
			Scanner.NextToken();
			self.Type.Parse(Scanner);
		if not Scanner.TokenNeeded('='):
			raise SyntaxError('"=" expected.');
		if self.Type.Type == None:
			self.Type.Type, self.Value = Scanner.NextToken();
		else:
			if self.Type.Array:
				raise SyntaxError('Arrays cannot be as constant.');
			Type, self.Value = Scanner.NextToken();
			if Type.lower() != self.Type.Type.lower():
				raise SyntaxError('Constant type inconsistent.');
		if not Scanner.TokenNeeded(';'):
			raise SyntaxError('";" expected.');
		return self;

class Variable(object):
	def __init__(self):
		self.Names = [];
		self.Array = False;
		self.Type = Type();
		self.ArrayLow = Expression();
		self.ArrayHigh = Expression();

	def Parse(self, Scanner, Parameter = False):
		if Parameter:
			self.Variable = False;
			if Scanner.TokenExpected('Var'):
				self.Variable = True;
				Scanner.NextToken();
		while Scanner.TokenExpected('Identifier'):
			self.Names.append(Scanner.NextToken()[1]);
			if not Scanner.TokenExpected(','):
				if not Scanner.TokenNeeded(':'):
					raise SyntaxError('":" expected.');
				break;
			Scanner.NextToken();
		self.Type.Parse(Scanner);
		if not Parameter and not Scanner.TokenNeeded(';'):
			raise SyntaxError('";" expected.');
		if Parameter and self.Type.Array and self.Variable:
			raise SyntaxError('Arrays cannot be as variable parameters.');
		return self;

class Function(object):
	def __init__(self):
		self.Name = '';
		self.Forward = False;
		self.Parameters = [];
		self.ReturnType = Type();
		self.Statements = Statements();
		self.Declarations = Declarations();

	def Parse(self, Scanner):
		Scanner.NextToken();
		Type, self.Name = Scanner.NextToken();
		if Type != 'Identifier':
			raise SyntaxError('Identifier expected.');
		if Scanner.TokenExpected('('):
			Scanner.NextToken();
			if Scanner.TokensExpected(['Var', 'Identifier']):
				self.Parameters.append(Variable().Parse(Scanner, True));
				while Scanner.TokenExpected(';'):
					Scanner.NextToken();
					self.Parameters.append(Variable().Parse(Scanner, True));
			if not Scanner.TokenNeeded(')'):
				raise SyntaxError('")" expected.');
		if not Scanner.TokenNeeded(':'):
			raise SyntaxError('":" expected.');
		self.ReturnType.Parse(Scanner);
		if self.ReturnType.Array:
			raise SyntaxError('Arrays cannot be as return type.');
		if not Scanner.TokenNeeded(';'):
			raise SyntaxError('";" expected.');
		if Scanner.TokenExpected('Forward'):
			self.Forward = True;
			Scanner.NextToken();
		else:
			self.Declarations.Parse(Scanner);
			self.Statements.Parse(Scanner);
		if not Scanner.TokenNeeded(';'):
			raise SyntaxError('";" expected.');
		return self;

class Procedure(object):
	def __init__(self):
		self.Name = '';
		self.Forward = False;
		self.Parameters = [];
		self.Statements = Statements();
		self.Declarations = Declarations();

	def Parse(self, Scanner):
		Scanner.NextToken();
		Type, self.Name = Scanner.NextToken();
		if Type != 'Identifier':
			raise SyntaxError('Identifier expected.');
		if Scanner.TokenExpected('('):
			Scanner.NextToken();
			if Scanner.TokensExpected(['Var', 'Identifier']):
				self.Parameters.append(Variable().Parse(Scanner, True));
				while Scanner.TokenExpected(';'):
					Scanner.NextToken();
					self.Parameters.append(Variable().Parse(Scanner, True));
			if not Scanner.TokenNeeded(')'):
				raise SyntaxError('")" expected.');
		if not Scanner.TokenNeeded(';'):
			raise SyntaxError('";" expected.');
		if Scanner.TokenExpected('Forward'):
			self.Forward = True;
			Scanner.NextToken();
		else:
			self.Declarations.Parse(Scanner);
			self.Statements.Parse(Scanner);
		if not Scanner.TokenNeeded(';'):
			raise SyntaxError('";" expected.');
		return self;

class Factor(object):
	def __init__(self):
		self.Type = None;
		self.Value = None;
		self.Prefix = None;

	def Parse(self, Scanner):
		Type, Value = Scanner.PeekToken();
		if Type == '(':
			Scanner.NextToken();
			self.Type = 'Expression';
			self.Value = Expression().Parse(Scanner);
			if not Scanner.TokenNeeded(')'):
				raise SyntaxError('")" expected.');
		elif Type == '+':
			Scanner.NextToken();
			self.Prefix = '+';
			self.Type = 'Factor';
			self.Value = Factor().Parse(Scanner);
		elif Type == '-':
			Scanner.NextToken();
			self.Prefix = '-';
			self.Type = 'Factor';
			self.Value = Factor().Parse(Scanner);
		elif Type == 'Not':
			Scanner.NextToken();
			self.Prefix = 'Not';
			self.Type = 'Factor';
			self.Value = Factor().Parse(Scanner);
		elif Type in ['Char', 'Real', 'String', 'Integer', 'Boolean']:
			Scanner.NextToken();
			self.Type = Type;
			self.Value = Value;
		elif Type in ['Type', 'Identifier']:
			self.Type = Type;
			self.Value = Value;
			if Scanner.TokenExpected('(', 1):
				self.Type = 'Invoking';
				self.Value = Invoking().Parse(Scanner, True);
			elif Scanner.TokenExpected('[', 1):
				Scanner.NextToken();
				Scanner.NextToken();
				self.Type = 'Indexing';
				self.Indexer = [Expression().Parse(Scanner)];
				while Scanner.TokenExpected(','):
					Scanner.NextToken();
					self.Indexer.append(Expression().Parse(Scanner));
				if not Scanner.TokenNeeded(']'):
					raise SyntaxError('"]" expected.');
			else:
				Scanner.NextToken();
		else:
			raise SyntaxError('Unexpected token "%s".' % (Value or Type));
		return self;

class Term(object):
	def __init__(self):
		self.Factors = [];
		self.Factor = Factor();

	def Parse(self, Scanner):
		self.Factor.Parse(Scanner);
		while Scanner.PeekToken()[0] in ['*', '/', 'Div', 'Mod', 'And', 'Shl', 'Shr']:
			Operator = Scanner.NextToken()[0];
			self.Factors.append((Operator, Factor().Parse(Scanner)));
		return self;

class SimpleExpr(object):
	def __init__(self):
		self.Terms = [];
		self.Term = Term();

	def Parse(self, Scanner):
		self.Term.Parse(Scanner);
		while Scanner.PeekToken()[0] in ['+', '-', 'Or', 'Xor']:
			Operator = Scanner.NextToken()[0];
			self.Terms.append((Operator, Term().Parse(Scanner)));
		return self;

class Expression(object):
	def __init__(self):
		self.Operator = None;
		self.Operand1 = SimpleExpr();
		self.Operand2 = None;

	def Parse(self, Scanner):
		self.Operand1.Parse(Scanner);
		if Scanner.PeekToken()[0] in ['<', '>', '<=', '>=', '<>', '=']:
			self.Operator = Scanner.NextToken()[0];
			self.Operand2 = SimpleExpr().Parse(Scanner);
		return self;

class If(object):
	def __init__(self):
		self.Expression = Expression();
		self.TrueStatement = Statement();
		self.FalseStatement = None;

	def Parse(self, Scanner):
		Scanner.NextToken();
		self.Expression.Parse(Scanner);
		if not Scanner.TokenNeeded('Then'):
			raise SyntaxError('"then" expected.');
		self.TrueStatement.Parse(Scanner);
		if Scanner.TokenExpected('Else'):
			Scanner.NextToken();
			self.FalseStatement = Statement().Parse(Scanner);
		return self;

class For(object):
	def __init__(self):
		self.Type = None;
		self.Init = Assignment();
		self.Stop = Expression();
		self.Statement = Statement();

	def Parse(self, Scanner):
		Scanner.NextToken();
		if not Scanner.TokensExpected(['[', ':='], 1):
			raise SyntaxError('For-loop must have an initialization.');
		self.Init.Parse(Scanner);
		if Scanner.TokenExpected('To'):
			self.Type = 'Inc';
			Scanner.NextToken();
		elif Scanner.TokenExpected('DownTo'):
			self.Type = 'Dec';
			Scanner.NextToken();
		else:
			raise SyntaxError('"to" or "downto" expected.');
		self.Stop.Parse(Scanner);
		if not Scanner.TokenNeeded('Do'):
			raise SyntaxError('"do" expected.');
		self.Statement.Parse(Scanner);
		return self;

class While(object):
	def __init__(self):
		self.Statement = Statement();
		self.Expression = Expression();

	def Parse(self, Scanner):
		Scanner.NextToken();
		self.Expression.Parse(Scanner);
		if not Scanner.TokenNeeded('Do'):
			raise SyntaxError('"do" expected.');
		self.Statement.Parse(Scanner);
		return self;

class Repeat(object):
	def __init__(self):
		self.Statements = [];
		self.Expression = Expression();

	def Parse(self, Scanner):
		Scanner.NextToken();
		while not Scanner.TokenExpected('Until'):
			if Scanner.PeekToken()[0] == None:
				raise SyntaxError('"until" expected.');
			self.Statements.append(Statement().Parse(Scanner));
			if not Scanner.TokenExpected('Until') and not Scanner.TokenNeeded(';'):
				raise SyntaxError('";" expected.');
		Scanner.NextToken();
		self.Expression.Parse(Scanner);
		return self;

class Case(object):
	def __init__(self):
		self.Statements = {};
		self.ConstantType = None;
		self.DefaultStatement = None;
		self.Expression = Expression();

	def Parse(self, Scanner):
		Scanner.NextToken();
		self.Expression.Parse(Scanner);
		if not Scanner.TokenNeeded('Of'):
			raise SyntaxError('"of" expected.');
		while not Scanner.TokenExpected('End'):
			if Scanner.TokenExpected('Else'):
				if len(self.Statements) == 0:
					raise SyntaxError('Else-statement cannot be placed at top.');
				if self.DefaultStatement != None:
					raise SyntaxError('A case-statement should only have one else-statement.');
				Scanner.NextToken();
				self.DefaultStatement = Statement().Parse(Scanner);
				if not Scanner.TokenNeeded(';'):
					raise SyntaxError('";" expected.');
			else:
				if self.ConstantType == None:
					self.ConstantType = Scanner.PeekToken()[0];
					if self.ConstantType not in ['Char', 'Integer']:
						raise SyntaxError('Case-item should be ordinary type.');
				Type, Key = Scanner.NextToken();
				if Type != self.ConstantType:
					raise SyntaxError('Inconsistent case-item type');
				if not Scanner.TokenNeeded(':'):
					raise SyntaxError('":" expected.');
				if Key in self.Statements.keys():
					raise SyntaxError('Duplicate case-item.');
				self.Statements[Key] = Statement().Parse(Scanner);
				if not Scanner.TokenNeeded(';'):
					raise SyntaxError('";" expected.');
		Scanner.NextToken();
		return self;

class Invoking(object):
	def __init__(self):
		self.Name = '';
		self.Factor = False;
		self.Parameters = [];

	def Parse(self, Scanner, Factor = False):
		self.Factor = Factor;
		Type, self.Name = Scanner.NextToken();
		if Type not in ['Type', 'Identifier']:
			raise SyntaxError('Identifier expected.');
		if Scanner.TokenExpected('('):
			Scanner.NextToken();
			while not Scanner.TokenExpected(')'):
				self.Parameters.append(Expression().Parse(Scanner));
				if not Scanner.TokenExpected(','):
					break;
				Scanner.NextToken();
			if not Scanner.TokenNeeded(')'):
				raise SyntaxError('")" expected.');
		return self;

class Assignment(object):
	def __init__(self):
		self.Target = '';
		self.Indexer = None;
		self.Expression = Expression();

	def Parse(self, Scanner):
		Type, self.Target = Scanner.NextToken();
		if Type != 'Identifier':
			raise SyntaxError('Identifier expected.');
		if Scanner.NextToken()[0] == ':=':
			self.Expression.Parse(Scanner);
		else:
			self.Indexer = [Expression().Parse(Scanner)];
			while Scanner.TokenExpected(','):
				Scanner.NextToken();
				self.Indexer.append(Expression().Parse(Scanner));
			if not Scanner.TokenNeeded(']'):
				raise SyntaxError('"]" expected.');
			if not Scanner.TokenNeeded(':='):
				raise SyntaxError('":=" expected.');
			self.Expression.Parse(Scanner);
		return self;

class Statement(object):
	def __init__(self):
		self.Type = 'Empty';
		self.Statement = None;

	def Parse(self, Scanner):
		if Scanner.TokenExpected(';'):
			pass
		elif Scanner.TokenExpected('If'):
			self.Type = 'If';
			self.Statement = If().Parse(Scanner);
		elif Scanner.TokenExpected('For'):
			self.Type = 'For';
			self.Statement = For().Parse(Scanner);
		elif Scanner.TokenExpected('Case'):
			self.Type = 'Case';
			self.Statement = Case().Parse(Scanner);
		elif Scanner.TokenExpected('While'):
			self.Type = 'While';
			self.Statement = While().Parse(Scanner);
		elif Scanner.TokenExpected('Repeat'):
			self.Type = 'Repeat';
			self.Statement = Repeat().Parse(Scanner);
		elif Scanner.TokenExpected('Begin'):
			self.Type = 'Block';
			self.Statement = Statements().Parse(Scanner);
		elif Scanner.TokensExpected(['[', ':='], 1):
			self.Type = 'Assignment';
			self.Statement = Assignment().Parse(Scanner);
		elif Scanner.TokenExpected('(', 1) or (Scanner.TokenExpected('Identifier') and Scanner.TokensExpected([';', 'End'], 1)):
			self.Type = 'Invoking';
			self.Statement = Invoking().Parse(Scanner);
		else:
			print(Scanner.PeekToken(1));
			print(Scanner.PeekToken(2));
			Token = Scanner.NextToken();
			raise SyntaxError('Unexpected token "%s".' % (Token[1] or Token[0]));
		return self;

class Declarations(object):
	def __init__(self):
		self.Declarations = [];

	def Parse(self, Scanner):
		while True:
			if Scanner.TokenExpected('Function'):
				self.Declarations.append(('Function', Function().Parse(Scanner)));
			elif Scanner.TokenExpected('Procedure'):
				self.Declarations.append(('Procedure', Procedure().Parse(Scanner)));
			elif Scanner.TokenExpected('Var'):
				Scanner.NextToken();
				if not Scanner.TokenExpected('Identifier'):
					raise SyntaxError('Identifier expected.');
				while Scanner.TokenExpected('Identifier'):
					self.Declarations.append(('Variable', Variable().Parse(Scanner)));
			elif Scanner.TokenExpected('Const'):
				Scanner.NextToken();
				if not Scanner.TokenExpected('Identifier'):
					raise SyntaxError('Identifier expected.');
				while Scanner.TokenExpected('Identifier'):
					self.Declarations.append(('Constant', Constant().Parse(Scanner)));
			else:
				break;
		return self;

class Statements(object):
	def __init__(self):
		self.Statements = [];

	def Parse(self, Scanner):
		if not Scanner.TokenNeeded('Begin'):
			raise SyntaxError('"begin" expected.');
		while not Scanner.TokenExpected('End'):
			if Scanner.PeekToken()[0] == None:
				raise SyntaxError('"end" expected.');
			self.Statements.append(Statement().Parse(Scanner));
			if not Scanner.TokenExpected('End') and not Scanner.TokenNeeded(';'):
				raise SyntaxError('";" expected.');
		if not Scanner.TokenNeeded('End'):
			raise SyntaxError('"end" expected.');
		return self;

class Program(object):
	def __init__(self, Scanner):
		self.Name = '';
		self.Scanner = Scanner;
		self.Statements = Statements();
		self.Declarations = Declarations();

	def Parse(self):
		if not self.Scanner.TokenNeeded('Program'):
			raise SyntaxError('"program" expected.');
		Token, self.Name = self.Scanner.NextToken();
		if Token != 'Identifier':
			raise SyntaxError('identifier expected.');
		if not self.Scanner.TokenNeeded(';'):
			raise SyntaxError('";" expected');
		self.Declarations.Parse(self.Scanner);
		self.Statements.Parse(self.Scanner);
		if not self.Scanner.TokenNeeded('.'):
			raise SyntaxError('"." expected');
		return self;
