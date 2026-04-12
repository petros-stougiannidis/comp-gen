from scanner.regex_parser import parse_regex

class TokenRegistry:
    
    def __init__(self):
        self.tokens = {}

    def register(self, name, pattern):
        ast = parse_regex(pattern)
        self.tokens[name] = ast
    
    def get_tokens(self):
        return self.tokens.items()  

    def get_names(self):
        return self.tokens.keys()  

    def get_ASTs(self):
        return self.tokens.values()  

class Token:
    _registry = {}

    def __init__(self, name, value=None):
        self.type = name
        self.value = value
        
    @classmethod
    def register(cls, name, pattern):
        ast = parse_regex(pattern)
        cls._registry[name] = ast
    
    @classmethod
    def get_tokens(cls):
        return cls._registry.items()    

    def __repr__(self):
        if self.value:
            return f"{self.value}::{self.type}"
        return f"{self.type}"

