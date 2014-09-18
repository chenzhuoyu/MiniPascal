'''
	Created on 2013-2-1

	@author: desperedo

	miniPascal Compiler Code Generator
'''

import Bytecode

class InvokableStub(object):
	def __init__(self, ID, Address, Function, ReturnMap):
		self.ID = ID;
		self.Address = Address;
		self.Function = Function;
		self.ReturnMap = ReturnMap;

class Generator(object):
	def __init__(self, Program):
		self.ID = 0;
		self.Level = 0;
		self.Program = Program;
		self.CodeStack = Bytecode.CodeStack();

		self.Builtins = {};
		self.VariableMap = {};
		self.InvokableMap = {};
		self.InvokingRequests = [];

		self.AddBuiltin('read'		, 'read'	, None	, False	, True);
		self.AddBuiltin('readln'	, 'readln'	, None	, False	, True);
		self.AddBuiltin('write'		, 'write'	, None	, False	, False);
		self.AddBuiltin('writeln'	, 'writeln'	, None	, False	, False);

		self.AddBuiltin('char'		, 'chr'		, 1		, True	, [False]);
		self.AddBuiltin('real'		, 'real'	, 1		, True	, [False]);
		self.AddBuiltin('string'	, 'str'		, 1		, True	, [False]);
		self.AddBuiltin('integer'	, 'int'		, 1		, True	, [False]);
		self.AddBuiltin('boolean'	, 'bool'	, 1		, True	, [False]);

		self.AddBuiltin('sin'		, 'sin'		, 1		, True	, [False]);
		self.AddBuiltin('cos'		, 'cos'		, 1		, True	, [False]);
		self.AddBuiltin('tan'		, 'tan'		, 1		, True	, [False]);
		self.AddBuiltin('sqrt'		, 'sqrt'	, 1		, True	, [False]);

		self.AddBuiltin('length'	, 'lens'	, 1		, True	, [False]);
		self.AddBuiltin('concat'	, 'cats'	, 2		, True	, [False, False]);
		self.AddBuiltin('copy'		, 'cpys'	, 3		, True	, [False, False, False]);
		self.AddBuiltin('insert'	, 'ints'	, 3		, False	, [False, True , False]);
		self.AddBuiltin('delete'	, 'dels'	, 3		, False	, [True , False, False]);

	def AddType(self, Name):
		self.Types[Name.lower()] = Name;

	def AddBuiltin(self, Name, Mnemonic, Params, Function, Variable):
		self.Builtins[Name.lower()] = {};
		self.Builtins[Name.lower()]['Params'] = Params;
		self.Builtins[Name.lower()]['Function'] = Function;
		self.Builtins[Name.lower()]['Variable'] = Variable;
		self.Builtins[Name.lower()]['Mnemonic'] = Mnemonic.lower();

	def MakeID(self):
		self.ID += 1;
		return self.ID;

	def UnmapLevel(self, Level, Map):
		Keys = [];
		for Key in Map:
			if Key[1] == Level:
				Keys.append(Key);
		for Key in Keys:
			if Map == self.VariableMap:
				self.CodeStack.PushBytecode('undef', Map[Key]);
			del Map[Key];

	def MapVariable(self, Name, Type):
		if Type.Array:
			ID = self.MapVariable(Name, Type.Type);
			self.CodeStack.PushBytecode('mkarr', Type.ArrayLow, Type.ArrayHigh);
			return ID;
		else:
			self.VariableMap[(Name.lower(), self.Level)] = self.MakeID();
			if Type.Type == 'Char':				self.CodeStack.PushBytecode('dchar', self.ID);
			elif Type.Type == 'Real':			self.CodeStack.PushBytecode('dfloat', self.ID);
			elif Type.Type == 'String':			self.CodeStack.PushBytecode('dstr', self.ID);
			elif Type.Type == 'Integer':		self.CodeStack.PushBytecode('dint', self.ID);
			elif Type.Type == 'Boolean':		self.CodeStack.PushBytecode('dbool', self.ID);
			return self.ID;

	def MapInvokable(self, Name, Address, Function, ReturnMap, ForwardMapping):
		if ForwardMapping:
			self.InvokableMap[(Name.lower(), self.Level - 1)] = InvokableStub(-1, 0, Function, ReturnMap);
		else:
			self.InvokableMap[(Name.lower(), self.Level - 1)] = InvokableStub(self.MakeID(), Address, Function, ReturnMap);

	def QueueInvokeRequest(self, Name, Code):
		Request = {};
		Request['Code'] = Code;
		Request['Name'] = Name.lower();
		self.InvokingRequests.append(Request);

	def GetVariableID(self, Name):
		Result = None;
		ResultLevel = -1;
		for Item, Level in self.VariableMap:
			if Level > ResultLevel and Item == Name.lower():
				ResultLevel = Level;
				Result = self.VariableMap[(Item, Level)];
		return Result;

	def GetInvokableStub(self, Name):
		Result = None;
		ResultLevel = -1;
		for Item, Level in self.InvokableMap:
			if Level > ResultLevel and Item == Name.lower():
				ResultLevel = Level;
				Result = self.InvokableMap[(Item, Level)];
		return Result;

	def AppendReturnItem(self, ReturnMap, ID, Index = -1):
		ReturnItem = {};
		ReturnItem['ID'] = ID;
		ReturnItem['Index'] = Index;
		ReturnMap.append(ReturnItem);

	def BuildReturnMap(self, Name, Parameters, ReturnType, ForwardMapping):
		Index = 0;
		ReturnMap = [];
		for Item in Parameters:
			for Param in Item.Names:
				ID = -1;
				Index += 1;
				if not ForwardMapping:
					ID = self.MapVariable(Param, Item.Type, Item.Array, Item.ArrayLow, Item.ArrayHigh);
					self.CodeStack.PushBytecode('pop', ID);
				if Item.Variable:
					self.AppendReturnItem(ReturnMap, ID, Index - 1);
		if not ForwardMapping and ReturnType != None:
			self.AppendReturnItem(ReturnMap, self.MapVariable(Name, ReturnType, False, None, None));
		return ReturnMap;

	def LinkInvokables(self):
		LinkedInvoking = [];
		for Request in self.InvokingRequests:
			Stub = self.GetInvokableStub(Request['Name']);
			if Stub != None and Stub.ID >= 0:
				LinkedInvoking.append(Request);
				Request['Code'].Operand = Stub.Address;
		for Request in LinkedInvoking:
			self.InvokingRequests.remove(Request);

	def LevelUp(self):
		self.Level += 1;

	def LevelDown(self, Forward):
		if not Forward:
			self.LinkInvokables();
			self.UnmapLevel(self.Level, self.VariableMap);
			self.UnmapLevel(self.Level, self.InvokableMap);
			self.CodeStack.PushBytecode('ret');
		self.Level -= 1;

	def GenerateFunction(self, Function):
		if not Function.Forward:
			Code = self.CodeStack.PushBytecode('br', 0);
		self.LevelUp();
		IP = self.CodeStack.IP;
		ReturnMap = self.BuildReturnMap(Function.Name, Function.Parameters, Function.ReturnType, Function.Forward);
		self.MapInvokable(Function.Name, IP, True, ReturnMap, Function.Forward);
		if not Function.Forward:
			self.GenerateDeclarations(Function.Declarations);
			self.GenerateStatements(Function.Statements);
			ReturnMap.reverse();
			for Item in ReturnMap:
				self.CodeStack.PushBytecode('push', Item['ID']);
			ReturnMap.reverse();
		self.LevelDown(Function.Forward);
		if not Function.Forward:
			Code.Operand = self.CodeStack.IP;

	def GenerateProcedure(self, Procedure):
		if not Procedure.Forward:
			Code = self.CodeStack.PushBytecode('br', 0);
		self.LevelUp();
		IP = self.CodeStack.IP;
		ReturnMap = self.BuildReturnMap(Procedure.Name, Procedure.Parameters, None, Procedure.Forward);
		self.MapInvokable(Procedure.Name, IP, False, ReturnMap, Procedure.Forward);
		if not Procedure.Forward:
			self.GenerateDeclarations(Procedure.Declarations);
			self.GenerateStatements(Procedure.Statements);
			ReturnMap.reverse();
			for Item in ReturnMap:
				self.CodeStack.PushBytecode('push', Item['ID']);
			ReturnMap.reverse();
		self.LevelDown(Procedure.Forward);
		if not Procedure.Forward:
			Code.Operand = self.CodeStack.IP;

	def GenerateFactor(self, Factor):
		if Factor.Type == 'Invoking':		self.GenerateInvoking(Factor.Value);
		elif Factor.Type == 'Expression':	self.GenerateExpression(Factor.Value);
		elif Factor.Type == 'Char':			self.CodeStack.PushBytecode('ldc', Factor.Value);
		elif Factor.Type == 'Real':			self.CodeStack.PushBytecode('ldf', Factor.Value);
		elif Factor.Type == 'Integer':		self.CodeStack.PushBytecode('ldi', Factor.Value);
		elif Factor.Type == 'String':		self.CodeStack.PushBytecode('lds', Factor.Value);
		elif Factor.Type == 'Boolean':		self.CodeStack.PushBytecode('ldtrue' if Factor.Value else 'ldfalse');
		elif Factor.Type == 'Identifier':	self.CodeStack.PushBytecode('push', self.GetVariableID(Factor.Value));
		elif Factor.Type == 'Factor':
			self.GenerateFactor(Factor.Value);
			if Factor.Prefix == '-':		self.CodeStack.PushBytecode('inv');
			elif Factor.Prefix == 'Not':	self.CodeStack.PushBytecode('not');
		elif Factor.Type == 'Indexing':
			Factor.Indexer.reverse();
			for Indexer in Factor.Indexer:
				self.GenerateExpression(Indexer);
			Factor.Indexer.reverse();
			self.CodeStack.PushBytecode('pusha', len(Factor.Indexer), self.GetVariableID(Factor.Value));

	def GenerateTerm(self, Term):
		self.GenerateFactor(Term.Factor);
		for Operator, Factor in Term.Factors:
			self.GenerateFactor(Factor);
			if Operator == '*':			self.CodeStack.PushBytecode('mul');
			elif Operator == '/':		self.CodeStack.PushBytecode('div');
			elif Operator == 'Div':		self.CodeStack.PushBytecode('idiv');
			elif Operator == 'Mod':		self.CodeStack.PushBytecode('mod');
			elif Operator == 'And':		self.CodeStack.PushBytecode('and');
			elif Operator == 'Shl':		self.CodeStack.PushBytecode('shl');
			elif Operator == 'Shr':		self.CodeStack.PushBytecode('shr');

	def GenerateSimpleExpr(self, SimpleExpr):
		self.GenerateTerm(SimpleExpr.Term);
		for Operator, Term in SimpleExpr.Terms:
			self.GenerateTerm(Term);
			if Operator == '+':			self.CodeStack.PushBytecode('add');
			elif Operator == '-':		self.CodeStack.PushBytecode('sub');
			elif Operator == 'Or':		self.CodeStack.PushBytecode('or');
			elif Operator == 'Xor':		self.CodeStack.PushBytecode('xor');

	def GenerateExpression(self, Expression):
		self.GenerateSimpleExpr(Expression.Operand1);
		if Expression.Operator != None:
			self.GenerateSimpleExpr(Expression.Operand2);
			if Expression.Operator == '=':		self.CodeStack.PushBytecode('equ');
			elif Expression.Operator == '<':	self.CodeStack.PushBytecode('lt');
			elif Expression.Operator == '>':	self.CodeStack.PushBytecode('gt');
			elif Expression.Operator == '<=':	self.CodeStack.PushBytecode('leq');
			elif Expression.Operator == '>=':	self.CodeStack.PushBytecode('geq');
			elif Expression.Operator == '<>':	self.CodeStack.PushBytecode('neq');

	def GenerateIf(self, If):
		self.GenerateExpression(If.Expression);
		Code = self.CodeStack.PushBytecode('brf', 0);
		self.GenerateStatement(If.TrueStatement);
		if If.FalseStatement == None:
			Code.Operand = self.CodeStack.IP;
		else:
			Instr = self.CodeStack.PushBytecode('br', 0);
			Code.Operand = self.CodeStack.IP;
			self.GenerateStatement(If.FalseStatement);
			Instr.Operand = self.CodeStack.IP;

	def GenerateFor(self, For):
		self.GenerateAssignment(For.Init);
		IP = self.CodeStack.IP;
		self.CodeStack.PushBytecode('push', self.GetVariableID(For.Init.Target));
		self.GenerateExpression(For.Stop);
		self.CodeStack.PushBytecode('gt' if For.Type == 'Inc' else 'lt');
		Code = self.CodeStack.PushBytecode('brt', 0);
		self.GenerateStatement(For.Statement);
		self.CodeStack.PushBytecode('push', self.GetVariableID(For.Init.Target));
		self.CodeStack.PushBytecode('ldi', 1);
		self.CodeStack.PushBytecode('add' if For.Type == 'Inc' else 'sub');
		self.CodeStack.PushBytecode('pop', self.GetVariableID(For.Init.Target));
		self.CodeStack.PushBytecode('br', IP);
		Code.Operand = self.CodeStack.IP;
		self.CodeStack.PushBytecode('push', self.GetVariableID(For.Init.Target));
		self.CodeStack.PushBytecode('ldi', 1);
		self.CodeStack.PushBytecode('sub' if For.Type == 'Inc' else 'add');
		self.CodeStack.PushBytecode('pop', self.GetVariableID(For.Init.Target));

	def GenerateCase(self, Case):
		ExitPoints = [];
		NextCaseItem = None;
		self.GenerateExpression(Case.Expression);
		Type = self.Types[Case.ConstantType.lower()];
		for Item in Case.Statements:
			self.CodeStack.PushBytecode('dup');
			if Type == 'Char':			self.CodeStack.PushBytecode('ldc', Item);
			elif Type == 'Integer':		self.CodeStack.PushBytecode('ldi', Item);
			self.CodeStack.PushBytecode('equ');
			NextCaseItem = self.CodeStack.PushBytecode('brf', 0);
			self.GenerateStatement(Case.Statements[Item]);
			ExitPoints.append(self.CodeStack.PushBytecode('br', 0));
			NextCaseItem.Operand = self.CodeStack.IP;
		if Case.DefaultStatement != None:
			self.GenerateStatement(Case.DefaultStatement);
		for Point in ExitPoints:
			Point.Operand = self.CodeStack.IP;
		self.CodeStack.PushBytecode('drop');

	def GenerateWhile(self, While):
		IP = self.CodeStack.IP;
		self.GenerateExpression(While.Expression);
		Code = self.CodeStack.PushBytecode('brf', 0);
		self.GenerateStatement(While.Statement);
		self.CodeStack.PushBytecode('br', IP);
		Code.Operand = self.CodeStack.IP;

	def GenerateRepeat(self, Repeat):
		IP = self.CodeStack.IP;
		for Statement in Repeat.Statements:
			self.GenerateStatement(Statement);
		self.GenerateExpression(Repeat.Expression);
		self.CodeStack.PushBytecode('brf', IP);

	def GenerateInvoking(self, Invoking):
		Invoking.Parameters.reverse();
		for Parameter in Invoking.Parameters:
			self.GenerateExpression(Parameter);
		Invoking.Parameters.reverse();
		if Invoking.Name.lower() not in self.Builtins.keys():
			self.QueueInvokeRequest(Invoking.Name, self.CodeStack.PushBytecode('call', 0));
			for Item in self.GetInvokableStub(Invoking.Name).ReturnMap:
				Index = Item['Index'];
				if Index >= 0:
					self.CodeStack.PushBytecode('pop', self.GetVariableID(Invoking.Parameters[Index].Operand1.Term.Factor.Value));
		else:
			Builtin = self.Builtins[Invoking.Name.lower()];
			if Builtin['Params'] == None:
				self.CodeStack.PushBytecode(Builtin['Mnemonic'], len(Invoking.Parameters));
				if Builtin['Variable']:
					for Parameter in Invoking.Parameters:
						self.CodeStack.PushBytecode('pop', self.GetVariableID(Parameter.Operand1.Term.Factor.Value));
			else:
				self.CodeStack.PushBytecode(Builtin['Mnemonic']);
				for I in range(Builtin['Params']):
					if Builtin['Variable'][I]:
						self.CodeStack.PushBytecode('pop', self.GetVariableID(Invoking.Parameters[I].Operand1.Term.Factor.Value));
			if Builtin['Function'] and not Invoking.Factor:
				self.CodeStack.PushBytecode('drop');

	def GenerateAssignment(self, Assignment):
		self.GenerateExpression(Assignment.Expression);
		if Assignment.Indexer == None:
			self.CodeStack.PushBytecode('pop', self.GetVariableID(Assignment.Target));
		else:
			Assignment.Indexer.reverse();
			for Indexer in Assignment.Indexer:
				self.GenerateExpression(Indexer);
			Assignment.Indexer.reverse();
			self.CodeStack.PushBytecode('popa', len(Assignment.Indexer), self.GetVariableID(Assignment.Target));

	def GenerateStatement(self, Statement):
		if Statement.Type == 'If':				self.GenerateIf(Statement.Statement);
		elif Statement.Type == 'For':			self.GenerateFor(Statement.Statement);
		elif Statement.Type == 'Case':			self.GenerateCase(Statement.Statement);
		elif Statement.Type == 'While':			self.GenerateWhile(Statement.Statement);
		elif Statement.Type == 'Repeat':		self.GenerateRepeat(Statement.Statement);
		elif Statement.Type == 'Invoking':		self.GenerateInvoking(Statement.Statement);
		elif Statement.Type == 'Assignment':	self.GenerateAssignment(Statement.Statement);
		elif Statement.Type == 'Block':			self.GenerateStatements(Statement.Statement);

	def GenerateDeclarations(self, Declarations):
		for Type, Item in Declarations.Declarations:
			if Type == 'Function':		self.GenerateFunction(Item);
			elif Type == 'Procedure':	self.GenerateProcedure(Item);
			elif Type == 'Variable':
				for Name in Item.Names:
					self.MapVariable(Name, Item.Type);

	def GenerateStatements(self, Statements):
		for Statement in Statements.Statements:
			self.GenerateStatement(Statement);

	def Generate(self):
		self.LevelUp();
		self.GenerateDeclarations(self.Program.Declarations);
		self.GenerateStatements(self.Program.Statements);
		self.LevelDown(False);
