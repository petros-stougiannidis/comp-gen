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

grammar = Grammar(startSymbol="S", productions=productions)
parser = LR1Parser(grammar)

precedences = [
    ("left",  ["+","-"]),
    ("left",  ["*","/"]),
]
parser.patch(precedences)
parser.print_conflicts()
# parser.print_action_table()

tokens = (token for token in scanner.scan("int + (int * (int + int))") if token.type != "WHITESPACE")
print(parser.parse(tokens))

# production["S"] = {("E",): a}
# production["E"] = {("E","+","T"): a,
#                     ("T",): a}
# production["T"] = {("T", "*", "F",): a,
#                     ("F",): a}
# production["F"] = {("(", "E",")"): a,
#                     ("int",): a}

#                     Token.register("+", r"+")
# Token.register("*", r"*")
# Token.register("(", r"(")
# Token.register(")", r")")
# Token.register("int", r"int")