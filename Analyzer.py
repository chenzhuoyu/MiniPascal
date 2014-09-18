'''
	Created on 2013-1-30

	@author: desperedo

	miniPascal Compiler Semantic Analyzer
'''

import Parser

class LogicalError(Exception): pass

class ValueType(object):
	def __init__(self, SingleVar, Array, Type, Constant, Value):
		self.Type = Type;
		self.Array = Array;
		self.Value = Value;
		self.Constant = Constant;
		self.SingleVar = SingleVar;

class InvokingType(object):
	def __init__(self, Type, Constant, Value):
		self.Type = Type;
		self.Value = Value;
		self.Constant = Constant;

class ConstantItem(object):
	def __init__(self, Level, Name, Type, Value):
		self.Type = Type;
		self.Level = Level;
		self.Value = Value;
		self.Name = Name.lower();

class VariableItem(object):
	def __init__(self, Level, Name, Type):
		self.Type = Type;
		self.Level = Level;
		self.Name = Name.lower();

class FunctionItem(object):
	def __init__(self, Level, Name, ReturnType, ParameterMap, Forward):
		self.Level = Level;
		self.Forward = Forward;
		self.Name = Name.lower();
		self.ReturnType = ReturnType;
		self.ParameterMap = ParameterMap;

class ProcedureItem(object):
	def __init__(self, Level, Name, ParameterMap, Forward):
		self.Level = Level;
		self.Forward = Forward;
		self.Name = Name.lower();
		self.ParameterMap = ParameterMap;

