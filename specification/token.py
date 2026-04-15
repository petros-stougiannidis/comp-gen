class TokenRegistry:
    
    def __init__(self):
        self.tokens = {}
        from todo.handwritten_regex_parser import LL1RegexParser
        self.regex_parser = LL1RegexParser()

    def register(self, name, pattern):
        ast = self.regex_parser.parse(pattern)
        if ast:
            self.tokens[name] = ast
        else:
            raise SyntaxError(f"Failed to parse {pattern}")
    
    def get_tokens(self):
        return self.tokens.items()  

    def get_names(self):
        return self.tokens.keys()  

    def get_ASTs(self):
        return self.tokens.values()  

class Token:
    
    def __init__(self, name, value=None):
        self.type = name
        self.value = value

    def __repr__(self):
        if self.value:
            return f"{self.value}::{self.type}"
        return f"{self.type}"

