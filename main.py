import sys
from specification import unicode
from scanner.scanner import Scanner
from specification.token import Token
from specification.grammar import Grammar
from parser.lr1parser import LR1Parser
from parser.ll1parser import LL1Parser

# LL1
Token.register("*", r"\*")
Token.register("?", r"\?")
Token.register("+", r"\+")
Token.register("(", r"\(")
Token.register(")", r"\)")
Token.register("|", r"\|")
Token.register("symbol", r"a|b")

scanner = Scanner()
if len(sys.argv) > 1 and sys.argv[1] == "pdf":
    scanner.nfa.generatePDF()

productions = dict()
productions["regex"] = {("concat", "A1"): None}
productions["A1"] = {("|", "regex"): None,
                    tuple(): None}
productions["concat"] = {("rep", "A2"): None}
productions["A2"] = {("concat",): None,
                    tuple(): None}
productions["rep"] = {("atom", "A3"): None}
productions["A3"] = {("*",): None,
                    ("?",): None,
                    ("+",): None,
                    tuple(): None}
productions["atom"] = {("(", "regex", ")"): None,
                    ("symbol",): None}

grammar = Grammar(start_symbol="regex", productions=productions)

if not grammar.is_LL1():
    grammar.print_LL1_conflicts()

parser = LL1Parser(grammar)

tokens = (token for token in scanner.scan("a(a?ab)*ba"))

print(parser.parse(tokens, print_stack=True))


# # LR1
# Token.register("WHITESPACE", r"\s+")
# Token.register("*", r"\*")
# Token.register("+", r"\+")
# Token.register("(", r"\(")
# Token.register(")", r"\)")
# Token.register("int", r"int")

# scanner = Scanner()
# if len(sys.argv) > 1 and sys.argv[1] == "pdf":
#     scanner.nfa.generatePDF()

# # TODO: implement action callbacks
# def action():
#     pass

# productions = {}
# productions["S"] = {("E",): action}
# productions["E"] = {("E", "+", "E"): action,
#                     ("E", "*", "E"): action,
#                     ("(", "E", ")"): action,
#                     ("int",): action}

# grammar = Grammar(start_symbol="S", productions=productions)
# print(grammar)
# if not grammar.is_LL1():
#     grammar.print_LL1_conflicts() 
# parser = LR1Parser(grammar)

# precedences = [
#     ("left",  ["+","-"]),
#     ("left",  ["*","/"]),
# ]
# parser.patch(precedences)
# parser.print_LR1_conflicts()

# tokens = (token for token in scanner.scan("int + (int * (int + int))") if token.type != "WHITESPACE")
# print(parser.parse(tokens))