from specification import unicode
from specification.grammar import concat1
from collections import defaultdict

class LR1Item:
    def __init__(self, lhs, rhs, dot=0, lookahead=None):
        self.lhs = lhs
        self.rhs = rhs          
        self.dot = dot       
        self.lookahead = lookahead if lookahead else set()

    def next_symbol(self):
        return self.rhs[self.dot] if self.dot < len(self.rhs) else None

    def get_right_context(self):
        return self.rhs[self.dot:]

    def is_complete(self):
        return self.dot == len(self.rhs)

    def advance(self):
        return LR1Item(self.lhs, self.rhs, self.dot + 1, set(self.lookahead))

    def __hash__(self):
        return hash((self.lhs, self.rhs, self.dot))

    def __eq__(self, other):
        return (self.lhs, self.rhs, self.dot) == (other.lhs, other.rhs, other.dot)

    def __repr__(self):
        processedRightHandSide = self.rhs[:self.dot]
        unprocessedRightHandSide = self.rhs[self.dot:]
        return f"[{self.lhs}{unicode.rightArrow}{processedRightHandSide}{unicode.dot}{unprocessedRightHandSide}]"

def epsilon_closure(start_item, grammar):
    
    lookahead_sets = defaultdict(set)
    lookahead_sets[start_item] = set(start_item.lookahead)

    worklist = [start_item]

    while worklist:

        item = worklist.pop()
        current_lookahead = lookahead_sets[item]

        marked_symbol = item.next_symbol()
        if marked_symbol in grammar.nonTerminals:
            right_context = item.advance().get_right_context()

            for rhs in grammar.delta[marked_symbol]:
                lookahead = grammar.first1(right_context)

                if unicode.epsilon in lookahead:
                    lookahead.remove(unicode.epsilon)
                    lookahead |= current_lookahead

                new_item = LR1Item(marked_symbol, rhs)
        
                if not lookahead <= lookahead_sets[new_item]:
                    lookahead_sets[new_item] |= lookahead
                    worklist.append(new_item)
                    updated = True


    return lookahead_sets

def build_canonical_LR1_automaton(grammar):
    start_item = LR1Item("S'", (grammar.startSymbol,), lookahead={"$"})
    
    action_table = defaultdict(lambda : defaultdict(lambda : None))
    states = dict()
    transition = defaultdict(lambda: defaultdict(int))
    states[0] = epsilon_closure(start_item, grammar)
    
    next_id = 0
    worklist = [0]
    next_id += 1

    while worklist:
        state = worklist.pop()

        for item, lookahead_set in states[state].items():
            if item.is_complete():
                for symbol in lookahead_set:
                    action_table[state][symbol] = item

            for symbol in lookahead_set:
                if concat1(grammar.first1(item.get_right_context()), {symbol}):
                    action_table[state][symbol] = "SHIFT"

            transition[state][item.next_symbol()] = next_id
            states[next_id] = epsilon_closure(item.advance(), grammar)
            if not next_id in worklist:
                worklist.append(next_id)
            next_id += 1
    






