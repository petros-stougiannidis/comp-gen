import sys
from scanner.scanner import Scanner
from specification.token import Token
from specification.grammar import Grammar

Token.register("IDENT", r"[a-zA-Z]+([0-9]|[a-zA-Z])*")
Token.register("NUMBER", r"[0-9]+")
Token.register("PLUS", r"\+")
Token.register("MINUS", r"-")
Token.register("WHITESPACE", r"\s+")
Token.register("LESS_OR_EQUAL", r"<=")
Token.register("LESS", r"<")
Token.register("SEMI", r";")

scanner = Scanner()

if len(sys.argv) > 1 and sys.argv[1] == "pdf":
    scanner.nfa.generatePDF()

# for token in scanner.scan("scanner/test.txt"):
#     if not token.token_type == "WHITESPACE":
#         print(token)

productions = dict()

def action():
    pass

productions["S"] = {("E",): action}
productions["E"] = {("NUMBER",): action,
                    ("NUMBER","PLUS","E"): action}

g = Grammar("S", productions)
print(g)

