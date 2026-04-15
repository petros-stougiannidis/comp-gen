import string
from scanner.abstract_regex_tree import Symbol, Concatenation, Union, KleeneClosure, Plus, Optional
from scanner.scanner import Scanner
from specification.token import TokenRegistry
from specification.grammar import Grammar
from parser.ll1parser import LL1Parser
from functools import reduce

regex_meta_characters = "|*+?()[]-\\"
META = set("|*+?()[]-\\")
WHITESPACE = set(" \t\n\r\f\v")

SYMBOL_CHARS = (
    set(string.ascii_letters)
    | set(string.digits)
    | set("!\"#$%&',./:;<=>@^_`~")
)


def character_range(start, end):
    return [character for character in range(ord(start), ord(end) + 1)]

def ignore():
    return lambda children: (lambda left: left)
def constructCharacterClass(): 
    return lambda children: reduce(Union, [Symbol(chr(character)) for character in character_range(children[0],children[2])])
def constructBinary(constructor, index):
    return lambda children: (lambda left: constructor(left, children[index]))
def constructUnary(constructor):
    return lambda children: (lambda node: constructor(node))
def apply():
    return lambda children: children[1](children[0])
def escape():
    lambda children : Symbol(frozenset({children[1]}))

def special_escape(c):
    ch = c[0]

    if isinstance(ch, list):
        ch = ch[0]

    if ch == 'd':
        return reduce(Union, [Symbol(str(i)) for i in range(10)])

    elif ch == 's':
        return reduce(Union, [Symbol(c) for c in WHITESPACE])

    else:
        return Symbol(frozenset(ch))


class LL1RegexParser:
    def __init__(self):

        regex_tokens = {}
        for character in regex_meta_characters:
            regex_tokens[character] = Symbol(frozenset({character}))
        regex_tokens["symbol"] = Symbol(frozenset(string.printable))

        self.scanner = Scanner(regex_tokens)

        # for token in self.scanner.scan(r"ab*\d"):
        #     print(token)

        productions = {} 
        productions["regex"] = {("concat", "A1"): apply()}
        productions["A1"] = {
            ("|", "regex"): constructBinary(Union, 1),
            tuple(): ignore()
        }
        productions["concat"] = {("rep", "A2"): apply()}
        productions["A2"] = {
            ("concat",): constructBinary(Concatenation, 0),
            tuple(): ignore()
        }
        productions["rep"] = {("atom", "A3"): apply()}
        productions["A3"] = {
            ("*",): constructUnary(KleeneClosure),
            ("?",): constructUnary(Optional),
            ("+",): constructUnary(Plus),
            tuple(): ignore()
        }
        productions["atom"] = {
            ("(", "regex", ")"): lambda c: c[1],
            ("[", "range_list", "]"): lambda c: c[1],
            ("symbol",): lambda c: Symbol(c[0]),
            ("\\", "escaped"): lambda c: c[1]
        }
        productions["escaped"] = {
            ("symbol",): special_escape,
            ("|",): lambda c: Symbol(c[0]),
            ("*",): lambda c: Symbol(c[0]),
            ("+",): lambda c: Symbol(c[0]),
            ("?",): lambda c: Symbol(c[0]),
            ("(",): lambda c: Symbol(c[0]),
            (")",): lambda c: Symbol(c[0]),
            ("[",): lambda c: Symbol(c[0]),
            ("]",): lambda c: Symbol(c[0]),
            ("-",): lambda c: Symbol(c[0]),
            ("\\",): lambda c: Symbol(c[0])
        }
        productions["range_list"] = {
            ("range", "range_list_tail"): apply()
        }
        productions["range_list_tail"] = {
            ("range", "range_list_tail"): constructBinary(Union, 0),
            tuple(): ignore()
        }
        productions["range"] = {
            ("symbol", "-", "symbol"): constructCharacterClass()
        }

        self.grammar = Grammar(start_symbol="regex", productions=productions, terminals=regex_tokens.keys())
        if not self.grammar.is_LL1():
            print(self.grammar.print_LL1_conflicts())
        self.parser = LL1Parser(self.grammar)

    def parse(self, regex):
        accepted, stack = self.parser.parse(self.scanner.scan(regex))
        return stack[0] if accepted else None

parser = LL1RegexParser()
# print(parser.parse("[a-cA-Z]"))



