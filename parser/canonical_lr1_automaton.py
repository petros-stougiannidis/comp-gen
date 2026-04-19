from specification.item import LR1Item
from specification.grammar import concat1
from collections import defaultdict

# data structure for accumulating lookahead symbols for LR1Items with the same core
class Closure:
    def __init__(self):
        self.lookahead = {}  # (lhs, rhs, dot) -> set(lookahead)

    def add(self, item):
        core = (item.lhs, item.rhs, item.dot)

        if core not in self.lookahead:
            self.lookahead[core] = set(item.lookahead)
            return True # new item

        old_size = len(self.lookahead[core])
        self.lookahead[core] |= set(item.lookahead)

        return len(self.lookahead[core]) > old_size  # changed?

    def items(self):
        for (lhs, rhs, dot), lookahead in self.lookahead.items():
            yield LR1Item(lhs, rhs, dot, lookahead)

    def __iter__(self):
        return self.items()

def epsilon_closure(items, grammar):
    closure = Closure()
    worklist = set()

    for item in items:
        closure.add(item)
        worklist.add(item)

    while worklist:
        item = worklist.pop()
        A = item.next_symbol()
        if A in grammar.non_terminals:
            right_context = item.advance().get_right_context()
            for rhs in grammar.delta[A]:
                lookahead = concat1(grammar.first1(right_context), item.lookahead)
                new_item = LR1Item(A, rhs, lookahead=lookahead)
                if closure.add(new_item):
                    worklist.add(new_item)
    return closure

class LR1State:

    def __init__(self, items, state_id=None):
        self.id = state_id
        self.items = frozenset(items)

    def is_final(self):
        return any(item.is_complete() for item in self.items)

    def __hash__(self):
        return hash(self.items)

    def __eq__(self, other):
        return isinstance(other, State) and self.items == other.items

    def __iter__(self):
        return iter(self.items)

class CanonicalLR1Automaton:
    def __init__(self, grammar):

        self._states = dict()
        self._transitions = dict()

        start_items = [LR1Item(grammar.start_symbol, rhs, lookahead={'$'}) for rhs in grammar.delta[grammar.start_symbol]]
        core = frozenset(start_items)
        closure = epsilon_closure(core, grammar)
        self._start_state = LR1State(closure, state_id=0)
        state_id = 1
        self._states[core] = self._start_state
        
        worklist = {self._start_state}

        while worklist:

            state = worklist.pop()
            
            new_cores = defaultdict(list)
            for item in state:
                if symbol := item.next_symbol():
                    new_cores[symbol].append(item.advance())

            for symbol, items in new_cores.items():
                core = frozenset(items)
                if core not in self._states:
                    closure = epsilon_closure(core, grammar)
                    new_state = LR1State(closure, state_id)
                    self._states[core] = new_state
                    state_id += 1
                    worklist.add(new_state)

                self._transitions[(state, symbol)] = self._states[core]

    @property
    def states(self):
        return self._states.values()

    @property
    def start_state(self):
        return self._start_state

    @property
    def transitions(self):
        return self._transitions
                    
    



            


