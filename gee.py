import re
import sys
import string

debug = False
dict = {}
tokens = []


class Statement(object):
    def __init__(self, statement):
        self.statement = statement

    def __str__(self):
        return str(self.statement)+"\n"


class StatementList(object):
    def __init__(self, statements):
        self.statements = statements

    def __str__(self):
        res = ""
        for statement in self.statements:
            res += str(statement)
        return res


class Block(object):
    def __init__(self, statements):
        self.statements = statements

    def __str__(self):
        return str(self.statements)


class Assignment(object):
    def __init__(self, op, left, right, eoln=";"):
        self.op = op
        self.left = left
        self.right = right
        self.eoln = eoln

    def __str__(self):
        return str(self.left) + " " + str(self.op) + " " + str(self.right)+self.eoln

#  Expression class and its subclasses


class Expression(object):
    def __str__(self):
        return ""


class BinaryExpr(Expression):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __str__(self):
        return str(self.op) + " " + str(self.left) + " " + str(self.right)


class GeeString(Expression):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(f"Geestring: {self.value}")


class Identifier(Expression):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return str(self.name)


class Number(Expression):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class WhileStmt():
    def __init__(self, expression, innerblk):
        self.expression = expression
        self.innerblk = innerblk

    def __str__(self):
        return "while" + " " + str(self.expression) + "\n" + str(self.innerblk) + "endwhile"


class IfStmt():
    def __init__(self, expression, ifblk, elseblk=None):
        self.expression = expression
        self.ifblk = ifblk
        self.elseblk = elseblk

    def __str__(self):
        return "if" + " " + str(self.expression) + "\n" + str(self.ifblk) + str(self.elseblk) + "endif"


def error(msg):
    # print msg
    sys.exit(msg)

# The "parse" function. This builds a list of tokens from the input string,
# and then hands it to a recursive descent parser for the PAL grammar.


def match(matchtok):
    tok = tokens.peek()
    if (tok != matchtok):
        error("Expecting " + matchtok)
    tokens.next()
    return tok


def factor():
    """factor     = string | number |  '(' expression ')' """
    """           = |   identifier """
    tok = tokens.peek()
    pos = tokens.position
    # print(tokens, tok, tokens.position)
    if debug:
        print("Factor: ", tok)
    if tok is None:
        # error("None")
        return None
    if re.match(Lexer.string, tok):
        expr = GeeString(tok)
        tokens.next()
        return expr
    if re.match(Lexer.identifier, tok):
        expr = Identifier(tok)
        tokens.next()
        return expr
    if re.match(Lexer.number, tok):
        expr = Number(tok)
        tokens.next()
        return expr
    if tok == "(":
        tokens.next()  # or match( tok )
        expr = expression()
        tokens.peek()
        tok = match(")")
        return expr
    tokens.position = pos
    return None


def term():
    """ term    = factor { ('*' | '/') factor } """

    tok = tokens.peek()
    pos = tokens.position
    if debug:
        print("Term: ", tok)
    left = factor()
    tok = tokens.peek()
    while tok == Lexer.mul or tok == Lexer.div:
        tokens.next()
        right = factor()
        left = BinaryExpr(tok, left, right)
        tok = tokens.peek()
    if left is None:
        tokens.position = pos
        # error("None")
        return None
    return left


def expression():
    """ expression = andExpr { "or" andExpr } """
    pos = tokens.position
    tok = tokens.peek()
    if debug:
        print("expression:", tok)
    left = andExpr()
    tok = tokens.peek()
    while tok == Lexer.token_or:
        tokens.next()
        right = andExpr()
        left = BinaryExpr(tok, left, right)
        tok = tokens.peek()
    if left is None:
        tokens.position = pos
        return None
    return left


def relationalExpr():
    """relationalExpr = addExpr { relation addExpr } """
    pos = tokens.position
    tok = tokens.peek()
    if debug:
        print("relationalExpr: ", tok)
    left = addExpr()
    tok = tokens.peek()
    if tok is not None and re.match(Lexer.relational, tok):
        matched_op = re.match(Lexer.relational, tok)
        tokens.next()
        right = addExpr()
        left = BinaryExpr(matched_op.string, left, right)
        tok = tokens.peek()
    if left is None:
        tokens.position = pos
        return None
    return left


