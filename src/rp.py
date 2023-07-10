#!/usr/bin/python3
from decimal import *
import math

# Token types : T_xxx
NUMBER 		= 0
MINUS		= 1		# op
PLUS		= 2		# op
DIV			= 3		# op
MUL			= 4		# op
POW			= 5		# op
FACT		= 6		# op
MOD			= 7		# op
LPAREN		= 8
RPAREN		= 9
COMMA		= 10	# functor expr separator
CSTR		= 11	# functor / constant
ILLEGAL		= 12	# not yet implemented ... -> error
EOF			= 13

# extra:
A2R			= 0.017453293	# x * (pi/180)
R2A			= 57.295779513	# x * (180/pi)

class Token(object):
	__slots__ = ['type', 'value']

	def __init__(self, type, value):
		self.type = type
		self.value = value

	def __str__(self):
		return 'Token({type}, {value})'.format(
			type=self.type,
			value=repr(self.value)
		)

	def __repr__(self):
		return self.__str__()

class Lexer(object):
	__slots__ = ['text', 'pos', 'current_char']
	def __init__(self, text):
		self.text = text
		self.pos = 0 # index into text
		self.current_char = self.text[self.pos]
		# self.illegals = 0
	def advance(self):
		self.pos += 1
		if self.pos > len(self.text) - 1:
			self.current_char = None # eof -> '\0' is a better check.
		else:
			self.current_char = self.text[self.pos]
	def skip_whitespace(self):
		while self.current_char is not None and self.current_char.isspace():
			self.advance()
	def number(self):
		# allow for INT, FLOAT and SPI-NUMBER
		result = ''
		dots = False
		es = False
		while self.current_char is not None:
			if self.current_char.isdigit() == False:
				if self.current_char == '.' and dots == False and es == False:
					dots = True
				elif self.current_char in ('e', 'E') and es == False:
					es = True
				else:
					break

			result += self.current_char
			self.advance()
		return result
	def cstr(self):
		result = ''
		while self.current_char is not None:
			if (self.current_char.isalpha() == False and self.current_char.isdigit() == False):
				break
			result += self.current_char
			self.advance()
		return result

	def get_next_token(self):
		while self.current_char is not None:

			if self.current_char.isspace():
				self.skip_whitespace()
				continue

			if self.current_char.isdigit() or self.current_char == '.':
				return Token(NUMBER, Decimal(self.number()))

			if self.current_char == '+':
				self.advance()
				return Token(PLUS, '+')

			if self.current_char == '-':
				self.advance()
				return Token(MINUS, '-')

			if self.current_char == '*':
				self.advance()
				return Token(MUL, '*')

			if self.current_char == '/':
				self.advance()
				return Token(DIV, '/')

			if self.current_char == '^':
				self.advance()
				return Token(POW, '^')

			if self.current_char == '!':
				self.advance()
				return Token(FACT, '!')

			if self.current_char == '%':
				self.advance()
				return Token(MOD, '%')

			if self.current_char == '(':
				self.advance()
				return Token(LPAREN, '(')

			if self.current_char == ')':
				self.advance()
				return Token(RPAREN, ')')

			if self.current_char == ',':
				self.advance()
				return Token(COMMA, ',')

			if self.current_char == '√':
				self.advance()
				return Token(CSTR, '√')

			# read cstr:
			# if isletter(self.current_char):
			# .isalpha is not the correct function for this check.
			if self.current_char.isalpha():
				return Token(CSTR, self.cstr())

			# self.illegals += 1
			return Token(ILLEGAL, '?')
		return Token(EOF, '\0')

class AST(object):
	pass

class FunCall(AST):
	__slots__ = ['token', 'fun', 'data']
	def __init__(self, fun, data = None):
		self.token = self.fun = fun
		self.data = data if data is not None else []

# unary
class PostOp(AST):
	__slots__ = ['token', 'op', 'left']
	def __init__(self, left, op):
		self.left = left
		self.token = self.op = op

class BinOp(AST):
	__slots__ = ['token', 'op', 'left', 'right']
	def __init__(self, left, op, right):
		self.left = left
		self.token = self.op = op
		self.right = right

class Num(AST):
	__slots__ = ['token', 'value']
	def __init__(self, token):
		self.token = token
		self.value = token.value

