'''
	Created on 2013-2-3

	@author: desperedo

	miniPascal Compiler AST Dumper
'''

LineNo = 1;

def Output(Level, Text):
	global LineNo;
	print(('%3d ' % LineNo) + ('\x1b[34m|\x1b[0m   ' * Level) + Text);
	LineNo += 1;

def GetTypeString(Type):
	if not Type.Array:
		return Type.Type;
	else:
		return ('Array [%d..%d] of ' % (Type.ArrayLow, Type.ArrayHigh)) + GetTypeString(Type.Type);

def DumpConstant(Constant, Level):
	Output(Level, 'Constant %s: %s = %s' % (Constant.Name, GetTypeString(Constant.Type), str(Constant.Value)));

def DumpVariable(Variable, Level, Parameter = False):
	for Name in Variable.Names:
		Output(Level, \
			('Variable "%s' + ('": *' if Parameter and Variable.Variable else '": ') + "%s") % \
			(Name, GetTypeString(Variable.Type)));

def DumpFunction(Function, Level):
	if not Function.Forward:
		Output(Level, 'Function "%s": "%s"' % (Function.Name, GetTypeString(Function.ReturnType)));
		if len(Function.Parameters) > 0:
			Output(Level + 1, 'Parameters:');
		for Parameter in Function.Parameters:
			DumpVariable(Parameter, Level + 2, True);
		DumpDeclarations(Function.Declarations, Level);
		DumpStatements(Function.Statements, Level);

def DumpProcedure(Procedure, Level):
	if not Procedure.Forward:
		Output(Level, 'Procedure "%s"' % Procedure.Name);
		if len(Procedure.Parameters) > 0:
			Output(Level + 1, 'Parameters:');
		for Parameter in Procedure.Parameters:
			DumpVariable(Parameter, Level + 2, True);
		DumpDeclarations(Procedure.Declarations, Level);
		DumpStatements(Procedure.Statements, Level);

def DumpFactor(Factor, Level):
	Output(Level, 'Factor:');
	if Factor.Type == 'Invoking':
		DumpInvoking(Factor.Value, Level + 1);
	elif Factor.Type == 'Expression':
		DumpExpression(Factor.Value, Level + 1);
	elif Factor.Type == 'Factor':
		Output(Level + 1, 'Prefix "%s"' % Factor.Prefix);
		DumpFactor(Factor.Value, Level + 1);
	elif Factor.Type == 'Indexing':
		Output(Level + 1, '"%s" indexed:' % Factor.Value);
		for Indexer in Factor.Indexer:
			DumpExpression(Indexer, Level + 2);
	else:
		Output(Level + 1, '"%s" typed "%s".' % (Factor.Value, Factor.Type));

def DumpTerm(Term, Level):
	Output(Level, 'Term:');
	DumpFactor(Term.Factor, Level + 1);
	for Factor in Term.Factors:
		Output(Level + 1, 'Operator "%s"' % Factor[0]);
		DumpFactor(Factor[1], Level + 1);

def DumpSimpleExpr(SimpleExpr, Level):
	Output(Level, 'Simple Expression:');
	DumpTerm(SimpleExpr.Term, Level + 1);
	for Term in SimpleExpr.Terms:
		Output(Level + 1, 'Operator "%s"' % Term[0]);
		DumpTerm(Term[1], Level + 1);

def DumpExpression(Expression, Level):
	Output(Level, 'Expression:');
	DumpSimpleExpr(Expression.Operand1, Level + 1);
	if Expression.Operator != None and Expression.Operand2 != None:
		Output(Level + 1, 'Operator "%s"' % Expression.Operator);
		DumpSimpleExpr(Expression.Operand2, Level + 1);

def DumpIf(If, Level):
	Output(Level, 'If:');
	DumpExpression(If.Expression, Level + 1);
	Output(Level, 'Then');
	DumpStatement(If.TrueStatement, Level + 1);
	if If.FalseStatement != None:
		Output(Level, 'Else');
		DumpStatement(If.FalseStatement, Level + 1);

def DumpFor(For, Level):
	Output(Level, 'For');
	Output(Level + 1, 'Initial:');
	DumpAssignment(For.Init, Level + 2);
	Output(Level + 1, 'Stop Value:');
	DumpExpression(For.Stop, Level + 2);
	DumpStatement(For.Statement, Level + 1);

def DumpCase(Case, Level):
	Output(Level, 'Case in "%s" Expression:' % Case.ConstantType);
	DumpExpression(Case.Expression, Level + 1);
	for Key in Case.Statements:
		Output(Level + 1, 'Item "%s":' % str(Key));
		DumpStatement(Case.Statements[Key], Level + 2);
	if Case.DefaultStatement != None:
		Output(Level + 1, 'Default:');
		DumpStatement(Case.DefaultStatement, Level + 2);

def DumpWhile(While, Level):
	Output(Level, 'While:');
	DumpExpression(While.Expression, Level + 1);
	Output(Level + 1, 'Do');
	DumpStatement(While.Statement, Level + 2);

def DumpRepeat(Repeat, Level):
	Output(Level, 'Repeat');
	for Statement in Repeat.Statements:
		DumpStatement(Statement, Level + 1);
	Output(Level, 'Until:');
	DumpExpression(Repeat.Expression, Level + 1);

def DumpInvoking(Invoking, Level):
	Index = 0;
	Output(Level, 'Invoking "%s"' % Invoking.Name);
	for Parameter in Invoking.Parameters:
		Index += 1;
		Output(Level + 1, 'Parameter %d:' % Index);
		DumpExpression(Parameter, Level + 2);

def DumpAssignment(Assignment, Level):
	Output(Level, 'Assignment to "%s"' % Assignment.Target);
	if Assignment.Indexer != None:
		Output(Level + 1, 'Indexers:');
		for Indexer in Assignment.Indexer:
			DumpExpression(Indexer, Level + 2);
	DumpExpression(Assignment.Expression, Level + 1);

def DumpStatement(Statement, Level):
	if Statement.Type == 'If':				DumpIf(Statement.Statement, Level);
	elif Statement.Type == 'For':			DumpFor(Statement.Statement, Level);
	elif Statement.Type == 'Case':			DumpCase(Statement.Statement, Level);
	elif Statement.Type == 'While':			DumpWhile(Statement.Statement, Level);
	elif Statement.Type == 'Repeat':		DumpRepeat(Statement.Statement, Level);
	elif Statement.Type == 'Invoking':		DumpInvoking(Statement.Statement, Level);
	elif Statement.Type == 'Assignment':	DumpAssignment(Statement.Statement, Level);
	elif Statement.Type == 'Block':			DumpStatements(Statement.Statement, Level);

def DumpDeclarations(Declarations, Level):
	for Type, Item in Declarations.Declarations:
		if Type == 'Constant':		DumpConstant(Item, Level + 1);
		elif Type == 'Variable':	DumpVariable(Item, Level + 1);
		elif Type == 'Function':	DumpFunction(Item, Level + 1);
		elif Type == 'Procedure':	DumpProcedure(Item, Level + 1);

def DumpStatements(Statements, Level):
	Output(Level, 'Begin');
	for Statement in Statements.Statements:
		DumpStatement(Statement, Level + 1);
	Output(Level, 'End');

def DumpProgram(Program):
	Output(0, 'program "%s"' % Program.Name);
	DumpDeclarations(Program.Declarations, 0);
	DumpStatements(Program.Statements, 0);