def andExpr():
    """ andExpr    = relationalExpr { "and" relationalExpr }"""
    pos = tokens.position
    tok = tokens.peek()
    if debug:
        print(f"andExpr: {tok}")
    left = relationalExpr()
    tok = tokens.peek()
    while tok == Lexer.token_and:
        tokens.next()
        right = relationalExpr()
        left = BinaryExpr(tok, left, right)
        tok = tokens.peek()
    if left is None:
        tokens.position = pos
        return None
    return left


def block():
    """ block = : eoln @ stmtlist ~ """
    pos = tokens.position
    isblk = False
    statements = ""
    if tokens.peek() == ":":
        tokens.next()
        if tokens.peek() == Lexer.eoln:
            tokens.next()
            if tokens.peek() == "@":
                tokens.next()
                statements = stmtlist()
                if statements is not None:
                    if tokens.peek() == "~":
                        tokens.next()
                        isblk = True
    if isblk == True:
        return Block(statements)
    tokens.position = pos
    return None


def ifstmt():
    """ ifStatement = "if" expression block   [ "else" block ] """
    pos = tokens.position
    tok = tokens.peek()
    if tok == Lexer.kw_if:
        tokens.next()
        expr = expression()
        ifblk = block()
        elseblk = Block("")
        if tokens.peek() == "else":
            tokens.next()
            elseblk = Block("else\n"+str(block()))
        if debug:
            print("IfStmt: ", str(IfStmt(expr, ifblk, elseblk)))
        return IfStmt(expr, ifblk, elseblk)
    tokens.position = pos
    if debug:
        print("Trying if statement, but not matching")
    return None


def whilestmt():
    """ whilestmt = "while" expression block """
    pos = tokens.position
    tok = tokens.peek()
    if tok == Lexer.kw_while:
        tokens.next()
        expr = expression()
        innerblk = block()
        return WhileStmt(expr, innerblk)
    tokens.position = pos
    if debug:
        print("Trying while statement, but not matching")
    return None


def statement():
    """ statement = (ifStatement |  whileStatement  |  assign )"""
    pos = tokens.position
    tok = tokens.peek()
    left = (ifstmt() or whilestmt() or assignstatement())
    if left is not None:
        return Statement(left)
    tokens.position = pos
    return None


def stmtlist():
    if len(tokens.tokens) == 0:
        return "\n"
    expr = ""
    lastpos = tokens.position
    statements = [expr]
    while True:
        lastpos = tokens.position
        expr = statement()
        if expr is None:
            return StatementList(statements)
        statements.append(str(expr))
    return StatementList(["Oh my god!!!!"])


def addExpr():
    """ addExpr    = term { ('+' | '-') term } """
    pos = tokens.position
    left = term()
    while tokens.peek() == Lexer.plus or tokens.peek() == Lexer.minus:
        op = tokens.peek()
        tokens.next()
        right = term()
        left = BinaryExpr(op, left, right)
    if left is None:
        tokens.position = pos
        return None
    return left


def parseStmtList():
    """ gee = { Statement } """
    return stmtlist()


def assignstatement():
    """ assign = ident "=" expression  eoln """
    tok = tokens.peek()
    pos = tokens.position
    if tok is None:
        return None
    if re.match(Lexer.identifier, tok):
        left = tok
        tokens.next()
        tok = tokens.peek()
        if tok == Lexer.equals:
            op = "="
            tokens.next()
            right = expression()
            if tokens.peek() == Lexer.eoln:
                tokens.next()
                return BinaryExpr(op, left, right)
    tokens.position = pos
    return None


