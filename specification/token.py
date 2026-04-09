from scanner.regex_parser import parse_regex

class Token:
    _registry = []

    def __init__(self, token_type, value=None):
        self.token_type = token_type
        self.value = value

    @classmethod
    def register(cls, name, pattern):
        ast = parse_regex(pattern)
        token = {"name": name, "pattern": pattern, "ast": ast}
        cls._registry.append(token)
        return token

    @classmethod
    def get_registry(cls):
        return cls._registry

    def __repr__(self):
        if self.value:
            return f"{self.value}::{self.token_type}"
        return f"{self.token_type}"