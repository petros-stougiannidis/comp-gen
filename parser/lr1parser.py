from specification import unicode
from specification.item import LR1Item
from parser.lr1_state import LR1State
from formatting.print import Sequence
from collections import defaultdict

class Shift:
    def __init__(self, terminal):
        self.terminal = terminal

    def __eq__(self, other):
        return isinstance(other, Shift) and self.terminal == other.terminal

    def __hash__(self):
        return hash(self.terminal)

    def __str__(self):
        return f'Shift: {self.terminal}'

class Reduction:
    def __init__(self, item):
        self.item = item

    def __eq__(self, other):
        return isinstance(other, Reduction) and self.item == other.item

    def __hash__(self):
        return hash(self.item)

    def __str__(self):
        return f'Reduce: {self.item}'

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

        self.start_state = LR1State(start_items, grammar, state_id=0)
        state_id = 1
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
                new_state = LR1State(core, grammar, state_id)
                state_id += 1
                transition[state][symbol] = new_state
                if new_state not in states:
                    worklist.append(new_state)

        return states, transition

    def action_table(self):
        grammar = self.grammar
        action_table = defaultdict(lambda: defaultdict(set))

        for state in self.states:
            for item in state:
                if item.is_complete():
                    for terminal in item.lookahead:
                        action_table[state][terminal].add(Reduction(item))

                symbol = item.next_symbol()
                if symbol in self.grammar.terminals:
                    action_table[state][symbol].add(Shift(symbol))

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
        if conflicts:
            print("Total number of conflics:", len(conflicts))
        for state, terminal, actions in conflicts:
            print(f"Conflict in state {state.id} on terminal '{terminal}':")
            for action in actions:
                print(f"\t• {action}")
            print()

    # TODO: implement myself
    def patch(self, precedences):
        precedence = {}
        associativity = {}

        for level, (assoc, operators) in enumerate(precedences):
            for op in operators:
                precedence[op] = level
                associativity[op] = assoc

        for state, terminal, actions in self.LR1_conflicts():
            shifts = [action for action in actions if isinstance(action, Shift)]
            reduces = [action for action in actions if isinstance(action, Reduction)]

            # only handle shift/reduce conflicts
            if len(shifts) == 1 and len(reduces) == 1:
                shift = shifts[0]
                reduce = reduces[0]

                shift_operator = terminal
                reduce_operator = self.get_rightmost_terminal(reduce.item)

                if shift_operator not in precedence or reduce_operator not in precedence:
                    continue  # cannot resolve

                if precedence[shift_operator] > precedence[reduce_operator]:
                    chosen = shift
                elif precedence[shift_operator] < precedence[reduce_operator]:
                    chosen = reduce
                else:
                    # same precedence → associativity
                    if associativity[shift_operator] == "left":
                        chosen = reduce
                    elif associativity[shift_operator] == "right":
                        chosen = shift
                    else:
                        continue  # leave conflict

                # patch table
                self.action_table[state][terminal] = {chosen}

    def get_rightmost_terminal(self, item):
        for symbol in reversed(item.rhs):
            if symbol in self.grammar.terminals:
                return symbol
        return None

    def get_action(self, current_state, token):
        actions = self.action_table[current_state][token]
        if not actions:
            raise SyntaxError(f"Unexpected token: {token} in state {current_state.id}")
        return next(iter(actions)) 

    def parse(self, tokens):
        final_reduction = LR1Item(self.grammar.artificial_start_symbol, (self.grammar.original_start_symbol,), dot=1, lookahead={'$'})
        parsing_stack, semantic_stack = [self.start_state], []

        for token in tokens:

            current_state = parsing_stack[-1]
            token, value = token.type, token.value
            
            action = self.get_action(current_state, token)
            
            while isinstance(action, Reduction):
                reduction = action
                if reduction.item == final_reduction:
                    return True, semantic_stack

                children = []
                
                for _ in range(len(reduction.item.rhs)):
                    parsing_stack.pop()
                    children.append(semantic_stack.pop())
                
                children.reverse()
                
                if callback := self.grammar.actions[(reduction.item.lhs, reduction.item.rhs)]:
                    semantic_stack.append(callback(children))
                else:
                    semantic_stack.append(children)
                
                parsing_stack.append(self.goto[parsing_stack[-1]][reduction.item.lhs])
                current_state = parsing_stack[-1]
                action = self.get_action(current_state, token)
            
            if isinstance(action, Shift):
                parsing_stack.append(self.goto[current_state][token])
                semantic_stack.append(value)
                current_state = parsing_stack[-1]
                continue                
            
        return False, semantic_stack