class Analyzer(object):
	def __init__(self, Program):
		self.Level = 0;
		self.Program = Program;

		self.Types = [];
		self.Builtins = {};
		self.ConstantTable = [];
		self.VariableTable = [];
		self.FunctionTable = [];
		self.ProcedureTable = [];

		self.Types.append('Char');
		self.Types.append('Real');
		self.Types.append('String');
		self.Types.append('Integer');
		self.Types.append('Boolean');

		self.AddBuiltin('read'		, 1, True	, None, ['Boolean']);
		self.AddBuiltin('write'		, 1, False	, None, None);
		self.AddBuiltin('readln'	, 0, True	, None, ['Boolean']);
		self.AddBuiltin('writeln'	, 0, False	, None, None);

		self.AddBuiltin('sin'	, ['Real'], [False], 'Real', None);
		self.AddBuiltin('cos'	, ['Real'], [False], 'Real', None);
		self.AddBuiltin('tan'	, ['Real'], [False], 'Real', None);
		self.AddBuiltin('sqrt'	, ['Real'], [False], 'Real', None);

		self.AddBuiltin('length', ['String'							], [False				], 'Integer'	, None);
		self.AddBuiltin('concat', ['String', 'String'				], [False, False		], 'String'		, None);
		self.AddBuiltin('insert', ['String', 'String' , 'Integer'	], [False, True , False	], None			, None);
		self.AddBuiltin('delete', ['String', 'Integer', 'Integer'	], [True , False, False	], None			, None);
		self.AddBuiltin('copy'  , ['String', 'Integer', 'Integer'	], [False, False, False	], 'String'		, None);

	def AddBuiltin(self, Name, Params, Variable, ReturnType, ForbiddenTypes):
		self.Builtins[Name.lower()] = {};
		self.Builtins[Name.lower()]['Params'] = Params;
		self.Builtins[Name.lower()]['Variable'] = Variable;
		self.Builtins[Name.lower()]['ReturnType'] = ReturnType;
		self.Builtins[Name.lower()]['ForbiddenTypes'] = ForbiddenTypes;

	def LevelUp(self):
		self.Level += 1;

	def LevelDown(self):
		self.ClearLevel(self.Level, self.ConstantTable);
		self.ClearLevel(self.Level, self.VariableTable);
		self.ClearLevel(self.Level, self.FunctionTable);
		self.ClearLevel(self.Level, self.ProcedureTable);
		self.Level -= 1;

	def ClearLevel(self, Level, List):
		Items = [];
		for Item in List:
			if Item.Level == Level:
				Items.append(Item);
		for Item in Items:
			List.remove(Item);

	def FindIdentifier(self, Name, List):
		Result = None;
		ResultLevel = -1;
		for Item in List:
			if Item.Level > ResultLevel and Item.Name == Name.lower():
				Result = Item;
				ResultLevel = Item.Level;
		return Result;

	def FindName(self, Name, List, Level):
		for Item in List:
			if Item.Level == Level and Item.Name == Name.lower():
				return Item;
		return None;

	def CheckDuplicate(self, Name, Level):
		if Name.lower() in self.Types or \
		   Name.lower() in self.Builtins.keys() or \
		   self.FindName(Name, self.ConstantTable, Level) != None or \
		   self.FindName(Name, self.VariableTable, Level) != None or \
		   self.FindName(Name, self.FunctionTable, Level) != None or \
		   self.FindName(Name, self.ProcedureTable, Level) != None:
			raise LogicalError('Identifier "%s" redeclaration.' % Name);

	def BuildParameterMap(self, Parameters):
		ParameterMap = [];
		for Item in Parameters:
			for Name in Item.Names:
				Attribute = {};
				Attribute['Name'] = Name.lower();
				Attribute['Type'] = Item.Type.Type;
				Attribute['Array'] = Item.Type.Array;
				Attribute['Variable'] = Item.Variable;
				Attribute['ArrayLow'] = Item.Type.ArrayLow;
				Attribute['ArrayHigh'] = Item.Type.ArrayHigh;
				ParameterMap.append(Attribute);
		return ParameterMap;

	def AddConstant(self, Name, Type, Value):
		self.CheckDuplicate(Name, self.Level);
		self.ConstantTable.append(ConstantItem(self.Level, Name, Type.Type, Value));

	def AddVariables(self, Names, Type):
		for Name in Names:
			self.CheckDuplicate(Name, self.Level);
			self.VariableTable.append(VariableItem(self.Level, Name, Type));

	def AddParameters(self, Parameters):
		for Item in Parameters:
			self.AddVariables(Item.Names, Item.Type);

	def AddParametersFromMap(self, Parameters, ParameterMap):
		if ParameterMap != self.BuildParameterMap(Parameters):
			raise LogicalError('Parameters are inconsistent with forward declaration.');
		self.AddParameters(Parameters);

	def AddReturnValue(self, Name, ReturnType, FunctionType):
		if ReturnType == FunctionType:
			self.AddVariables([Name], ReturnType);
		else:
			raise LogicalError('Function return-type is inconsistent with forward declaration.');

	def AddFunction(self, Name, ReturnType, Parameters, Forward):
		Function = self.FindName(Name, self.FunctionTable, self.Level - 1);
		if Function != None:
			if Forward or not Function.Forward:
				raise LogicalError('Identifier "%s" redeclaration.' % Name);
			Function.Forward = False;
			self.AddReturnValue(Name, ReturnType, Function.ReturnType);
			self.AddParametersFromMap(Parameters, Function.ParameterMap);
		else:
			if not Forward:
				self.AddParameters(Parameters);
				self.AddReturnValue(Name, ReturnType, ReturnType);
			self.CheckDuplicate(Name, self.Level - 1);
			self.FunctionTable.append(FunctionItem(
				self.Level - 1, Name, ReturnType.Type, self.BuildParameterMap(Parameters), Forward));

	def AddProcedure(self, Name, Parameters, Forward):
		Procedure = self.FindName(Name, self.ProcedureTable, self.Level - 1);
		if Procedure != None:
			if Forward or not Procedure.Forward:
				raise LogicalError('Identifier "%s" redeclaration.' % Name);
			Procedure.Forward = False;
			self.AddParametersFromMap(Parameters, Procedure.ParameterMap);
		else:
			if not Forward:
				self.AddParameters(Parameters);
			self.CheckDuplicate(Name, self.Level - 1);
			self.ProcedureTable.append(ProcedureItem(self.Level - 1, Name, self.BuildParameterMap(Parameters), Forward));

	def CheckCast(self, From, To):
		if From == To:								return True;
		if From == 'Char' and To == 'String':		return True;
		if From == 'Char' and To == 'Integer':		return True;
		if From == 'Real' and To == 'Integer':		return True;
		if From == 'Integer' and To == 'Char':		return True;
		if From == 'Integer' and To == 'Real':		return True;
		if From == 'Integer' and To == 'Boolean':	return True;
		if From == 'Boolean' and To == 'Integer':	return True;
		return False;

	def GetMaxType(self, Type1, Type2):
		if Type1 not in self.Types:						return None;
		elif Type2 not in self.Types:					return None;
		elif Type1 == Type2:							return Type1;
		elif Type1 == 'Char' and Type2 == 'String':		return Type2;
		elif Type1 == 'String' and Type2 == 'Char':		return Type1;
		elif Type1 == 'Integer' and Type2 == 'Real':	return Type2;
		elif Type1 == 'Real' and Type2 == 'Integer':	return Type1;
		return None;

	def BuildTerm(self, Name, *Terms):
		NewTerm = Parser.Term();
		NewTerm.Factor.Type = 'Invoking';
		NewTerm.Factor.Value = Parser.Invoking();
		NewTerm.Factor.Value.Name = Name;
		NewTerm.Factor.Value.Factor = True;
		for Term in Terms:
			Expression = Parser.Expression();
			Expression.Operand1.Term = Term;
			NewTerm.Factor.Value.Parameters.append(Expression);
		return NewTerm;

	def BuildFactor(self, Name, *Factors):
		NewFactor = Parser.Factor();
		NewFactor.Type = 'Invoking';
		NewFactor.Value = Parser.Invoking();
		NewFactor.Value.Name = Name;
		NewFactor.Value.Factor = True;
		for Factor in Factors:
			Expression = Parser.Expression();
			Expression.Operand1.Term.Factor = Factor;
			NewFactor.Value.Parameters.append(Expression);
		return NewFactor;

	def BuildSimpleExpr(self, Name, *SimpleExprs):
		NewSimpleExpr = Parser.SimpleExpr();
		NewSimpleExpr.Term.Factor.Type = 'Invoking';
		NewSimpleExpr.Term.Factor.Value = Parser.Invoking();
		NewSimpleExpr.Term.Factor.Value.Name = Name;
		NewSimpleExpr.Term.Factor.Value.Factor = True;
		for SimpleExpr in SimpleExprs:
			Expression = Parser.Expression();
			Expression.Operand1 = SimpleExpr;
			NewSimpleExpr.Term.Factor.Value.Parameters.append(Expression);
		return NewSimpleExpr;

	def BuildExpression(self, Name, *Expressions):
		NewExpression = Parser.Expression();
		NewExpression.Operand1.Term.Factor.Type = 'Invoking';
		NewExpression.Operand1.Term.Factor.Value = Parser.Invoking();
		NewExpression.Operand1.Term.Factor.Value.Name = Name;
		NewExpression.Operand1.Term.Factor.Value.Factor = True;
		for Expression in Expressions:
			NewExpression.Operand1.Term.Factor.Value.Parameters.append(Expression);
		return NewExpression;

	def ConvertTerm(self, Term, Type, TargetType):
		if Type == TargetType:								return Term;
		elif Type == 'Char' and TargetType == 'String':		return self.BuildTerm('String', Term);
		elif Type == 'Integer' and TargetType == 'Real':	return self.BuildTerm('Real', Term);
		else: raise LogicalError('Implicit conversion from "%s" to "%s" is unsupported.' % (Type, TargetType));

	def ConvertFactor(self, Factor, Type, TargetType):
		if Type == TargetType:								return Factor;
		elif Type == 'Char' and TargetType == 'String':		return self.BuildFactor('String', Factor);
		elif Type == 'Integer' and TargetType == 'Real':	return self.BuildFactor('Real', Factor);
		else: raise LogicalError('Implicit conversion from "%s" to "%s" is unsupported.' % (Type, TargetType));

	def ConvertSimpleExpr(self, SimpleExpr, Type, TargetType):
		if Type == TargetType:								return SimpleExpr;
		elif Type == 'Char' and TargetType == 'String':		return self.BuildSimpleExpr('String', SimpleExpr);
		elif Type == 'Integer' and TargetType == 'Real':	return self.BuildSimpleExpr('Real', SimpleExpr);
		else: raise LogicalError('Implicit conversion from "%s" to "%s" is unsupported.' % (Type, TargetType));

	def ConvertExpression(self, Expression, Type, TargetType):
		if Type == TargetType:								return Expression;
		elif Type == 'Char' and TargetType == 'String':		return self.BuildExpression('String', Expression);
		elif Type == 'Integer' and TargetType == 'Real':	return self.BuildExpression('Real', Expression);
		else: raise LogicalError('Implicit conversion from "%s" to "%s" is unsupported.' % (Type, TargetType));

	def ConstantCast(self, Constant, TargetType):
		if Constant.Type == TargetType:								return Constant.Value;
		elif Constant.Type == 'Char' and TargetType == 'String':	return str(Constant.Value);
		elif Constant.Type == 'Integer' and TargetType == 'Real':	return float(Constant.Value);
		else: raise LogicalError('Implicit conversion from "%s" to "%s" is unsupported.' % (Constant.Type, TargetType));

	def InvokingResultCast(self, Type, TargetType, Value):
		if Type == 'Char' and TargetType == 'String':		return str(Value);
		if Type == 'Char' and TargetType == 'Integer':		return ord(Value);
		if Type == 'Real' and TargetType == 'Integer':		return int(Value);
		if Type == 'Integer' and TargetType == 'Char':		return chr(Value);
		if Type == 'Integer' and TargetType == 'Real':		return float(Value);
		if Type == 'Boolean' and TargetType == 'Integer':	return 1 if Value else 0;
		if Type == 'Integer' and TargetType == 'Boolean':	return True if Value != 0 else False;
		return Value;

	def ApplyPrefix(self, Type, Prefix, Operand):
		if Prefix == '+':		return Operand;
		if Prefix == '-':		return -Operand;
		if Prefix == 'Not':		return ~Operand if Type == 'Integer' else not Operand;
		raise LogicalError('Unknown operator "%s".' % Prefix);

	def ApplyOperator(self, Type, Operand1, Operator, Operand2):
		Value1 = self.ConstantCast(Operand1, Type);
		Value2 = self.ConstantCast(Operand2, Type);
		if Operator == '+':		return Value1 + Value2;
		if Operator == '-':		return Value1 - Value2;
		if Operator == '*':		return Value1 * Value2;
		if Operator == '/':		return Value1 / Value2;
		if Operator == '>':		return Value1 > Value2;
		if Operator == '<':		return Value1 < Value2;
		if Operator == '=':		return Value1 == Value2;
		if Operator == '>=':	return Value1 >= Value2;
		if Operator == '<=':	return Value1 <= Value2;
		if Operator == '<>':	return Value1 != Value2;
		if Operator == 'Mod':	return Value1 % Value2;
		if Operator == 'Xor':	return Value1 ^ Value2;
		if Operator == 'Div':	return Value1 // Value2;
		if Operator == 'Shl':	return Value1 << Value2;
		if Operator == 'Shr':	return Value1 >> Value2;
		if Operator == 'Or':	return (Value1 | Value2) if Type == 'Integer' else (Value1 or Value2);
		if Operator == 'And':	return (Value1 & Value2) if Type == 'Integer' else (Value1 and Value2);
		raise LogicalError('Unknown operator "%s".' % Operator);

	def AnalyzeFunction(self, Function):
		self.LevelUp();
		self.AddFunction(Function.Name, Function.ReturnType, Function.Parameters, Function.Forward);
		if not Function.Forward:
			self.AnalyzeDeclarations(Function.Declarations);
			self.AnalyzeStatements(Function.Statements);
		self.LevelDown();

	def AnalyzeProcedure(self, Procedure):
		self.LevelUp();
		self.AddProcedure(Procedure.Name, Procedure.Parameters, Procedure.Forward);
		if not Procedure.Forward:
			self.AnalyzeDeclarations(Procedure.Declarations);
			self.AnalyzeStatements(Procedure.Statements);
		self.LevelDown();

	def AnalyzeFactor(self, Factor):
		if Factor.Type in self.Types:
			return ValueType(False, False, Factor.Type, True, Factor.Value);
		elif Factor.Type == 'Expression':
			Expression = self.AnalyzeExpression(Factor.Value);
			return ValueType(False, Expression.Array, Expression.Type, Expression.Constant, Expression.Value);
		elif Factor.Type == 'Invoking':
			Invoking = self.AnalyzeInvoking(Factor.Value);
			if Invoking.Type == None:
				raise LogicalError('Procedure "%s" have no return values that cannot be computed.' % Factor.Value);
			return ValueType(False, False, Invoking.Type, Invoking.Constant, Invoking.Value);
		elif Factor.Type == 'Factor':
			NewFactor = self.AnalyzeFactor(Factor.Value);
			if NewFactor.Array:
				raise LogicalError('Array itself cannot be computed directly.');
			if NewFactor.Type in ['Char', 'String'] or \
			   (Factor.Prefix != 'Not' and NewFactor.Type == 'Boolean') or \
			   (Factor.Prefix == 'Not' and NewFactor.Type not in ['Boolean', 'Integer']):
				raise LogicalError('"%s" operation is not defined with "%s".' % (Factor.Prefix, NewFactor.Type));
			if not NewFactor.Constant:
				return ValueType(False, False, NewFactor.Type, False, None);
			else:
				Factor.Type = NewFactor.Type;
				Factor.Value = self.ApplyPrefix(NewFactor.Type, Factor.Prefix, NewFactor.Value);
				Factor.Prefix = None;
				return ValueType(False, False, NewFactor.Type, True, Factor.Value);
		elif Factor.Type == 'Identifier':
			Variable = self.FindIdentifier(Factor.Value, self.VariableTable);
			Constant = self.FindIdentifier(Factor.Value, self.ConstantTable);
			if Variable != None:
				return ValueType(True, Variable.Type.Array, Variable.Type.Type, False, None);
			elif Constant != None:
				Factor.Type = Constant.Type;
				Factor.Value = Constant.Value;
				return ValueType(False, False, Factor.Type, True, Factor.Value);
			else:
				NewInvoking = Parser.Invoking();
				NewInvoking.Factor = True;
				NewInvoking.Name = Factor.Value;
				Invoking = self.AnalyzeInvoking(NewInvoking);
				if Invoking.Type == None:
					raise LogicalError('Procedure "%s" have no return values that cannot be computed.' % Factor.Value);
				Factor.Type = 'Invoking';
				Factor.Value = NewInvoking;
				return ValueType(False, False, Invoking.Type, Invoking.Constant, Invoking.Value);
		elif Factor.Type == 'Indexing':
			Variable = self.FindIdentifier(Factor.Value, self.VariableTable);
			if Variable == None:
				if self.FindIdentifier(Factor.Value, self.ConstantTable):		raise LogicalError('Cannot index constants.');
				elif self.FindIdentifier(Factor.Value, self.FunctionTable):		raise LogicalError('Cannot index functions.');
				elif self.FindIdentifier(Factor.Value, self.ProcedureTable):	raise LogicalError('Cannot index procedures.');
				else: raise LogicalError('Identifier "%s" used but never declared.' % Factor.Value);
			VariableType = Variable.Type.Type;
			for I in range(len(Factor.Indexer)):
				if VariableType == 'String':
					VariableType = 'Char';
				elif VariableType not in self.Types:
					VariableType = VariableType.Type;
				else:
					raise LogicalError('Cannot index regular variables');
				Expression = self.AnalyzeExpression(Factor.Indexer[I]);
				if Expression.Array:
					raise LogicalError('Array itself cannot be computed directly.');
				if Expression.Type != 'Integer':
					Factor.Indexer[I] = self.ConvertExpression(Factor.Indexer[I], Expression.Type, 'Integer');
			return ValueType(True, VariableType not in self.Types, VariableType, False, None);

	def AnalyzeTerm(self, Term):
		Factors = [];
		ForceReal = False;
		Factor1 = self.AnalyzeFactor(Term.Factor);
		MaxType = Factor1.Type;
		for Operator, Factor in Term.Factors:
			if Operator == '/':
				ForceReal = True;
			Factor2 = self.AnalyzeFactor(Factor);
			Factor1.Array |= Factor2.Array;
			Factor1.Constant &= Factor2.Constant;
			Factor1.SingleVar &= Factor2.SingleVar;
			NewMaxType = self.GetMaxType(MaxType, Factor2.Type);
			if NewMaxType == None:
				raise LogicalError('Implicit conversion from "%s" to "%s" is unsupported.' % (Factor2.Type, MaxType));
			MaxType = NewMaxType;
			Factors.append(Factor2);
			if Factor1.Array:
				raise LogicalError('Array itself cannot be computed directly.');
			if MaxType in ['Char', 'String'] or \
			   (Operator != 'And' and MaxType == 'Boolean') or \
			   (Operator == 'And' and MaxType not in ['Boolean', 'Integer']) or \
			   (Operator in ['Div', 'Mod', 'Shl', 'Shr'] and MaxType != 'Integer'):
				raise LogicalError('"%s" operation is not defined with "%s".' % (Operator, MaxType));
		if ForceReal:
			NewMaxType = self.GetMaxType('Real', MaxType);
			if NewMaxType == None:
				raise LogicalError('Implicit conversion from "Real" to "%s" is unsupported.' % MaxType);
			MaxType = NewMaxType;
		if not Factor1.Constant:
			Term.Factor = self.ConvertFactor(Term.Factor, Factor1.Type, MaxType);
			for I in range(len(Term.Factors)):
				Term.Factors[I] = (Term.Factors[I][0], \
					self.ConvertFactor(Term.Factors[I][1], Factors[I].Type, MaxType));
			return ValueType(Factor1.SingleVar, Factor1.Array, MaxType, False, None);
		else:
			Result = Factor1;
			for I in range(len(Term.Factors)):
				Result = ValueType(False, False, MaxType, True, \
					self.ApplyOperator(MaxType, Result, Term.Factors[I][0], Factors[I]));
			Term.Factors = [];
			Term.Factor = Parser.Factor();
			Term.Factor.Type = MaxType;
			Term.Factor.Value = Result.Value;
			return Result;

	def AnalyzeSimpleExpr(self, SimpleExpr):
		Terms = [];
		Term1 = self.AnalyzeTerm(SimpleExpr.Term);
		MaxType = Term1.Type;
		for Operator, Term in SimpleExpr.Terms:
			Term2 = self.AnalyzeTerm(Term);
			Term1.Array |= Term2.Array;
			Term1.Constant &= Term2.Constant;
			Term1.SingleVar &= Term2.SingleVar;
			NewMaxType = self.GetMaxType(Term2.Type, MaxType);
			if NewMaxType == None:
				raise LogicalError('Implicit conversion from "%s" to "%s" is unsupported.' % (Term2.Type, MaxType));
			Terms.append(Term2);
			MaxType = NewMaxType;
			if Term1.Array:
				raise LogicalError('Array itself cannot be computed directly.');
			if (Operator in '+-' and MaxType == 'Boolean') or \
			   (Operator != '+' and MaxType in ['Char', 'String']) or \
			   (Operator in ['Or', 'Xor'] and MaxType not in ['Boolean', 'Integer']):
				raise LogicalError('"%s" operation is not defined with "%s".' % (Operator, MaxType));
		if Term1.Constant:
			Result = Term1;
			for I in range(len(SimpleExpr.Terms)):
				Result = ValueType(False, False, MaxType, True, \
					self.ApplyOperator(MaxType, Result, SimpleExpr.Terms[I][0], Terms[I]));
			SimpleExpr.Terms = [];
			SimpleExpr.Term = Parser.Term();
			SimpleExpr.Term.Factor.Type = MaxType;
			SimpleExpr.Term.Factor.Value = Result.Value;
			return Result;
		else:
			if MaxType not in ['Char', 'String']:
				SimpleExpr.Term = self.ConvertTerm(SimpleExpr.Term, Term1.Type, MaxType);
				for I in range(len(SimpleExpr.Terms)):
					SimpleExpr.Terms[I] = (SimpleExpr.Terms[I][0], \
						self.ConvertTerm(SimpleExpr.Terms[I][1], Terms[I].Type, MaxType));
			elif len(SimpleExpr.Terms) > 0:
				MaxType = 'String';
				SimpleExpr.Term = self.BuildTerm('Concat', \
					self.ConvertTerm(SimpleExpr.Term, Term1.Type, 'String'), \
					self.ConvertTerm(SimpleExpr.Terms[0][1], Terms[0].Type, 'String'));
				for I in range(1, len(SimpleExpr.Terms)):
					SimpleExpr.Term = self.BuildTerm('Concat', SimpleExpr.Term, \
						self.ConvertTerm(SimpleExpr.Terms[I][1], Terms[I].Type, 'String'));
				SimpleExpr.Terms = [];
			return ValueType(Term1.SingleVar, Term1.Array, MaxType, False, None);

	def AnalyzeExpression(self, Expression):
		SimpleExpr1 = self.AnalyzeSimpleExpr(Expression.Operand1);
		if Expression.Operand2 != None:
			SimpleExpr2 = self.AnalyzeSimpleExpr(Expression.Operand2);
			SimpleExpr1.Array |= SimpleExpr2.Array;
			SimpleExpr1.Constant &= SimpleExpr2.Constant;
			SimpleExpr1.SingleVar &= SimpleExpr2.SingleVar;
			if SimpleExpr1.Array:
				raise LogicalError('Array itself cannot be computed directly.');
			MaxType = self.GetMaxType(SimpleExpr1.Type, SimpleExpr2.Type);
			if MaxType == None:
				raise LogicalError('Type "%s" and "%s" are incompatiable.' % (SimpleExpr1.Type, SimpleExpr2.Type));
			if not SimpleExpr1.Constant:
				Expression.Operand1 = self.ConvertSimpleExpr(Expression.Operand1, SimpleExpr1.Type, MaxType);
				Expression.Operand2 = self.ConvertSimpleExpr(Expression.Operand2, SimpleExpr2.Type, MaxType);
				return ValueType(SimpleExpr1.SingleVar, False, 'Boolean', False, None);
			else:
				Expression.Operator = None;
				Expression.Operand2 = None;
				Expression.Operand1 = Parser.SimpleExpr();
				Expression.Operand1.Term.Factor.Type = MaxType;
				Expression.Operand1.Term.Factor.Value = self.ApplyOperator(MaxType, SimpleExpr1, Expression.Operator, SimpleExpr2);
				return ValueType(False, False, MaxType, True, Expression.Operand1.Term.Factor.Value);
		return SimpleExpr1;

	def AnalyzeIf(self, If):
		Expression = self.AnalyzeExpression(If.Expression);
		if Expression.Array:
			raise LogicalError('Array itself cannot be computed directly.');
		if Expression.Type != 'Boolean':
			raise LogicalError('Condition should be Boolean expression.');
		self.AnalyzeStatement(If.TrueStatement);
		if If.FalseStatement != None:
			self.AnalyzeStatement(If.FalseStatement);

	def AnalyzeFor(self, For):
		if For.Init.Indexer != None:
			raise LogicalError('Array cannot be as loop control variable.');
		InitType = self.AnalyzeAssignment(For.Init);
		Expression = self.AnalyzeExpression(For.Stop);
		if Expression.Array:
			raise LogicalError('Array itself cannot be computed directly.');
		if InitType != 'Integer' or Expression.Type != 'Integer':
			raise LogicalError('For-loop boundary type must be integer.');
		self.AnalyzeStatement(For.Statement);

	def AnalyzeCase(self, Case):
		Expression = self.AnalyzeExpression(Case.Expression);
		if Expression.Array:
			raise LogicalError('Array itself cannot be computed directly.');
		if Expression != Case.ConstantType:
			if Expression.Type in ['Char', 'Integer']:
				raise LogicalError('Case expression type inconsistant');
			else:
				raise LogicalError('Case expression should be ordinal type.');
		for Key in Case.Statements:
			self.AnalyzeStatement(Case.Statements[Key]);
		if Case.DefaultStatement != None:
			self.AnalyzeStatement(Case.DefaultStatement);

	def AnalyzeWhile(self, While):
		Expression = self.AnalyzeExpression(While.Expression);
		if Expression.Array:
			raise LogicalError('Array itself cannot be computed directly.');
		if Expression.Type != 'Boolean':
			raise LogicalError('Condition should be Boolean expression.');
		self.AnalyzeStatement(While.Statement);

	def AnalyzeRepeat(self, Repeat):
		for Item in Repeat.Statements:
			self.AnalyzeStatement(Item);
		Expression = self.AnalyzeExpression(Repeat.Expression);
		if Expression.Array:
			raise LogicalError('Array itself cannot be computed directly.');
		if Expression.Type != 'Boolean':
			raise LogicalError('Condition should be Boolean expression.');

	def AnalyzeInvoking(self, Invoking):
		if Invoking.Name in self.Types:
			if len(Invoking.Parameters) != 1:
				raise LogicalError('Type-cast takes exactly 1 argument(s), %d given.' % len(Invoking.Parameters));
			Expression = self.AnalyzeExpression(Invoking.Parameters[0]);
			if Expression.Array:
				raise LogicalError;('Invalid type-cast from "Array" to "%s".' % Invoking.Name);
			if not self.CheckCast(Expression.Type, Invoking.Name):
				raise LogicalError('Invalid type-cast from "%s" to "%s".' % (Expression.Type, Invoking.Name));
			if not Expression.Constant:
				return InvokingType(Invoking.Name, False, None);
			else:
				return InvokingType(Invoking.Name, True, \
					self.InvokingResultCast(Expression.Type, Invoking.Name, Expression.Value));
		elif Invoking.Name.lower() in self.Builtins.keys():
			Builtin = self.Builtins[Invoking.Name.lower()];
			if isinstance(Builtin['Params'], int):
				if len(Invoking.Parameters) < Builtin['Params']:
					raise LogicalError('Built-in "%s" requires at least %d parameter(s).' % (Invoking.Name, Builtin['Params']));
				for Parameter in Invoking.Parameters:
					Expression = self.AnalyzeExpression(Parameter);
					if Expression.Array:
						raise LogicalError('Array itself cannot be passed as parameters.');
					if Builtin['Variable'] and not Expression.SingleVar:
						raise LogicalError('Variable required for passing variable formal parameter.');
					if Builtin['ForbiddenTypes'] != None and Expression.Type in Builtin['ForbiddenTypes']:
						raise LogicalError('"%s" is not allowed be passed to "%s".' % (Expression.Type, Invoking.Name));
			else:
				TypeText = 'Procedure' if Builtin['ReturnType'] == None else 'Function';
				if len(Builtin['Params']) != len(Invoking.Parameters):
					raise LogicalError('%s "%s" takes exactly %d argument(s), %d given.' %
						(TypeText, Invoking.Name, len(Builtin['Params']), len(Invoking.Parameters)));
				for I in range(len(Builtin['Params'])):
					Expression = self.AnalyzeExpression(Invoking.Parameters[I]);
					if Expression.Array:
						raise LogicalError('Array itself cannot be passed as variable parameters.');
					if not Builtin['Variable'][I]:
						if Expression.Type != Builtin['Params'][I]:
							Invoking.Parameters[I] = self.ConvertExpression(\
								Invoking.Parameters[I], Expression.Type, Builtin['Params'][I]);
					else:
						if not Expression.SingleVar:
							raise LogicalError('Variable required for passing variable formal parameter.');
						if Expression.Type != Builtin['Params'][I]:
							raise LogicalError('Actual parameters are inconsistant with formal parameters.');
			return InvokingType(Builtin['ReturnType'], False, None);
		else:
			Invokable = self.FindIdentifier(Invoking.Name, self.FunctionTable);
			if Invokable != None:
				TypeText = 'Function';
				ReturnType = Invokable.ReturnType;
			else:
				ReturnType = None;
				TypeText = 'Procedure';
				Invokable = self.FindIdentifier(Invoking.Name, self.ProcedureTable);
				if Invokable == None:
					if self.FindIdentifier(Invoking.Name, self.ConstantTable): raise LogicalError('Constants are not callable.');
					elif self.FindIdentifier(Invoking.Name, self.VariableTable): raise LogicalError('Variables are not callable.');
					else: raise LogicalError('Identifier "%s" used but never declared.' % Invoking.Name);
			ActualParameters = [];
			for Expression in Invoking.Parameters:
				ActualParameters.append(self.AnalyzeExpression(Expression));
			if len(ActualParameters) != len(Invokable.ParameterMap):
				raise LogicalError('%s "%s" takes exactly %d argument(s), %d given.' % \
					(TypeText, Invoking.Name, len(Invokable.ParameterMap), len(ActualParameters)));
			for I in range(len(ActualParameters)):
				ActualParameter = ActualParameters[I];
				FormalParameter = Invokable.ParameterMap[I];
				if FormalParameter['Array']:
					if not ActualParameter.Array or (FormalParameter['Type'] != ActualParameter.Type):
						raise LogicalError('Actual parameters are inconsistant with formal parameters.');
				else:
					if ActualParameter.Array:
						raise LogicalError('Actual parameters are inconsistant with formal parameters.');
					elif not FormalParameter['Variable']:
						if FormalParameter['Type'] != ActualParameter.Type:
							Invoking.Parameters[I] = self.ConvertExpression(\
								Invoking.Parameters[I], ActualParameter.Type, FormalParameter['Type']);
					elif not ActualParameter.SingleVar:
						raise LogicalError('Variable required for variable formal parameter.');
					elif FormalParameter['Type'] != ActualParameter.Type:
						raise LogicalError('Actual parameters are inconsistant with formal parameters.');
			return InvokingType(ReturnType, False, None);

	def AnalyzeAssignment(self, Assignment):
		Text = 'assign to' if Assignment.Indexer == None else 'index';
		Target = self.FindIdentifier(Assignment.Target, self.VariableTable);
		if Target == None:
			if self.FindIdentifier(Assignment.Target, self.ConstantTable): raise LogicalError('Cannot %s constants.', Text);
			elif self.FindIdentifier(Assignment.Target, self.FunctionTable): raise LogicalError('Cannot %s functions.', Text);
			elif self.FindIdentifier(Assignment.Target, self.ProcedureTable): raise LogicalError('Cannot %s procedures.', Text);
			else: raise LogicalError('Identifier "%s" used but never declared.' % Assignment.Target);
		TargetType = Target.Type.Type;
		if Assignment.Indexer != None:
			for I in range(len(Assignment.Indexer)):
				if TargetType == 'String':
					TargetType = 'Char';
				elif TargetType not in self.Types:
					TargetType = TargetType.Type;
				else:
					raise LogicalError('Cannot index regular variables');
				Expression = self.AnalyzeExpression(Assignment.Indexer[I]);
				if Expression.Array:
					raise LogicalError('Array itself cannot be computed directly.');
				if Expression.Type != 'Integer':
					Assignment.Indexer[I] = self.ConvertExpression(Assignment.Indexer[I], Expression.Type, 'Integer');
		if TargetType not in self.Types:
			raise LogicalError('Array itself cannot be assigned directly.');
		Expression = self.AnalyzeExpression(Assignment.Expression);
		if Expression.Array:
			raise LogicalError('Array itself cannot be computed directly.');
		Assignment.Expression = self.ConvertExpression(Assignment.Expression, Expression.Type, TargetType);
		return TargetType;

	def AnalyzeStatement(self, Statement):
		if Statement.Type == 'If':				self.AnalyzeIf(Statement.Statement);
		elif Statement.Type == 'For':			self.AnalyzeFor(Statement.Statement);
		elif Statement.Type == 'Case':			self.AnalyzeCase(Statement.Statement);
		elif Statement.Type == 'While':			self.AnalyzeWhile(Statement.Statement);
		elif Statement.Type == 'Repeat':		self.AnalyzeRepeat(Statement.Statement);
		elif Statement.Type == 'Invoking':		self.AnalyzeInvoking(Statement.Statement);
		elif Statement.Type == 'Assignment':	self.AnalyzeAssignment(Statement.Statement);
		elif Statement.Type == 'Block':			self.AnalyzeStatements(Statement.Statement);

	def AnalyzeDeclarations(self, Declarations):
		StripTable = [];
		for Type, Item in Declarations.Declarations:
			if Type == 'Function':		self.AnalyzeFunction(Item);
			elif Type == 'Procedure':	self.AnalyzeProcedure(Item);
			elif Type == 'Constant':
				StripTable.append((Type, Item));
				self.AddConstant(Item.Name, Item.Type, Item.Value);
			elif Type == 'Variable':
				if Item.Type.Array:
					IndexType = Item.Type;
					while IndexType.Array:
						ArrayLow = self.AnalyzeExpression(IndexType.ArrayLow);
						ArrayHigh = self.AnalyzeExpression(IndexType.ArrayHigh);
						if not ArrayLow.Constant or not ArrayHigh.Constant:
							raise LogicalError('Array bound should be constant expression.');
						if ArrayLow.Type != 'Integer' or ArrayHigh.Type != 'Integer':
							raise LogicalError('Array bound should be integer constant expression.');
						if ArrayLow.Value > ArrayHigh.Value:
							raise LogicalError('Array upper bound should greater than lower bound.');
						IndexType.ArrayLow = ArrayLow.Value;
						IndexType.ArrayHigh = ArrayHigh.Value;
						IndexType = IndexType.Type;
				self.AddVariables(Item.Names, Item.Type);
		for Item in StripTable:
			Declarations.Declarations.remove(Item);

	def AnalyzeStatements(self, Statements):
		for Statement in Statements.Statements:
			self.AnalyzeStatement(Statement);

	def Analyze(self):
		self.AnalyzeDeclarations(self.Program.Declarations);
		self.AnalyzeStatements(self.Program.Statements);
