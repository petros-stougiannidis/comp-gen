from specification import unicode
from specification.grammar import concat1
from specification.item import LR1Item
from formatting.print import Sequence
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
    worklist = []

    for item in items:
        closure.add(item)
        worklist.append(item)

    while worklist:
        item = worklist.pop()
        A = item.next_symbol()
        if A in grammar.non_terminals:
            right_context = item.advance().get_right_context()
            for rhs in grammar.delta[A]:
                lookahead = concat1(grammar.first1(right_context), item.lookahead)
                new_item = LR1Item(A, rhs, lookahead=lookahead)
                if closure.add(new_item):
                    worklist.append(new_item)
    return closure

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
        if not isinstance(other, LR1State):
            return False
        return self.identity == other.identity

    def __iter__(self):
        return self.items()

class LR1Parser:
    def __init__(self, grammar):
        self.grammar = grammar
        self.states, self.goto = self.canonical_LR1_automaton()
        self.action_table = self.action_table()

    def canonical_LR1_automaton(self):
        grammar = self.grammar
        states = set()
        transition = defaultdict(lambda: defaultdict(lambda: None))
        start_items = [LR1Item(grammar.start_symbol, rhs, lookahead={'$'}) for rhs in grammar.delta[grammar.start_symbol]]

        self.start_state = LR1State(start_items, grammar)
        worklist = [self.start_state]

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

    # TODO: change action specification
    def action_table(self):
        grammar = self.grammar
        action_table = defaultdict(lambda: defaultdict(set))

        for state in self.states:
            for terminal in grammar.terminals:
                for item in state:     
                    if item.is_complete() and terminal in item.lookahead:
                        action_table[state][terminal].add(("reduce", item))

                    if  item.next_symbol() in grammar.terminals \
                        and terminal in concat1(grammar.first1(item.get_right_context()), item.lookahead):

                        action_table[state][terminal].add(("shift", terminal))

        return action_table

    def LR1_conflicts(self):
        conflicts = []

        for state in self.states:
            for terminal in self.grammar.terminals:
                actions = self.action_table[state][terminal]
                if len(actions) > 1:
                    conflicts.append((state, terminal, actions))

        return conflicts

    def print_LR1_conflicts(self):
        conflicts = self.LR1_conflicts()
        for state, terminal, actions in conflicts:
            print(f"Conflict in state {id(state)} on '{terminal}':")
            for action in actions:
                print(f"  {action}")
            print()

    # TODO: implement
    def patch(self, precedences):
        precedence = {}
        associativity = {}

        for level, (assoc, operators) in enumerate(precedences):
            for op in operators:
                precedence[op] = level
                associativity[op] = assoc

        for state, terminal, actions in self.LR1_conflicts():
            shifts = [a for a in actions if a[0] == "shift"]
            reduces = [a for a in actions if a[0] == "reduce"]

            # only handle shift/reduce conflicts
            if len(shifts) == 1 and len(reduces) == 1:
                shift = shifts[0]
                reduce = reduces[0]

                shift_op = terminal
                reduce_item = reduce[1]
                reduce_op = self.get_rightmost_terminal(reduce_item)

                if shift_op not in precedence or reduce_op not in precedence:
                    continue  # cannot resolve

                if precedence[shift_op] > precedence[reduce_op]:
                    chosen = shift
                elif precedence[shift_op] < precedence[reduce_op]:
                    chosen = reduce
                else:
                    # same precedence → associativity
                    assoc = associativity[shift_op]
                    if assoc == "left":
                        chosen = reduce
                    elif assoc == "right":
                        chosen = shift
                    else:
                        continue  # nonassoc → leave conflict

                # patch table
                self.action_table[state][terminal] = {chosen}

    def get_rightmost_terminal(self, item):
        for symbol in reversed(item.rhs):
            if symbol in self.grammar.terminals:
                return symbol
        return None

    def parse2(self, tokens):
        final_reduction = LR1Item(self.grammar.artificial_start_symbol, self.grammar.original_start_symbol, dot=1, lookahead={'$'})
        tokens = list(tokens)
        
        i = 0
        stack = [self.start_state]
        while True:
            current_state = stack[-1]

            token = tokens[i].type

            actions = self.action_table[current_state][token]
            if not actions:
                raise SyntaxError(f"Unexpected token {token} in state {id(current_state)}")

            action = next(iter(actions)) 
            

            if action[0] == "shift":
                stack.append(self.goto[current_state][token])
                i += 1 
                continue

            elif action[0] == "reduce":# and any([item.is_complete() for item in current_state]):
                
                item = action[1]
                if item == final_reduction:
                    return True
                
                for _ in range(len(item.rhs)):
                    stack.pop()
                stack.append(self.goto[stack[-1]][item.lhs])
                continue

        return False

    def get_action(self, current_state, token):
        actions = self.action_table[current_state][token]
        if not actions:
            raise SyntaxError(f"Unexpected token {token} in state {id(current_state)}")
        return next(iter(actions)) 

    def parse(self, tokens):
        final_reduction = LR1Item(self.grammar.artificial_start_symbol, self.grammar.original_start_symbol, dot=1, lookahead={'$'})
        stack = [self.start_state]

        for token in tokens:
            current_state = stack[-1]
            token = token.type
            
            action = self.get_action(current_state, token)
            while action[0] == "reduce":
                item = action[1]
                if item == final_reduction:
                    return True
                
                for _ in range(len(item.rhs)):
                    stack.pop()
                stack.append(self.goto[stack[-1]][item.lhs])
                current_state = stack[-1]
                action = self.get_action(current_state, token)
            
            if action[0] == "shift":
                stack.append(self.goto[current_state][token])
                current_state = stack[-1]
                continue                
            
        return False