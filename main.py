from sys import argv as command_line_arguments
from scanner.scanner import Scanner
from specification.token import TokenRegistry
from specification.grammar import Grammar
from parser.lr1parser import LR1Parser
from parser.ll1parser import LL1Parser
from scanner.abstract_regex_tree import Union, Concatenation, KleeneClosure, Optional, Plus, Symbol
from visualization.graph import render_nfa, render_lr1

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
    render_nfa(scanner.nfa)

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

    tokens = scanner.scan(r"(a|b)*cd+")

    accepted, stack = parser.parse(tokens, print_stack=("-stack" in command_line_arguments))
    print(accepted, stack[0] if stack else None)

if "-lr1" in command_line_arguments:
    lr1_tokens = TokenRegistry()
    lr1_tokens.register("WHITESPACE", r"\s+")
    lr1_tokens.register("*", r"\*")
    lr1_tokens.register("+", r"\+")
    lr1_tokens.register("(", r"\(")
    lr1_tokens.register(")", r"\)")
    lr1_tokens.register("int", r"[0-9]+")

    scanner = Scanner(lr1_tokens)
    render_nfa(scanner.nfa)
    
    from visualization.graph import render_nfa
    render_nfa(scanner.nfa)

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
    render_lr1(parser.automaton)

    precedences = [
        ("left",  ["+","-"]),
        ("left",  ["*","/"]),
    ]
    parser.patch(precedences)
    parser.print_LR1_conflicts()

    tokens = (token for token in scanner.scan("0 + (12 * (34 + 3))") if token.type != "WHITESPACE")

    accepted, stack = parser.parse(tokens)
    print(accepted, stack[0] if stack else None)


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
    render_nfa(scanner.nfa)

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
    render_lr1(parser.automaton)

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
    render_nfa(scanner.nfa)

    productions = {}
    productions["file"] = {
        ("line", "tail"): lambda child: child[0] + child[1],
        tuple(): []
    }
    productions["tail"] = {
        ("line", "tail"): lambda child: child[0] + child[1],
        tuple(): []
    }
    productions["line"] = {
        ("spec", "NEW_LINE"): lambda child: [child[0]],
        ("spec",): lambda child: [child[0]],
    }
    productions["spec"] = {
        ("KEY", "EQ", "VAL"): lambda child: (child[0], child[1], child[2])
    }

    grammar = Grammar(start_symbol="file", productions=productions, terminals=conf_tokens.get_names())
    
    parser = LR1Parser(grammar)
    render_lr1(parser.automaton)
    parser.print_LR1_conflicts()

    tokens = (token for token in scanner.scan_file("test.txt") if token.type != "SPACE")
    accepted, stack = parser.parse(tokens)
    print(accepted, stack[0] if stack else None)

if "-debug" in command_line_arguments:
    
    lr1_tokens = TokenRegistry()
    lr1_tokens.register("c", r"c")
    lr1_tokens.register("d", r"d")

    scanner = Scanner(lr1_tokens)
    render_nfa(scanner.nfa)

    
    productions = {}
    productions["S"] = {("C", "C"): None}
    productions["C"] = {("c", "C"): None, ("d",): None}

    grammar = Grammar(start_symbol="S", productions=productions, terminals=lr1_tokens.get_names())
    parser = LR1Parser(grammar)
    render_lr1(parser.automaton)




