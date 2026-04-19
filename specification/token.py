class TokenRegistry:
    
    def __init__(self):
        self.tokens = {}
        from scanner.regex_parser import LR1RegexParser
        self.regex_parser = LR1RegexParser()

    def register(self, name, pattern):
        ast = self.regex_parser.parse(pattern)
        self.tokens[name] = ast
        # TODO: return string or ast for composition
        return ast

    def get_tokens(self):
        return self.tokens.items()  

    def get_names(self):
        return self.tokens.keys()

class Token:
    
    def __init__(self, name, value=None):
        self.type = name
        self.value = value

    def __repr__(self):
        if self.value:
            return f"{self.value}::{self.type}"
        return f"{self.type}"

