from sys import argv as command_line_arguments
from scanner.scanner import Scanner
from specification.token import TokenRegistry
from specification.grammar import Grammar
from parser.lr1parser import LR1Parser
from parser.ll1parser import LL1Parser
from scanner.abstract_regex_tree import Union, Concatenation, KleeneClosure, Optional, Plus, Symbol

if "-ll1" in command_line_arguments:
    ll1_tokens = TokenRegistry()
    ll1_tokens.register("*", r"\*")
    ll1_tokens.register("?", r"\?")
    ll1_tokens.register("+", r"\+")
    ll1_tokens.register("(", r"\(")
    ll1_tokens.register(")", r"\)")
    ll1_tokens.register("|", r"\|")
    ll1_tokens.register("symbol", r"[a-zA-Z]")

    scanner = Scanner(ll1_tokens)
    if "-pdf" in command_line_arguments:
        scanner.nfa.generatePDF()

    def ignore():
        return lambda child: (lambda left: left)
    def constructBinary(constructor, index):
        return lambda child: (lambda left: constructor(left, child[index]))
    def constructUnary(constructor):
        return lambda child: (lambda node: constructor(node))
    def apply():
        return lambda child: child[1](child[0])

    productions = dict()
    productions["regex"] = {("concat", "A1"): apply()}
    productions["A1"] = {("|", "regex"): constructBinary(Union, 1),
                        tuple(): ignore()}
    productions["concat"] = {("rep", "A2"): apply() }
    productions["A2"] = {("concat",): constructBinary(Concatenation, 0),
                        tuple(): ignore()}
    productions["rep"] = {("atom", "A3"): apply()}
    productions["A3"] = {("*",): constructUnary(KleeneClosure),
                        ("?",): constructUnary(Optional),
                        ("+",): constructUnary(Plus),
                        tuple(): ignore()}
    productions["atom"] = {("(", "regex", ")"): lambda c: c[1],
                        ("symbol",): lambda c: Symbol(c[0])}

    grammar = Grammar(start_symbol="regex", productions=productions, terminals=ll1_tokens.get_names())
    if "-grammar" in command_line_arguments:
        print(grammar)
        if not grammar.is_LL1():
            grammar.print_LL1_conflicts()

    parser = LL1Parser(grammar)

    tokens = scanner.scan("(a|b)*cd+")

    accepted, stack = parser.parse(tokens, print_stack=("-stack" in command_line_arguments))
    print(stack, stack[0])

if "-lr1" in command_line_arguments:
    # LR1
    lr1_tokens = TokenRegistry()
    lr1_tokens.register("WHITESPACE", r"\s+")
    lr1_tokens.register("*", r"\*")
    lr1_tokens.register("+", r"\+")
    lr1_tokens.register("(", r"\(")
    lr1_tokens.register(")", r"\)")
    lr1_tokens.register("int", r"\d*")

    scanner = Scanner(lr1_tokens)
    if "-pdf" in command_line_arguments:
        scanner.nfa.generatePDF()

    # TODO: implement action callbacks

    productions = {}
    productions["S"] = {("E",): lambda c : c[0]}
    productions["E"] = {("E", "+", "E"): lambda c: ("+", c[0], c[2]),
                        ("E", "*", "E"): lambda c: ("*", c[0], c[2]),
                        ("(", "E", ")"): lambda c: c[1],
                        ("int",): lambda c: c[0]}

    grammar = Grammar(start_symbol="S", productions=productions, terminals=lr1_tokens.get_names())
    if "-grammar" in command_line_arguments:
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

    tokens = (token for token in scanner.scan("0 + (12 * (34 + 3))") if token.type != "WHITESPACE")

    accepted, stack = parser.parse(tokens)
    print(stack[0])


if "-reg" in command_line_arguments:
    # LR1
    reg_tokens = TokenRegistry()
    reg_tokens.register(".", r".")
    reg_tokens.register("*", r"\*")
    reg_tokens.register("?", r"\?")
    reg_tokens.register("+", r"\+")
    reg_tokens.register("(", r"\(")
    reg_tokens.register(")", r"\)")
    reg_tokens.register("|", r"\|")
    reg_tokens.register("symbol", r"[a-zA-Z]")

    scanner = Scanner(reg_tokens)
    if "-pdf" in command_line_arguments:
        scanner.nfa.generatePDF()

    # TODO: implement action callbacks

    productions = {}
    productions["regex"] = {("regex", ".", "regex"): lambda c: Concatenation(c[0], c[2]),
                        ("regex", "|", "regex"): lambda c: Union(c[0], c[2]),
                        ("regex", "*"): lambda c: KleeneClosure(c[0]),
                        ("regex", "+"): lambda c: Plus(c[0]),
                        ("regex", "?"): lambda c: Optional(c[0]),
                        ("(", "regex", ")"): lambda c: c[1],
                        ("symbol",): lambda c: Symbol(c[0])}

    grammar = Grammar(start_symbol="regex", productions=productions, terminals=reg_tokens.get_names())
    if "-grammar" in command_line_arguments:
        print(grammar)
        if not grammar.is_LL1():
            grammar.print_LL1_conflicts() 

    parser = LR1Parser(grammar)

    precedences = [
        ("left", ["|"]),          # lowest
        ("left", ["."]),          # concatenation
        ("right", ["*", "+", "?"])  # highest (postfix)
    ]
    parser.patch(precedences)
    parser.print_LR1_conflicts()

    tokens = scanner.scan("a.b.c|s.f")

    accepted, stack = parser.parse(tokens)
    print(accepted, stack[0] if stack else None)


if "-conf" in command_line_arguments:
    # LR1
    conf_tokens = TokenRegistry()
    conf_tokens.register("NEW_LINE", r"\n")
    conf_tokens.register("SPACE", r"\s")
    conf_tokens.register("KEY", r"[a-zA-Z]+")
    conf_tokens.register("EQ", r"=")
    conf_tokens.register("VAL", r"[0-9]")

    scanner = Scanner(conf_tokens)
    if "-pdf" in command_line_arguments:
        scanner.nfa.generatePDF()

    # TODO: implement action callbacks

    # productions = {}
    # productions["file"] = {
    #     ("line", "tail"): None,
    #     tuple(): None
    # }
    # productions["tail"] = {
    #     ("line",): None,
    #     tuple(): None
    # }
    # productions["line"] = {
    #     ("KEY", "EQ", "VAL", "NEW_LINE"): None,
    #     ("KEY", "EQ", "VAL"): None
    # }
    productions = {}
    productions["file"] = {
        ("line", "tail"): None,
        tuple(): None
    }
    productions["tail"] = {
        ("line", "tail"): None,
        tuple(): None
    }
    productions["line"] = {
        ("spec", "NEW_LINE"): None,
        ("spec",): None,
    }
    productions["spec"] = {
        ("KEY", "EQ", "VAL"): None
    }

    grammar = Grammar(start_symbol="file", productions=productions, terminals=conf_tokens.get_names())

    parser = LR1Parser(grammar)

    # precedences = [
    #     ("left", ["|"]),          # lowest
    #     ("left", ["."]),          # concatenation
    #     ("right", ["*", "+", "?"])  # highest (postfix)
    # ]
    # parser.patch(precedences)
    parser.print_LR1_conflicts()

    tokens = (token for token in scanner.scan_file("test.txt"))
    for t in tokens:
        print(t)

    tokens = (token for token in scanner.scan_file("test.txt") if token.type != "SPACE")
    accepted, stack = parser.parse(tokens)
    print(accepted, stack)

