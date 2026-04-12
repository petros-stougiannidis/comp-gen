import sys
from specification import unicode
from scanner.scanner import Scanner
from specification.token import TokenRegistry
from specification.grammar import Grammar
from parser.lr1parser import LR1Parser
from parser.ll1parser import LL1Parser

# LL1
ll1_tokens = TokenRegistry()
ll1_tokens.register("*", r"\*")
ll1_tokens.register("?", r"\?")
ll1_tokens.register("+", r"\+")
ll1_tokens.register("(", r"\(")
ll1_tokens.register(")", r"\)")
ll1_tokens.register("|", r"\|")
ll1_tokens.register("symbol", r"a|b")

scanner = Scanner(ll1_tokens)
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

grammar = Grammar(start_symbol="regex", productions=productions, terminals=ll1_tokens.get_names())
print(grammar)
if not grammar.is_LL1():
    grammar.print_LL1_conflicts()

parser = LL1Parser(grammar)

tokens = (token for token in scanner.scan("a(a?ab)*ba"))

print(parser.parse(tokens, print_stack=True))


# LR1
lr1_tokens = TokenRegistry()
lr1_tokens.register("WHITESPACE", r"\s+")
lr1_tokens.register("*", r"\*")
lr1_tokens.register("+", r"\+")
lr1_tokens.register("(", r"\(")
lr1_tokens.register(")", r"\)")
lr1_tokens.register("int", r"int")

scanner = Scanner(lr1_tokens)
if len(sys.argv) > 1 and sys.argv[1] == "pdf":
    scanner.nfa.generatePDF()

# TODO: implement action callbacks
def action():
    pass

productions = {}
productions["S"] = {("E",): None}
productions["E"] = {("E", "+", "E"): None,
                    ("E", "*", "E"): None,
                    ("(", "E", ")"): None,
                    ("int",): None}

grammar = Grammar(start_symbol="S", productions=productions, terminals=lr1_tokens.get_names())
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
