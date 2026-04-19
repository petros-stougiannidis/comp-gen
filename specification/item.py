from formatting.print import Sequence, pretty_set

class Item:
    def __init__(self, lhs, rhs, dot=0):
        self.lhs = lhs
        self.rhs = tuple(rhs)
        self.dot = dot

    def is_complete(self):
        return self.dot == len(self.rhs)

    def advance(self):
        if not self.is_complete():
            return Item(self.lhs, self.rhs, self.dot+1)
        raise RuntimeError(f"{self} is already complete")

    def next_symbol(self):
        return self.rhs[self.dot] if not self.is_complete() else None

    def get_right_context(self):
        return self.rhs[self.dot:]

    def __repr__(self):
        before = Sequence(self.rhs[:self.dot])
        after = Sequence(self.rhs[self.dot:])

        if before and after:
            return f"[{self.lhs} → {before} • {after}]"
        elif before:
            return f"[{self.lhs} → {before} •]"
        elif after:
            return f"[{self.lhs} → • {after}]"
        else:
            return f"[{self.lhs} → •]"

    def __eq__(self, other):
        return isinstance(other, Item) and (self.lhs, self.rhs, self.dot) == (other.lhs, other.rhs, other.dot)

    def __hash__(self):
        return hash((self.lhs, self.rhs, self.dot))

class LR1Item(Item):
    def __init__(self, lhs, rhs, dot=0, lookahead=None):
        super().__init__(lhs, rhs, dot)                
        self.lookahead = set(lookahead or [])

    def advance(self):
        if not self.is_complete():
            return LR1Item(self.lhs, self.rhs, self.dot + 1, self.lookahead)
        raise RuntimeError(f"{self} is already complete")

    def __hash__(self):
        return hash((self.lhs, self.rhs, self.dot, frozenset(self.lookahead)))

    def __eq__(self, other):
        return isinstance(other, LR1Item) and \
            (self.lhs, self.rhs, self.dot, self.lookahead) == \
            (other.lhs, other.rhs, other.dot, other.lookahead)

    def __repr__(self):
        base = super().__repr__()
        return f"{base[:-1]}, {pretty_set(self.lookahead)}]"