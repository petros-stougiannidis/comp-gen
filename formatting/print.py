class Sequence(tuple):
    def __repr__(self):
        return " ".join(map(str, self))

    def __bool__(self):
        return len(self) > 0

def print_set(s):
        return "{" + ", ".join(sorted(s)) + "}"