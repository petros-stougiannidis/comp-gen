class Sequence(tuple):
    def __repr__(self):
        return " ".join(map(str, self)) if self else 'ε'

    def __bool__(self):
        return len(self) > 0

def escape_char(c):
    if c == " ":
        return r"\s"   # or "␠" if you prefer visual symbol
    if c == "\n":
        return r"\n"
    if c == "\t":
        return r"\t"
    if c == "\r":
        return r"\r"
    return c


def print_set(s):
    return "{" + ", ".join(sorted(escape_char(c) for c in s)) + "}"