import sys
from specification import unicode
from scanner.scanner import Scanner
from specification.token import Token
from specification.grammar import Grammar
from parser.lr1parser import LR1Parser

Token.register("WHITESPACE", r"\s+")
Token.register("*", r"\*")
Token.register("+", r"\+")
Token.register("(", r"\(")
Token.register(")", r"\)")
Token.register("int", r"int")

scanner = Scanner()
if len(sys.argv) > 1 and sys.argv[1] == "pdf":
    scanner.nfa.generatePDF()

# TODO: implement action callbacks
def action():
    pass

productions = {}
productions["S"] = {("E",): action}
productions["E"] = {("E", "+", "E"): action,
                    ("E", "*", "E"): action,
                    ("(", "E", ")"): action,
                    ("int",): action}

grammar = Grammar(start_symbol="S", productions=productions)
print(grammar)
if not grammar.is_LL1():
    grammar.print_LL1_conflicts() 
parser = LR1Parser(grammar)

precedences = [
    ("left",  ["+","-"]),
    ("left",  ["*","/"]),
]
parser.patch(precedences)
parser.print_LR1_conflicts()

tokens = (token for token in scanner.scan("int + (int * (int + int))") if token.type != "WHITESPACE")
print(parser.parse(tokens))