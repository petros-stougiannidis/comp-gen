import sys
from specification import unicode
from scanner.scanner import Scanner
from specification.token import Token
from specification.grammar import Grammar
from parser.lr1parser import build_canonical_LR1_automaton, LR1Item

# Token.register("IDENT", r"[a-zA-Z]+([0-9]|[a-zA-Z])*")
# Token.register("NUMBER", r"[0-9]+")
# Token.register("PLUS", r"\+")
# Token.register("MINUS", r"-")
# Token.register("WHITESPACE", r"\s+")
# Token.register("LESS_OR_EQUAL", r"<=")
# Token.register("LESS", r"<")
# Token.register("SEMI", r";")
Token.register("a", r"a")
Token.register("b", r"b")
Token.register("c", r"c")

scanner = Scanner()
if len(sys.argv) > 1 and sys.argv[1] == "pdf":
    scanner.nfa.generatePDF()

def action():
    pass

productions = dict()
productions["S"] = {("A",): action}
productions["A"] = {("A", "B", "a"): action,
                    ("c",): action}
productions["B"] = {("b",): action,
                    tuple(): action}

grammar = Grammar("S", productions)
# print(grammar)
build_canonical_LR1_automaton(grammar)