class Parser(object):
	__slots__ = ['lexer', 'current_token']
	def __init__(self, lexer):
		self.lexer = lexer
		# set current token to the first token taken from the input
		self.current_token = self.lexer.get_next_token()
	def eat(self, token_type):
		if self.current_token.type == token_type:
			self.current_token = self.lexer.get_next_token()
		else:
			print("# eat error")
			self.current_token = Token(EOF, '\0')

	# func:
	# CSTR LPAREN expr RPAREN
	# CSTR LPAREN expr COMMA expr RPAREN
	def factor(self):
		"""factor : NUMBER | LPAREN expr RPAREN | factor FACT | (MINUS, PLUS) factor """
		token = self.current_token
		node = None # issue
		if token.type == NUMBER:
			self.eat(NUMBER)
			node = Num(token)
		elif token.type == LPAREN:
			self.eat(LPAREN)

			# remove empty ()
			if self.current_token.type == RPAREN:
				self.eat(RPAREN)
				return self.factor()

			node = self.expr()
			self.eat(RPAREN)
		elif token.type in (MINUS, PLUS):
			self.eat(token.type)
			node = PostOp(left=self.factor(), op=token)
		elif token.type == CSTR:
			cstr_data = []
			self.eat(CSTR)

			# for named constants like pi
			if self.current_token.type != LPAREN:
				node = FunCall(fun=token, data=cstr_data)
				return node

			self.eat(LPAREN)
			while self.current_token.type != RPAREN:
				node2 = self.expr()
				cstr_data.append(node2)
				if self.current_token.type == COMMA:
					self.eat(COMMA)
			self.eat(RPAREN)

			node = FunCall(fun=token, data=cstr_data)

		# check for !
		while self.current_token.type == FACT:
			# print("factor : op fact")
			self.eat(FACT)
			node = PostOp(left=node, op=Token(FACT, '!'))

		# this being split will give us troubles later.
		if self.current_token.type == CSTR:
			token = self.current_token
			self.eat(CSTR)
			node2 = FunCall(fun=token, data=[])
			node = BinOp(left=node, op=Token(MUL, '*'), right=node2)

		return node
	def term(self):
		"""term : factor ((MUL | DIV | POW | MOD) factor)*"""
		node = self.factor()

		while self.current_token.type in (MUL, DIV, POW, MOD):
			token = self.current_token
			if token.type == MUL:
				self.eat(MUL)
			elif token.type == DIV:
				self.eat(DIV)
			elif token.type == POW:
				self.eat(POW)
			elif token.type == MOD:
				self.eat(MOD)

			node = BinOp(left=node, op=token, right=self.factor())

		return node
	def expr(self):
		"""
		expr	: term ((PLUS | MINUS) term)*
		term	: factor ((MUL | DIV | POW | MOD) factor)*
		factor	: NUMBER | LPAREN expr RPAREN |
				: factor FACT | (MINUS, PLUS) factor
		"""
		node = self.term()

		while self.current_token.type in (PLUS, MINUS):
			token = self.current_token
			if token.type == PLUS:
				self.eat(PLUS)
			elif token.type == MINUS:
				self.eat(MINUS)

			node = BinOp(left=node, op=token, right=self.term())

		return node
	def parse(self):
		return self.expr()

# auto function router
class NodeVisitor(object):
	def visit(self, node):
		method_name = 'visit_' + type(node).__name__
		visitor = getattr(self, method_name, self.generic_visit)
		return visitor(node)

	def generic_visit(self, node):
		raise Exception('No visit_{} method'.format(type(node).__name__))

