from abc import ABC, abstractmethod
from collections import defaultdict

from scanner.nfa import NFA

class Regex(ABC):
    _counter = 0

    def __init__(self):
        self.first = set()
        self.last = set()
        self.empty = False
        self.next = set()
        self.id = Regex._counter
        Regex._counter += 1

    @abstractmethod
    def berry_sethi(self, next_states, transitions):
        pass

    def to_nfa(self):
        start_state = f"start_{self.id}"
        transitions = defaultdict(lambda: defaultdict(set))

        final_states = set(self.last)
        if self.empty:
            final_states.add(start_state)

        for leaf in self.first:
            transitions[start_state][leaf.label].add(leaf)

        self.berry_sethi(self.next, transitions)

        return NFA({start_state}, final_states, transitions)

class Symbol(Regex):
    def __init__(self, label):
        super().__init__()
        self.label = label
        self.empty = False
        self.first = {self}
        self.last = {self}

    def berry_sethi(self, next_states, transitions):
        self.next = next_states
        for leaf in next_states:
            transitions[self][leaf.label].add(leaf)

    def __repr__(self):
        return f"{self.label};{self.id}"

    def __str__(self):
        return self.label

class EmptyWord(Regex):
    def __init__(self):
        super().__init__()
        self.empty = True
        self.first = set()
        self.last = set()

    def berry_sethi(self, next_states, transitions):
        self.next = next_states

    def __str__(self):
        return "ε"

class UnaryExpression(Regex):
    def __init__(self, sub):
        super().__init__()
        self.sub = sub

class BinaryExpression(Regex):
    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right

class Concatenation(BinaryExpression):
    def __init__(self, left, right):
        super().__init__(left, right)
        self.empty = left.empty and right.empty
        self.first = left.first | (right.first if left.empty else set())
        self.last = right.last | (left.last if right.empty else set())

    def berry_sethi(self, next_states, transitions):
        self.next = next_states
        self.left.berry_sethi(
            self.right.first | (next_states if self.right.empty else set()),
            transitions,
        )
        self.right.berry_sethi(next_states, transitions)

    def __str__(self):
        return f'{self.left}•{self.right}'

class Union(BinaryExpression):
    def __init__(self, left, right):
        super().__init__(left, right)
        self.empty = left.empty or right.empty
        self.first = left.first | right.first
        self.last = left.last | right.last

    def berry_sethi(self, next_states, transitions):
        self.next = next_states
        self.left.berry_sethi(next_states, transitions)
        self.right.berry_sethi(next_states, transitions)

    def __str__(self):
        return f'({self.left}|{self.right})'

class KleeneClosure(UnaryExpression):
    def __init__(self, sub):
        super().__init__(sub)
        self.empty = True
        self.first = sub.first
        self.last = sub.last

    def berry_sethi(self, next_states, transitions):
        self.next = next_states
        self.sub.berry_sethi(self.sub.first | next_states, transitions)

    def __str__(self):
        return f'({self.sub})*'

class Plus(UnaryExpression):
    def __init__(self, sub):
        super().__init__(sub)
        self.empty = sub.empty
        self.first = sub.first
        self.last = sub.last

    def berry_sethi(self, next_states, transitions):
        self.next = next_states
        self.sub.berry_sethi(self.sub.first | next_states, transitions)

    def __str__(self):
        return f'({self.sub})+'

class Optional(UnaryExpression):
    def __init__(self, sub):
        super().__init__(sub)
        self.empty = True
        self.first = sub.first
        self.last = sub.last

    def berry_sethi(self, next_states, transitions):
        self.next = next_states
        self.sub.berry_sethi(next_states, transitions)

    def __str__(self):
        return f'({self.sub})?'

