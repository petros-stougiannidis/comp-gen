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
tokens.register("INT", r"[0-9]+")
tokens.register("+", r"\+")

scanner = Scanner(tokens)

grammar = Grammar(
    start_symbol="E",
    productions={
        "E": {
            ("E", "+", "E"): lambda c: ("+", c[0], c[2]),
            ("INT",): lambda c: c[0],
        }
    },
    terminals=tokens.get_names()
)

parser = LR1Parser(grammar)

stream = scanner.scan("1 + 2 + 3")

accepted, result = parser.parse(stream)
print(accepted, result)