class Interpreter(NodeVisitor):
	__slots__ = ['parser']
	def __init__(self, parser):
		self.parser = parser

	def visit_BinOp(self, node):
		# print("BinOp")
		lval = Decimal(self.visit(node.left))

		if node.op.type == FACT:
			if lval == lval.to_integral_value():
				return math.factorial(int(lval))
			else:
				return math.gamma(lval + 1)

		rval = Decimal(self.visit(node.right))

		if node.op.type == PLUS:
			return lval + rval
		elif node.op.type == MINUS:
			return lval - rval
		elif node.op.type == MUL:
			return lval * rval
		elif node.op.type == DIV:
			return lval / rval
		elif node.op.type == POW:
			return lval ** rval
		elif node.op.type == MOD:
			return lval % rval

	# more like a UnaryOp
	def visit_PostOp(self, node):
		# print("PostOp")
		val = self.visit(node.left)
		lval = Decimal(val)
		if node.op.type == FACT:
			if lval == lval.to_integral_value():
				return math.factorial(abs(int(lval)))
			else:
				return math.gamma(lval + 1)
		if node.op.type == MINUS:
			return -lval
		if node.op.type == PLUS:
			return +lval
		return val

	def visit_Num(self, node):
		# print("Num")
		return node.value

	def visit_NoneType(self, node):
		# print("Error")
		return 0

	def visit_FunCall(self, node):
		# print("funcall")
		if node.data == None:
			return None

		cstr = node.token.value
		data = []
		for n in node.data:
			data.append(self.visit(n))

		# this should be placed in something else. * visit_Constant *
		if len(data) >= 0:
			if cstr == "PI" or cstr == "pi" or cstr == "π":
				return math.pi
			if cstr == "TAU" or cstr == "tau" or cstr == "τ":
				return math.tau
			if cstr == "e" or cstr == "euler":
				return math.e

		# note: this only accepts lowercase tokens:
		if len(data) == 1:
			# TODO: clean it. this looks horrible.
			# we should just use the name-hash fnlut and a small lru cache.
			"""
			fn = fnlut[cstr]
			if fn is None:
				return 0
			return fn(data[0])
			"""

			# trigonometric
			if cstr == "sin":
				return math.sin(data[0])
			if cstr == "cos":
				return math.cos(data[0])
			if cstr == "tan":
				return math.tan(data[0])

			# inverse trigonometric
			if cstr == "asin":
				return math.asin(data[0])
			if cstr == "acos":
				return math.acos(data[0])
			if cstr == "atan":
				return math.atan(data[0])

			# hyperbolic trigonometric
			if cstr == "sinh":
				return math.sinh(data[0])
			if cstr == "cosh":
				return math.cosh(data[0])
			if cstr == "tanh":
				return math.tanh(data[0])
			if cstr == "asinh":
				return math.asinh(data[0])
			if cstr == "acosh":
				return math.acosh(data[0])
			if cstr == "atanh":
				return math.atanh(data[0])

			if cstr == "sqrt" or cstr == "√":
				return math.sqrt(data[0])

			# i√ is questionable...
			if cstr == "isqrt" or cstr == "i√":
				return math.isqrt(data[0])

			if cstr == "factorial" or cstr == "fact":
				if data[0] == data[0].to_integral_value():
					return math.factorial(abs(int(data[0])))
				else:
					return math.gamma(data[0] + 1)

			if cstr == "gamma" or cstr == "Γ":
				# should it be plus one? i think so.
				return math.gamma(data[0] + 1)

			if cstr == "log10":
				return math.log10(data[0])

			if cstr == "rad":
				return data[0] * Decimal(A2R)

			if cstr == "deg":
				return data[0] * Decimal(R2A)

		if len(data) >= 1:
			if cstr == "ln":
				return math.log(data[0])

			if cstr == "log":
				if len(data) == 1:
					return math.log10(data[0])
				if len(data) == 2:
					return math.log(data[0], data[1])

			if cstr == "max":
				return max(data)

			if cstr == "min":
				return min(data)

			if cstr == "sums":
				sums = 0
				for v in data:
					sums += v
				return sums

		if len(data) >= 2:
			if cstr == "atan2":
				return math.atan2(data[0], data[1])

			if cstr == "sum":
				l = data[0]
				r = data[1]
				if l > r:
					# input error
					return 0

				# note: could be using python stuff:
				# return sum(range(int(l), int(r) + 1))
				if l == l.to_integral_value():
					if l in (0, 1):
						return (r * (r + 1)) / 2

				# reg.naive:
				i = l
				while l <= r:
					# i += l++
					i += l
					l += 1
				return i
		return 0

	def interpret(self):
		tree = self.parser.parse()
		res = self.visit(tree)
		return res

# meat and potatoes:
def solve_text(text: str):
	# TODO: actually make each class compute on the whole set of tokens
	# and not run all through the interpreter as the same time we check parsing or lexing.
	lexer = Lexer(text)
	parser = Parser(lexer)
	interpreter = Interpreter(parser)
	"""
	# move down one
	if lexer.illegals > 0:
		# print("# input contains illegal characters")
		return None
	"""
	result = interpreter.interpret()

	# dont allow the result to be printed out in spi format
	if result != None:
		result = Decimal(result)
		if result == result.to_integral_value():
			result = int(result)

	return result

