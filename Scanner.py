'''
	Created on 2013-1-24

	@author: desperedo

	miniPascal Compiler Scanner/Lexer
'''

NUMBER_CONSTANT = '0123456789';
HEX_NUMBER_CONSTANT = '0123456789abcdef';
IDENTIFIER_CONSTANT = '_abcdefghijklmnopqrstuvwxyz';

class LexicalError(Exception): pass

class Scanner(object):
	def __init__(self, Source):
		self.Index = 0;
		self.Source = Source;

		self.CacheIndex = 0;
		self.CachedToken = [];

		self.Types = {};
		self.Operators = {};
		self.ReservedWords = {};

		self.Types['char'] = 'Char';
		self.Types['real'] = 'Real';
		self.Types['string'] = 'String';
		self.Types['boolean'] = 'Boolean';
		self.Types['integer'] = 'Integer';

		self.Operators['or'] = 'Or';
		self.Operators['and'] = 'And';
		self.Operators['not'] = 'Not';
		self.Operators['xor'] = 'Xor';
		self.Operators['shl'] = 'Shl';
		self.Operators['shr'] = 'Shr';
		self.Operators['div'] = 'Div';
		self.Operators['mod'] = 'Mod';

		self.ReservedWords['program'] = 'Program';
		self.ReservedWords['function'] = 'Function';
		self.ReservedWords['procedure'] = 'Procedure';
		self.ReservedWords['forward'] = 'Forward';

		self.ReservedWords['begin'] = 'Begin';
		self.ReservedWords['end'] = 'End';

		self.ReservedWords['of'] = 'Of';
		self.ReservedWords['var'] = 'Var';
		self.ReservedWords['array'] = 'Array';
		self.ReservedWords['const'] = 'Const';

		self.ReservedWords['if'] = 'If';
		self.ReservedWords['then'] = 'Then';
		self.ReservedWords['else'] = 'Else';
		self.ReservedWords['case'] = 'Case';
		self.ReservedWords['for'] = 'For';
		self.ReservedWords['to'] = 'To';
		self.ReservedWords['downto'] = 'DownTo';
		self.ReservedWords['do'] = 'Do';
		self.ReservedWords['while'] = 'While';
		self.ReservedWords['repeat'] = 'Repeat';
		self.ReservedWords['until'] = 'Until';

	def Unget(self):
		self.Index -= 1;

	def GetChar(self):
		return '\0' if self.Index >= len(self.Source) else self.Source[self.Index];

	def NextChar(self):
		if self.Index >= len(self.Source):
			return '\0';
		else:
			self.Index += 1;
			return self.Source[self.Index - 1];

	def SkipSpaces(self):
		while self.GetChar() in ' \t\r\n':
			self.NextChar();

	def GetCharLiteral(self):
		Char = self.NextChar();
		if Char != '$' and Char not in NUMBER_CONSTANT:
			return None;
		else:
			Token, Value = self.ProcessNumber(Char);
			return chr(Value) if Token == 'Integer' else None;

	def ProcessNumber(self, Char):
		String = '';
		if Char == '$':
			Char = self.NextChar().lower();
			if Char not in HEX_NUMBER_CONSTANT:
				self.Unget();
				raise LexicalError('Illegal character "$".');
			while Char in HEX_NUMBER_CONSTANT:
				String += Char;
				Char = self.NextChar().lower();
			self.Unget();
			return 'Integer', int(String, 16);
		else:
			IsFloat = False;
			while Char in NUMBER_CONSTANT or (not IsFloat and Char == '.'):
				if Char == '.':
					IsFloat = True;
					if self.GetChar() == '.':
						IsFloat = False;
						break;
				String += Char;
				Char = self.NextChar();
			self.Unget();
			if String.endswith('.'):
				raise LexicalError('Illegal character ".".');
			if IsFloat:
				return 'Real', float(String);
			else:
				return 'Integer', int(String, 10);

	def ProcessString(self, Char):
		Value = '';
		while Char == '#' or Char == "'":
			if Char == '#':
				Char = self.GetCharLiteral();
				if Char == None:
					raise LexicalError('Invalid ASCII character literal.');
				Value += Char;
				Char = self.NextChar();
			else:
				Char = self.NextChar();
				if Char == '\0':
					raise LexicalError('Unterminated string literal.');
				while Char != "'":
					Value += Char;
					Char = self.NextChar();
					if Char == '\0':
						raise LexicalError('Unterminated string literal.');
				Char = self.NextChar();
				if Char == "'":
					Value += "'";
		self.Unget();
		if len(Value) == 1:
			return 'Char', Value;
		else:
			return 'String', Value;

	def ProcessComment(self, Char):
		if Char == '/':
			Char = self.NextChar();
			while Char not in '\0\r\n':
				Char = self.NextChar();
		if Char == '{':
			Char = self.NextChar();
			while Char != '}':
				if Char == '\0':
					raise LexicalError('Unterminated comment.');
				Char = self.NextChar();
		if Char == '(':
			self.NextChar();
			Char = self.NextChar();
			Next = self.NextChar();
			while Char != '*' or Next != ')':
				if Char == '\0' or Next == '\0':
					raise LexicalError('Unterminated comment.');
				Char = Next;
				Next = self.NextChar();
		return 'Comment', None;

	def ProcessOperator(self, Char):
		if Char in '+-*=;,)[]':
			return Char, None;
		elif Char == '{':
			return self.ProcessComment(Char);
		elif Char == '.':
			if self.GetChar() != '.':
				return '.', None;
			else:
				self.NextChar();
				return '..', None;
		elif Char == ':':
			if self.GetChar() != '=':
				return ':', None;
			else:
				self.NextChar();
				return ':=', None;
		elif Char == '>':
			if self.GetChar() != '=':
				return '>', None;
			else:
				self.NextChar();
				return '>=', None;
		elif Char == '/':
			if self.GetChar() != '/':
				return '/', None;
			else:
				return self.ProcessComment(Char);
		elif Char == '(':
			if self.GetChar() != '*':
				return '(', None;
			else:
				return self.ProcessComment(Char);
		elif Char == '<':
			if self.GetChar() == '=':
				self.NextChar();
				return '<=', None;
			elif self.GetChar() == '>':
				self.NextChar();
				return '<>', None;
			else:
				return '<', None;
		else:
			raise LexicalError('Illegal character "%c".' % Char);

	def ProcessIdentifier(self, Char):
		Identifier = '';
		while Char.lower() in NUMBER_CONSTANT or Char.lower() in IDENTIFIER_CONSTANT:
			Identifier += Char;
			Char = self.NextChar();
		self.Unget();
		if Identifier.lower() == 'true':						return 'Boolean', True;
		elif Identifier.lower() == 'false':						return 'Boolean', False;
		elif Identifier.lower() in self.Types.keys():			return 'Type', self.Types[Identifier.lower()];
		elif Identifier.lower() in self.Operators.keys():		return self.Operators[Identifier.lower()], None;
		elif Identifier.lower() in self.ReservedWords.keys():	return self.ReservedWords[Identifier.lower()], None;
		else:													return 'Identifier', Identifier;

	def ScanToken(self):
		self.SkipSpaces();
		Char = self.NextChar();
		if Char == '\0':								return None, None;
		elif Char == '#' or Char == "'":				return self.ProcessString(Char);
		elif Char == '$' or Char in NUMBER_CONSTANT:	return self.ProcessNumber(Char);
		elif Char.lower() in IDENTIFIER_CONSTANT:		return self.ProcessIdentifier(Char);
		else:											return self.ProcessOperator(Char);

	def NextToken(self):
		if self.CacheIndex < len(self.CachedToken):
			self.CacheIndex += 1;
			return self.CachedToken[self.CacheIndex - 1];
		else:
			Token, Value = self.ScanToken();
			while Token == 'Comment':
				Token, Value = self.ScanToken();
			self.CacheIndex += 1;
			self.CachedToken.append((Token, Value));
			return Token, Value;

	def PeekToken(self, SkipCount = 0):
		CacheIndex = self.CacheIndex;
		while SkipCount > 0:
			SkipCount -= 1;
			self.NextToken();
		Token, Value = self.NextToken();
		self.CacheIndex = CacheIndex;
		return Token, Value;

	def TokenNeeded(self, Token):
		return self.NextToken()[0] == Token;

	def TokenExpected(self, Token, SkipCount = 0):
		return self.PeekToken(SkipCount)[0] == Token;

	def TokensExpected(self, Tokens, SkipCount = 0):
		return self.PeekToken(SkipCount)[0] in Tokens;
