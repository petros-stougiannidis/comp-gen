from formatting.print import Sequence

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
        before = self.rhs[:self.dot]
        after = self.rhs[self.dot:]
        return f"[{self.lhs} → {Sequence(before)} • {Sequence(after)}]"

    def __eq__(self, other):
        if not isinstance(other, Item):
            return False
        return (self.lhs, self.rhs, self.dot) == (other.lhs, other.rhs, other.dot)

    def __hash__(self):
        return hash((self.lhs, self.rhs, self.dot))

class LR1Item(Item):
    def __init__(self, lhs, rhs, dot=0, lookahead=None):
        super().__init__(lhs, rhs, dot)                
        self.lookahead = set(lookahead or [])

    def advance(self):
        return LR1Item(self.lhs, self.rhs, self.dot + 1, self.lookahead)

    def __hash__(self):
        return hash((self.lhs, self.rhs, self.dot, frozenset(self.lookahead)))

    def __eq__(self, other):
        if not isinstance(other, LR1Item):
            return False
        return (self.lhs, self.rhs, self.dot, self.lookahead) == \
            (other.lhs, other.rhs, other.dot, other.lookahead)

    def __repr__(self):
        before = self.rhs[:self.dot]
        after = self.rhs[self.dot:]
        lookahead = self.lookahead if self.lookahead else "{}"
        return f"[{self.lhs} → {Sequence(before)} • {Sequence(after)}, {lookahead}]"