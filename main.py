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

# for token in scanner.scan("scanner/test.txt"):
#     if not token.token_type == "WHITESPACE":
#         print(token)

productions = dict()

def action():
    pass

productions["S"] = {("A",): action}
productions["A"] = {("A", "B", "a"): action,
                    ("c",): action}
productions["B"] = {("b",): action,
                    tuple(): action}

grammar = Grammar("S", productions)

print(grammar)
build_canonical_LR1_automaton(grammar)

# i = LR1Item("A", "ABC", )
# print(i)
# print(i.get_right_context_of_next_symbol())