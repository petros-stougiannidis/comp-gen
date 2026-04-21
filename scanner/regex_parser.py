import string
from scanner.abstract_regex_tree import Symbol, Concatenation, Union, KleeneClosure, Plus, Optional
from scanner.scanner import Scanner
from specification.grammar import Grammar
from parser.ll1_parser import LL1Parser
from parser.lr1_parser import LR1Parser
from functools import reduce

regex_meta_characters = set("|*+?()[]-\\^.")
escaped_character_classes = {
    r'\d': set(string.digits),
    r'\D': set(string.printable) - set(string.digits),
    r'\w': set(string.ascii_letters + string.digits + '_'),
    r'\W': set(string.printable) - set(string.ascii_letters + string.digits + '_'),
    r'\s': set(string.whitespace),
    r'\S': set(string.printable) - set(string.whitespace),
    r'\n': {'\n'},
    r'\t': {'\t'},
    r'\r': {'\r'},
    r'\0': {'\0'},
    r'\f': {'\f'},
    r'\v': {'\v'},
}

def escaped_class(escape_sequence):
    if escape_sequence in escaped_character_classes:
        return escaped_character_classes[escape_sequence]
    escaped_character = escape_sequence[1:]
    if escaped_character in regex_meta_characters:
        return {escaped_character}
    raise SyntaxError(f"Unknown escape sequence: {escaped_character}")

def character_range(start, end):
    start, end = min(ord(start), ord(end)), max(ord(start), ord(end))
    return {chr(character) for character in range(start, end + 1)}

class LR1RegexParser:

    def __init__(self):
    
        regex_tokens = {}
        # 1. priority: detect escape sequences
        regex_tokens[f'escaped'] = Concatenation(Symbol('\\'), Symbol(string.printable))
        # 2. priority: detect regex meta characters
        for character in regex_meta_characters:
            regex_tokens[character] = Symbol(character)
        # 3. priority: detect every other character
        regex_tokens["symbol"] = Symbol(set(string.printable))

        self.scanner = Scanner(regex_tokens)

        productions = {}
        productions["regex"] = {
            ("regex", "|", "term"): lambda c: Union(c[0], c[2]),
            ("term",):              lambda c: c[0],
        }
        productions["term"] = {
            ("term", "factor"):  lambda c: Concatenation(c[0], c[1]),
            ("factor",):         lambda c: c[0],
        }
        productions["factor"] = {
            ("atom", "*"): lambda c: KleeneClosure(c[0]),
            ("atom", "+"): lambda c: Plus(c[0]),
            ("atom", "?"): lambda c: Optional(c[0]),
            ("atom",):     lambda c: c[0],
        }
        productions["atom"] = {
            ("symbol",):                lambda c: Symbol(c[0]),
            ("escaped",):               lambda c: Symbol(escaped_class(c[0])),
            (".",):                     lambda c: Symbol(set(string.printable)),
            ("(", "regex", ")"):        lambda c: c[1],
            ("[", "classes", "]"):      lambda c: Symbol(c[1]),
            ("[", "^", "classes", "]"): lambda c: Symbol(set(string.printable) - c[2]),
        }
        # each class inside [] contributes to the set of characters specified by []
        productions["classes"] = {
            ("class", "classes"):   lambda c: c[0] | c[1],
            tuple():                lambda c: set(),
        }
        # a class inside [] can be a single symbol, a range of symbols or 
        # a set of characters described by an escape sequence
        productions["class"] = {
            ("symbol",):                lambda c: set(c[0]),
            ("symbol", "-", "symbol"):  lambda c: character_range(c[0], c[2]),
            ("escaped",):               lambda c: escaped_class(c[0]),
        }

        grammar = Grammar(start_symbol="regex", productions=productions, terminals=regex_tokens.keys())
        self.parser = LR1Parser(grammar)

    def parse(self, regex_string):

        accepted, stack = self.parser.parse(self.scanner.scan(regex_string))
        return stack[0] if accepted else None