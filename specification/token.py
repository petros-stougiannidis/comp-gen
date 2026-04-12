from scanner.regex_parser import parse_regex

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