def parse(text):
    global tokens
    tokens = Lexer(text)
    # print(tokens)
    # expr = assignstatement()
    # expr = addExpr()
    # expr = relationalExpr()
    # expr = andExpr()
    # expr = expression()
    # print(str(expr))
    # expr = assignstatement()
    # print(str(expr))
    #     Or:
    stmtlist = parseStmtList()
    print(str(stmtlist))
    if (tokens.position != len(tokens.tokens)):
        error("Unsuccesful parse")
    return


# Lexer, a private class that represents lists of tokens from a Gee
# statement. This class provides the following to its clients:
#
#   o A constructor that takes a string representing a statement
#       as its only parameter, and that initializes a sequence with
#       the tokens from that string.
#
#   o peek, a parameterless message that returns the next token
#       from a token sequence. This returns the token as a string.
#       If there are no more tokens in the sequence, this message
#       returns None.
#
#   o removeToken, a parameterless message that removes the next
#       token from a token sequence.
#
#   o __str__, a parameterless message that returns a string representation
#       of a token sequence, so that token sequences can print nicely

class Lexer:

    # The constructor with some regular expressions that define Gee's lexical rules.
    # The constructor uses these expressions to split the input expression into
    # a list of substrings that match Gee tokens, and saves that list to be
    # doled out in response to future "peek" messages. The position in the
    # list at which to dole next is also saved for "nextToken" to use.
    kw_while = "while"
    kw_if = "if"
    eoln = ";"
    equals = "="
    mul = "*"
    div = "/"
    minus = "-"
    plus = "+"
    token_or = "or"
    token_and = "and"
    special = r"\(|\)|\[|\]|,|:|;|@|~|;|\$"
    relational = "<=?|>=?|==?|!="
    arithmetic = "\+|\-|\*|/"
    #char = r"'."
    string = r"'[^']*'" + "|" + r'"[^"]*"'
    number = r"\-?\d+(?:\.\d+)?"
    literal = string + "|" + number
    #idStart = r"a-zA-Z"
    #idChar = idStart + r"0-9"
    #identifier = "[" + idStart + "][" + idChar + "]*"
    identifier = "[a-zA-Z]\w*"
    lexRules = literal + "|" + special + "|" + \
        relational + "|" + arithmetic + "|" + identifier

    def __init__(self, text):
        self.tokens = re.findall(Lexer.lexRules, text)
        # print(self.tokens)
        self.position = 0
        self.indent = [0]

    # The peek method. This just returns the token at the current position in the
    # list, or None if the current position is past the end of the list.

    def peek(self):
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        else:
            return None

    # The removeToken method. All this has to do is increment the token sequence's
    # position counter.

    def next(self):
        self.position = self.position + 1
        return self.peek()

    # An "__str__" method, so that token sequences print in a useful form.

    def __str__(self):
        return "<Lexer at " + str(self.position) + " in " + str(self.tokens) + ">"


def chkIndent(line):
    ct = 0
    for ch in line:
        if ch != " ":
            return ct
        ct += 1
    return ct


def delComment(line):
    pos = line.find("#")
    if pos > -1:
        line = line[0:pos]
        line = line.rstrip()
    return line


def mklines(filename):
    inn = open(filename, "r")
    lines = []
    pos = [0]
    ct = 0
    for line in inn:
        ct += 1
        line = line.rstrip()+";"
        line = delComment(line)
        if len(line) == 0 or line == ";":
            continue
        indent = chkIndent(line)
        line = line.lstrip()
        if indent > pos[-1]:
            pos.append(indent)
            line = '@' + line
        elif indent < pos[-1]:
            while indent < pos[-1]:
                del (pos[-1])
                line = '~' + line
        print(ct, "\t", line)
        lines.append(line)
    # print len(pos)
    undent = ""
    for i in pos[1:]:
        undent += "~"
    lines.append(undent)
    # print undent
    return lines


def main():
    """main program for testing"""
    global debug
    ct = 0
    for opt in sys.argv[1:]:
        if opt[0] != "-":
            break
        ct = ct + 1
        if opt == "-d":
            debug = True
    if len(sys.argv) < 2+ct:
        print("Usage:  %s filename" % sys.argv[0])
        return
    parse("".join(mklines(sys.argv[1+ct])))
    return


main()
