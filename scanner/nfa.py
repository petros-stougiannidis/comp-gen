import os
import graphviz
import tempfile

class NFA:
    def __init__(self, start_states, final_states, transitions):
        self.start_states = start_states
        self.final_states = final_states
        self.transitions = transitions

    def transition(self, current_states, symbol):
        result = set()
        for state in current_states:
            for symbol_set, destination_states in self.transitions[state].items():
                if symbol in symbol_set:
                    result |= destination_states
                    # TODO: investigate this break
                    # break
        return result

    def accepts(self, word):
        current_states = self.start_states
        for s in word:
            current_states = self.transition(current_states, s)
        return any(state in self.final_states for state in current_states)