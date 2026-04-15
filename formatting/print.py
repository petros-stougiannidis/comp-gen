class Sequence(tuple):
    def __repr__(self):
        return " ".join(map(str, self)) if self else 'ε'

    def __bool__(self):
        return len(self) > 0

def descape(character):
    if character == " ":
        return " "   # or "␠" if you prefer visual symbol
    if character == "\n":
        return r"\n"
    if character == "\t":
        return r"\t"
    if character == "\r":
        return r"\r"
    if character == "\f":
        return r"\f"
    if character == "\v":
        return r"\v"
    return character

def pretty_set(ugly_set):
    return "{" + ", ".join(sorted(descape(character) for character in ugly_set)) + "}"