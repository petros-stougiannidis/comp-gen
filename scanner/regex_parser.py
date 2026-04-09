import string
from scanner.abstract_regex_tree import Symbol, Union, KleeneClosure, Plus, Concatenation

PRINTABLE = set(string.printable)
DIGITS = set("0123456789")
WHITESPACE = set(" \t\n\r\v\f")
WORD = set(string.ascii_letters + string.digits + "_")

def _class_for_escape(ch):
    if ch == "d":
        return set(DIGITS)
    if ch == "D":
        return PRINTABLE - DIGITS
    if ch == "s":
        return set(WHITESPACE)
    if ch == "S":
        return PRINTABLE - WHITESPACE
    if ch == "w":
        return set(WORD)
    if ch == "W":
        return PRINTABLE - WORD
    return None

def regex_tokenize(pattern):
    tokens = []
    i = 0

    while i < len(pattern):
        c = pattern[i]

        if c in "()|*+?":
            tokens.append(c)
            i += 1
            continue

        if c == "\\":
            if i + 1 >= len(pattern):
                raise RuntimeError("Dangling escape at end of regex")
            esc = pattern[i + 1]
            cls = _class_for_escape(esc)
            if cls is not None:
                tokens.append(("CLASS", cls))
            else:
                tokens.append(("LITERAL", esc))
            i += 2
            continue

        if c == "[":
            i += 1
            if i >= len(pattern):
                raise RuntimeError("Unterminated character class")

            negated = False
            if pattern[i] == "^":
                negated = True
                i += 1

            chars = set()
            while i < len(pattern) and pattern[i] != "]":
                if pattern[i] == "\\":
                    if i + 1 >= len(pattern):
                        raise RuntimeError("Dangling escape inside character class")
                    esc = pattern[i + 1]
                    cls = _class_for_escape(esc)
                    if cls is not None:
                        chars |= cls
                    else:
                        chars.add(esc)
                    i += 2
                    continue

                if i + 2 < len(pattern) and pattern[i + 1] == "-" and pattern[i + 2] != "]":
                    start = pattern[i]
                    end = pattern[i + 2]
                    if ord(start) > ord(end):
                        raise RuntimeError(f"Invalid range {start}-{end}")
                    for code in range(ord(start), ord(end) + 1):
                        chars.add(chr(code))
                    i += 3
                    continue

                chars.add(pattern[i])
                i += 1

            if i >= len(pattern) or pattern[i] != "]":
                raise RuntimeError("Unterminated character class")

            i += 1
            if negated:
                chars = PRINTABLE - chars
            tokens.append(("CLASS", chars))
            continue

        tokens.append(("LITERAL", c))
        i += 1

    return tokens


def parse_regex(pattern):
    tokens = regex_tokenize(pattern)
    pos = 0

    def peek():
        return tokens[pos] if pos < len(tokens) else None

    def consume(expected=None):
        nonlocal pos
        tok = peek()
        if tok is None:
            raise RuntimeError("Unexpected end of regex")
        if expected is not None and tok != expected:
            raise RuntimeError(f"Expected {expected}, got {tok}")
        pos += 1
        return tok

    def make_union(nodes):
        if not nodes:
            return EmptyWord()
        node = nodes[0]
        for nxt in nodes[1:]:
            node = Union(node, nxt)
        return node

    def parse_expr():
        node = parse_concat()
        while peek() == "|":
            consume("|")
            rhs = parse_concat()
            node = Union(node, rhs)
        return node

    def parse_concat():
        nodes = []
        while peek() is not None and peek() not in (")", "|"):
            nodes.append(parse_repeat())

        if not nodes:
            return EmptyWord()

        node = nodes[0]
        for nxt in nodes[1:]:
            node = Concatenation(node, nxt)
        return node

    def parse_repeat():
        node = parse_atom()
        while peek() in ("*", "+", "?"):
            op = consume()
            if op == "*":
                node = KleeneClosure(node)
            elif op == "+":
                node = Plus(node)
            elif op == "?":
                node = Optional(node)
        return node

    def parse_atom():
        tok = peek()
        if tok is None:
            raise RuntimeError("Unexpected end of regex")

        if tok == "(":
            consume("(")
            node = parse_expr()
            consume(")")
            return node
        tok = consume()

        
        if isinstance(tok, tuple):
            kind, value = tok
            if kind == "LITERAL":
                return Symbol(value)
            if kind == "CLASS":
                # symbols = [Symbol(ch) for ch in sorted(value)]
                if not value:
                    raise RuntimeError("Empty character class")
                # node = symbols[0]
                # for nxt in symbols[1:]:
                    # node = Union(node, nxt)
                return Symbol(frozenset(value))

        if isinstance(tok, str):
            return Symbol(tok)

        raise RuntimeError(f"Unsupported token: {tok}")

    node = parse_expr()
    if pos != len(tokens):
        raise RuntimeError("Unexpected tokens at end of regex")
    return node