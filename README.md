# comp-gen

## Overview

`comp-gen` is a modular compiler construction toolkit implemented in Python.

It provides components for the automatic construction of lexers and parsers.

---

## Features

- Token definition using regular expressions  
- Automatic lexer generation from defined tokens  
- Context-free grammar definition and analysis  
- Automatic LL(1) and LR(1) parser generation from grammar definitions  
- Construction of ASTs with semantic actions  
- Visualization of automata and parser states  

---

## Example

```python
tokens = TokenRegistry()
tokens.register("whitespace", r"\s+")
tokens.register("*", r"\*")
tokens.register("+", r"\+")
tokens.register("(", r"\(")
tokens.register(")", r"\)")
tokens.register("int", r"[0-9]+")

scanner = Scanner(tokens)

productions = {}
productions["S"] = {("E",): lambda c : eval_ast(c[0])}
productions["E"] = {("E", "+", "E"): lambda c: ("+", c[0], c[2]),
                    ("E", "*", "E"): lambda c: ("*", c[0], c[2]),
                    ("(", "E", ")"): lambda c: c[1],
                    ("int",): lambda c: c[0]}

def eval_ast(ast):
    match ast:
        case ("+", left, right):
            return eval_ast(left) + eval_ast(right)
        case ("*", left, right):
            return eval_ast(left) * eval_ast(right)
        case _:
            return int(ast)

grammar = Grammar(start_symbol="S", productions=productions, terminals=tokens.get_names())

precedences = [
    ("left",  ["+"]),
    ("left",  ["*"]),
]
parser = LR1Parser(grammar, precedences)
# render_lr1(parser.automaton)

tokens = (token for token in scanner.scan("0 + (12 * (34 + 3))") if token.type != "whitespace")

accepted, stack = parser.parse(tokens)
if accepted:
    print(stack[0])




