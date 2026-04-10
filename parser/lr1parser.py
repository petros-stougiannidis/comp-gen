from specification import unicode
from specification.grammar import concat1
from collections import defaultdict

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
        if not isinstance(other, LR1Item):
            return False
        return (self.lhs, self.rhs, self.dot, self.lookahead) == \
            (other.lhs, other.rhs, other.dot, other.lookahead)

    def __repr__(self):
        before = self.rhs[:self.dot]
        after = self.rhs[self.dot:]
        lookahead = self.lookahead if self.lookahead else "{}"
        return f"[{self.lhs} → {before} • {after}, {lookahead}]"

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

class LR1Parser:
    def __init__(self, grammar):
        self.grammar = grammar
        self.states, self.goto = self.canonical_LR1_automaton()
        self.action_table = self.action_table()
        self.print_action_table()

    def canonical_LR1_automaton(self):
        grammar = self.grammar
        states = set()
        transition = defaultdict(lambda: defaultdict(lambda: None))
        start_items = [LR1Item(grammar.startSymbol, rhs, lookahead={'$'}) for rhs in grammar.delta[grammar.startSymbol]]

        start_state = LR1State(start_items, grammar)
        worklist = [start_state]

        while worklist:
            
            state = worklist.pop()
            states.add(state)
            new_state_core = defaultdict(list)
            for item in state:
                symbol = item.next_symbol()
                if not symbol:
                    continue
                new_state_core[symbol].append(item.advance())

            for symbol, core in new_state_core.items():
                new_state = LR1State(core, grammar)
                transition[state][symbol] = new_state
                if new_state not in states:
                    worklist.append(new_state)

        return states, transition

    def action_table(self):
        grammar = self.grammar
        action_table = defaultdict(lambda: defaultdict(lambda: None))

        for state in self.states:
            for terminal in grammar.terminals:
                for item in state:     
                    if item.is_complete() and terminal in item.lookahead:
                        action_table[state][terminal] = item

                    if  item.next_symbol() in grammar.terminals \
                        and terminal in concat1(grammar.first1(item.get_right_context()), item.lookahead):

                        action_table[state][terminal] = "s"
        return action_table

    def print_action_table(self):
        state_list = list(self.states)
        state_id = {s: i for i, s in enumerate(state_list)}

        terminals = list(self.grammar.terminals) 

        # Header
        header = ["STATE"] + terminals
        print(" | ".join(f"{h:^15}" for h in header))
        print("-" * (17 * len(header)))

        for s in state_list:
            row = [str(state_id[s])]

            for t in terminals:
                entry = self.action_table[s].get(t)

                if entry is None:
                    cell = ""

                # SHIFT (even if broken)
                elif isinstance(entry, tuple) and len(entry) >= 2 and entry[0] == "s":
                    target = entry[1]
                    if target in state_id:
                        cell = f"s{state_id[target]}"
                    else:
                        cell = f"s({target})"   # shows the bug

                # REDUCE (if you ever store it properly later)
                elif isinstance(entry, tuple) and entry[0] == "r":
                    lhs, rhs = entry[1]
                    cell = f"r({lhs}→{''.join(rhs)})"

                # ACCEPT
                elif entry == ("acc",) or entry == "acc":
                    cell = "acc"

                # RAW LR1Item (your current case)
                elif hasattr(entry, "lhs"):
                    cell = f"{entry.lhs}→{''.join(entry.rhs)}"

                # Fallback (super important for debugging)
                else:
                    cell = str(entry)

                row.append(cell)

            print(" | ".join(f"{c:^15}" for c in row))