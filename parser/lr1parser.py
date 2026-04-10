from specification import unicode
from specification.grammar import concat1
from collections import defaultdict

class LR1State:
    def __init__(self, core, grammar):
        self.core = core
        self.closure = epsilon_closure(core, grammar)
        self.identity = frozenset({(item.lhs, item.rhs, item.dot, frozenset(item.lookahead)) for item in self.closure})
    
    def items(self):
        for item in self.closure:
            yield item

    def __hash__(self):
        return hash(self.identity)

    def __eq__(self, other):
        return self.identity == other.identity

    def __iter__(self):
        return self.items()

class Closure:
    def __init__(self):
        self.lookahead = {}  # (lhs, rhs, dot) -> set(lookahead)

    def add(self, item):
        core = (item.lhs, item.rhs, item.dot)

        if core not in self.lookahead:
            self.lookahead[core] = set(item.lookahead)
            return True  # new item

        old_size = len(self.lookahead[core])
        self.lookahead[core] |= set(item.lookahead)

        return len(self.lookahead[core]) > old_size  # changed?

    def items(self):
        for (lhs, rhs, dot), lookahead in self.lookahead.items():
            yield LR1Item(lhs, rhs, dot, lookahead)

    def __iter__(self):
        return self.items()

class LR1Item:
    def __init__(self, lhs, rhs, dot=0, lookahead=None):
        self.lhs = lhs           
        self.rhs = tuple(rhs)
        self.dot = dot                  
        self.lookahead = set(lookahead or [])

    def core(self):
        return (self.lhs, self.rhs, self.dot)

    def next_symbol(self):
        return self.rhs[self.dot] if self.dot < len(self.rhs) else None

    def get_right_context(self):
        return self.rhs[self.dot:]
            
    def is_complete(self):
        return self.dot == len(self.rhs)

    def advance(self):
        return LR1Item(self.lhs, self.rhs, self.dot + 1, self.lookahead)

    def __hash__(self):
        return hash((self.lhs, self.rhs, self.dot, frozenset(self.lookahead)))

    def __eq__(self, other):
        return (self.lhs, self.rhs, self.dot, self.lookahead) == \
               (other.lhs, other.rhs, other.dot, other.lookahead)

    def __repr__(self):
        before = self.rhs[:self.dot]
        after = self.rhs[self.dot:]
        lookahead = self.lookahead if self.lookahead else "{}"
        return f"[{self.lhs} → {before} • {after}, {lookahead}]"

def epsilon_closure(items, grammar):
    closure = Closure()
    worklist = []

    for item in items:
        closure.add(item)
        worklist.append(item)

    while worklist:
        item = worklist.pop()
        A = item.next_symbol()
        if A in grammar.nonTerminals:
            right_context  = item.advance().get_right_context()
            for rhs in grammar.delta[A]:
                lookahead = concat1(grammar.first1(right_context), item.lookahead)
                new_item = LR1Item(A, rhs, lookahead=lookahead)
                if closure.add(new_item):
                    worklist.append(new_item)
    return closure


def build_canonical_LR1_automaton(grammar):
    transition = defaultdict(lambda: defaultdict(lambda: None))
    start_item = LR1Item(grammar.startSymbol, ("A",) , lookahead={'$'}) # TODO revert test

    start_state = LR1State([start_item], grammar)
    worklist = [start_state]

    while worklist:
        
        state = worklist.pop() # list of items
        
        new_state_core = defaultdict(list)
        for item in state:
            symbol = item.next_symbol()
            if not symbol:
                continue
            new_state_core[symbol].append(item.advance())

        for symbol, core in new_state_core.items():
            new_state = LR1State(core, grammar)
            transition[state][symbol] = new_state
            if new_state not in worklist:
                worklist.append(new_state)

    return transition